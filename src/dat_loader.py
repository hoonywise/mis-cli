import logging
import sys
from datetime import datetime
from pathlib import Path
import shutil
import os

# Add the parent directory to Python path so we can import from libs
sys.path.append(str(Path(__file__).parent.parent))
from libs.layout_definitions import LAYOUTS                   # ✅ Works with sys.path
from libs.oracle_db_connector import get_connection          # ✅ Works with sys.path

# --- Setup paths relative to CLI structure ---
BASE_DIR = os.environ.get("MIS_INSTANCE_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
DATA_DIR = Path(BASE_DIR) / "dat_loader" / "pending"
LOG_DIR = Path(BASE_DIR) / "dat_loader" / "log"
COMPLETED_DIR = Path(BASE_DIR) / "dat_loader" / "completed"
MASTER_LOG = os.path.join(BASE_DIR, "mis-cli.log")
HISTORY_LOG = os.path.join(BASE_DIR, "history.log")

# Create directories if they don't exist
LOG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
COMPLETED_DIR.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"dat_loader_{timestamp}.log"
CHECKPOINT_FILE = LOG_DIR / "loader_checkpoint.txt"
LOAD_MOST_RECENT_FIRST = False

def log_action(action):
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"{timestamp} - {action}\n"
    with open(MASTER_LOG, "a", encoding="utf-8") as f:
        f.write(message)
    with open(HISTORY_LOG, "a", encoding="utf-8") as f:
        f.write(message)

# Remove any existing handlers first
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    filename=str(LOG_FILE),
    filemode="w",
    format="%(asctime)s %(levelname)s: %(message)s",
    level=logging.INFO
)

# Add console handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
logging.getLogger().addHandler(console)

logging.info("Logging initialized. Log file: %s", LOG_FILE)
log_action(f"Logging initialized. Log file: {LOG_FILE}")

CHECKPOINT_FILE = LOG_DIR / "loader_checkpoint.txt"

# --- Helper functions ---

def parse_line(line, layout):
    parsed = {}
    line_len = len(line)
    for name, start, end in layout:
        if start < line_len:
            parsed[name] = line[start:min(end, line_len)].strip()
        else:
            parsed[name] = ""
    return parsed

def create_indexes(cursor, table_name, layout):
    """Create indexes on key columns if they exist in the layout."""
    index_fields = [
        "GI01_DISTRICT_COLLEGE_ID",
        "GI03_TERM_ID",
        "SB00_STUDENT_ID",
        "EB00_EMPLOYEE_ID"
    ]
    for col in index_fields:
        if any(col == name for name, _, _ in layout):
            idx_name = f"IDX_{table_name}_{col}"
            try:
                cursor.execute(f'CREATE INDEX {idx_name} ON {table_name} ({col})')
                logging.info(f"Created index {idx_name} on {table_name}({col})")
                log_action(f"Created index {idx_name} on {table_name}({col})")
            except Exception as e:
                if "already exists" not in str(e):
                    logging.error(f"Index creation failed for {idx_name}: {e}")
                    log_action(f"Index creation failed for {idx_name}: {e}")

def ensure_table_exists(cursor, table_name, layout):
    """Create table if it does not exist."""
    cursor.execute("""
        SELECT COUNT(*) FROM all_tables 
        WHERE table_name = :1 AND owner = USER
    """, [table_name.upper()])
    exists = cursor.fetchone()[0] > 0
    if not exists:
        columns = ', '.join([
            f'{name} VARCHAR2({end-start})'
            for name, start, end in layout
        ])
        create_sql = f'CREATE TABLE {table_name} ({columns})'
        cursor.execute(create_sql)
        logging.info(f"Created table {table_name}")
        log_action(f"Created table {table_name}")
        create_indexes(cursor, table_name, layout)

def delete_existing_term(cursor, table_name, term_id):
    """Delete existing records for the term in the table."""
    # Assumes GI03_TERM_ID is always present and is the term column
    try:
        cursor.execute(
            f"DELETE FROM {table_name} WHERE GI03_TERM_ID = :1",
            [term_id]
        )
        logging.info(f"Deleted existing records for term {term_id} in {table_name}")
        log_action(f"Deleted existing records for term {term_id} in {table_name}")
    except Exception as e:
        logging.warning(f"Could not delete records for term {term_id} in {table_name}: {e}")
        log_action(f"Could not delete records for term {term_id} in {table_name}: {e}")

def insert_rows(cursor, table_name, layout, rows):
    """Insert parsed rows into the table."""
    columns = [name for name, _, _ in layout]
    col_str = ', '.join(columns)
    val_str = ', '.join([f':{i+1}' for i in range(len(columns))])
    insert_sql = f"INSERT INTO {table_name} ({col_str}) VALUES ({val_str})"
    for row in rows:
        values = [row.get(col, '') for col in columns]
        cursor.execute(insert_sql, values)

def load_file(filename, layout, conn, resume_line=0):
    cursor = conn.cursor()
    table_name = f"MIS_{filename.stem[-2:]}"
    term_id = filename.stem[3:6]
    ensure_table_exists(cursor, table_name, layout)
    delete_existing_term(cursor, table_name, term_id)
    rows = []
    expected_len = layout[-1][2]
    short_line_warned = False  # Track if we've warned for this file
    with open(filename, "r") as f:
        for i, line in enumerate(f):
            if i < resume_line:
                continue
            if len(line) < expected_len and not short_line_warned:
                logging.warning(
                    f"{filename} appears to use an older format: line length {len(line)} (expected {expected_len}). "
                    "All missing fields will be set to blank for this file."
                )
                log_action(
                    f"{filename} appears to use an older format: line length {len(line)} (expected {expected_len}). "
                    "All missing fields will be set to blank for this file."
                )
                short_line_warned = True
            row = parse_line(line, layout)
            rows.append(row)
            if len(rows) >= 1000:
                insert_rows(cursor, table_name, layout, rows)
                conn.commit()
                rows = []
                with open(CHECKPOINT_FILE, "w") as cp:
                    cp.write(f"{filename},{i}\n")
    if rows:
        insert_rows(cursor, table_name, layout, rows)
        conn.commit()
    cursor.close()

def main():
    log_action("===== DAT Loader script started =====")
# Resume logic (commented out for future use)
# resume_file, resume_line = None, 0
# if Path(CHECKPOINT_FILE).exists():
#     with open(CHECKPOINT_FILE) as cp:
#         line = cp.read().strip()
#         if line:
#             resume_file, resume_line = line.split(",")
#             resume_line = int(resume_line)

    files = sorted(
        [f for f in DATA_DIR.glob("U8*.*") if f.suffix.lower() == ".dat"],
        reverse=LOAD_MOST_RECENT_FIRST
    )

    for file in files:
        layout_key = file.stem[-2:]
        if layout_key in ("TX", "CC"):
            logging.info(f"Skipping {file.name}: file type {layout_key} is ignored.")
            log_action(f"Skipping {file.name}: file type {layout_key} is ignored.")
            continue

        layout = LAYOUTS.get(layout_key)
        if not layout:
            logging.warning(f"Skipping {file.name}: no layout found.")
            log_action(f"Skipping {file.name}: no layout found.")
            continue

        # Always reload the entire file if resuming
        start_line = 0
        logging.info(f"Loading {file.name} (starting at line {start_line})...")
        log_action(f"Loading {file.name} (starting at line {start_line})...")
        conn = get_connection("dwh") 
        try:
            load_file(file, layout, conn, resume_line=start_line)
            # After successful load, move file to completed
            try:
                shutil.move(str(file), COMPLETED_DIR / file.name)
                logging.info(f"Moved {file.name} to completed folder.")
                log_action(f"Moved {file.name} to completed folder.")
                # Remove checkpoint file if it exists
                if Path(CHECKPOINT_FILE).exists():
                    Path(CHECKPOINT_FILE).unlink()
            except Exception as e:
                logging.error(f"Failed to move {file.name} to completed: {e}")
                log_action(f"Failed to move {file.name} to completed: {e}")
        except Exception as e:
            logging.error(f"Error loading {file.name}: {e}")
            log_action(f"Error loading {file.name}: {e}")
            log_action("===== DAT Loader script finished with error =====")
            break  # Stop on error so you can resume later
        finally:
            conn.close()
    log_action("===== DAT Loader script finished =====")
        
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Batch loader interrupted by user (Ctrl+C). Exiting gracefully.")
        log_action("Batch loader interrupted by user (Ctrl+C). Exiting gracefully.")
        log_action("===== DAT Loader script finished with interruption =====")
        print("\nBatch loader interrupted by user. Exiting gracefully.")
    finally:
        for handler in logging.root.handlers:
            handler.flush()
        sys.exit(0)