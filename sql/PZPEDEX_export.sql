SELECT
    (
        c.pzebrec_gi90 || c.pzebrec_gi01 || c.pzebrec_gi03 || c.pzebrec_eb00 || c.pzebrec_eb01 || c.pzebrec_eb02 || c.pzebrec_eb03 || c.pzebrec_eb04
    ) || (
        c.pzebrec_eb05 || c.pzebrec_eb06 || c.pzebrec_eb07 || c.pzebrec_eb08 || c.pzebrec_eb09 || c.pzebrec_eb10 || c.pzebrec_eb11 || c.pzebrec_eb12 || c.pzebrec_eb13 || c.pzebrec_eb14
    ) || '      ' AS eb
FROM
    pzebrec c
WHERE
    c.pzebrec_gi03 = '{gi03_val}'
    AND c.pzebrec_gi01 = '{gi01_val}'
    and c.pzebrec_report_no <> '7525'