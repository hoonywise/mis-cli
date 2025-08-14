import os
import re
import glob
import sys
import argparse
from collections import defaultdict
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
                        # Add final line ending if original content ended with one
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

def detect_available_terms(input_dir):
    terms = set()
    file_pattern = re.compile(r'[A-Z]{2}_\d{3}_(\d{3})_\d+(?:_rev)?\.txt$')
    for root, _, files in os.walk(input_dir):
        for filename in files:
            match = file_pattern.match(filename)
            if match:
                terms.add(match.group(1))
    return sorted(list(terms), reverse=True)

def detect_target_terms(target_dir):
    """Scan target directory to detect terms from dat files"""
    terms = set()
    file_pattern = re.compile(r'U86(\d{3})[A-Z]{2}\.dat$')
    
    for filename in os.listdir(target_dir):
        match = file_pattern.match(filename)
        if match:
            terms.add(match.group(1))
    
    return sorted(list(terms), reverse=True)  # Return most recent terms first

def find_latest_versions(input_dir, term):
    latest_files = defaultdict(lambda: defaultdict(dict))
    file_pattern = re.compile(r'([A-Z]{2})_(\d{3})_(\d{3})_(\d+)(?:_rev)?\.txt$')
    for root, _, files in os.walk(input_dir):
        for filename in files:
            match = file_pattern.match(filename)
            if match:
                file_type, college, file_term, version = match.groups()
                if file_term != term:
                    continue
                version = int(version)
                file_path = os.path.join(root, filename)
                if version not in latest_files[file_type][college] or \
                   "_rev" in filename and version in latest_files[file_type][college]:
                    latest_files[file_type][college][version] = file_path
    result = {}
    for file_type in latest_files:
        result[file_type] = {}
        for college in latest_files[file_type]:
            if latest_files[file_type][college]:
                latest_version = max(latest_files[file_type][college].keys())
                result[file_type][college] = latest_files[file_type][college][latest_version]
    return result

def create_target_files(latest_versions, target_dir, term):
    """Create new target files by concatenating the raw bytes of the latest input files (mimics manual copy-paste)."""
    for file_type, colleges in latest_versions.items():
        target_file = f"U86{term}{file_type}.dat"
        target_path = os.path.join(target_dir, target_file)
        print(f"\nCreating target file: {target_file}")
        log_action(f"\nCreating target file: {target_file}")

        file_existed = os.path.exists(target_path)

        with open(target_path, 'wb') as outfile:
            for college, source_file in colleges.items():
                with open(source_file, 'rb') as infile:
                    data = infile.read()
                    # Remove all trailing line endings
                    while data.endswith(b'\r\n') or data.endswith(b'\n'):
                        if data.endswith(b'\r\n'):
                            data = data[:-2]
                        elif data.endswith(b'\n'):
                            data = data[:-1]
                    # Only write if the file is not empty
                    if data:
                        outfile.write(data + b'\r\n')    
                file_info = os.path.basename(source_file)
                print(f"  - Copied {college} records from {file_info}")
                log_action(f"  - Copied {college} records from {file_info}")

        print(f"  Target file created by raw copy with {len(colleges)} source files")
        log_action(f"  Target file created by raw copy with {len(colleges)} source files")
        if file_existed:
            print(f"  Note: Existing file was overwritten")
            log_action(f"  Note: Existing file was overwritten")

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
    
    print(f"  TX file created with {len(tx_records)} entries")
    log_action(f"  TX file created with {len(tx_records)} entries")
    
    # Report if we overwrote an existing file
    if file_existed:
        print(f"  Note: Existing file was overwritten")
        log_action(f"  Note: Existing file was overwritten")
# ...existing code...

def main():
    log_action("===== DAT Paste script started =====")
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description="Create data files from latest versions")
    parser.add_argument("-t", "--term", help="Term code (if not specified, will use most recent term found)")
    parser.add_argument("-i", "--input", help="Input directory")
    parser.add_argument("-o", "--output", help="Output directory")
    args = parser.parse_args()

    # Set default paths relative to the CLI project structure
    if not args.input:
        args.input = os.path.join(BASE_DIR, "shared_export")
    if not args.output:
        args.output = os.path.join(BASE_DIR, "final_dat")
    
    try:
        # Check if input directory exists
        if not os.path.exists(args.input):
            raise ValueError(f"Shared export directory not found: {args.input}")
        
        # Create output directory if it doesn't exist
        os.makedirs(args.output, exist_ok=True)
        
        # Detect available terms in input directory
        input_terms = detect_available_terms(args.input)
        if not input_terms:
            raise ValueError(f"No valid data files found in shared export directory")
        
        # Determine which term to process
        term_to_process = args.term
        if not term_to_process:
            # Use most recent term by default
            term_to_process = input_terms[0]
        
        if term_to_process not in input_terms:
            raise ValueError(f"Term {term_to_process} not found in shared export directory. Available terms: {', '.join(input_terms)}")
        
        print(f"Starting DAT paste process for term {term_to_process}")
        log_action(f"Starting DAT paste process for term {term_to_process}")
        print(f"Reading from: shared_export")
        log_action(f"Reading from: shared_export")
        print(f"Writing to: final_dat")
        log_action(f"Writing to: final_dat")    

        # First, trim trailing spaces in CB files
        trim_trailing_spaces_in_files(args.input, "CB", 220)
        
        # Find the latest versions of all files for this term
        latest_versions = find_latest_versions(args.input, term_to_process)
        
        # Report what we found
        print(f"Found latest versions for {len(latest_versions)} file types:")
        log_action(f"Found latest versions for {len(latest_versions)} file types:")
        for file_type, colleges in latest_versions.items():
            campus_versions = []
            for campus, path in colleges.items():
                # Extract version from filename
                m = re.match(r'[A-Z]{2}_\d{3}_\d{3}_(\d+)(?:_rev)?\.txt$', os.path.basename(path))
                if m:
                    version = m.group(1)
                    campus_versions.append(f"{campus} ({version})")
                else:
                    campus_versions.append(f"{campus}")
            print(f"  {file_type}: {', '.join(campus_versions)}")
            log_action(f"  {file_type}: {', '.join(campus_versions)}")

        # Prompt user before proceeding (only once)
        while True:
            user_input = input("Proceed with DAT processing? (Y/N/q): ").strip().lower()
            if user_input == "y":
                break
            elif user_input == "n":
                sys.exit(2)
            elif user_input == "q":
                sys.exit(3)
            else:
                print("Please enter Y, N, or Q.")   
                log_action("Please enter Y, N, or Q.") 
        
        # Create target files for this term
        create_target_files(latest_versions, args.output, term_to_process)
        
        # Generate TX file with record counts
        generate_tx_file(args.output, term_to_process)
        
        print("\nDAT paste process completed successfully")
        log_action("\nDAT paste process completed successfully")
        print("Final DAT files available in final_dat folder")
        log_action("Final DAT files available in final_dat folder")
        log_action("===== DAT Paste script finished =====")
    
    except Exception as e:
        print(f"Error: {e}")
        log_action(f"Error: {e}")
        log_action("===== DAT Paste script finished with error =====")

if __name__ == "__main__":
    main()