import logging
import sys
from datetime import datetime
from pathlib import Path
import shutil
import csv
import os

# Add the parent directory to Python path so we can import from libs
sys.path.append(str(Path(__file__).parent.parent))
from libs.oracle_db_connector import get_connection

# --- Setup paths relative to CLI structure ---
BASE_DIR = os.environ.get("MIS_INSTANCE_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
DATA_DIR = Path(BASE_DIR) / "error_report_loader" / "pending"
LOG_DIR = Path(BASE_DIR) / "error_report_loader" / "log"
COMPLETED_DIR = Path(BASE_DIR) / "error_report_loader" / "completed"
MASTER_LOG = os.path.join(BASE_DIR, "mis-cli.log")
HISTORY_LOG = os.path.join(BASE_DIR, "history.log")

# Create directories if they don't exist
LOG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
COMPLETED_DIR.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"error_report_loader_{timestamp}.log"
CHECKPOINT_FILE = LOG_DIR / "error_loader_checkpoint.txt"

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

TABLE_NAME = "MIS_ERROR_REPORTS"

# --- Helper functions ---
def ensure_table_exists(cursor, columns):
    cursor.execute("""
        SELECT COUNT(*) FROM all_tables 
        WHERE table_name = :1 AND owner = USER
    """, [TABLE_NAME.upper()])
    exists = cursor.fetchone()[0] > 0
    
    if not exists:
        # Create new table
        col_defs = [f'{col} VARCHAR2(4000)' for col in columns]
        create_sql = f'CREATE TABLE {TABLE_NAME} ({", ".join(col_defs)})'
        cursor.execute(create_sql)
        logging.info(f"Created table {TABLE_NAME}")
        log_action(f"Created table {TABLE_NAME}")
    else:
        # Check for missing columns and add them
        cursor.execute("""
            SELECT column_name FROM all_tab_columns 
            WHERE table_name = :1 AND owner = USER
        """, [TABLE_NAME.upper()])
        existing_columns = {row[0] for row in cursor.fetchall()}
        
        for col in columns:
            if col.upper() not in existing_columns:
                alter_sql = f'ALTER TABLE {TABLE_NAME} ADD ({col} VARCHAR2(4000))'
                cursor.execute(alter_sql)
                logging.info(f"Added column {col} to existing table {TABLE_NAME}")
                log_action(f"Added column {col} to existing table {TABLE_NAME}")

def insert_rows(cursor, columns, rows):
    col_str = ', '.join(columns)
    val_str = ', '.join([f':{i+1}' for i in range(len(columns))])
    insert_sql = f"INSERT INTO {TABLE_NAME} ({col_str}) VALUES ({val_str})"
    for row in rows:
        cursor.execute(insert_sql, row)

def process_file(file_path, resume_line=0):
    report_no = int(file_path.stem.split('_')[1])
    activity_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(file_path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)
        # Put ACTIVITY_DATE at the end (far right)
        columns = ['REPORT_NO'] + [h.replace(' ', '_').upper() for h in headers] + ['ACTIVITY_DATE']
        
        # Use centralized database connector for DWH connection
        conn = get_connection("dwh")
        if not conn:
            logging.error("❌ Failed to connect to Data Warehouse database")
            log_action("❌ Failed to connect to Data Warehouse database")
            return None
            
        cursor = conn.cursor()
        ensure_table_exists(cursor, columns)
        
        term_id_idx = headers.index('Term Id')
        college_id_idx = headers.index('College Id')
        
        # Collect all unique (Term Id, College Id) pairs in the file
        unique_pairs = set()
        term_id_for_folder = None
        for row in reader:
            term_id = row[term_id_idx].strip()
            college_id = row[college_id_idx].strip()
            unique_pairs.add((term_id, college_id))
            if term_id_for_folder is None:
                term_id_for_folder = term_id
        
        # Reset reader to beginning after collecting pairs
        csvfile.seek(0)
        next(reader)  # skip header again
        
        for term_id, college_id in unique_pairs:
            cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE REPORT_NO = :1 AND TERM_ID = :2 AND COLLEGE_ID = :3", [report_no, term_id, college_id])
            logging.info(f"Deleted existing records for REPORT_NO={report_no}, TERM_ID={term_id}, COLLEGE_ID={college_id}")
            log_action(f"Deleted existing records for REPORT_NO={report_no}, TERM_ID={term_id}, COLLEGE_ID={college_id}")
        conn.commit()
        
        # Now insert with activity date at the end
        rows = []
        for i, row in enumerate(reader):
            if i < resume_line:
                continue
            # Add REPORT_NO at beginning and ACTIVITY_DATE at the end
            rows.append([report_no] + row + [activity_date])
            if len(rows) >= 1000:
                insert_rows(cursor, columns, rows)
                conn.commit()
                rows = []
                with open(CHECKPOINT_FILE, "w") as cp:
                    cp.write(f"{file_path},{i}\n")
                    
        if rows:
            insert_rows(cursor, columns, rows)
            conn.commit()
            
        cursor.close()
        conn.close()
        
    logging.info(f"Loaded {file_path.name} into {TABLE_NAME} with activity date {activity_date}")
    log_action(f"Loaded {file_path.name} into {TABLE_NAME} with activity date {activity_date}")
    return term_id_for_folder

def main():
    # Check if data directory exists and has files
    if not DATA_DIR.exists():
        logging.error(f"Data directory not found: {DATA_DIR}")
        log_action(f"Data directory not found: {DATA_DIR}")
        print("Please create the data directory and place your error_*.csv files there")
        return
    
    resume_file = None
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE) as cp:
            line = cp.read().strip()
            if line:
                resume_file, _ = line.split(",")
                
    files = sorted(DATA_DIR.glob("error_*.csv"))
    
    if not files:
        logging.info("No error_*.csv files found in data directory")
        log_action("No error_*.csv files found in data directory")
        print(f"No error_*.csv files found in: {DATA_DIR}")
        return
    
    print(f"Starting error report loader...")
    print(f"Reading from: data/error_report_loader/pending")
    print(f"Writing to: Data Warehouse database")
    print(f"Completed files moved to: data/error_report_loader/completed")
    
    for file in files:
        if resume_file and str(file) != resume_file:
            continue
        start_line = 0
        try:
            logging.info(f"Processing {file.name} (starting at line {start_line})...")
            log_action(f"Processing {file.name} (starting at line {start_line})...")
            process_file(file, resume_line=start_line)
            
            # --- Move file directly to completed folder ---
            shutil.move(str(file), COMPLETED_DIR / file.name)
            logging.info(f"Moved {file.name} to completed folder.")
            log_action(f"Moved {file.name} to completed folder.")
                
            if CHECKPOINT_FILE.exists():
                CHECKPOINT_FILE.unlink()
            resume_file = None
            
        except Exception as e:
            logging.error(f"Error processing {file.name}: {e}")
            log_action(f"Error processing {file.name}: {e}")
            break  # Stop on error so you can resume later
    
    print("\nError report loading completed successfully")
    print("Files processed and moved to completed folder")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Error report loader interrupted by user (Ctrl+C). Exiting gracefully.")
        print("\nError report loader interrupted by user. Exiting gracefully.")
    finally:
        for handler in logging.root.handlers:
            handler.flush()
        sys.exit(0)