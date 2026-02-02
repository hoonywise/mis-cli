SELECT
    c.szxbrec_gi90,
    c.szxbrec_gi01,
    c.szxbrec_gi03,
    '   ' AS szxbrec_gi02,
    c.szxbrec_cb01,
    c.szxbrec_xb00,
    c.szxbrec_xb01,
    c.szxbrec_xb02,
    '      ' AS szxbrec_xb03,
    c.szxbrec_xb04,
    c.szxbrec_xb05,
    c.szxbrec_xb06,
    ' ' AS szxbrec_xb07,
    c.szxbrec_xb08,
    c.szxbrec_xb09,
    c.szxbrec_xb10,
    c.szxbrec_xb11,
    c.szxbrec_cb00,
    c.szxbrec_xb12,
    c.szxbrec_xb13
FROM
    szxbrec c
WHERE c.szxbrec_gi03 = '{gi03_val}'
  AND c.szxbrec_gi01 = '{gi01_val}'
  AND c.szxbrec_report_no = 'CALB1'