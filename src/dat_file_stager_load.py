import os
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

history_dir = os.path.join(BASE_DIR, "history_dat")
pending_dir = os.path.join(BASE_DIR, "dat_loader", "pending")

log_action("===== DAT File Stager Load script started =====")

# Find all subfolders with integer names
version_folders = [
    f for f in os.listdir(history_dir)
    if os.path.isdir(os.path.join(history_dir, f)) and f.isdigit()
]

if not version_folders:
    print("No version folders found in data/history_dat.")
    log_action("No version folders found in data/history_dat.")
    log_action("===== DAT File Stager Load script finished with error =====")
    exit(1)

# Get the highest version number
latest_version = max(map(int, version_folders))
latest_folder = os.path.join(history_dir, str(latest_version))

print(f"Copying from version folder: {latest_folder}")
log_action(f"Copying from version folder: {latest_folder}")

# Ensure pending_dir exists
os.makedirs(pending_dir, exist_ok=True)

# Copy contents (overwrite if exists)
for item in os.listdir(latest_folder):
    if item == "history.log":
        continue  # Skip copying history.log
    src = os.path.join(latest_folder, item)
    dst = os.path.join(pending_dir, item)
    if os.path.isdir(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dst)

print(f"Copied contents of version {latest_version} to {pending_dir}")
log_action(f"Copied contents of version {latest_version} to {pending_dir}")
log_action("===== DAT File Stager Load script finished =====")