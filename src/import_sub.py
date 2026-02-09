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

log_action("===== Import Submission script started =====")

# Read config.ini
config = configparser.ConfigParser()
config.read('config/config.ini')

# Get the submission path from config.ini
submission_path = config.get('submission', 'path', fallback=None)
if not submission_path:
    print("No submission path set in config.ini under [submission] section.")
    log_action("No submission path set in config.ini under [submission] section.")
    log_action("===== Import Submission script finished with error =====")
    exit(1)

# List available term folders (ignore folders with 'Calendar File' in the name)
available_terms = [
    name for name in os.listdir(submission_path)
    if os.path.isdir(os.path.join(submission_path, name)) and 'calendar file' not in name.lower()
]

# Auto-detect current term from BASE_DIR
current_term = os.path.basename(BASE_DIR)

selected_term = None
if current_term in available_terms:
    print(f"Auto-detected current term: {current_term}")
    selected_term = current_term
else:
    if not available_terms:
        print("No term folders found in submission path.")
        log_action("No term folders found in submission path.")
        log_action("===== Import Submission script finished with error =====")
        exit(1)
    print("Available term folders:")
    for idx, term in enumerate(available_terms, 1):
        print(f"{idx}. {term}")
    selected_idx = input("Select a term folder to import (number): ").strip()
    if not selected_idx.isdigit() or not (1 <= int(selected_idx) <= len(available_terms)):
        print("Invalid selection.")
        log_action("Invalid term folder selection.")
        log_action("===== Import Submission script finished with error =====")
        exit(1)
    selected_term = available_terms[int(selected_idx) - 1]

source_folder = os.path.join(submission_path, selected_term)

def find_folder_case_insensitive(parent_dir, target_name):
    for name in os.listdir(parent_dir):
        if name.lower() == target_name.lower() and os.path.isdir(os.path.join(parent_dir, name)):
            return name
    return target_name  # fallback if not found

external_root = os.path.join(source_folder, find_folder_case_insensitive(source_folder, "External Files"))

folders_to_copy = [
    (
        os.path.join(source_folder, find_folder_case_insensitive(source_folder, "Data Extracts")),
        os.path.join(BASE_DIR, "shared_export"),
        "Data Extracts"
    ),
    (
        os.path.join(source_folder, find_folder_case_insensitive(source_folder, "dat")),
        os.path.join(BASE_DIR, "history_dat"),
        "dat"
    ),
    (
        os.path.join(source_folder, find_folder_case_insensitive(source_folder, "Final dat")),
        os.path.join(BASE_DIR, "final_dat"),
        "Final dat"
    ),
    (
        os.path.join(source_folder, find_folder_case_insensitive(source_folder, "Error Reports")),
        os.path.join(BASE_DIR, "error_report_loader", "completed"),
        "Error Reports"
    ),
    (
        os.path.join(external_root, "sg_loader"),
        os.path.join(BASE_DIR, "sg_loader"),
        "External Files/sg_loader"
    ),
    (
        os.path.join(external_root, "csv_loader"),
        os.path.join(BASE_DIR, "csv_loader"),
        "External Files/csv_loader"
    ),
    (
        os.path.join(external_root, "manual_download"),
        os.path.join(BASE_DIR, "manual_download"),
        "External Files/manual_download"
    ),
]

for src, dst, desc in folders_to_copy:
    if os.path.exists(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)
        print(f"Imported {desc} to {dst}")
        log_action(f"Imported {desc} to {dst}")
    else:
        print(f"Source folder '{src}' does not exist. Skipping {desc}.")
        log_action(f"Source folder '{src}' does not exist. Skipped {desc}.")

print("Import complete!")
log_action("Import complete!")
log_action("===== Import Submission script finished =====")
