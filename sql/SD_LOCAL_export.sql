SELECT
    (
        c.szsdrec_gi90 ||
        c.szsdrec_gi01 ||
        c.szsdrec_gi03 ||
        c.szsdrec_sb02 ||
        c.szsdrec_sb00 ||
        c.szsdrec_sd01 ||
        '   ' ||
        ' ' ||
        '   ' ||
        c.szsdrec_sd05 ||
        c.szsdrec_sd06 ||
        '          '
    ) AS SD
FROM
    szsdrec c
WHERE
    c.szsdrec_gi03 = '{gi03_val}'
    AND c.szsdrec_gi01 = '{gi01_val}'
    AND c.szsdrec_report_no = 'CALB1'