SELECT
    c.pzejrec_gi90,
    c.pzejrec_gi01,
    c.pzejrec_gi03,
    c.pzejrec_eb00,
    c.pzejrec_ej01,
    c.pzejrec_ej02,
    c.pzejrec_ej03,
    c.pzejrec_ej04,
    c.pzejrec_ej05,
    c.pzejrec_ej06,
    c.pzejrec_ej07,
    c.pzejrec_ej08
FROM
    pzejrec c
WHERE
    c.pzejrec_gi03 = '{gi03_val}' 
    AND c.pzejrec_gi01 = '{gi01_val}'
    and c.pzejrec_report_no <> '7525'