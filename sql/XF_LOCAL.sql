SELECT
    c.SZXFREC_GI90,
    c.SZXFREC_GI01,
    c.SZXFREC_GI03,
    c.SZXFREC_CB01,
    c.SZXFREC_XB00,
    c.SZXFREC_XF00,
    c.SZXFREC_XF01,
    c.SZXFREC_XF02,
    c.SZXFREC_XF03,
    c.SZXFREC_XF04,
    c.SZXFREC_XF05,
    c.SZXFREC_XF06,
    c.SZXFREC_XF07,
    c.SZXFREC_CB00
FROM
    szxfrec c
WHERE
    {gi03_col} = '{gi03_val}'
    AND {gi01_col} = '{gi01_val}'
    AND c.szxfrec_report_no = 'CALB1'