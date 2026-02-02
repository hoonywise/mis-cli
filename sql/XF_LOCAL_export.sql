SELECT
    (
        c.szxfrec_gi90 ||
        c.szxfrec_gi01 ||
        c.szxfrec_gi03 ||
        c.szxfrec_cb01 ||
        c.szxfrec_xb00 ||
        c.szxfrec_xf00 ||
        c.szxfrec_xf01 ||
        c.szxfrec_xf02 ||
        c.szxfrec_xf03 ||
        c.szxfrec_xf04 ||
        c.szxfrec_xf05 ||
        c.szxfrec_xf06 ||
        c.szxfrec_xf07 ||
        c.szxfrec_cb00 ||
        '    '
        ) AS xf
FROM
    szxfrec c
WHERE c.szxfrec_gi03 = '{gi03_val}'
  AND c.szxfrec_gi01 = '{gi01_val}'
  AND c.szxfrec_report_no = 'CALB1'