SELECT
    (
        c.szsvrec_gi90 ||
        c.szsvrec_gi01 ||
        c.szsvrec_gi03 ||
        c.szsvrec_sb02 ||
        c.szsvrec_sb00 ||
        c.szsvrec_sv01 ||
        ' ' ||
        c.szsvrec_sv03 ||
        c.szsvrec_sv04 ||
        c.szsvrec_sv05 ||
        c.szsvrec_sv06 ||
        ' ' ||
        c.szsvrec_sv08 ||
        c.szsvrec_sv09 ||
        c.szsvrec_sv10 ||
        '         '
    ) AS SV
FROM
    szsvrec c
WHERE
    c.szsvrec_gi03 = '{gi03_val}'
    AND c.szsvrec_gi01 = '{gi01_val}'
    AND c.szsvrec_report_no = 'CALB1'