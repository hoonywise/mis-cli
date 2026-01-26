SELECT
    (
        c.rzsfrec_gi90 ||
        c.rzsfrec_gi01 ||
        c.rzsfrec_gi03 ||
        c.rzsfrec_sb02 ||
        c.rzsfrec_sb00 ||
        c.rzsfrec_sf01 ||
        c.rzsfrec_sf03 ||
        c.rzsfrec_sf04 ||
        CASE
            WHEN c.rzsfrec_sf05 = 'Z' THEN 'I'
            ELSE c.rzsfrec_sf05
        END ||
        c.rzsfrec_sf06 ||
        c.rzsfrec_sf07 ||
        c.rzsfrec_sf08 ||
        c.rzsfrec_sf09 ||
        c.rzsfrec_sf10 ||
        c.rzsfrec_sf11 ||
        CASE
            WHEN INSTR(c.rzsfrec_sf17, '-') > 0 THEN '999999'
            ELSE c.rzsfrec_sf17
        END ||
        c.rzsfrec_sf23 ||
        c.rzsfrec_sf24 ||
        '    '
    ) AS SF
FROM
    rzsfrec c
WHERE
    c.rzsfrec_gi03 = '{gi03_val}'
    AND c.rzsfrec_gi01 = '{gi01_val}'
    AND c.rzsfrec_report_no = 'CALB1'