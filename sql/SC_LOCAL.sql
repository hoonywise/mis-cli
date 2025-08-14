SELECT
    c.szscrec_gi90,
    c.szscrec_gi01,
    c.szscrec_gi03,
    c.szscrec_sb00,
    c.szscrec_sc01,
    c.szscrec_sc02,
    c.szscrec_sc03,
    c.szscrec_sc04,
    c.szscrec_sc05,
    c.szscrec_sc06,
    c.szscrec_sc07,
    c.szscrec_sc08,
    c.szscrec_sc09,
    c.szscrec_sc10,
    c.szscrec_sc11,
    c.szscrec_sc18
FROM
    szscrec c
WHERE
    c.szscrec_gi03 = '{gi03_val}'
    AND c.szscrec_gi01 = '{gi01_val}'
    AND c.szscrec_report_no = 'CALB1'