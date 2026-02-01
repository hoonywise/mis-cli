import subprocess
import sys
from colorama import init, Fore, Style as ColoramaStyle
import questionary
import os
from datetime import datetime
from questionary import Style as QuestionaryStyle

from src.instance_selector import select_instance

# Check if config/config.ini exists, if not, run config_setup.py
if not os.path.exists(os.path.join("config", "config.ini")):
    subprocess.run(["python", "src/config_setup.py"])

# Instance selection
current_term, _ = select_instance()
if current_term is None:
    print("No instance selected. Exiting CLI.")
    sys.exit(0)
BASE_DIR = os.path.join(os.getcwd(), "data", current_term)
DATA_DIR = BASE_DIR  # or use subfolders as needed

MASTER_LOG = os.path.join(BASE_DIR, "mis-cli.log")
HISTORY_LOG = os.path.join(BASE_DIR, "history.log")

custom_style = QuestionaryStyle([
    ("pointer", "fg:#00ff00 bold"),  # color/style for the pointer
])

# Reset both log files at startup
with open(MASTER_LOG, "w", encoding="utf-8") as f:
    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Log started\n")

with open(HISTORY_LOG, "w", encoding="utf-8") as f:
    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Log started\n")

init(autoreset=True)

def run_config_setup():
    subprocess.run(["python", "src/config_setup.py"])
    input("Press Enter to return to the menu...")

def show_current_instance():
    print(Fore.GREEN + f"Current Instance: {current_term}" + ColoramaStyle.RESET_ALL)

def log_action(action):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"{timestamp} - {action}\n"
    with open(MASTER_LOG, "a", encoding="utf-8") as f:
        f.write(message)
    with open(HISTORY_LOG, "a", encoding="utf-8") as f:
        f.write(message)

def get_last_action():
    if not os.path.exists(MASTER_LOG):
        return "No actions yet."
    with open(MASTER_LOG, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if not lines:
            return "No actions yet."
        return lines[-1].strip()

def show_last_action():
    last = get_last_action()
    print(Fore.YELLOW + f"Last Action: {last}" + ColoramaStyle.RESET_ALL)

def print_logo():
    print(Fore.CYAN + ColoramaStyle.BRIGHT + r"""
 __  __ ___ ____      ____ _     ___ 
|  \/  |_ _/ ___|    / ___| |   |_ _|
| |\/| || |\___ \   | |   | |    | | 
| |  | || | ___) /  \ |___| |___ | | 
|_|  |_|___|____/    \____|_____|___|

Created by: Jihoon Ahn <github: hoonywise>
Email: hoonywise@proton.me
Check for updates at https://github.com/hoonywise/mis-cli/releases
""" + ColoramaStyle.RESET_ALL)

def run_gvprmis_export_batch():
    env = os.environ.copy()
    env["MIS_INSTANCE_PATH"] = BASE_DIR
    subprocess.run(["python", "src/gvprmis_export_batch.py"], env=env)
    log_action("GVPRMIS SQL Export Batch")
    input("Press Enter to return to the menu...")

#def run_gvprmis_export_batch_custom():
#    env = os.environ.copy()
#    env["MIS_INSTANCE_PATH"] = BASE_DIR
#    subprocess.run(["python", "src/gvprmis_export_batch_custom.py"], env=env)
#    log_action("Raw SQL Export Batch")
#    input("Press Enter to return to the menu...")

def run_gvprmis_processing():
    env = os.environ.copy()
    env["MIS_INSTANCE_PATH"] = BASE_DIR    
    subprocess.run(["python", "src/gvprmis_processing.py"], env=env)
    log_action("GVPRMIS.dat / SVRCAXX.dat Processing")
    input("Press Enter to return to the menu...")

def run_row_replace():
    env = os.environ.copy()
    env["MIS_INSTANCE_PATH"] = BASE_DIR 
    subprocess.run(["python", "src/row_replace.py"], env=env)
    log_action("Replace Partial Records in DAT")
    input("Press Enter to return to the menu...")

def run_error_stripper():
    env = os.environ.copy()
    env["MIS_INSTANCE_PATH"] = BASE_DIR 
    subprocess.run(["python", "src/error_stripper.py"], env=env)
    log_action("Strip Records in DAT")
    input("Press Enter to return to the menu...")

def run_dat_file_stager():
    env = os.environ.copy()
    env["MIS_INSTANCE_PATH"] = BASE_DIR 
    subprocess.run(["python", "src/dat_file_stager.py"], env=env)
    log_action("Stage Final DAT to Input DAT")
    input("Press Enter to return to the menu...")

def run_dat_loader():
    try:
        env = os.environ.copy()
        env["MIS_INSTANCE_PATH"] = BASE_DIR 
        subprocess.run(["python", "src/dat_loader.py"], env=env)
        log_action("DAT Loader (Database)")
    except KeyboardInterrupt:
        print("\nDAT Loader interrupted by user.")
    input("Press Enter to return to the menu...")

def run_error_report_loader():
    try:
        env = os.environ.copy()
        env["MIS_INSTANCE_PATH"] = BASE_DIR 
        subprocess.run(["python", "src/error_report_loader.py"], env=env)
        log_action("Error Report Loader (Database)")
    except KeyboardInterrupt:
        print("\nError Report Loader interrupted by user.")
    input("Press Enter to return to the menu...")

def run_sg26_sg29_loader():
    try:
        env = os.environ.copy()
        env["MIS_INSTANCE_PATH"] = BASE_DIR 
        subprocess.run(["python", "src/sg26_sg29_loader.py"], env=env)
        log_action("SG26/SG29 Loader (Database)")
    except KeyboardInterrupt:
        print("\nSG26/SG29 Loader interrupted by user.")
    input("Press Enter to return to the menu...")
    
def run_csv_loader():
    try:
        env = os.environ.copy()
        env["MIS_INSTANCE_PATH"] = BASE_DIR 
        subprocess.run(["python", "src/csv_loader.py"], env=env)
        log_action("CSV Loader (Database)")
    except KeyboardInterrupt:
        print("\nCSV Loader interrupted by user.")
    input("Press Enter to return to the menu...")
    
def run_invalid_rows():
    try:
        env = os.environ.copy()
        env["MIS_INSTANCE_PATH"] = BASE_DIR 
        subprocess.run(["python", "src/invalid_rows.py"], env=env)
        log_action("Invalid Rows Identifier")
    except KeyboardInterrupt:
        print("\nInvalid Rows Identifier interrupted by user.")
    input("Press Enter to return to the menu...")
        
def run_finalize_submission():
    try:
        env = os.environ.copy()
        env["MIS_INSTANCE_PATH"] = BASE_DIR 
        subprocess.run(["python", "src/finalize_sub.py"], env=env)
        log_action("Copy Submission to OneDrive")
    except KeyboardInterrupt:
        print("\nFinalize Submission interrupted by user.")
    input("Press Enter to return to the menu...")

def run_import_submission():
    try:
        env = os.environ.copy()
        env["MIS_INSTANCE_PATH"] = BASE_DIR
        subprocess.run(["python", "src/import_sub.py"], env=env)
        log_action("Import Submission from OneDrive")
    except KeyboardInterrupt:
        print("\nImport Submission interrupted by user.")
    input("Press Enter to return to the menu...")

def run_open_explorer():
    try:
        env = os.environ.copy()
        env["MIS_INSTANCE_PATH"] = BASE_DIR
        subprocess.run(["python", "src/open_explorer.py"], env=env)
        log_action("Open Term Folder in Explorer")
    except KeyboardInterrupt:
        print("\nOpen Term Folder in Explorer interrupted by user.")
    input("Press Enter to return to the menu...")
        
def run_dat_file_stager_load():
    try:
        env = os.environ.copy()
        env["MIS_INSTANCE_PATH"] = BASE_DIR 
        subprocess.run(["python", "src/dat_file_stager_load.py"], env=env)
        log_action("DAT File Stager (Load)")
    except KeyboardInterrupt:
        print("\nDAT File Stager (Load) interrupted by user.")
    input("Press Enter to return to the menu...")

def run_dat_file_stager_hist():
    try:
        env = os.environ.copy()
        env["MIS_INSTANCE_PATH"] = BASE_DIR 
        subprocess.run(["python", "src/dat_file_stager_hist.py"], env=env)
        log_action("Stage History DAT to Input DAT")
    except KeyboardInterrupt:
        print("\nDAT File Stager (History) interrupted by user.")
    input("Press Enter to return to the menu...")
    
def run_instance_delete():
    global current_term, BASE_DIR, DATA_DIR, MASTER_LOG, HISTORY_LOG
    env = os.environ.copy()
    env["MIS_INSTANCE_PATH"] = BASE_DIR
    subprocess.run(["python", "src/instance_delete.py"], env=env)
    input("Press Enter to return to the menu...")

    # Return True if the current instance folder was deleted
    return not os.path.exists(BASE_DIR)

def run_si_export_sp():
    env = os.environ.copy()
    env["MIS_INSTANCE_PATH"] = BASE_DIR
    # Prompt for term value
    gi03_val = questionary.text(
        "Enter gi03_val (term, e.g. 253):",
        validate=lambda t: t.isdigit() and len(t) > 0
    ).ask()
    if not gi03_val:
        print("No term entered. Returning to menu.")
        return
    # Run the export script
    subprocess.run(
        ["python", "src/si_export_sp.py", "SI_EXTRACT_SP.sql", f"gi03_val={gi03_val}"],
        env=env
    )
    log_action(f"SI Extract Export for term {gi03_val}")
    input("Press Enter to return to the menu...")
    
def run_pdis_export():
    env = os.environ.copy()
    env["MIS_INSTANCE_PATH"] = BASE_DIR
    # Prompt for term value
    gi03_val = questionary.text(
        "Enter gi03_val (term, e.g. 253):",
        validate=lambda t: t.isdigit() and len(t) > 0
    ).ask()
    if not gi03_val:
        print("No term entered. Returning to menu.")
        return
    # Run the export script
    subprocess.run(
        ["python", "src/pdis_export.py", "PDIS_EXTRACT.sql", f"gi03_val={gi03_val}"],
        env=env
    )
    log_action(f"PDIS Extract Export for term {gi03_val}")
    input("Press Enter to return to the menu...")

def run_dat_processing():
    """Handle DAT processing with method selection"""
    while True:
        method_choice = questionary.select(
            "Select DAT processing method:",
            choices=[
                "Compile (rewrite method)",
                "Paste (copy/paste method)",
                questionary.Separator(),
                "Back to main menu"
            ],
            pointer="→",
            style=custom_style
        ).ask()
        
        env = os.environ.copy()
        env["MIS_INSTANCE_PATH"] = BASE_DIR

        if method_choice is None or method_choice.startswith("Back to main menu"):
            return
        elif method_choice.startswith("Compile"):
            print("Running DAT Compile...")
            result = subprocess.run(["python", "src/dat_compile.py"], env=env)
            log_action("Compile New DAT Set (Compile)")
            input("Press Enter to return to the menu...")
            if result.returncode == 2:
                continue  # Go back to run_dat_processing menu
            elif result.returncode == 3:
                break     # Go back to data_editing_stripping_menu
            else:
                return
        elif method_choice.startswith("Paste"):
            print("Running DAT Paste...")
            result = subprocess.run(["python", "src/dat_paste.py"], env=env)
            log_action("Compile New DAT Set (Paste)")
            input("Press Enter to return to the menu...")
            if result.returncode == 2:
                continue
            elif result.returncode == 3:
                break
            else:
                return

def data_extract_preparation_menu():
    while True:
        os.system('cls')
        print_logo()
        show_current_instance()
        show_last_action()
        choice = questionary.select(
            "Data Extract and Preparation:",
            choices=[
                questionary.Separator(),
                "GVPRMIS.dat / SVRCAXX.dat Processing",
                "GVPRMIS SQL Export Batch",
#                "Raw SQL Export Batch",
                "SI Extract Export (Student ID/SSN)",
                "PDIS Extract Export (Student ID/SSN)",  
                questionary.Separator(),
                "Back to Main Menu"
            ],
            pointer="→",
            style=custom_style
        ).ask()
        if choice is None:
            continue
        elif choice.startswith("Back to Main Menu"):
            break
        elif choice.startswith("GVPRMIS.dat / SVRCAXX.dat Processing"):            
            run_gvprmis_processing()
        elif choice.startswith("GVPRMIS SQL Export Batch"):
            run_gvprmis_export_batch()
#        elif choice.startswith("Raw SQL Export Batch"):
#            run_gvprmis_export_batch_custom()
        elif choice.startswith("SI Extract Export"):
            run_si_export_sp()
        elif choice.startswith("PDIS Extract Export"):
            run_pdis_export()

def data_editing_stripping_menu():
    while True:
        os.system('cls')
        print_logo()
        show_current_instance()
        show_last_action()
        choice = questionary.select(
            "Data Editing and Stripping:",
            choices=[
                questionary.Separator(),
                "Replace Partial Records in DAT",
                "Compile New DAT Set",
                "Strip Records in DAT",
                "Invalid Rows Identifier",
                questionary.Separator(),
                "Stage Final DAT to Input DAT",
                "Stage History DAT to Input DAT",
                questionary.Separator(),
                "Back to Main Menu"
            ],
            pointer="→",  # <-- Change the arrow here!
            style=custom_style
        ).ask()
        if choice is None:
            continue
        elif choice.startswith("Back to Main Menu"):
            break
        elif choice.startswith("Stage Final DAT to Input DAT"):
            run_dat_file_stager()
        elif choice.startswith("Stage History DAT to Input DAT"):
            run_dat_file_stager_hist()
        elif choice.startswith("Replace Partial Records in DAT"):
            run_row_replace()
        elif choice.startswith("Compile New DAT Set"):
            run_dat_processing()
        elif choice.startswith("Strip Records in DAT"):
            run_error_stripper()
        elif choice.startswith("Invalid Rows Identifier"):
            run_invalid_rows()

def database_operations_menu():
    while True:
        os.system('cls')
        print_logo()
        show_current_instance()
        show_last_action()
        choice = questionary.select(
            "Database Operations Options:",
            choices=[
                questionary.Separator(),
                "Error Report Loader",
                "SG26/SG29 Loader",
                "DAT Loader",
                "CSV Loader",                
                questionary.Separator(),
                "Stage Highest Version to DAT Loader",
                questionary.Separator(),
                "Back to Main Menu"
            ],
            pointer="→",  # <-- Change the arrow here!
            style=custom_style
        ).ask()
        if choice is None:
            continue
        elif choice.startswith("Back to Main Menu"):
            break
        elif choice.startswith("Stage Highest Version to DAT Loader"):
            run_dat_file_stager_load()
        elif choice.startswith("Error Report Loader"):
            run_error_report_loader()
        elif choice.startswith("SG26/SG29 Loader"):
            run_sg26_sg29_loader()
        elif choice.startswith("DAT Loader"):
            run_dat_loader()
        elif choice.startswith("CSV Loader"):
            run_csv_loader()
            
def onedrive_menu():
    while True:
        os.system('cls')
        print_logo()
        show_current_instance()
        show_last_action()
        choice = questionary.select(
            "Finalize:",
            choices=[
                questionary.Separator(),
                "Copy Submission to OneDrive",
                "Import Submission from OneDrive",
                questionary.Separator(),
                "Back to Main Menu"
            ],
            pointer="→",  # <-- Change the arrow here!
            style=custom_style
        ).ask()
        if choice is None:
            continue
        elif choice.startswith("Back to Main Menu"):
            break
        elif choice.startswith("Copy Submission to OneDrive"):
            run_finalize_submission()
        elif choice.startswith("Import Submission from OneDrive"):
            run_import_submission()
            
def main_menu():
    try:
        while True:
            os.system('cls')
            print_logo()
            show_current_instance()
            show_last_action()
            choice = questionary.select(
                "Main Menu:",
                choices=[
                    questionary.Separator(),
                    "Data Extract and Preparation",
                    "Data Editing and Stripping",
                    "Database Operations",
                    "OneDrive Operations",
                    questionary.Separator(),
                    "Open Term Folder in Explorer",
                    "Change Instance Term",
                    "Delete Instance Term",
                    "Setup/Update Configuration",
                    "Exit"
                ],
                pointer="→",  # <-- Change the arrow here!
                style=custom_style
            ).ask()
            if choice is None or choice.startswith("Exit"):
                log_action("Exit")
                print(Fore.MAGENTA + "Goodbye!")
                sys.exit(0)
            elif choice.startswith("Setup/Update Configuration"):
                run_config_setup()
            elif choice.startswith("Open Term Folder in Explorer"):
                run_open_explorer()
            elif choice.startswith("Change Instance Term"):
                global current_term, BASE_DIR, DATA_DIR, MASTER_LOG, HISTORY_LOG
                new_term, _ = select_instance()
                if new_term is None:
                    print("No instance selected. Returning to main menu.")
                    continue
                current_term = new_term
                BASE_DIR = os.path.join(os.getcwd(), "data", current_term)
                DATA_DIR = BASE_DIR
                MASTER_LOG = os.path.join(BASE_DIR, "mis-cli.log")
                HISTORY_LOG = os.path.join(BASE_DIR, "history.log")
                print(Fore.GREEN + f"Switched to instance: {current_term}" + ColoramaStyle.RESET_ALL)
                log_action(f"Switched to instance: {current_term}")
            elif choice.startswith("Delete Instance Term"):
                was_deleted = run_instance_delete()
                if was_deleted:
                    print(Fore.RED + f"Current instance '{current_term}' was deleted. Please select a new instance." + ColoramaStyle.RESET_ALL)
                    new_term, _ = select_instance()
                    if new_term is None:
                        print("No instance selected. Exiting CLI.")
                        sys.exit(0)
                    current_term = new_term
                    BASE_DIR = os.path.join(os.getcwd(), "data", current_term)
                    DATA_DIR = BASE_DIR
                    MASTER_LOG = os.path.join(BASE_DIR, "mis-cli.log")
                    HISTORY_LOG = os.path.join(BASE_DIR, "history.log")
                    print(Fore.GREEN + f"Switched to instance: {current_term}" + ColoramaStyle.RESET_ALL)
                    log_action(f"Switched to instance: {current_term}")
            elif choice.startswith("Data Extract and Preparation"):
                data_extract_preparation_menu()
            elif choice.startswith("Data Editing and Stripping"):
                data_editing_stripping_menu()
            elif choice.startswith("Database Operations"):
                database_operations_menu()
            elif choice.startswith("OneDrive Operations"):
                onedrive_menu()
    except KeyboardInterrupt:
        print(Fore.MAGENTA + "\nCLI interrupted by user. Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main_menu()