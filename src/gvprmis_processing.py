import os
import glob
import sys
import re
import shutil
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

def clean_folder(folder):
    """Delete all files and subfolders in the given folder, skipping locked items."""
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isdir(file_path):
            # Try to delete contents of subfolder, not the subfolder itself
            for subname in os.listdir(file_path):
                subpath = os.path.join(file_path, subname)
                try:
                    if os.path.isfile(subpath) or os.path.islink(subpath):
                        os.unlink(subpath)
                    elif os.path.isdir(subpath):
                        shutil.rmtree(subpath)
                except Exception as e:
                    print(f"Warning: Could not delete {subpath}: {e}")
                    log_action(f"Warning: Could not delete {subpath}: {e}")
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Warning: Could not delete {file_path}: {e}")
            log_action(f"Warning: Could not delete {file_path}: {e}")

def extract_file_info(first_line):
    """Extract file type, campus, and term from the first line of the dat file"""
    if len(first_line) < 8:
        raise ValueError("First line too short to extract file info")
    
    # Extract first 8 characters (e.g., "CB863253")
    file_prefix = first_line[:8]
    
    # Parse the components
    file_type = file_prefix[:2]    # FF (e.g., "CB")
    campus = file_prefix[2:5]      # CCC (e.g., "863")
    term = file_prefix[5:8]        # TTT (e.g., "253")
    
    return file_type, campus, term

def select_latest_dat_files(input_folder):
    """Select the highest numbered gvprmis, svrcasy, or svrppca file for each file type/campus/term combination"""
    gvprmis_pattern = os.path.join(input_folder, "gvprmis_*.dat")
    svrcasy_pattern = os.path.join(input_folder, "svrcasy_*.dat")
    svrppca_pattern = os.path.join(input_folder, "svrppca_*.dat")
    all_gvprmis = glob.glob(gvprmis_pattern)
    all_svrcasy = glob.glob(svrcasy_pattern)
    all_svrppca = glob.glob(svrppca_pattern)
    
    file_groups = {}
    # --- Process gvprmis files ---
    gvprmis_num_pattern = re.compile(r'gvprmis_(\d+)\.dat$')
    for file_path in all_gvprmis:
        filename = os.path.basename(file_path)
        match = gvprmis_num_pattern.search(filename)
        if not match:
            continue
        file_number = int(match.group(1))
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                first_line = file.readline().strip()
            if not first_line:
                continue
            file_type, campus, term = extract_file_info(first_line)
            key = (file_type, campus, term)
            if key not in file_groups or file_number > file_groups[key]['number']:
                file_groups[key] = {'number': file_number, 'path': file_path}
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            log_action(f"Error reading {filename}: {e}")
            continue

    # --- Process svrcasy files (for SY files) ---
    svrcasy_num_pattern = re.compile(r'svrcasy_(\d+)\.dat$')
    for file_path in all_svrcasy:
        filename = os.path.basename(file_path)
        match = svrcasy_num_pattern.search(filename)
        if not match:
            continue
        file_number = int(match.group(1))
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                first_line = file.readline().strip()
            if not first_line:
                continue
            file_type, campus, term = extract_file_info(first_line)
            if file_type != "SY":
                continue  # Only process SY files from svrcasy
            key = (file_type, campus, term)
            if key not in file_groups or file_number > file_groups[key]['number']:
                file_groups[key] = {'number': file_number, 'path': file_path}
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            log_action(f"Error reading {filename}: {e}")
            continue

    # --- Process svrppca files (for PP files) ---
    svrppca_num_pattern = re.compile(r'svrppca_(\d+)\.dat$')
    for file_path in all_svrppca:
        filename = os.path.basename(file_path)
        match = svrppca_num_pattern.search(filename)
        if not match:
            continue
        file_number = int(match.group(1))
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                first_line = file.readline().strip()
            if not first_line:
                continue
            file_type, campus, term = extract_file_info(first_line)
            if file_type != "PP":
                continue  # Only process PP files from svrppca
            key = (file_type, campus, term)
            if key not in file_groups or file_number > file_groups[key]['number']:
                file_groups[key] = {'number': file_number, 'path': file_path}
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            log_action(f"Error reading {filename}: {e}")
            continue
    
    # Return the latest file for each group
    latest_files = [info['path'] for info in file_groups.values()]
    
    # Show which files were selected
    all_files = all_gvprmis + all_svrcasy + all_svrppca
    if len(all_files) > len(latest_files):
        print(f"Found {len(all_files)} total dat files, selected {len(latest_files)} latest versions:")
        log_action(f"Found {len(all_files)} total dat files, selected {len(latest_files)} latest versions:")
        for key, info in file_groups.items():
            file_type, campus, term = key
            filename = os.path.basename(info['path'])
            print(f"  {file_type}_{campus}_{term}: {filename} (version: {info['number']})")
            log_action(f"  {file_type}_{campus}_{term}: {filename} (version: {info['number']})")
    # Always prompt, regardless of file counts
    while True:
        user_input = input("Proceed with processing? (Y/q): ").strip().lower()
        if user_input == "y":
            break
        elif user_input == "q":
            print("Operation cancelled by user.")
            log_action("Operation cancelled by user.")
            sys.exit(3)
        else:
            print("Please enter Y or Q.")
            log_action("Please enter Y or Q.")
    
    return latest_files

def get_next_version_number(output_folder, file_type, campus, term):
    """Determine the next version number for the output file."""
    output_file_type = "XB" if file_type in ["XE", "XF"] else file_type
    pattern = rf"{output_file_type}_{campus}_{term}_(\d+)\.txt"

    versions = []
    regex = re.compile(pattern)
    if os.path.exists(output_folder):
        for fname in os.listdir(output_folder):
            m = regex.match(fname)
            if m:
                versions.append(int(m.group(1)))
    if not versions:
        return "01"
    next_version = max(versions) + 1
    return f"{next_version:02d}"

def group_xb_files(dat_files):
    """Group XB, XE, XF files by campus and term for combination"""
    xb_groups = {}
    other_files = []
    
    for file_path in dat_files:
        try:
            # Read first line to get file info
            with open(file_path, 'r', encoding='utf-8') as file:
                first_line = file.readline().strip()
            
            if not first_line:
                continue
                
            file_type, campus, term = extract_file_info(first_line)
            
            if file_type in ['XB', 'XE', 'XF']:
                # Group by campus and term
                key = (campus, term)
                if key not in xb_groups:
                    xb_groups[key] = {'XB': None, 'XE': None, 'XF': None}
                xb_groups[key][file_type] = file_path
            else:
                other_files.append(file_path)
                
        except Exception as e:
            print(f"Error reading {os.path.basename(file_path)}: {e}")
            log_action(f"Error reading {os.path.basename(file_path)}: {e}")
            other_files.append(file_path)  # Treat as regular file
    
    return xb_groups, other_files

def combine_xb_files(xb_group, campus, term, output_folder):
    """Combine XB, XE, XF files into a single XB output file"""
    try:
        # Get next version number for XB file
        campus_folder = os.path.join(output_folder, campus)
        os.makedirs(campus_folder, exist_ok=True)
        version = get_next_version_number(campus_folder, "XB", campus, term)
        
        # Create output filename
        output_filename = f"XB_{campus}_{term}_{version}.txt"
        output_file_path = os.path.join(campus_folder, output_filename)
        
        # Combine files in order: XB, XE, XF
        file_order = ['XB', 'XE', 'XF']
        total_lines = 0
        files_used = []
        
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            for file_type in file_order:
                if xb_group[file_type] is not None:
                    input_file_path = xb_group[file_type]
                    files_used.append(os.path.basename(input_file_path))
                    
                    # Copy content from input file
                    with open(input_file_path, 'r', encoding='utf-8') as input_file:
                        lines = input_file.readlines()
                        output_file.writelines(lines)
                        total_lines += len(lines)
        
        print(f"Combined XB files → {os.path.join(campus, output_filename)}")
        log_action(f"Combined XB files → {os.path.join(campus, output_filename)}")
        print(f"  Campus: {campus}, Term: {term}, Version: {version}")
        log_action(f"  Campus: {campus}, Term: {term}, Version: {version}")
        print(f"  Files combined: {', '.join(files_used)}")
        log_action(f"  Files combined: {', '.join(files_used)}")
        print(f"  Total lines: {total_lines}")
        log_action(f"  Total lines: {total_lines}")
        
        return os.path.join(campus, output_filename)
        
    except Exception as e:
        print(f"Error combining XB files for campus {campus}, term {term}: {e}")
        log_action(f"Error combining XB files for campus {campus}, term {term}: {e}")
        return None

def process_regular_dat_file(input_file_path, output_folder):
    """Process a single non-XB dat file and copy it to output folder with new name"""
    try:
        # Read the first line to extract file info
        with open(input_file_path, 'r', encoding='utf-8') as file:
            first_line = file.readline().strip()
        
        if not first_line:
            print(f"Warning: {os.path.basename(input_file_path)} is empty, skipping")
            log_action(f"Warning: {os.path.basename(input_file_path)} is empty, skipping")
            return None
        
        # Extract file information
        file_type, campus, term = extract_file_info(first_line)
        
        # Validate campus code
        if campus not in ['860', '861', '862', '863']:
            print(f"Warning: {os.path.basename(input_file_path)} has invalid campus code '{campus}', skipping")
            log_action(f"Warning: {os.path.basename(input_file_path)} has invalid campus code '{campus}', skipping")
            return None
        
        # Ensure campus subfolder exists
        campus_folder = os.path.join(output_folder, campus)
        os.makedirs(campus_folder, exist_ok=True)
        
        # Get next version number
        version = get_next_version_number(campus_folder, file_type, campus, term)
        
        # Create output filename
        output_filename = f"{file_type}_{campus}_{term}_{version}.txt"
        output_file_path = os.path.join(campus_folder, output_filename)
        
        # Copy the file (preserves exact content and formatting)
        shutil.copy2(input_file_path, output_file_path)
        
        print(f"Processed: {os.path.basename(input_file_path)} → {os.path.join(campus, output_filename)}")
        log_action(f"Processed: {os.path.basename(input_file_path)} → {os.path.join(campus, output_filename)}")
        print(f"  File Type: {file_type}, Campus: {campus}, Term: {term}, Version: {version}")
        log_action(f"  File Type: {file_type}, Campus: {campus}, Term: {term}, Version: {version}")
        
        return os.path.join(campus, output_filename)
        
    except Exception as e:
        print(f"Error processing {os.path.basename(input_file_path)}: {e}")
        log_action(f"Error processing {os.path.basename(input_file_path)}: {e}")
        return None

def main():
    log_action("===== GVPRMIS Processing script started =====")
    try:
        """Main function to process all dat files"""
        # Use new data folder structure
        input_folder = os.path.join(BASE_DIR, "manual_download")
        output_folder = os.path.join(BASE_DIR, "shared_export")
        
        # Check if input folder exists
        if not os.path.exists(input_folder):
            print(f"Error: Manual download folder '{input_folder}' not found")
            log_action(f"Error: Manual download folder '{input_folder}' not found")
            print("Please create the folder and place your manually downloaded .dat files there")
            log_action("Please create the folder and place your manually downloaded .dat files there")
            return
        
        # Create output folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"Created shared export folder: {output_folder}")
            log_action(f"Created shared export folder: {output_folder}")
        
        # Select only the latest files for each file type/campus/term
        dat_files = select_latest_dat_files(input_folder)  # Updated function name
        
        if not dat_files:
            print(f"No dat files found in manual download folder")
            log_action(f"No dat files found in manual download folder")
            print("Supported file types: gvprmis_*.dat, svrcasy_*.dat")
            log_action("Supported file types: gvprmis_*.dat, svrcasy_*.dat")
            return
        
        print(f"\nProcessing {len(dat_files)} selected dat file(s):")
        log_action(f"Processing {len(dat_files)} selected dat file(s):")
        for file_path in dat_files:
            print(f"  - {os.path.basename(file_path)}")
            log_action(f"  - {os.path.basename(file_path)}")
        
        print("\nAnalyzing files...")
        log_action("Analyzing files...")
        
        # Group XB, XE, XF files and separate other files
        xb_groups, other_files = group_xb_files(dat_files)
        
        # Process files
        processed_files = []
        failed_files = []
        
        # Process XB file groups (combine XB, XE, XF)
        if xb_groups:
            print(f"\nProcessing {len(xb_groups)} XB file group(s)...")
            log_action(f"Processing {len(xb_groups)} XB file group(s)...")
            for (campus, term), xb_group in xb_groups.items():
                result = combine_xb_files(xb_group, campus, term, output_folder)
                if result:
                    processed_files.append(result)
                else:
                    failed_files.append(f"XB group for campus {campus}, term {term}")
        
        # Process other files normally
        if other_files:
            print(f"\nProcessing {len(other_files)} regular file(s)...")
            log_action(f"Processing {len(other_files)} regular file(s)...")
            for input_file_path in other_files:
                result = process_regular_dat_file(input_file_path, output_folder)
                if result:
                    processed_files.append(result)
                else:
                    failed_files.append(os.path.basename(input_file_path))
        
        # Summary
        print(f"\n{'='*50}")
        log_action(f"\n{'='*50}")
        print(f"Processing Summary:")
        log_action(f"Processing Summary:")
        print(f"  Successfully processed: {len(processed_files)} files")
        log_action(f"  Successfully processed: {len(processed_files)} files")
        print(f"  Failed: {len(failed_files)} files")
        log_action(f"  Failed: {len(failed_files)} files")

        if processed_files:
            print(f"\nGenerated files:")
            log_action(f"\nGenerated files:")
            for filename in sorted(processed_files):
                print(f"  - {filename}")
                log_action(f"  - {filename}")

        if failed_files:
            print(f"\nFailed files:")
            log_action(f"\nFailed files:")
            for filename in failed_files:
                print(f"  - {filename}")
                log_action(f"  - {filename}")
        
        print(f"\nFiles saved to shared export folder for other scripts to use")
        log_action(f"\nFiles saved to shared export folder for other scripts to use")
        log_action("===== GVPRMIS Processing script completed =====")
    except Exception as e:
        print(f"Error: {e}")
        log_action(f"Error: {e}")
        log_action("===== GVPRMIS Processing script finished with error =====")

if __name__ == "__main__":
    main()