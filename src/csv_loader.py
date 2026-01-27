import sys
import os
from pathlib import Path
import pandas as pd
import glob
import shutil
from datetime import datetime

BASE_DIR = os.environ.get("MIS_INSTANCE_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
MASTER_LOG = os.path.join(BASE_DIR, "mis-cli.log")
HISTORY_LOG = os.path.join(BASE_DIR, "history.log")

def log_action(action):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"{timestamp} - {action}\n"
    with open(MASTER_LOG, "a", encoding="utf-8") as f:
        f.write(message)
    with open(HISTORY_LOG, "a", encoding="utf-8") as f:
        f.write(message)

# Add the parent directory to Python path so we can import from libs
sys.path.append(str(Path(__file__).parent.parent))
from libs.oracle_db_connector import get_connection

# Correct data paths: mis-cli/data/sg_loader/input and completed
data_dir = Path(BASE_DIR) / "csv_loader"
input_folder = data_dir / "input"
completed_folder = data_dir / "completed"
os.makedirs(completed_folder, exist_ok=True)

# Patterns for both SG26 and SG29, CSV and XLSX
patterns = [
    str(input_folder / "*VR*.csv"),
    str(input_folder / "*VR*.xlsx"),
]

def table_exists(cur, table_name):
    cur.execute(
        "SELECT COUNT(*) FROM user_tables WHERE table_name = :tbl",
        {"tbl": table_name.upper()}
    )
    return cur.fetchone()[0] > 0

def create_table(cur, table_name, columns):
    col_defs = ', '.join([f'"{col}" VARCHAR2(4000)' for col in columns])
    sql = f'CREATE TABLE "{table_name.upper()}" ({col_defs})'
    cur.execute(sql)
    print(f"🆕 Created table {table_name}")
    log_action(f"Created table {table_name}")

log_action("===== CSV Loader script started =====")

conn = get_connection(section="dwh") # Use your actual section name here
if conn is None:
    print("❌ Could not connect to DWH database.") 
    log_action("Could not connect to DWH database.")
    sys.exit(1)
cur = conn.cursor()

# Gather all matching files
input_files = []
for pattern in patterns:
    input_files.extend(glob.glob(pattern))
    
if not input_files:
    print("No CSV input files found.")
    log_action("No CSV input files found.")
else:
    for input_file in input_files:
        filename = os.path.basename(input_file)

        print(f"Processing {filename} ...")
        log_action(f"Processing {filename} ...")
        # Use appropriate pandas reader
        if filename.endswith(".csv"):
            df = pd.read_csv(input_file)
        elif filename.endswith(".xlsx"):
            df = pd.read_excel(input_file)
        else:
            log_action(f"Skipped unknown file format: {filename}")
            continue

        # Get GI90 value from first row and set table name
        gi90_value = str(df['GI90'].iloc[0]).lower()
        table_name = f"mis_{gi90_value}_ext"

        if not table_exists(cur, table_name):
            create_table(cur, table_name, df.columns)

        # Assumes all rows in the file have the same CCC and TTT
        ccc = str(df['GI01'].iloc[0])
        ttt = str(df['GI03'].iloc[0])

        # Delete existing records for this campus/term
        delete_sql = f'''
            DELETE FROM "{table_name.upper()}"
            WHERE "GI01" = :ccc AND "GI03" = :ttt
        '''
        cur.execute(delete_sql, {"ccc": ccc, "ttt": ttt})
        print(f"🗑️ Deleted existing records for campus {ccc}, term {ttt}")
        log_action(f"Deleted existing records for campus {ccc}, term {ttt}")

        # Insert new records
        cols = ','.join([f'"{col}"' for col in df.columns])
        placeholders = ','.join([f":{i+1}" for i in range(len(df.columns))])
        insert_sql = f'INSERT INTO "{table_name.upper()}" ({cols}) VALUES ({placeholders})'
        cur.executemany(insert_sql, df.values.tolist())
        print(f"✅ Loaded {len(df)} rows into {table_name}")
        log_action(f"Loaded {len(df)} rows into {table_name}")

        # Move file to completed and rename based on CCC and TTT
        ext = ".csv" if filename.endswith(".csv") else ".xlsx"
        new_filename = f"{ccc}_{ttt}_{gi90_value}{ext}"
        dest_file = os.path.join(completed_folder, new_filename)
        shutil.move(input_file, dest_file)
        print(f"Moved and renamed {filename} to {new_filename}.")
        log_action(f"Moved and renamed {filename} to {new_filename}.")

    conn.commit()

cur.close()
conn.close()
print("🎉 All done!")
log_action("All done!")
log_action("===== CSV Loader script finished =====")