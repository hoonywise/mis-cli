import subprocess
import os
import questionary
from questionary import Separator, Style as QuestionaryStyle
from datetime import datetime

custom_style = QuestionaryStyle([
    ("pointer", "fg:#00ff00 bold"),
])

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

mis_export_script = "src/gvprmis_export.py"

# Parse params file to build a mapping of campus to file list
def parse_params_file(params_file):
    campus_files = {}
    current_campus = None
    with open(params_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("# Campus"):
                current_campus = line.split()[-1]
                campus_files[current_campus] = []
            elif not line.startswith("#") and current_campus:
                campus_files[current_campus].append(line)
    # Employee files are those for 860, student files are for 861/862/863
    employee_files = [(f, f.replace("_export.sql", "")) for f in campus_files.get("860", [])]
    student_files_by_campus = {}
    for campus in ("861", "862", "863"):
        student_files_by_campus[campus] = [(f, f.replace("_export.sql", "")) for f in campus_files.get(campus, [])]
    return employee_files, student_files_by_campus

def run_export_jobs(jobs, gi03_val, export_flag):
    for job in jobs:
        sql_file, campus, extra_params = job
        params = [f"gi03_val={gi03_val}", f"gi01_val={campus}"] + extra_params
        print(f"\nProcessing: {sql_file} gi03_val={gi03_val} gi01_val={campus} {' '.join(extra_params)}")
        log_action(f"Processing: {sql_file} gi03_val={gi03_val} gi01_val={campus} {' '.join(extra_params)}")
        cmd = ["python", mis_export_script, sql_file] + params
        if export_flag:
            cmd.append(export_flag)
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"  Error processing {sql_file} for campus {campus}")
            log_action(f"Error processing {sql_file} for campus {campus}")
        else:
            print(f"  Done: {sql_file} for campus {campus}")
            log_action(f"Done: {sql_file} for campus {campus}")

def main():
    log_action("===== GVPRMIS Export Batch script started =====")
    while True:
        export_format = questionary.select(
            "Choose export format:",
            choices=["Text", "CSV"],
            style=custom_style
        ).ask()

        if export_format == "CSV":
            params_file = "config/sql_batch_params_custom_csv.txt"
            export_flag = "--csv"
        else:
            params_file = "config/sql_batch_params_custom.txt"
            export_flag = None

        print("Using params file:", params_file)
        log_action(f"Using params file: {params_file}")

        employee_files, student_files_by_campus = parse_params_file(params_file)

        while True:
            # 1. Employee/Student prompt
            group = questionary.select(
                "Select export group:",
                choices=[
                    "Employee (PZPEDEX, PZPAEXT for campus 860)",
                    "Student (All other file types for campuses 861, 862, 863)",
                    Separator(),
                    "Quit"
                ],
                pointer="→",
                style=custom_style
            ).ask()
            if group is None or group.startswith("Quit"):
                print("Exiting batch export.")
                log_action("Exiting batch export.")
                log_action("===== GVPRMIS Export Batch script finished =====")
                return

            jobs = []

            if group.startswith("Employee"):
                file_choices = [f[1] for f in employee_files] + ["ALL"]
                print("Tip: Press Enter with nothing selected to go back to the previous menu.")
                log_action("Tip: Press Enter with nothing selected to go back to the previous menu.")
                selected_files = questionary.checkbox(
                    "Select Employee file types to export (PZPEDEX, PZPAEXT):",
                    choices=file_choices,
                    style=custom_style
                ).ask()
                if not selected_files:
                    continue
                if "ALL" in selected_files:
                    selected_files = [f[1] for f in employee_files]
                gi03_val = questionary.text(
                    "Enter gi03_val (term, e.g. 253):",
                    validate=lambda t: t.isdigit() and len(t) > 0
                ).ask()
                if not gi03_val:
                    continue
                confirm = questionary.select(
                    f"Proceed with Employee export for files: {', '.join(selected_files)} and gi03_val={gi03_val}?",
                    choices=["Yes", "No (start over)", "Quit"],
                    style=custom_style
                ).ask()
                if confirm == "Quit":
                    print("Exiting batch export.")
                    log_action("Exiting batch export.")
                    return
                if confirm != "Yes":
                    continue
                for sql_file, display in employee_files:
                    if display in selected_files:
                        jobs.append((sql_file, "860", []))

            elif group.startswith("Student"):
                campus_choices = ["861", "862", "863", "ALL"]
                print("Tip: Press Enter with nothing selected to go back to the previous menu.")
                log_action("Tip: Press Enter with nothing selected to go back to the previous menu.")
                selected_campuses = questionary.checkbox(
                    "Select campus/campuses (gi01_val):",
                    choices=campus_choices,
                    style=custom_style
                ).ask()
                if not selected_campuses:
                    continue
                if "ALL" in selected_campuses:
                    selected_campuses = ["861", "862", "863"]
                    campus_mode = "ALL"
                else:
                    campus_mode = None

                campus_file_map = {}
                if campus_mode == "ALL":
                    all_files = set()
                    campus_file_lookup = {}
                    for campus in ["861", "862", "863"]:
                        for f in student_files_by_campus[campus]:
                            display = f[1]
                            all_files.add(display)
                            campus_file_lookup.setdefault(display, set()).add(campus)
                    labeled_file_choices = []
                    for display in sorted(all_files):
                        campuses = campus_file_lookup.get(display, set())
                        if len(campuses) == 1:
                            campus_label = f" ({','.join(campuses)})"
                            labeled_file_choices.append(f"{display}{campus_label}")
                        else:
                            labeled_file_choices.append(display)
                    labeled_file_choices.append("ALL")
                    print("Tip: Press Enter with nothing selected to go back to the previous menu.")
                    log_action("Tip: Press Enter with nothing selected to go back to the previous menu.")
                    selected_files = questionary.checkbox(
                        f"Select Student file types to export for ALL campuses:",
                        choices=labeled_file_choices,
                        style=custom_style
                    ).ask()
                    if not selected_files:
                        continue
                    if "ALL" in selected_files:
                        selected_files = sorted(all_files)
                    cleaned_selected_files = []
                    for display in selected_files:
                        if display.endswith(")"):
                            cleaned_selected_files.append(display.split(" (")[0])
                        else:
                            cleaned_selected_files.append(display)
                    campus_file_map = {campus: [] for campus in ["861", "862", "863"]}
                    for display in cleaned_selected_files:
                        for campus in campus_file_lookup.get(display, []):
                            campus_file_map[campus].append(display)
                else:
                    for campus in selected_campuses:
                        campus_files = student_files_by_campus.get(campus, [])
                        file_choices = [f[1] for f in campus_files] + ["ALL"]
                        print("Tip: Press Enter with nothing selected to go back to the previous menu.")
                        log_action("Tip: Press Enter with nothing selected to go back to the previous menu.")
                        selected_files = questionary.checkbox(
                            f"Select Student file types to export for campus {campus}:",
                            choices=file_choices,
                            style=custom_style
                        ).ask()
                        if not selected_files:
                            break
                        if "ALL" in selected_files:
                            selected_files = [f[1] for f in campus_files]
                        campus_file_map[campus] = selected_files
                    else:
                        pass
                    if len(campus_file_map) != len(selected_campuses):
                        continue

                gi03_val = questionary.text(
                    "Enter gi03_val (term, e.g. 253):",
                    validate=lambda t: t.isdigit() and len(t) > 0
                ).ask()
                if not gi03_val:
                    continue
                summary = []
                for campus, files in campus_file_map.items():
                    summary.append(f"Campus {campus}: {', '.join(files)}")
                confirm = questionary.select(
                    f"Proceed with Student export for:\n  {'; '.join(summary)}\n  gi03_val={gi03_val}?",
                    choices=["Yes", "No (start over)", "Quit"],
                    style=custom_style
                ).ask()
                if confirm == "Quit":
                    print("Exiting batch export.")
                    log_action("Exiting batch export.")
                    return
                if confirm != "Yes":
                    continue
                for campus, files in campus_file_map.items():
                    campus_files = student_files_by_campus.get(campus, [])
                    for sql_file, display in campus_files:
                        if display in files:
                            jobs.append((sql_file, campus, []))

            # Run jobs
            run_export_jobs(jobs, gi03_val, export_flag)
            break  # After successful export, break out of inner loop

        again = questionary.select(
            "Run another batch export?",
            choices=["Yes", "No (quit)"],
            style=custom_style
        ).ask()
        if again != "Yes":
            print("Exiting batch export.")
            log_action("Exiting batch export.")
            log_action("===== GVPRMIS Export Batch script finished =====")
            break

    log_action("===== GVPRMIS Export Batch script finished =====")

if __name__ == "__main__":
    main()