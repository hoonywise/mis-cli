SELECT
    (
        c.szxerec_gi90 ||
        c.szxerec_gi01 ||
        c.szxerec_gi03 ||
        c.szxerec_cb01 ||
        c.szxerec_xb00 ||
        c.szxerec_eb00 ||
        c.szxerec_xf00 ||
        c.szxerec_xe01 ||
        c.szxerec_xe02 ||
        c.szxerec_xe03 ||
        c.szxerec_xe04 ||
        c.szxerec_cb00 ||
        '                 '
        ) AS xe
FROM
    szxerec c
WHERE c.szxerec_gi03 = '{gi03_val}'
  AND c.szxerec_gi01 = '{gi01_val}'
  AND c.szxerec_report_no = 'CALB1'