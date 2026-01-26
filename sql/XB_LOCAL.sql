SELECT
    c.SZXBREC_GI90,
    c.SZXBREC_GI01,
    c.SZXBREC_GI03,
    '   ' as SZXBREC_GI02,
    c.SZXBREC_CB01,
    c.SZXBREC_XB00,
    c.SZXBREC_XB01,
    c.SZXBREC_XB02,
    '      ' as SZXBREC_XB03,
    c.SZXBREC_XB04,
    c.SZXBREC_XB05,
    c.SZXBREC_XB06,
    ' ' as SZXBREC_XB07,
    c.SZXBREC_XB08,
    c.SZXBREC_XB09,
    c.SZXBREC_XB10,
    c.SZXBREC_XB11,
    c.SZXBREC_CB00,
    c.SZXBREC_XB12,
    c.szxbrec_xb13
FROM
    szxbrec c
WHERE
    {gi03_col} = '{gi03_val}'
    AND {gi01_col} = '{gi01_val}'
    AND c.szxbrec_report_no = 'CALB1'