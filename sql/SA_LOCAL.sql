SELECT
    c.szsarec_gi90,
    c.szsarec_GI01,
    c.szsarec_GI03,
    c.szsarec_sb02,
    c.szsarec_sb00,
    c.szsarec_sa01,
    c.szsarec_sa03,
    c.szsarec_sa04,
    c.szsarec_sa05
FROM
    szsarec c
WHERE
    szsarec_gi03 = '{gi03_val}'
    AND szsarec_gi01 = '{gi01_val}'
    AND c.szsarec_report_no = 'CALB1'