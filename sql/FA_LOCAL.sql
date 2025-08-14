SELECT
    c.RZFAREC_gi90,
    c.RZFAREC_GI01,
    c.RZFAREC_GI03_SUB,
    c.RZFAREC_GI03_AWARD,
    c.RZFAREC_sb00,
    c.RZFAREC_sf21,
    c.RZFAREC_sf22
FROM
    rzfarec c
WHERE
    c.rzfarec_gi03_sub = '{gi03_val}'
    AND c.rzfarec_gi01 = '{gi01_val}'
    AND c.rzfarec_report_no = 'CALB1'