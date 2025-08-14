SELECT
    (
        c.SZXBREC_GI90 ||
        c.SZXBREC_GI01 ||
        c.SZXBREC_GI03 ||
        '   ' ||
        c.SZXBREC_CB01 ||
        c.SZXBREC_XB00 ||
        c.SZXBREC_XB01 ||
        c.SZXBREC_XB02 ||
        '      ' ||
        c.SZXBREC_XB04 ||
        c.SZXBREC_XB05 ||
        c.SZXBREC_XB06 ||
        ' ' ||
        c.SZXBREC_XB08 ||
        c.SZXBREC_XB09 ||
        c.SZXBREC_XB10 ||
        c.SZXBREC_XB11 ||
        c.SZXBREC_CB00 ||
        c.SZXBREC_XB12 ||
        '      '
    ) AS XB
FROM
    szxbrec c
WHERE
    c.szxbrec_gi03 = '{gi03_val}'
    AND c.szxbrec_gi01 = '{gi01_val}'
    AND c.szxbrec_report_no = 'CALB1'
union all
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
    )
FROM
    szxerec c
WHERE
    c.szxerec_gi03 = '{gi03_val}'
    AND c.szxerec_gi01 = '{gi01_val}'
    AND c.szxerec_report_no = 'CALB1'
union all
SELECT
    (
        c.SZXFREC_GI90 ||
        c.SZXFREC_GI01 ||
        c.SZXFREC_GI03 ||
        c.SZXFREC_CB01 ||
        c.SZXFREC_XB00 ||
        c.SZXFREC_XF00 ||
        c.SZXFREC_XF01 ||
        c.SZXFREC_XF02 ||
        c.SZXFREC_XF03 ||
        c.SZXFREC_XF04 ||
        c.SZXFREC_XF05 ||
        c.SZXFREC_XF06 ||
        c.SZXFREC_XF07 ||
        c.SZXFREC_CB00 ||
        '    '
    )
FROM
    szxfrec c
WHERE
    c.szxfrec_gi03 = '{gi03_val}'
    AND c.szxfrec_gi01 = '{gi01_val}'
    AND c.szxfrec_report_no = 'CALB1'