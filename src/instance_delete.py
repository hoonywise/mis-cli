import os
import shutil
import subprocess
import questionary
import stat
from datetime import datetime

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_ROOT = os.path.join(BASE_PATH, "data")
INSTANCE_HISTORY = os.path.join(BASE_PATH, "instance_history.log")

def explorer_windows_open():
    # Check for running explorer.exe processes
    result = subprocess.run('tasklist /FI "IMAGENAME eq explorer.exe"', capture_output=True, text=True, shell=True)
    return "explorer.exe" in result.stdout

def prompt_and_handle_explorer():
    if explorer_windows_open():
        close = questionary.confirm(
            "Explorer windows are open and may cause folder delete to fail. "
            "Would you like to close all Explorer windows?").ask()
        if close:
            subprocess.run("taskkill /f /im explorer.exe", shell=True)
            print("All Explorer windows closed.")
            subprocess.Popen("explorer.exe")  # Only restart if closed
        else:
            print("Proceeding without closing Explorer windows.")

def log_instance_action(action):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(INSTANCE_HISTORY, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} - {action}\n")

def list_instances():
    return [d for d in os.listdir(DATA_ROOT)
            if os.path.isdir(os.path.join(DATA_ROOT, d)) and d.isdigit() and len(d) == 3]
    
def on_rm_error(func, path, exc_info):
    # Suppress error messages
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass  # Suppress all exceptions

def delete_instance():
    prompt_and_handle_explorer()
    instances = list_instances()
    if not instances:
        print("No instances to delete.")
        return
    to_delete = questionary.select(
        "Select a term instance to delete:",
        choices=instances + ["Cancel"]
    ).ask()
    if to_delete == "Cancel" or to_delete is None:
        print("Delete cancelled.")
        log_instance_action("Delete cancelled.")
        return
    confirm = questionary.confirm(
        f"Are you sure you want to delete instance '{to_delete}'? This cannot be undone."
    ).ask()
    if confirm:
        shutil.rmtree(os.path.join(DATA_ROOT, to_delete), onerror=on_rm_error)
        print(f"Instance '{to_delete}' deleted.")
        log_instance_action(f"Instance '{to_delete}' deleted.")
    else:
        print("Delete cancelled.")
        log_instance_action("Delete cancelled.")

def main():
    print("=== MIS CLI Instance Delete ===")
    delete_instance()

if __name__ == "__main__":
    main()
