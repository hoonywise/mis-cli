import oracledb
import sys
import os
import re
import shutil
import csv
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from libs.oracle_db_connector import get_connection
from datetime import datetime

BASE_DIR = os.environ.get("MIS_INSTANCE_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
MASTER_LOG = os.path.join(BASE_DIR, "mis-cli.log")
HISTORY_LOG = os.path.join(BASE_DIR, "history.log")

csv_mode = False
if "--csv" in sys.argv:
    csv_mode = True
    sys.argv.remove("--csv")

def log_action(action):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"{timestamp} - {action}\n"
    with open(MASTER_LOG, "a", encoding="utf-8") as f:
        f.write(message)
    with open(HISTORY_LOG, "a", encoding="utf-8") as f:
        f.write(message)

# Usage: python gvprmis_export.py input.sql

def clean_folder(folder):
    """Delete all files and subfolders in the given folder, skipping locked items."""
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isdir(file_path):
            # Try to delete contents of subfolder, not the subfolder itself
            for subname in os.listdir(file_path):
                subpath = os.path.join(file_path, subname)
                try:
                    if os.path.isfile(subpath) or os.path.islink(subpath):
                        os.unlink(subpath)
                    elif os.path.isdir(subpath):
                        shutil.rmtree(subpath)
                except Exception as e:
                    print(f"Warning: Could not delete {subpath}: {e}")
                    log_action(f"Warning: Could not delete {subpath}: {e}")
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Warning: Could not delete {file_path}: {e}")
            log_action(f"Warning: Could not delete {file_path}: {e}")

if len(sys.argv) < 2:
    print("Usage: python gvprmis_export.py input.sql [param1=val1 param2=val2 ...]")
    log_action("Usage: python gvprmis_export.py input.sql [param1=val1 param2=val2 ...]")
    sys.exit(1)

sql_file = sys.argv[1]
param_pairs = sys.argv[2:]

# SQL file path (update to look in project root's sql folder)
sql_folder = os.path.join(os.path.dirname(__file__), "..", "sql")
if not os.path.isabs(sql_file):
    sql_file = os.path.join(sql_folder, sql_file)

# Parse parameters into a dict
params = {}
for pair in param_pairs:
    if '=' in pair:
        k, v = pair.split('=', 1)
        k = k.lstrip(':')  # Remove leading colon if present
        params[k] = v

# Read SQL from file
with open(sql_file, "r", encoding="utf-8") as f:
    sql = f.read()

# Substitute parameters in SQL (simple replacement: :param or {param})
for k, v in params.items():
    # Replace :param or {param} in SQL
    sql = re.sub(rf":{k}\b", f"'{v}'", sql)
    sql = sql.replace(f"{{{k}}}", v)

# Connect to database using oracle_db_connector
conn = get_connection("prod")
if not conn:
    print("❌ Failed to connect to Production database")
    log_action("❌ Failed to connect to Production database")
    sys.exit(1)

# Substitute parameters in SQL (simple replacement: :param or {param})
for k, v in params.items():
    sql = re.sub(rf":{k}\b", f"'{v}'", sql)
    sql = sql.replace(f"{{{k}}}", v)

# Check for any remaining :param variables
unbound_vars = re.findall(r":\w+", sql)
if unbound_vars:
    print(f"❌ Unbound SQL variables found: {', '.join(unbound_vars)}")
    log_action(f"❌ Unbound SQL variables found: {', '.join(unbound_vars)}")
    sys.exit(1)

cur = conn.cursor()
cur.execute("ALTER SESSION SET NLS_DATE_FORMAT = 'MM/DD/YY'")
cur.execute(sql)

# Output base folder - write directly to shared export folder
output_base = os.path.join(BASE_DIR, "shared_export")

# Read first row to extract file info
first_row = cur.fetchone()
if not first_row:
    print("No data returned from query.")
    log_action("No data returned from query.")
    sys.exit(1)

if csv_mode:
    # Expect first_row to be a tuple like (file_type, campus, term, ...)
    if len(first_row) < 3:
        print("First row does not contain enough columns for file info.")
        log_action("First row does not contain enough columns for file info.")
        sys.exit(1)
    file_type = str(first_row[0])
    campus = str(first_row[1])
    term = str(first_row[2])
    first_line = ",".join(str(col) for col in first_row)  # for header row in CSV
else:
    first_line = str(first_row[0])
    if len(first_line) < 8:
        print("First line too short to extract file info.")
        log_action("First line too short to extract file info.")
        sys.exit(1)
    file_type = first_line[:2]
    campus = first_line[2:5]
    term = first_line[5:8]

# Determine output subfolder
campus_folder = os.path.join(output_base, campus)
os.makedirs(campus_folder, exist_ok=True)

# --- Version Checking ---
ext = ".csv" if csv_mode else ".txt"
pattern = re.compile(rf"{file_type}_{campus}_{term}_(\d+){re.escape(ext)}$")

def get_versions(folder):
    versions = []
    if os.path.exists(folder):
        for f in os.listdir(folder):
            m = pattern.match(f)
            if m:
                versions.append(int(m.group(1)))
    return versions

# Check the shared export folder for versioning
output_versions = get_versions(campus_folder)
next_version = max(output_versions) + 1 if output_versions else 1
version_str = f"{next_version:02d}"

# --- Output File Writing ---
output_file = os.path.join(campus_folder, f"{file_type}_{campus}_{term}_{version_str}{ext}")

if csv_mode:
    with open(output_file, "w", encoding="utf-8", newline='') as fout:
        writer = csv.writer(fout)
        # Write header row using cursor description
        headers = [desc[0] for desc in cur.description]
        writer.writerow(headers)
        # Write first row and all remaining rows
        writer.writerow(first_row)
        for row in cur:
            writer.writerow(row)
else:
    with open(output_file, "w", encoding="utf-8", newline='') as fout:
        lines = [first_line]
        for row in cur:
            line = "".join(str(col) if col is not None else "" for col in row)
            lines.append(line)
        fout.write('\r\n'.join(lines))

# --- REMOVED: Copy/Mirror Logic ---
# No more mirroring - other scripts will read directly from shared_export
    
cur.close()
conn.close()

print(f"Export complete: {output_file}")
log_action(f"Export complete: {output_file}")
print(f"Data available in shared_export folder for other scripts to process")
log_action(f"Data available in shared_export folder for other scripts to process")