import os
import shutil
import configparser
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
        
log_action("===== Finalize Submission script started =====")

# Read config.ini
config = configparser.ConfigParser()
config.read('config/config.ini')

# Get the submission path from config.ini (add this key to your config)
submission_path = config.get('submission', 'path', fallback=None)
if not submission_path:
    print("No submission path set in config.ini under [submission] section.")
    log_action("No submission path set in config.ini under [submission] section.")
    log_action("===== Finalize Submission script finished with error =====")
    exit(1)

# Use the current term instance as the subfolder name
current_term = os.path.basename(BASE_DIR)
target_folder = os.path.join(submission_path, current_term)

if os.path.exists(target_folder):
    overwrite = input(f"Folder '{current_term}' already exists. Overwrite? (Y/N): ").strip().lower()
    if overwrite != 'y':
        print("Operation cancelled.")
        log_action("Operation cancelled.")
        log_action("===== Finalize Submission script finished with cancellation =====")
        exit(0)

os.makedirs(target_folder, exist_ok=True)

folders_to_copy = [
    (os.path.join(BASE_DIR, "shared_export"), os.path.join(target_folder, "Data Extracts"), "shared_export"),
    (os.path.join(BASE_DIR, "history_dat"), os.path.join(target_folder, "dat (subs)"), "history_dat"),
    (os.path.join(BASE_DIR, "error_report_loader", "completed"), os.path.join(target_folder, "Error Reports"), "error_report_loader/completed"),
]

for src, dst, desc in folders_to_copy:
    if os.path.exists(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)
        print(f"Copied {desc} to {dst}")
        log_action(f"Copied {desc} to {dst}")
    else:
        print(f"Source folder '{src}' does not exist. Skipping {desc}.")
        log_action(f"Source folder '{src}' does not exist. Skipped {desc}.")

print("All done!")
log_action("All done!")
log_action("===== Finalize Submission script finished =====")