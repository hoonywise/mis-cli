SELECT
    (
        c.SZXEREC_GI90 ||
        c.SZXEREC_GI01 ||
        c.SZXEREC_GI03 ||
        c.SZXEREC_CB01 ||
        c.SZXEREC_XB00 ||
        c.SZXEREC_EB00 ||
        c.SZXEREC_XF00 ||
        c.SZXEREC_XE01 ||
        c.SZXEREC_XE02 ||
        c.SZXEREC_XE03 ||
        c.SZXEREC_XE04 ||
        c.SZXEREC_CB00 ||
        '                 '
    ) AS XE
FROM
    szxerec c
WHERE
    {gi03_col} = '{gi03_val}'
    AND {gi01_col} = '{gi01_val}'
    AND c.szxerec_report_no = 'CALB1'