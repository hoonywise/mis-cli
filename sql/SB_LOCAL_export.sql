SELECT
    (
        c.szsbrec_gi90 || c.szsbrec_gi01 || c.szsbrec_gi03 || c.szsbrec_sb02 || c.szsbrec_sb00 || c.szsbrec_sb01 || c.szsbrec_sb03 || c.szsbrec_sb04 || '  '
    ) || (
        c.szsbrec_sb06 || ' ' || c.szsbrec_sb08 || c.szsbrec_sb09 || ' ' || c.szsbrec_sb11 || c.szsbrec_sb12 || '      ' || c.szsbrec_sb14 || c.szsbrec_sb15
    ) || (
        c.szsbrec_sb16 || c.szsbrec_sb17 || c.szsbrec_sb18 || c.szsbrec_sb19 || c.szsbrec_sb20 || c.szsbrec_sb21 || c.szsbrec_sb22 || c.szsbrec_sb23 || c.szsbrec_sb24
    ) || (
        ' ' || c.szsbrec_sb26 || c.szsbrec_sb27 || c.szsbrec_sb28 || c.szsbrec_sb29 || c.szsbrec_sb30 || c.szsbrec_sb31 || c.szsbrec_sb32 || c.szsbrec_sb33 || c.szsbrec_sb34
    ) || c.szsbrec_sb35 || c.szsbrec_sb36 || c.szsbrec_sb37 || c.szsbrec_sb38 || c.szsbrec_sb39 || '       ' AS sb
FROM
    szsbrec c
WHERE
    c.szsbrec_gi03 = '{gi03_val}'
    AND c.szsbrec_gi01 = '{gi01_val}'
    AND c.szsbrec_report_no = 'CALB1'
    