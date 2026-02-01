import os
import questionary

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_ROOT = os.path.join(BASE_PATH, "data")


def list_term_folders():
    # List all folders in data/ that are named as 3-digit terms
    return [d for d in os.listdir(DATA_ROOT)
            if os.path.isdir(os.path.join(DATA_ROOT, d)) and d.isdigit() and len(d) == 3]

def get_current_term():
    instance_path = os.environ.get("MIS_INSTANCE_PATH")
    if instance_path and os.path.isdir(instance_path):
        term = os.path.basename(instance_path)
        if term.isdigit() and len(term) == 3:
            return term, instance_path
    return None, None

def main():
    print("=== Open Term Folder in Explorer ===")
    term_folders = list_term_folders()
    current_term, current_path = get_current_term()

    choices = []
    if current_term:
        choices.append({"name": f"Open Currently Selected Term ({current_term})", "value": current_path})
    else:
        choices.append({"name": "Open Currently Selected Term (not set)", "disabled": "No current term"})

    choices += [{"name": t, "value": os.path.join(DATA_ROOT, t)} for t in term_folders]

    selected = questionary.select(
        "Select a term folder to open in Explorer:",
        choices=choices
    ).ask()

    if selected:
        print(f"Opening {selected} in Explorer...")
        os.startfile(selected)
    else:
        print("No folder selected.")

if __name__ == "__main__":
    main()
