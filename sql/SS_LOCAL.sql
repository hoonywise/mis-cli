SELECT
    c.szssrec_gi90,
    c.szssrec_gi01,
    c.szssrec_gi03,
    c.szssrec_sb02,
    c.szssrec_sb00,
    c.szssrec_ss01,
    c.szssrec_ss02,
    c.szssrec_ss03,
    c.szssrec_ss04,
    c.szssrec_ss05,
    c.szssrec_ss06,
    c.szssrec_ss07,
    c.szssrec_ss08,
    c.szssrec_ss09,
    c.szssrec_ss10,
    c.szssrec_ss11,
    c.szssrec_ss12,
    c.szssrec_ss13,
    c.szssrec_ss14,
    c.szssrec_ss15,
    c.szssrec_ss16,
    c.szssrec_ss17,
    c.szssrec_ss18,
    c.szssrec_ss19,
    c.szssrec_ss20
FROM
    szssrec c
WHERE
    c.szssrec_gi03 = '{gi03_val}'
    AND c.szssrec_gi01 = '{gi01_val}'
    AND c.szssrec_report_no = 'CALB1'