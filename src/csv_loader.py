import sys
import os
from pathlib import Path
import pandas as pd
import glob
import re
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

# We'll scan for all CSV/XLSX files in the input folder (filename validation happens per-file)

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

# Gather all .csv and .xlsx files in the input folder
input_files = []
input_files.extend(glob.glob(str(input_folder / "*.csv")))
input_files.extend(glob.glob(str(input_folder / "*.xlsx")))
    
if not input_files:
    print("No CSV input files found.")
    log_action("No CSV input files found.")
else:
    for input_file in input_files:
        filename = os.path.basename(input_file)

        print(f"Processing {filename} ...")
        log_action(f"Processing {filename} ...")

        # Strict filename validation: exactly one alphabetic run of length 2, rest digits/underscores
        base = os.path.splitext(filename)[0]
        alpha_runs = re.findall(r"[A-Za-z]+", base)
        if len(alpha_runs) != 1 or len(alpha_runs[0]) != 2:
            msg = f"Skipping {filename}: expected exactly one 2-letter alpha token in filename (e.g. 861_TV_257)"
            print("⚠️", msg)
            log_action(msg)
            continue
        code = alpha_runs[0].lower()
        rest = re.sub(r"[A-Za-z]+", "", base)
        if not re.fullmatch(r"[0-9_]+", rest):
            msg = f"Skipping {filename}: filename contains unexpected characters besides the 2-letter code"
            print("⚠️", msg)
            log_action(msg)
            continue

        # code becomes the GI90 value used in table name; we keep Oracle behavior of uppercasing table identifiers
        gi90_value = code
        table_name = f"mis_{gi90_value}_ext"

        try:
            # Use appropriate pandas reader and coerce values to strings for consistency
            if filename.endswith(".csv"):
                df = pd.read_csv(input_file, encoding="utf-8-sig", dtype=str)
            elif filename.endswith(".xlsx"):
                df = pd.read_excel(input_file, dtype=str)
            else:
                log_action(f"Skipped unknown file format: {filename}")
                continue

            # Normalize column names to be case-insensitive and strip BOM/whitespace
            df.columns = (
                df.columns.astype(str)
                .str.strip()
                .str.replace('\ufeff', '', regex=False)
                .str.upper()
            )

            # Validate required columns exist after normalization (GI01 and GI03 are required)
            required = {"GI01", "GI03"}
            found = set(df.columns.tolist())
            if not required.issubset(found):
                msg = f"Required columns missing in {filename}. Found columns: {df.columns.tolist()}"
                print("❌", msg)
                log_action(msg)
                continue

            # Ensure all data values are strings (consistent with table creation of VARCHAR2)
            df = df.astype(str)

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
            # Validate SB00 values: strict format ^@\d{8}$
            # df columns have been normalized to uppercase earlier
            orig_columns = df.columns.tolist()
            if 'SB00' not in df.columns:
                msg = f"SB00 column missing in {filename}; marking all rows as not loaded and skipping DB insert"
                print("⚠️", msg)
                log_action(msg)
                # mark all as not loaded and save annotated file
                df['LOADED'] = 'N'
                ext = ".csv" if filename.endswith(".csv") else ".xlsx"
                new_filename = f"{ccc}_{ttt}_{gi90_value}{ext}"
                dest_file = os.path.join(completed_folder, new_filename)
                if ext == '.csv':
                    df.to_csv(dest_file, index=False, encoding='utf-8-sig')
                else:
                    df.to_excel(dest_file, index=False)
                log_action(f"Saved annotated (no SB00) file: {new_filename}")
                # Remove the original input file after saving annotated copy
                try:
                    os.remove(input_file)
                    log_action(f"Removed original input file: {filename}")
                except Exception as e:
                    log_action(f"Failed to remove original input file {filename}: {e}")
            else:
                sb = df['SB00'].fillna('').astype(str).str.strip()
                valid_mask = sb.str.match(r'^\d*$')  # placeholder, will replace next line
                # strict pattern: @ followed by 8 digits
                valid_mask = sb.str.match(r'^@\d{8}$')

                df_to_insert = df[valid_mask].copy()
                num_valid = len(df_to_insert)
                num_invalid = len(df) - num_valid

                # Insert only valid rows (if any)
                if num_valid > 0:
                    cols = ','.join([f'"{col}"' for col in orig_columns])
                    placeholders = ','.join([f":{i+1}" for i in range(len(orig_columns))])
                    insert_sql = f'INSERT INTO "{table_name.upper()}" ({cols}) VALUES ({placeholders})'
                    cur.executemany(insert_sql, df_to_insert[orig_columns].values.tolist())
                    print(f"✅ Loaded {num_valid} rows into {table_name}")
                    log_action(f"Loaded {num_valid} rows into {table_name}")
                else:
                    print(f"⚠️ No valid SB00 rows to insert for {filename}")
                    log_action(f"No valid SB00 rows to insert for {filename}")

                # Annotate original dataframe with LOADED column and save to completed folder
                df['LOADED'] = valid_mask.map({True: 'Y', False: 'N'})
                ext = ".csv" if filename.endswith(".csv") else ".xlsx"
                new_filename = f"{ccc}_{ttt}_{gi90_value}{ext}"
                dest_file = os.path.join(completed_folder, new_filename)
                if ext == '.csv':
                    df.to_csv(dest_file, index=False, encoding='utf-8-sig')
                else:
                    df.to_excel(dest_file, index=False)
                log_action(f"Saved annotated file {new_filename}: {num_valid} loaded, {num_invalid} skipped")
                print(f"Saved annotated file {new_filename}: {num_valid} loaded, {num_invalid} skipped")
                # Remove the original input file after saving annotated copy
                try:
                    os.remove(input_file)
                    log_action(f"Removed original input file: {filename}")
                except Exception as e:
                    log_action(f"Failed to remove original input file {filename}: {e}")

        except Exception as e:
            err_msg = f"Error processing {filename}: {e}"
            print("❌", err_msg)
            log_action(err_msg)
            # continue to next file without aborting entire run
            continue

    conn.commit()

cur.close()
conn.close()
print("🎉 All done!")
log_action("All done!")
log_action("===== CSV Loader script finished =====")
