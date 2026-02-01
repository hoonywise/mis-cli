import os
import questionary
from datetime import datetime

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_ROOT = os.path.join(BASE_PATH, "data")
INSTANCES_DIR = DATA_ROOT  # All term folders go under data/
INSTANCE_HISTORY = os.path.join(BASE_PATH, "instance_history.log")


def log_instance_action(action):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(INSTANCE_HISTORY, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} - {action}\n")


def list_instances():
    # List all folders in data/ that are named as 3-digit terms
    return [d for d in os.listdir(INSTANCES_DIR)
            if os.path.isdir(os.path.join(INSTANCES_DIR, d)) and d.isdigit() and len(d) == 3]

def create_instance(term):
    instance_path = os.path.join(INSTANCES_DIR, term)
    os.makedirs(instance_path, exist_ok=True)
    # List of working subfolders to create
    subfolders = [
        "error_report_loader",
        "final_dat",
        "history_dat",
        "input_dat",
        "sg_loader",
        "shared_export",
        "dat_loader",
        "manual_download",
        "error_report_strip",
        "csv_loader"
    ]
    for folder in subfolders:
        folder_path = os.path.join(instance_path, folder)
        os.makedirs(folder_path, exist_ok=True)
        # Create sub-subfolders as specified
        if folder in ["dat_loader", "error_report_loader"]:
            for sub in ["pending", "completed", "log"]:
                os.makedirs(os.path.join(folder_path, sub), exist_ok=True)
        elif folder in ["sg_loader", "csv_loader"]:
            for sub in ["completed", "input"]:
                os.makedirs(os.path.join(folder_path, sub), exist_ok=True)
    log_instance_action(f"Created instance: {term} with subfolders")
    return instance_path

def select_instance():
    instances = list_instances()
    choices = instances + ["Create new instance", "Exit to main menu"]
    selected = questionary.select(
        "Select a term instance:",
        choices=choices
    ).ask()
    if selected == "Create new instance":
        term = questionary.text(
            "Enter new term code (e.g., 253) or 'q' to cancel:",
            validate=lambda t: (t.isdigit() and len(t) == 3) or t.lower() == 'q'
        ).ask()
        if term is None or term.lower() == 'q':
            print("Cancelled instance creation. Returning to main menu.")
            log_instance_action("Cancelled instance creation.")
            return None, None
        instance_path = create_instance(term)
        print(f"Created new instance at {instance_path}")
        open_explorer = questionary.confirm(
            "Would you like to open this folder in Explorer?"
        ).ask()
        if open_explorer:
            os.startfile(instance_path)
        log_instance_action(f"Selected new instance: {term}")
        return term, instance_path
    elif selected == "Exit to main menu":
        print("Returning to main menu.")
        log_instance_action("Exited to main menu from instance selector.")
        return None, None
    else:
        instance_path = os.path.join(INSTANCES_DIR, selected)
        print(f"Selected instance: {selected}")
        open_explorer = questionary.confirm(
            "Would you like to open this folder in Explorer?"
        ).ask()
        if open_explorer:
            os.startfile(instance_path)
        log_instance_action(f"Selected existing instance: {selected}")
        return selected, instance_path

def main():
    print("=== MIS CLI Instance Selector ===")
    term, path = select_instance()
    print(f"Current instance: {term}")
    print(f"Instance path: {path}")

if __name__ == "__main__":
    main()
