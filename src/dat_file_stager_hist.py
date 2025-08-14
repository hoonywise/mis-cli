import os
import sys
import shutil
from pathlib import Path
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

def list_history_folders(history_dir):
    folders = []
    for item in history_dir.iterdir():
        if item.is_dir() and item.name.isdigit() and len(item.name) == 2:
            mtime = datetime.fromtimestamp(item.stat().st_mtime)
            folders.append((item.name, mtime))
    folders.sort(key=lambda x: int(x[0]))
    return folders

def main():
    log_action("===== DAT File Stager Hist script started =====")
    history_dir = Path(BASE_DIR) / "history_dat"
    input_dir = Path(BASE_DIR) / "input_dat"

    if not history_dir.exists():
        print(f"History directory not found: {history_dir}")
        log_action(f"History directory not found: {history_dir}")
        log_action("===== DAT File Stager Hist script finished with error =====")
        return 1

    folders = list_history_folders(history_dir)
    if not folders:
        print("No version folders found in history_dat.")
        log_action("No version folders found in history_dat.")
        log_action("===== DAT File Stager Hist script finished with error =====")
        return 1

    print("Available history versions:")
    log_action("Available history versions:")
    for name, mtime in folders:
        print(f"  {name}   (last modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
        log_action(f"  {name}   (last modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')})")

    while True:
        user_input = input("Enter folder number to stage (e.g., 03), or 'q'/'c' to cancel: ").strip().lower()
        if user_input in ("q", "c"):
            print("Operation cancelled by user.")
            log_action("Operation cancelled by user.")
            log_action("===== DAT File Stager Hist script finished =====")
            return 0
        if user_input.isdigit() and len(user_input) == 2:
            selected = history_dir / user_input
            if selected.exists() and selected.is_dir():
                files = list(selected.iterdir())
                if not files:
                    print(f"No files found in {selected}.")
                    log_action(f"No files found in {selected}.")
                    continue
                print(f"\nContents of {selected}:")
                log_action(f"\nContents of {selected}:")
                for f in files:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    print(f"  {f.name}   (last modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
                    log_action(f"  {f.name}   (last modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
                while True:
                    cont = input("Continue? (Y/N/q): ").strip().lower()
                    if cont == "y":
                        input_dir.mkdir(parents=True, exist_ok=True)
                        print(f"\nCopying files from {selected} to {input_dir} ...")
                        log_action(f"\nCopying files from {selected} to {input_dir} ...")
                        for f in files:
                            if f.name == "history.log":
                                continue  # Skip copying history.log
                            dest = input_dir / f.name
                            if f.is_file():
                                shutil.copy2(f, dest)
                                print(f"  Copied {f.name}")
                                log_action(f"  Copied {f.name}")
                            elif f.is_dir():
                                shutil.copytree(f, dest, dirs_exist_ok=True)
                                print(f"  Copied folder {f.name}")
                                log_action(f"  Copied folder {f.name}")
                        print("Staging complete. Files are now in input_dat.")
                        log_action("Staging complete. Files are now in input_dat.")
                        log_action("===== DAT File Stager Hist script finished =====")
                        return 0
                    elif cont == "n":
                        break
                    elif cont == "q":
                        print("Operation cancelled by user.")
                        log_action("Operation cancelled by user.")
                        log_action("===== DAT File Stager Hist script finished =====")
                        return 0
                    else:
                        print("Please enter Y, N, or Q.")
                        log_action("Please enter Y, N, or Q.")
            else:
                print(f"Folder {user_input} does not exist.")
                log_action(f"Folder {user_input} does not exist.")
        else:
            print("Invalid input. Please enter a two-digit folder number, or 'q'/'c' to cancel.")
            log_action("Invalid input. Please enter a two-digit folder number, or 'q'/'c' to cancel.")

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        log_action("\nOperation cancelled by user.")
        log_action("===== DAT File Stager Hist script finished with error =====")
        sys.exit(1)