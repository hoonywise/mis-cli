SELECT
    c.szserec_gi90,
    c.szserec_gi01,
    c.szserec_gi03,
    c.szserec_sb02,
    c.szserec_sb00,
    c.szserec_se01,
    c.szserec_se02,
    c.szserec_se03,
    c.szserec_se04,
    c.szserec_se05,
    c.szserec_se06,
    c.szserec_se07,
    c.szserec_se08,
    c.szserec_se09,
    c.szserec_se10
FROM
    szserec c
WHERE
    c.szserec_gi03 = '{gi03_val}'
    AND c.szserec_gi01 = '{gi01_val}'
    AND c.szserec_report_no = 'CALB1'