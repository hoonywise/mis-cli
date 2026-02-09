import os
import re
import shutil
import argparse
from collections import defaultdict
from datetime import datetime
import questionary

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

def trim_trailing_spaces_in_files(input_dir, file_type="CB", target_length=220):
    """
    WARNING: This function operates on raw bytes and assumes all characters are single-byte (e.g., ASCII or cp1252).
    If the input TXT file contains special or multi-byte UTF-8 characters (such as ™, é, etc.), 
    this function may break those characters, truncate them incorrectly, or result in lines with incorrect byte lengths.
    For UTF-8 files with special characters, manual review and correction is recommended.
    """
    print(f"Scanning for {file_type} files to ensure exactly {target_length} characters per line...")
    log_action(f"Scanning for {file_type} files to ensure exactly {target_length} characters per line...")
    file_pattern = re.compile(rf'{file_type}_\d{{3}}_\d{{3}}_\d+(?:_rev)?\.txt$')
    files_processed = 0

    for root, _, files in os.walk(input_dir):
        for filename in files:
            if file_pattern.match(filename):
                file_path = os.path.join(root, filename)

                # Read the file content in binary mode to handle line endings correctly
                with open(file_path, 'rb') as f:
                    binary_content = f.read()
                    
                # Detect line ending type (Windows \r\n or Unix \n)
                if b'\r\n' in binary_content:
                    line_ending = b'\r\n'
                    print(f"  {filename} uses Windows-style line endings (\\r\\n)")
                    log_action(f"  {filename} uses Windows-style line endings (\\r\\n)")
                else:
                    line_ending = b'\n'
                    print(f"  {filename} uses Unix-style line endings (\\n)")
                    log_action(f"  {filename} uses Unix-style line endings (\\n)")
                    
                # Split the content by line endings
                binary_lines = binary_content.split(line_ending)
                
                # Check if any line needs processing (not exactly target_length)
                needs_processing = False
                for i, line in enumerate(binary_lines):
                    if len(line) != target_length:
                        needs_processing = True
                        print(f"    Line {i+1}: Length {len(line)} (expected {target_length})")
                        log_action(f"    Line {i+1}: Length {len(line)} (expected {target_length})")
                        # Print a sample if not empty
                        if line and i < 3:  # Just check first few lines
                            print(f"    Sample ending: {line[-10:] if len(line) >= 10 else line}")
                            log_action(f"    Sample ending: {line[-10:] if len(line) >= 10 else line}")
                        break

                if needs_processing:
                    # Process each line to ensure exact length
                    processed_lines = []
                    modified_count = 0
                    lines_too_short = 0
                    lines_too_long = 0
                    
                    for line in binary_lines:
                        if len(line) > target_length:
                            # Trim to exactly target_length chars
                            trimmed_line = line[:target_length]
                            lines_too_long += 1
                            modified_count += 1
                        elif len(line) < target_length and line:  # Skip empty last line
                            # For lines that are too short, pad with spaces
                            trimmed_line = line.ljust(target_length)
                            lines_too_short += 1
                            modified_count += 1
                        else:
                            # Exactly right length or empty last line, leave it alone
                            trimmed_line = line

                        processed_lines.append(trimmed_line)
                    
                    # Join with the original line ending and write back
                    with open(file_path, 'wb') as f:
                        f.write(line_ending.join(processed_lines))
                        if binary_content.endswith(line_ending):
                            f.write(line_ending)
                    
                    files_processed += 1
                    print(f"  Processed {filename}: {modified_count} lines modified")
                    log_action(f"  Processed {filename}: {modified_count} lines modified")
                    if lines_too_long > 0:
                        print(f"    - {lines_too_long} lines were too long and were trimmed")
                        log_action(f"    - {lines_too_long} lines were too long and were trimmed")
                    if lines_too_short > 0:
                        print(f"    - {lines_too_short} lines were too short and were padded")
                        log_action(f"    - {lines_too_short} lines were too short and were padded")

    if files_processed > 0:
        print(f"Completed: Processed {files_processed} {file_type} files to ensure {target_length} characters per line")
        log_action(f"Completed: Processed {files_processed} {file_type} files to ensure {target_length} characters per line")
    else:
        print(f"No {file_type} files needed processing (all already at exactly {target_length} characters per line)")
        log_action(f"No {file_type} files needed processing (all already at exactly {target_length} characters per line)")
                                
def detect_available_terms(input_txt_dir):
    """Scan input_txt/<campus>/ subfolders to detect available terms from filenames"""
    terms = set()
    for campus in os.listdir(input_txt_dir):
        campus_dir = os.path.join(input_txt_dir, campus)
        if not os.path.isdir(campus_dir):
            continue
        for filename in os.listdir(campus_dir):
            match = re.match(r'[A-Z]{2}_\d{3}_(\d{3})_\d+\.txt$', filename)
            if match:
                terms.add(match.group(1))
    return sorted(list(terms), reverse=True)

def detect_target_terms(input_dat_dir):
    """Scan input_dat/ for U86TTTFF.dat files to detect terms"""
    terms = set()
    for filename in os.listdir(input_dat_dir):
        match = re.match(r'U86(\d{3})[A-Z]{2}\.dat$', filename)
        if match:
            terms.add(match.group(1))
    return sorted(list(terms), reverse=True)

def find_latest_versions(input_txt_dir, term):
    """Find the latest version of each file for each campus"""
    latest_files = defaultdict(lambda: defaultdict(dict))
    for campus in os.listdir(input_txt_dir):
        campus_dir = os.path.join(input_txt_dir, campus)
        if not os.path.isdir(campus_dir):
            continue
        for filename in os.listdir(campus_dir):
            match = re.match(r'([A-Z]{2})_(\d{3})_(\d{3})_(\d+)\.txt$', filename)
            if match:
                file_type, college, file_term, version = match.groups()
                if file_term != term:
                    continue
                version = int(version)
                if version not in latest_files[file_type][college] or \
                   version > max(latest_files[file_type][college].keys()):
                    latest_files[file_type][college][version] = os.path.join(campus_dir, filename)
    # Get the latest version for each file_type and college
    result = {}
    for file_type in latest_files:
        result[file_type] = {}
        for college in latest_files[file_type]:
            if latest_files[file_type][college]:
                latest_version = max(latest_files[file_type][college].keys())
                result[file_type][college] = latest_files[file_type][college][latest_version]
    return result

def copy_missing_dat_files(input_dat_dir, output_dir, term, updated_files):
    """Copy .dat files for the term from input_dat to output if not already present (not updated)"""
    for filename in os.listdir(input_dat_dir):
        match = re.match(rf'U86{term}[A-Z]{{2}}\.dat$', filename)
        if match:
            output_path = os.path.join(output_dir, filename)
            if filename not in updated_files and not os.path.exists(output_path):
                input_path = os.path.join(input_dat_dir, filename)
                shutil.copy2(input_path, output_path)
                print(f"  Copied unchanged file to output: {filename}")
                log_action(f"  Copied unchanged file to output: {filename}")

def update_all_files(latest_versions, input_dat_dir, output_dir, term):
    """Update all dat files from input_dat, write revised files to output/"""
    updated_files = set()
    for file_type, colleges in latest_versions.items():
        dat_file = f"U86{term}{file_type}.dat"
        dat_path = os.path.join(input_dat_dir, dat_file)
        output_path = os.path.join(output_dir, dat_file)
        if not os.path.exists(dat_path):
            print(f"Input .dat file not found: {dat_path}")
            log_action(f"Input .dat file not found: {dat_path}")
            continue
        print(f"\nProcessing {dat_file}")
        log_action(f"\nProcessing {dat_file}")
        with open(dat_path, 'r') as file:
            current_content = file.readlines()
        new_content = current_content.copy()
        for college, source_file in colleges.items():
            with open(source_file, 'r') as file:
                latest_records = file.readlines()
            # Normalize line endings: strip any trailing \r or \n, then add a single \n
            latest_records = [line.rstrip('\r\n') + '\n' for line in latest_records if line.strip() != '']
            if file_type == "XB":
                # Remove all XB/XE/XF records for this campus/term
                prefixes = [f"{ftype}{college}{term}" for ftype in ("XB", "XE", "XF")]
                new_content = [line for line in new_content if not any(line.startswith(prefix) for prefix in prefixes)]
                # Use the first prefix for insert index (usually XB)
                insert_index = find_insert_index(new_content, prefixes[0])
            else:
                line_prefix = f"{file_type}{college}{term}"
                new_content = [line for line in new_content if not line.startswith(line_prefix)]
                insert_index = find_insert_index(new_content, line_prefix)
            new_content[insert_index:insert_index] = latest_records
            print(f"  - Updated {college} records from {os.path.basename(source_file)} ({len(latest_records)} records)")
            log_action(f"  - Updated {college} records from {os.path.basename(source_file)} ({len(latest_records)} records)")
        os.makedirs(output_dir, exist_ok=True)
        with open(output_path, 'w') as file:
            file.writelines(new_content)
        print(f"  Output file written: {output_path}")
        log_action(f"  Output file written: {output_path}")
        updated_files.add(dat_file)
    return updated_files

def find_insert_index(content_lines, line_prefix):
    """Find the appropriate insertion index for new records"""
    for i, line in enumerate(content_lines):
        # Only compare with lines that have a valid prefix (first 2 chars alphabetic)
        if len(line) >= 2 and line[0:2].isalpha():
            # If this line comes alphabetically after our prefix, insert before it
            if line > line_prefix:
                return i
    
    # If no suitable position found, append at the end
    return len(content_lines)

def generate_tx_file(target_dir, term):
    """Generate a TX file with record counts after all other files are processed"""
    tx_file = f"U86{term}TX.dat"
    tx_path = os.path.join(target_dir, tx_file)
    tx_records = []

    print(f"\nGenerating TX file: {tx_file}")
    log_action(f"\nGenerating TX file: {tx_file}")

    # Scan all DAT files in the target directory for this term
    file_pattern = re.compile(rf"U86{term}([A-Z]{{2}})\.dat$")

    for filename in os.listdir(target_dir):
        match = file_pattern.match(filename)
        if match and filename != tx_file:  # Skip the TX file itself
            file_type = match.group(1)
            file_path = os.path.join(target_dir, filename)

            # Count total records in the file (across all colleges)
            total_count = 0

            with open(file_path, 'r') as file:
                for line in file:
                    # Count any valid record line (starts with alphabetic prefix)
                    if len(line) >= 2 and line[0:2].isalpha():
                        total_count += 1

            # Create a TX record for this file type using 860 as the district code
            target_filename = f"U86{term}{file_type}DAT"
            tx_record = f"TX860{term}{file_type}{total_count:08d}{target_filename}\n"
            tx_records.append(tx_record)

    # Sort records for consistency
    tx_records.sort()

    # Count how many TX records we have and add the special TX record for the TX file itself
    tx_count = len(tx_records) + 1  # +1 for the TX entry we're about to add

    # Add the special TX record with contact information
    contact_info = "LI-BUGG         CHERRY    7148084787          STANCO        GABRIELLE 7148084858          AHN           JIHOON   7148084877                                        "
    tx_record = f"TX860{term}TX{tx_count:08d}U86{term}TXDAT{contact_info}\n"
    tx_records.append(tx_record)

    # Check if file already existed before we write to it
    file_existed = os.path.exists(tx_path)

    # Write the TX file
    with open(tx_path, 'w') as file:
        file.writelines(tx_records)

    print(f"  TX file {tx_file} {'overwritten' if file_existed else 'created'} with {len(tx_records)} entries")
    log_action(f"  TX file {tx_file} {'overwritten' if file_existed else 'created'} with {len(tx_records)} entries")
        
def main():
    log_action("===== Row replace script started =====") 
    parser = argparse.ArgumentParser(description="Update data files from latest versions")
    parser.add_argument("-t", "--term", help="Term code (if not specified, will use most recent term found)")
    parser.add_argument("-x", "--input_txt", help="Input TXT base directory")
    parser.add_argument("-d", "--input_dat", help="Input DAT directory")
    parser.add_argument("-o", "--output", help="Output directory")
    args = parser.parse_args()

    # Set default paths relative to the CLI project structure
    if not args.input_txt:
        args.input_txt = os.path.join(BASE_DIR, "shared_export")
    if not args.input_dat:
        args.input_dat = os.path.join(BASE_DIR, "input_dat")
    if not args.output:
        args.output = os.path.join(BASE_DIR, "final_dat")

    try:
        # Check if required directories exist
        if not os.path.exists(args.input_txt):
            raise ValueError(f"Shared export directory not found: {args.input_txt}")
        if not os.path.exists(args.input_dat):
            raise ValueError(f"Input DAT directory not found: {args.input_dat}")
        
        # Create output directory if it doesn't exist
        os.makedirs(args.output, exist_ok=True)

        # --- CB file length enforcement step ---
        trim_trailing_spaces_in_files(args.input_txt, "CB", 220)

        input_terms = detect_available_terms(args.input_txt)
        if not input_terms:
            raise ValueError(f"No valid data files found in {args.input_txt} directory")
        target_terms = detect_target_terms(args.input_dat)
        if not target_terms:
            raise ValueError(f"No .dat files found in {args.input_dat} directory")
        common_terms = set(input_terms).intersection(set(target_terms))
        term_to_process = args.term
        if not term_to_process:
            for term in input_terms:
                if term in target_terms:
                    term_to_process = term
                    break
        if not term_to_process or term_to_process not in common_terms:
            raise ValueError(f"Term {term_to_process} not found in both directories. Available terms: {', '.join(sorted(common_terms))}")
        
        print(f"Starting row replace process for term {term_to_process}")
        log_action(f"Starting row replace process for term {term_to_process}")
        print(f"Reading latest MIS files from: shared_export")
        log_action(f"Reading latest MIS files from: shared_export")
        print(f"Reading base DAT files from: input_dat")
        log_action(f"Reading base DAT files from: input_dat")
        print(f"Writing updated files to: final_dat")
        log_action(f"Writing updated files to: final_dat")
        
        latest_versions = find_latest_versions(args.input_txt, term_to_process)
        print(f"Found latest versions for {len(latest_versions)} file types:")
        log_action(f"Found latest versions for {len(latest_versions)} file types:")
        all_campuses = set()
        for file_type, colleges in latest_versions.items():
            campus_versions = []
            for campus, path in colleges.items():
                # Extract version from filename
                m = re.match(r'[A-Z]{2}_\d{3}_\d{3}_(\d+)\.txt$', os.path.basename(path))
                if m:
                    version = m.group(1)
                    campus_versions.append(f"{campus} ({version})")
                else:
                    campus_versions.append(f"{campus}")
            print(f"  {file_type}: {', '.join(campus_versions)}")
            log_action(f"  {file_type}: {', '.join(campus_versions)}")
            all_campuses.update(colleges.keys())
        all_campuses = sorted(all_campuses)
        print(f"Available campuses for term {term_to_process}: {', '.join(all_campuses)}")
        log_action(f"Available campuses for term {term_to_process}: {', '.join(all_campuses)}")

        while True:
            try:
                campus_choices = ["ALL"] + all_campuses
                selected_campuses = questionary.checkbox(
                    "Select campus/campuses to process:",
                    choices=campus_choices
                ).ask()
            except KeyboardInterrupt:
                action = questionary.select(
                    "Operation interrupted. What would you like to do?",
                    choices=["Start over", "Main menu"]
                ).ask()
                if action == "Start over":
                    continue
                print("Returning to main menu.")
                log_action("Row replace interrupted; returning to main menu.")
                return 0

            if not selected_campuses:
                print("Operation cancelled by user.")
                log_action("Operation cancelled by user.")
                return 0
            if "ALL" in selected_campuses:
                selected_campuses = list(all_campuses)
            else:
                selected_campuses = sorted([c for c in selected_campuses if c in all_campuses])
            if not selected_campuses:
                print("Operation cancelled by user.")
                log_action("Operation cancelled by user.")
                return 0

            print(f"Processing campuses: {', '.join(selected_campuses)}")
            log_action(f"Processing campuses: {', '.join(selected_campuses)}")

            # Build per-campus file selections
            campus_file_map = {}
            try:
                for campus in selected_campuses:
                    file_labels = []
                    label_to_file_type = {}
                    for file_type, colleges in latest_versions.items():
                        if campus not in colleges:
                            continue
                        path = colleges[campus]
                        m = re.match(r'[A-Z]{2}_\d{3}_\d{3}_(\d+)\.txt$', os.path.basename(path))
                        version = m.group(1) if m else "?"
                        label = f"{file_type} (v{version})"
                        file_labels.append(label)
                        label_to_file_type[label] = file_type

                    if not file_labels:
                        msg = f"No files available for campus {campus}; cancelling."
                        print(msg)
                        log_action(msg)
                        return 0

                    choices = ["ALL"] + sorted(file_labels)
                    selected_files = questionary.checkbox(
                        f"Select file types to replace for campus {campus}:",
                        choices=choices
                    ).ask()
                    if not selected_files:
                        print("Operation cancelled by user.")
                        log_action("Operation cancelled by user.")
                        return 0
                    if "ALL" in selected_files:
                        campus_file_map[campus] = sorted(label_to_file_type.values())
                    else:
                        campus_file_map[campus] = sorted([label_to_file_type[f] for f in selected_files if f in label_to_file_type])

                    if not campus_file_map[campus]:
                        print("Operation cancelled by user.")
                        log_action("Operation cancelled by user.")
                        return 0

            except KeyboardInterrupt:
                action = questionary.select(
                    "Operation interrupted. What would you like to do?",
                    choices=["Start over", "Main menu"]
                ).ask()
                if action == "Start over":
                    continue
                print("Returning to main menu.")
                log_action("Row replace interrupted; returning to main menu.")
                return 0

            summary = []
            for campus in selected_campuses:
                summary.append(f"Campus {campus}: {', '.join(campus_file_map.get(campus, []))}")
            try:
                confirm = questionary.select(
                    f"Proceed with replace for term {term_to_process}?\n  " + "\n  ".join(summary),
                    choices=["Yes", "No (start over)", "Quit"]
                ).ask()
            except KeyboardInterrupt:
                action = questionary.select(
                    "Operation interrupted. What would you like to do?",
                    choices=["Start over", "Main menu"]
                ).ask()
                if action == "Start over":
                    continue
                print("Returning to main menu.")
                log_action("Row replace interrupted; returning to main menu.")
                return 0

            if confirm == "Quit":
                print("Operation cancelled by user.")
                log_action("Operation cancelled by user.")
                return 0
            if confirm != "Yes":
                continue

            # Filter latest_versions to only include selected campuses and file types
            filtered_latest_versions = {}
            for file_type, colleges in latest_versions.items():
                filtered_colleges = {campus: path for campus, path in colleges.items() if campus in selected_campuses and file_type in campus_file_map.get(campus, [])}
                if filtered_colleges:
                    filtered_latest_versions[file_type] = filtered_colleges

            updated_files = update_all_files(filtered_latest_versions, args.input_dat, args.output, term_to_process)
            # Copy any .dat files for the term not already in output
            copy_missing_dat_files(args.input_dat, args.output, term_to_process, updated_files)
            print("\nRow replace process completed successfully")
            log_action("Row replace process completed successfully")
            print(f"Updated DAT files available in final_dat folder for other scripts")
            log_action(f"Updated DAT files available in final_dat folder for other scripts")
            generate_tx_file(args.output, term_to_process)
            log_action("===== Row replace script finished successfully =====")
            break
    except Exception as e:
        print(f"Error: {e}")
        log_action(f"Error: {e}")
        log_action("===== Row replace script finished with error =====")

if __name__ == "__main__":
    main()
