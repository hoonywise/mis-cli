#!/usr/bin/env python3
"""
DAT File Stager

This script copies DAT files from final_dat to input_dat, replacing any existing files.
This allows you to stage processed files as input for further processing workflows.

Author: Jihoon Ahn
Date: July 2025
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
import re
from datetime import datetime

BASE_DIR = os.environ.get("MIS_INSTANCE_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
DATA_DIR = os.path.join(BASE_DIR, "data")
MASTER_LOG = os.path.join(BASE_DIR, "mis-cli.log")
HISTORY_LOG = os.path.join(BASE_DIR, "history.log")

def log_action(action):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"{timestamp} - {action}\n"
    with open(MASTER_LOG, "a", encoding="utf-8") as f:
        f.write(message)
    with open(HISTORY_LOG, "a", encoding="utf-8") as f:
        f.write(message)

def get_next_version_number(history_dir):
    """Determine the next version number for history folder."""
    if not history_dir.exists():
        history_dir.mkdir(parents=True, exist_ok=True)
        return "01"
    
    # Find all existing version folders (01, 02, 03, etc.)
    version_pattern = re.compile(r'^(\d{2})$')
    versions = []
    
    for item in history_dir.iterdir():
        if item.is_dir():
            match = version_pattern.match(item.name)
            if match:
                versions.append(int(match.group(1)))
    
    if not versions:
        return "01"
    
    next_version = max(versions) + 1
    return f"{next_version:02d}"

def copy_dat_files(source_dir, target_dir, history_dir=None, dry_run=False):
    """Copy all DAT files from source to target directory."""
    if not source_dir.exists():
        raise ValueError(f"Source directory not found: {source_dir}")

    target_dir.mkdir(parents=True, exist_ok=True)

    history_version_dir = None
    if history_dir:
        version_number = get_next_version_number(history_dir)
        history_version_dir = history_dir / version_number
        if not dry_run:
            history_version_dir.mkdir(parents=True, exist_ok=True)

    dat_files = list(source_dir.glob("*.dat"))
    copied_count = 0
    for dat_file in sorted(dat_files):
        target_file = target_dir / dat_file.name
        if not dry_run:
            try:
                shutil.copy2(dat_file, target_file)
                if history_version_dir:
                    history_file = history_version_dir / dat_file.name
                    shutil.copy2(dat_file, history_file)
                copied_count += 1
            except Exception as e:
                print(f"    Error copying {dat_file.name}: {e}")
                log_action(f"    Error copying {dat_file.name}: {e}")
        else:
            copied_count += 1

    return copied_count, history_version_dir.name if history_version_dir else None

def main():
    log_action("===== DAT File Stager script started =====")
    """Main function to orchestrate the DAT file staging process."""
    parser = argparse.ArgumentParser(description="Stage final DAT files to input directory")
    parser.add_argument("-s", "--source", help="Source directory (final_dat)")
    parser.add_argument("-t", "--target", help="Target directory (input_dat)")
    parser.add_argument("-r", "--history", help="History directory (history_dat)")
    parser.add_argument("-n", "--dry-run", action="store_true", 
                       help="Show what would be copied without actually copying")
    args = parser.parse_args()
    
    # Set default paths relative to the CLI project structure
    if not args.source:
        args.source = Path(BASE_DIR) / "final_dat"
    else:
        args.source = Path(args.source)

    if not args.target:
        args.target = Path(BASE_DIR) / "input_dat"
    else:
        args.target = Path(args.target)

    if not args.history:
        args.history = Path(BASE_DIR) / "history_dat"
    else:
        args.history = Path(args.history)
    
    try:
        print("=== DAT File Stager ===")
        log_action("=== DAT File Stager ===")
        print(f"Source: final_dat")
        log_action(f"Source: final_dat")
        print(f"Target: input_dat")
        log_action(f"Target: input_dat")
        print(f"History: history_dat")
        log_action(f"History: history_dat")        
        
        if args.dry_run:
            print("DRY RUN MODE - No files will be copied")
            log_action("DRY RUN MODE - No files will be copied")
        
        print()
        
        # Find all DAT files in source
        dat_files = list(args.source.glob("*.dat"))

        if not dat_files:
            print(f"No DAT files found in {args.source}")
            log_action(f"No DAT files found in {args.source}")
            return 0

        print(f"Found {len(dat_files)} DAT file(s) to stage:")
        log_action(f"Found {len(dat_files)} DAT file(s) to stage:")
        for dat_file in sorted(dat_files):
            target_file = args.target / dat_file.name
            exists_msg = " (will overwrite)" if target_file.exists() else " (new)"
            print(f"  {dat_file.name}{exists_msg}")
            log_action(f"  {dat_file.name}{exists_msg}")

        # Prompt user before proceeding
        while True:
            user_input = input("Proceed with staging? (Y/q): ").strip().lower()
            if user_input == "y":
                break
            elif user_input == "q":
                print("Operation cancelled by user.")
                log_action("Operation cancelled by user.")
                sys.exit(3)
            else:
                print("Please enter Y or Q.")
                log_action("Please enter Y or Q.")

        # Now perform the staging (call only once)
        copied_count, history_version = copy_dat_files(args.source, args.target, args.history, args.dry_run)

        print(f"\n=== Staging Complete ===")
        log_action(f"\n=== Staging Complete ===")
        if args.dry_run:
            print(f"Would stage {copied_count} DAT files")
            log_action(f"Would stage {copied_count} DAT files")
            print(f"Would create history version: {get_next_version_number(args.history)}")
            log_action(f"Would create history version: {get_next_version_number(args.history)}")
        else:
            print(f"Successfully staged {copied_count} DAT files")
            log_action(f"Successfully staged {copied_count} DAT files")
            print(f"Files copied to: input_dat")
            log_action(f"Files copied to: input_dat")
            if history_version:
                print(f"History saved as version: {history_version}")
                log_action(f"History saved as version: {history_version}")
            print("Final DAT files are now available in input_dat for further processing")
            log_action("Final DAT files are now available in input_dat for further processing")

            # Copy history.log to the history version folder (only if not dry run and history_version exists)
            history_log_path = Path(BASE_DIR) / "history.log"
            history_version_dir = args.history / history_version
            if history_log_path.exists():
                shutil.copy2(history_log_path, history_version_dir / "history.log")
                print(f"history.log copied to: {history_version_dir}")
                log_action(f"history.log copied to: {history_version_dir}")
                # Reset history.log for next session
                with open(history_log_path, "w", encoding="utf-8") as f:
                    f.write("")

        print(f"\n=== Staging Complete ===")      
        log_action(f"\n=== Staging Complete ===")       
        
    except Exception as e:
        print(f"Error: {e}")
        log_action(f"Error: {e}")
        log_action("===== DAT File Stager script finished with error =====")
        return 1
    
    log_action("===== DAT File Stager script finished =====")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        log_action("\nOperation cancelled by user.")
        sys.exit(1)
