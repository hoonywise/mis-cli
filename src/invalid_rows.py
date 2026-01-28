
import sys
import os
import oracledb
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from libs.oracle_db_connector import get_connection

def get_lookup(conn, gi03_val, gi01_sb00_pairs):
    lookup = {}
    if not gi01_sb00_pairs:
        return lookup
    # Build SQL with IN clause for (gi01, sb00)
    in_clause = ', '.join([f"(:gi01_{i}, :sb00_{i})" for i in range(len(gi01_sb00_pairs))])
    sql = f'''
        SELECT
            c.szsbrec_gi01 as gi01,
            c.szsbrec_gi03 as gi03,
            c.szsbrec_sb00 as sb00,
            c.szsbrec_pidm as pidm,
            fw_get_id(c.szsbrec_pidm) as id
        FROM
            szsbrec c
        WHERE
            c.szsbrec_gi03 = :gi03_val
            AND (c.szsbrec_gi01, c.szsbrec_sb00) IN ({in_clause})
            AND c.szsbrec_report_no = 'CALB1'
    '''
    params = {"gi03_val": gi03_val}
    for i, (gi01, sb00) in enumerate(gi01_sb00_pairs):
        params[f"gi01_{i}"] = gi01
        params[f"sb00_{i}"] = sb00
    with conn.cursor() as cur:
        cur.execute(sql, params)
        for row in cur.fetchall():
            gi01 = str(row[0]).strip()
            gi03 = str(row[1]).strip()
            sb00 = str(row[2]).strip()
            pidm = row[3]
            pid = row[4]
            lookup[(gi01, gi03, sb00)] = (gi01, gi03, sb00, pidm, pid)
    return lookup


def get_invalid_rows(file_path, invalid_row_numbers, lookup):
    results = []
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        for idx, line in enumerate(f, 1):
            if idx in invalid_row_numbers:
                # Extract gi01 (positions 3-5), gi03 (positions 6-8), sb00 (positions 11-19, 9 chars)
                gi01 = line[2:5].strip()
                gi03 = line[5:8].strip()
                student_id = line[10:19+1]
                sb00 = student_id.strip()
                key = (gi01, gi03, sb00)
                gi01_val, gi03_val, sb00_val, pidm, pid = lookup.get(key, (gi01, gi03, sb00, "N/A", "N/A"))
                invalids = []
                line_content = line.rstrip('\n\r')
                for i, c in enumerate(line_content):
                    if (
                        ord(c) > 127 or
                        (ord(c) < 32 and c not in '\t\n\r') or
                        (c.isspace() and c not in ' \t\n\r')
                    ):
                        snippet_start = max(0, i-10)
                        snippet_end = min(len(line_content), i+10)
                        snippet = line_content[snippet_start:snippet_end]
                        invalids.append((i+1, c, ord(c), snippet))
                if invalids:
                    print(f"Record {idx} | GI01: {gi01_val} | GI03: {gi03_val} | SB00: {sb00_val} | PIDM: {pidm} | ID: {pid}")
                    for pos, char, code, snippet in invalids:
                        print(f"  Invalid char at pos {pos}: '{char}' (U+{code:04X}) in ...{snippet}...")
                    print()
                results.append((idx, gi01_val, gi03_val, sb00_val, pidm, pid, invalids))
    return results

if __name__ == "__main__":
    # Interactive prompt for gi03 (data folder)
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
    gi03_folders = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d)) and d.isdigit()]
    if not gi03_folders:
        print("No gi03 folders found in /data.")
        sys.exit(1)
    print("Available gi03 terms:")
    for i, folder in enumerate(gi03_folders, 1):
        print(f"  {i}. {folder}")
    while True:
        gi03_val = input("Enter gi03 value from above: ").strip()
        if gi03_val in gi03_folders:
            break
        print("Invalid gi03 value. Please try again.")

    # Find the .dat file in final_dat
    final_dat_dir = os.path.join(data_dir, gi03_val, 'final_dat')
    dat_files = [f for f in os.listdir(final_dat_dir) if f.endswith('SB.dat')]
    if not dat_files:
        print(f"No SB.dat file found in {final_dat_dir}.")
        sys.exit(1)
    if len(dat_files) > 1:
        print("Multiple SB.dat files found. Please select:")
        for i, f in enumerate(dat_files, 1):
            print(f"  {i}. {f}")
        dat_file = dat_files[int(input("Select file number: ")) - 1]
    else:
        dat_file = dat_files[0]
    file_path = os.path.join(final_dat_dir, dat_file)
    print(f"Selected file: {file_path}")


    # Prompt for record numbers or paste notification text
    import re
    rec_input = input("Paste record row numbers or notification message: ").strip()
    # Extract all numbers that look like record numbers (e.g., after 'line: ')
    invalid_row_numbers = [int(n) for n in re.findall(r"line: '?(\d+)", rec_input)]
    if not invalid_row_numbers:
        # Fallback: extract any standalone numbers
        invalid_row_numbers = [int(x) for x in re.findall(r"\d+", rec_input)]
    if not invalid_row_numbers:
        print("No valid row numbers found.")
        sys.exit(1)

    # Extract gi03 from the first row, and collect (gi01, sb00) pairs from specified rows
    gi01_sb00_pairs = []
    row_gi01_gi03_sb00 = {}
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        for idx, line in enumerate(f, 1):
            if idx == 1:
                gi03_val = line[5:8].strip()
            if idx in invalid_row_numbers:
                gi01 = line[2:5].strip()
                student_id = line[10:19+1]
                sb00 = student_id.strip()
                gi01_sb00_pairs.append((gi01, sb00))
                row_gi01_gi03_sb00[idx] = (gi01, gi03_val, sb00)

    conn = get_connection("prod")
    if not conn:
        print("❌ Failed to connect to Production database")
        sys.exit(1)

    lookup = get_lookup(conn, gi03_val, gi01_sb00_pairs)

    # Add a blank line after DB connected message
    print()

    def get_invalid_rows_grouped_by_gi01(file_path, invalid_row_numbers, lookup):
        # Collect results grouped by gi01
        grouped = {}
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for idx, line in enumerate(f, 1):
                if idx in invalid_row_numbers:
                    gi01, gi03, sb00 = row_gi01_gi03_sb00[idx]
                    key = (gi01, gi03, sb00)
                    gi01_val, gi03_val, sb00_val, pidm, pid = lookup.get(key, (gi01, gi03, sb00, "N/A", "N/A"))
                    invalids = []
                    line_content = line.rstrip('\n\r')
                    for i, c in enumerate(line_content):
                        if (
                            ord(c) > 127 or
                            (ord(c) < 32 and c not in '\t\n\r') or
                            (c.isspace() and c not in ' \t\n\r')
                        ):
                            snippet_start = max(0, i-10)
                            snippet_end = min(len(line_content), i+10)
                            snippet = line_content[snippet_start:snippet_end]
                            invalids.append((i+1, c, ord(c), snippet))
                    if invalids:
                        grouped.setdefault(gi01_val, []).append((idx, gi01_val, gi03_val, sb00_val, pidm, pid, invalids))
        # Print grouped results
        for gi01_val in sorted(grouped.keys()):
            print(f"GI01: {gi01_val}\n")
            for (idx, gi01_val, gi03_val, sb00_val, pidm, pid, invalids) in grouped[gi01_val]:
                print(f"Record {idx} | GI01: {gi01_val} | GI03: {gi03_val} | SB00: {sb00_val} | PIDM: {pidm} | ID: {pid}")
                for pos, char, code, snippet in invalids:
                    print(f"  Invalid char at pos {pos}: '{char}' (U+{code:04X}) in ...{snippet}...")
                print()
        return grouped

    get_invalid_rows_grouped_by_gi01(file_path, invalid_row_numbers, lookup)
