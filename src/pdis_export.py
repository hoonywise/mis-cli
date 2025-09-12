import oracledb
import sys
import os
import re
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from libs.oracle_db_connector import get_connection
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

if len(sys.argv) < 3:
    print("Usage: python pdis_export.py PDIS_EXTRACT.sql gi03_val=<term>")
    log_action("Usage: python pdis_export.py PDIS_EXTRACT.sql gi03_val=<term>")
    sys.exit(1)

sql_file = sys.argv[1]
param_pair = sys.argv[2]

# SQL file path
sql_folder = os.path.join(os.path.dirname(__file__), "..", "sql")
if not os.path.isabs(sql_file):
    sql_file = os.path.join(sql_folder, sql_file)

# Parse gi03_val
if '=' not in param_pair or not param_pair.startswith("gi03_val="):
    print("Parameter must be in the form gi03_val=<term>")
    log_action("Parameter must be in the form gi03_val=<term>")
    sys.exit(1)
gi03_val = param_pair.split('=', 1)[1]

# Output folder
output_base = os.path.join(BASE_DIR, "shared_export", "pdis_export")
os.makedirs(output_base, exist_ok=True)

# Output files
output_files = [
    (['861', '862'], os.path.join(output_base, "NorthOCCollege-Input-CR.txt")),
    (['863'], os.path.join(output_base, "NorthOCCollege-Input-NCR.txt")),
]

with open(sql_file, "r", encoding="utf-8") as f:
    sql_template = f.read()

conn = get_connection("prod")
if not conn:
    print("❌ Failed to connect to Production database")
    log_action("❌ Failed to connect to Production database")
    sys.exit(1)

cur = conn.cursor()
cur.execute("ALTER SESSION SET NLS_DATE_FORMAT = 'MM/DD/YY'")

for gi01_vals, output_file in output_files:
    lines = []
    for gi01_val in gi01_vals:
        sql = sql_template.replace('{gi03_val}', gi03_val).replace('{gi01_val}', gi01_val)
        # Use bind variable for gi01_val
        cur.execute(sql)
        rows = cur.fetchall()
        if not rows:
            print(f"No data returned from query for gi01_val {gi01_val}.")
            log_action(f"No data returned from query for gi01_val {gi01_val}.")
            continue
        for row in rows:
            line = "".join(str(col) if col is not None else "" for col in row)
            lines.append(line)
    if lines:
        with open(output_file, "w", encoding="utf-8", newline='') as fout:
            fout.write('\r\n'.join(lines))
        print(f"Export complete: {output_file}")
        log_action(f"Export complete: {output_file}")
    else:
        print(f"No data returned for any gi01_val in {gi01_vals}.")
        log_action(f"No data returned for any gi01_val in {gi01_vals}.")

cur.close()
conn.close()
