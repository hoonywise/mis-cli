SELECT
    (
        c.szcwrec_gi90 ||
        c.szcwrec_gi01 ||
        c.szcwrec_gi03 ||
        c.szcwrec_sb00 ||
        c.szcwrec_sc12 ||
        c.szcwrec_sc13 ||
        c.szcwrec_sc14 ||
        c.szcwrec_sc15 ||
        c.szcwrec_sc16 ||
        c.szcwrec_sc17 ||
        '                                  '
    ) AS CW
FROM
    szcwrec c
WHERE
    c.szcwrec_gi03 = '{gi03_val}'
    AND c.szcwrec_gi01 = '{gi01_val}'
    AND c.szcwrec_report_no = 'CALB1'