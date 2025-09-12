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
    print("Usage: python si_export.py SI_EXTRACT_SP.sql gi03_val=<term>")
    log_action("Usage: python si_export.py SI_EXTRACT_SP.sql gi03_val=<term>")
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

# Compute dynamic terms for IN clause
gi03_val_int = int(gi03_val)
terms = [gi03_val_int - 5, gi03_val_int - 3, gi03_val_int + 3]
terms_str = ', '.join(str(t) for t in terms)

# Read SQL and substitute {gi03_val}
with open(sql_file, "r", encoding="utf-8") as f:
    sql = f.read()
sql = sql.format(gi03_val=terms_str)

# Check for unbound variables
unbound_vars = re.findall(r":\w+", sql)
if unbound_vars:
    print(f"❌ Unbound SQL variables found: {', '.join(unbound_vars)}")
    log_action(f"❌ Unbound SQL variables found: {', '.join(unbound_vars)}")
    sys.exit(1)

conn = get_connection("prod")
if not conn:
    print("❌ Failed to connect to Production database")
    log_action("❌ Failed to connect to Production database")
    sys.exit(1)

cur = conn.cursor()
cur.execute("ALTER SESSION SET NLS_DATE_FORMAT = 'MM/DD/YY'")
cur.execute(sql)

output_base = os.path.join(BASE_DIR, "shared_export", "si_export_sp")
os.makedirs(output_base, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = os.path.join(output_base, f"si_export_sp_{timestamp}.txt")

first_row = cur.fetchone()
if not first_row:
    print("No data returned from query.")
    log_action("No data returned from query.")
    sys.exit(1)

with open(output_file, "w", encoding="utf-8", newline='') as fout:
    lines = [str(first_row[0])]
    for row in cur:
        line = "".join(str(col) if col is not None else "" for col in row)
        lines.append(line)
    fout.write('\r\n'.join(lines))

cur.close()
conn.close()

print(f"Export complete: {output_file}")
log_action(f"Export complete: {output_file}")