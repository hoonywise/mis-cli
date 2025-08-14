#!/usr/bin/env python3
"""
MIS Error Record Stripper

This script removes problematic records from MIS DAT files based on analyst-marked
error reports. It reads CSV files with analyst markings and removes specified 
records from corresponding DAT files.

Author: MIS Department  
Date: July 2025
"""


import csv
import os
import sys
import re
import argparse
from pathlib import Path
from collections import defaultdict
import questionary
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

def find_error_reports(error_reports_dir):
    """Find all error CSV files in the error reports directory."""
    if not error_reports_dir.exists():
        return []
    
    error_files = list(error_reports_dir.glob("error_*.csv"))
    return sorted(error_files)

def process_marked_error_report(csv_file, strip_column="STRIP"):
    """Extract records marked for stripping by analysts."""
    print(f"Processing marked error report: {csv_file.name}")
    log_action(f"Processing marked error report: {csv_file.name}")
    
    file_type_records = defaultdict(set)
    total_rows = 0
    marked_rows = 0
    
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            # Try to detect if it's a CSV with headers
            sample = f.read(1024)
            f.seek(0)
            
            # Check if first row contains expected headers
            first_line = f.readline().strip()
            f.seek(0)
            
            has_headers = any(header in first_line.upper() for header in 
                            ['ERROR TYPE', 'FILE TYPE', 'RECORD NUMBER', 'STRIP'])
            
            reader = csv.reader(f)
            
            if has_headers:
                headers = next(reader)
                # Find column indices
                try:
                    error_type_idx = next(i for i, h in enumerate(headers) if 'ERROR TYPE' in h.upper())
                    file_type_idx = next(i for i, h in enumerate(headers) if 'FILE TYPE' in h.upper())
                    record_num_idx = next(i for i, h in enumerate(headers) if 'RECORD NUMBER' in h.upper())
                    strip_idx = next(i for i, h in enumerate(headers) if strip_column.upper() in h.upper())
                except StopIteration:
                    print(f"Error: Required columns not found in {csv_file.name}")
                    log_action(f"Error: Required columns not found in {csv_file.name}")
                    print(f"Expected columns: Error Type, File Type, Record Number, {strip_column}")                    
                    log_action(f"Expected columns: Error Type, File Type, Record Number, {strip_column}")
                    return {}, 0, 0
            else:
                # Assume standard positions if no headers
                error_type_idx, file_type_idx, record_num_idx = 2, 3, 4
                strip_idx = 5  # Assume STRIP column is 6th column (index 5)
            
            for row in reader:
                total_rows += 1
                
                # Skip if not enough columns
                if len(row) <= max(error_type_idx, file_type_idx, record_num_idx, strip_idx):
                    continue
                
                # Check if marked for stripping
                strip_value = row[strip_idx].strip().upper()
                if strip_value not in ['Y', 'YES', '1', 'TRUE']:
                    continue
                
                marked_rows += 1
                file_type = row[file_type_idx].strip().upper()
                record_number = row[record_num_idx].strip()
                
                if file_type and record_number.isdigit():
                    # Consolidate XE/XF into XB
                    if file_type in ['XE', 'XF']:
                        file_type = 'XB'
                    
                    file_type_records[file_type].add(int(record_number))
        
        print(f"  Found {marked_rows} records marked for stripping out of {total_rows} total rows")
        log_action(f"  Found {marked_rows} records marked for stripping out of {total_rows} total rows")
        if file_type_records:
            print(f"  File types to process: {', '.join(sorted(file_type_records.keys()))}")
            log_action(f"  File types to process: {', '.join(sorted(file_type_records.keys()))}")
            for file_type, records in file_type_records.items():
                print(f"    {file_type}: {len(records)} records")
                log_action(f"    {file_type}: {len(records)} records")
        
        return file_type_records, total_rows, marked_rows
        
    except Exception as e:
        print(f"Error processing {csv_file.name}: {e}")
        log_action(f"Error processing {csv_file.name}: {e}")
        return {}, 0, 0

def find_dat_files(input_dat_dir):
    """Find all DAT files in the input directory."""
    if not input_dat_dir.exists():
        return {}
    
    dat_files = {}
    for dat_file in input_dat_dir.glob("*.dat"):
        # Extract file type from DAT filename (e.g., U86249CB.dat -> CB)
        match = re.search(r'(\w*?)([A-Z]{2})\.dat$', dat_file.name, re.IGNORECASE)
        if match:
            file_type = match.group(2).upper()
            dat_files[file_type] = dat_file
    
    return dat_files

def strip_records_from_dat(input_file, output_file, records_to_remove):
    """Remove specified record numbers from DAT file."""
    if not records_to_remove:
        # No records to remove, just copy the file
        import shutil
        shutil.copy2(input_file, output_file)
        return 0
    
    removed_count = 0
    
    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            
            for line_num, line in enumerate(infile, 1):
                if line_num in records_to_remove:
                    removed_count += 1
                else:
                    outfile.write(line)
        
        return removed_count
        
    except Exception as e:
        print(f"    Error processing {input_file.name}: {e}")
        log_action(f"    Error processing {input_file.name}: {e}")
        return 0

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
    log_action("===== Error Stripper script started =====")
    """Main function to orchestrate the error stripping process."""
    parser = argparse.ArgumentParser(description="Strip problematic records from MIS DAT files")
    parser.add_argument("-i", "--input_dat", help="Input DAT directory")
    parser.add_argument("-e", "--error_reports", help="Error reports directory")
    parser.add_argument("-o", "--output", help="Output directory")
    parser.add_argument("-c", "--strip_column", default="STRIP", 
                       help="Column name that marks records for stripping (default: STRIP)")
    args = parser.parse_args()
    
    # Set default paths relative to the CLI project structure
    if not args.input_dat:
        args.input_dat = Path(BASE_DIR) / "input_dat"
    else:
        args.input_dat = Path(args.input_dat)
    
    # Set the error reports directory to completed
    if not args.error_reports:
        args.error_reports = Path(BASE_DIR) / "error_report_loader" / "completed"
    else:
        args.error_reports = Path(args.error_reports)
    
    # Set output directory
    if not args.output:
        args.output = Path(BASE_DIR) / "final_dat"
    else:
        args.output = Path(args.output)
    args.output.mkdir(parents=True, exist_ok=True)

    # Find all error_XX.csv files
    error_files = sorted(args.error_reports.glob("error_*.csv"))
    if not error_files:
        raise ValueError("No error_*.csv files found in error_report_loader/completed directory")

    # Find the highest error report number
    import re
    error_nums = []
    for ef in error_files:
        m = re.match(r"error_(\d+)\.csv", ef.name)
        if m:
            error_nums.append(int(m.group(1)))
    if not error_nums:
        raise ValueError("No valid error_XX.csv files found.")

    highest_num = max(error_nums)
    highest_file = args.error_reports / f"error_{highest_num:02d}.csv"

    print(f"Highest error report found: error_{highest_num:02d}.csv")
    log_action(f"Highest error report found: error_{highest_num:02d}.csv")
    user_input = input(
        f"Press Enter to process error_{highest_num:02d}.csv, "
        "enter a different number (e.g., 03) to process error_XX.csv, "
        "or type 'q' to cancel: "
    ).strip()

    if user_input.lower() == 'q':
        print("Operation cancelled by user.")
        log_action("Operation cancelled by user.")
        return 0

    if user_input:
        try:
            num = int(user_input)
            selected_file = args.error_reports / f"error_{num:02d}.csv"
            if not selected_file.exists():
                print(f"File {selected_file.name} does not exist.")
                log_action(f"File {selected_file.name} does not exist.")
                return 0
        except ValueError:
            print("Invalid input. Please enter a number like 03 or 'q' to cancel.")
            log_action("Invalid input. Please enter a number like 03 or 'q' to cancel.")
            return 0
    else:
        selected_file = highest_file


    print(f"Processing {selected_file.name}...")
    log_action(f"Processing {selected_file.name}...")

    # Read CSV into list of dicts
    with open(selected_file, 'r', encoding='utf-8-sig') as f:
        reader = list(csv.DictReader(f))
        fieldnames = reader[0].keys() if reader else []

    # Add STRIP column if missing
    if 'STRIP' not in fieldnames:
        fieldnames = list(fieldnames) + ['STRIP']
        for row in reader:
            row['STRIP'] = ''

    # Interactive selection loop
    while True:
        # 1. Prompt for Error Type
        error_types = sorted({row['Error Type'].strip() for row in reader if row.get('Error Type', '').strip()})
        if not error_types:
            print("No Error Types found in the error report.")
            log_action("No Error Types found in the error report.")
            return 0
        print("Tip: Press Enter with nothing selected to go back to the previous menu.")
        log_action("Tip: Press Enter with nothing selected to go back to the previous menu.")
        selected_error_types = questionary.checkbox(
            "Select Error Type(s) to process:",
            choices=["ALL"] + error_types
        ).ask()
        if not selected_error_types:
            print("No Error Type selected. Exiting.")
            log_action("No Error Type selected. Exiting.")
            return 0
        if "ALL" in selected_error_types:
            selected_error_types = error_types

        # 2. Prompt for File Type (filtered by Error Type)
        file_types = sorted({row['File Type'].strip() for row in reader if row.get('Error Type', '').strip() in selected_error_types and row.get('File Type', '').strip()})
        if not file_types:
            print("No File Types found for the selected Error Type(s). Exiting.")
            log_action("No File Types found for the selected Error Type(s). Exiting.")
            return 0
        print("Tip: Press Enter with nothing selected to go back to the previous menu.")
        log_action("Tip: Press Enter with nothing selected to go back to the previous menu.")
        selected_file_types = questionary.checkbox(
            "Select File Type(s) to process:",
            choices=["ALL"] + file_types
        ).ask()
        if not selected_file_types:
            print("No File Type selected. Exiting.")
            log_action("No File Type selected. Exiting.")
            return 0
        if "ALL" in selected_file_types:
            selected_file_types = file_types

        # 3. Confirm
        confirm = questionary.select(
            "Proceed with stripping?",
            choices=["Yes", "No (back to Error Type selection)", "Quit to CLI"]
        ).ask()
        if confirm == "Yes":
            break
        elif confirm.startswith("No"):
            continue
        elif confirm.lower().startswith("quit"):
            print("Operation cancelled by user.")
            log_action("Operation cancelled by user.")
            return 0

    # Mark STRIP='Y' for selected rows
    marked_rows = 0
    for row in reader:
        if row.get('Error Type', '').strip() in selected_error_types and row.get('File Type', '').strip() in selected_file_types:
            row['STRIP'] = 'Y'
            marked_rows += 1

    # Write back to CSV (overwrite)
    with open(selected_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reader)

    print(f"\nMarked {marked_rows} records for stripping in {selected_file.name}.")
    log_action(f"\nMarked {marked_rows} records for stripping in {selected_file.name}.")

    # Now proceed with the rest of the stripping logic as before
    all_records_to_strip = defaultdict(set)
    file_records, total_rows, marked_rows2 = process_marked_error_report(
        selected_file, args.strip_column)
    total_marked = marked_rows2
    for file_type, records in file_records.items():
        all_records_to_strip[file_type].update(records)

    if not all_records_to_strip:
        print(f"\nNo records marked for stripping found in {selected_file.name}.")
        log_action(f"\nNo records marked for stripping found in {selected_file.name}.")
        return

    print(f"\nTotal records marked for stripping: {total_marked}")
    log_action(f"\nTotal records marked for stripping: {total_marked}")
    print(f"File types to process: {len(all_records_to_strip)}")
    log_action(f"File types to process: {len(all_records_to_strip)}")
    for file_type, records in all_records_to_strip.items():
        print(f"  {file_type}: {len(records)} unique records")
        log_action(f"  {file_type}: {len(records)} unique records")

    # Find available DAT files
    available_dat_files = find_dat_files(args.input_dat)
    if not available_dat_files:
        raise ValueError("No DAT files found in input directory")

    print(f"\nAvailable DAT files: {len(available_dat_files)}")
    log_action(f"\nAvailable DAT files: {len(available_dat_files)}")
    for file_type, dat_file in available_dat_files.items():
        print(f"  {file_type}: {dat_file.name}")
        log_action(f"  {file_type}: {dat_file.name}")

    # Process each file type
    print(f"\nProcessing files...")
    log_action(f"\nProcessing files...")
    total_removed = 0
    processed_files = 0

    for file_type, records_to_remove in all_records_to_strip.items():
        if file_type not in available_dat_files:
            print(f"  Warning: No DAT file found for {file_type} - skipping")
            log_action(f"  Warning: No DAT file found for {file_type} - skipping")
            continue

        input_file = available_dat_files[file_type]
        output_file = args.output / input_file.name

        print(f"  Processing {file_type}: {input_file.name}")
        log_action(f"  Processing {file_type}: {input_file.name}")
        print(f"    Removing {len(records_to_remove)} records...")
        log_action(f"    Removing {len(records_to_remove)} records...")

        removed = strip_records_from_dat(input_file, output_file, records_to_remove)

        print(f"    Removed {removed} records → {output_file.name}")
        log_action(f"    Removed {removed} records → {output_file.name}")
        total_removed += removed
        processed_files += 1

    # Copy any DAT files that don't need stripping
    for file_type, dat_file in available_dat_files.items():
        if file_type not in all_records_to_strip:
            output_file = args.output / dat_file.name
            if not output_file.exists():
                import shutil
                shutil.copy2(dat_file, output_file)
                print(f"  Copied {file_type}: {dat_file.name} (no errors to strip)")
                log_action(f"  Copied {file_type}: {dat_file.name} (no errors to strip)")
                processed_files += 1

    print(f"\n=== Error Stripping Complete ===")
    log_action(f"\n=== Error Stripping Complete ===")
    print(f"Files processed: {processed_files}")
    log_action(f"Files processed: {processed_files}")
    print(f"Total records removed: {total_removed}")
    log_action(f"Total records removed: {total_removed}")
    print(f"Clean files available in: final_dat")
    log_action(f"Clean files available in: final_dat")

    # --- Add TX file generation here ---
    # Try to infer the term from one of the DAT filenames
    dat_files = list(args.output.glob("U86*??.dat"))
    if dat_files:
        print(f"  Checking DAT filename for term extraction: {dat_files[0].name}")
        log_action(f"  Checking DAT filename for term extraction: {dat_files[0].name}")
        match = re.match(r'U86([A-Z0-9]{3})[A-Z]{2}\.dat$', dat_files[0].name, re.IGNORECASE)
        if match:
            term = match.group(1)
            generate_tx_file(str(args.output), term)
        else:
            print("Could not infer term code from DAT filenames. TX file not generated.")
            log_action("Could not infer term code from DAT filenames. TX file not generated.")
    else:
        print("No DAT files found in output directory. TX file not generated.")     
        log_action("No DAT files found in output directory. TX file not generated.")     

    # --- Move processed error report to loader/pending ---
    pending_dir = Path(BASE_DIR) / "error_report_loader" / "pending"
    pending_dir.mkdir(parents=True, exist_ok=True)
    dest = pending_dir / selected_file.name
    try:
        selected_file.rename(dest)
        print(f"Moved {selected_file.name} to {dest}")
        log_action(f"Moved {selected_file.name} to {dest}")
    except Exception as e:
        print(f"Could not move {selected_file.name} to {dest}: {e}")      
        log_action(f"Could not move {selected_file.name} to {dest}: {e}")         

    log_action("===== Error Stripper script finished =====")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        log_action("\nOperation cancelled by user.")
        sys.exit(1)