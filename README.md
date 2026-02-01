# MIS-CLI

A command-line Python tool to assist users in processing and editing California college MIS files, customized for NOCCCD.

Created by Jihoon Ahn ([@hoonywise](https://github.com/hoonywise))  
Contact: hoonywise@proton.me

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Main Menu Options](#main-menu-options)
  - [Data Extract and Preparation](#data-extract-and-preparation)
  - [Data Editing and Stripping](#data-editing-and-stripping)
  - [Database Operations](#database-operations)
  - [OneDrive Operations](#onedrive-operations)
  - [Open Term Folder in Explorer](#open-term-folder-in-explorer)
  - [Change Instance Term](#change-instance-term)
  - [Delete Instance Term](#delete-instance-term)
  - [Setup/Update Configuration](#setupupdate-configuration)
- [Script Summaries](#script-summaries)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## Overview
MIS-CLI is a comprehensive CLI tool designed to streamline the workflow for California college MIS file management, including extraction, editing, database operations, and submission handling.

## Installation
- Download the latest release from the [Releases](https://github.com/hoonywise/MIS-CLI/releases) page.
- Extract the zip file and run the executable file.

## Getting Started
- When the bat file is first run, it will prompt the user to enter the following:
  - DWH username: Username of the user who has access to the DWH database.
  - DWH password: Password of the user who has access to the DWH database.
  - DWH DSN: Data Source Name of the DWH database listed in the tnsnames.ora (ie. DWHDB_DB).
  - PROD username: Username of the user who has access to the PROD database.
  - PROD password: Password of the user who has access to the PROD database.
  - PROD DSN: Data Source Name of the PROD database listed in the tnsnames.ora (ie. PROD_DB).
  - Submission path: Path where the submission files will be stored in OneDrive.

## Main Menu Options

### Data Extract and Preparation

| Menu Item                                 | Script(s)                        | Description                                                                 |
|--------------------------------------------|-----------------------------------|-----------------------------------------------------------------------------|
| GVPRMIS.dat / SVRCAXX.dat Processing       | `gvprmis_processing.py`           | Process manually downloaded GVPRMIS.dat or SVRCAXX.dat files.               |
| GVPRMIS SQL Export Batch                   | `gvprmis_export_batch.py`         | Runs export scripts for GVAREPT, PZPEDEX, PZPAEXT. Must run Banner jobs first. |
| SI Extract Export (Student ID/SSN)         | `si_export_sp.py`                 | Runs custom SI export scripts. Currently only for SP file.                  |
| PDIS Extract Export (Student ID/SSN)       | `pdis_export.py`                  | Runs PDIS student SSN files for county submission.                          |

### Data Editing and Stripping

| Menu Item                                 | Script(s)                        | Description                                                                 |
|--------------------------------------------|-----------------------------------|-----------------------------------------------------------------------------|
| Replace Partial Records in DAT             | `row_replace.py`                  | Replaces partial records in DAT files according to college code and latest file extracts. |
| Compile New DAT set                        | `dat_compile.py`, `dat_paste.py`  | Compiles new set of DAT files from extracts in shared_export folder. Can select from 'Compile' or 'Paste' method of data writing. |
| Strip Records in DAT                       | `error_stripper.py`               | Strips records from DAT based on the latest error report number in DWH.     |
| Invalid Rows Identifier                    | `invalid_rows.py`                 | Detects exact locations in the SB records for invalid ASCII characters and spacing. |
| Stage Final DAT to Input DAT               | `dat_file_stager.py`              | Stages DAT files in final_dat folder to input_dat folder for historical record keeping. |
| Stage History DAT to Input DAT             | `dat_file_stager_hist.py`         | Stages DAT files in history_dat folder to input_dat folder for editing.     |

### Database Operations

| Menu Item                                 | Script(s)                        | Description                                                                 |
|--------------------------------------------|-----------------------------------|-----------------------------------------------------------------------------|
| Error Report Loader                        | `error_report_loader.py`          | Loads error reports from 'pending' folder into DWH. Moves completed reports to 'completed' folder. |
| SG26/SG29 Loader                           | `sg26_sg29_loader.py`             | Loads SG26/SG29 external csv/excel files from 'input' folder into DWH. Moves completed files to 'completed' folder. |
| DAT Loader                                 | `dat_loader.py`                   | Loads submitted DAT files to DWH. Must stage files first using 'Stage Highest Version to DAT Loader'. |
| CSV Loader                                 | `csv_loader.py`                   | Loads other external csv/excel files into DWH.                              |
| Stage Highest Version to DAT Loader         | `dat_file_stager_load.py`         | Stages highest version of DAT files in history_dat folder to DAT Loader.    |

### OneDrive Operations

| Menu Item                                 | Script(s)                        | Description                                                                 |
|--------------------------------------------|-----------------------------------|-----------------------------------------------------------------------------|
| Copy Submission to OneDrive                | `finalize_sub.py`                 | Copies all files from error_report_loader, history_dat, shared_export to OneDrive folder for safe keeping. |
| Import Submission from OneDrive            | `import_sub.py`                   | Imports all files from OneDrive folder to error_report_loader, history_dat, shared_export folders. |

### Open Term Folder in Explorer

| Menu Item                                 | Script(s)                        | Description                                                                 |
|--------------------------------------------|-----------------------------------|-----------------------------------------------------------------------------|
| Open Term Folder in Explorer               | `open_explorer.py`                | Opens a selected or current term folder in Windows Explorer.                |

### Change Instance Term

| Menu Item                                 | Script(s)                        | Description                                                                 |
|--------------------------------------------|-----------------------------------|-----------------------------------------------------------------------------|
| Change Instance Term                       | `instance_selector.py`            | Switches between term instances.                                            |

### Delete Instance Term

| Menu Item                                 | Script(s)                        | Description                                                                 |
|--------------------------------------------|-----------------------------------|-----------------------------------------------------------------------------|
| Delete Instance Term                       | `instance_delete.py`              | Deletes a term instance and its associated files. Must ensure files are copied to OneDrive first. |

### Setup/Update Configuration

| Menu Item                                 | Script(s)                        | Description                                                                 |
|--------------------------------------------|-----------------------------------|-----------------------------------------------------------------------------|
| Setup/Update Configuration                 | `config_setup.py`                 | Same as the initial setup. Run this to update configuration.                |


## License

This project is licensed under the MIT License. See the LICENSE file for details.

```
MIT License

Copyright (c) 2026 Jihoon Ahn

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
