SELECT
    (
        c.szcbrec_gi90 || c.szcbrec_gi01 || c.szcbrec_gi03 || c.szcbrec_cb00 || c.szcbrec_cb01 || c.szcbrec_cb02 || c.szcbrec_cb03 || c.szcbrec_cb04
    ) || (
        c.szcbrec_cb05 || c.szcbrec_cb06 || c.szcbrec_cb07 || c.szcbrec_cb08 || c.szcbrec_cb09 || c.szcbrec_cb10 || c.szcbrec_cb11 || c.szcbrec_cb12 || c.szcbrec_cb13
    ) || (
        c.szcbrec_cb14 || c.szcbrec_cb15 || c.szcbrec_cb16 || c.szcbrec_cb17 || c.szcbrec_cb18 || c.szcbrec_cb19 || c.szcbrec_cb20 || c.szcbrec_cb21 || c.szcbrec_cb22
    ) || c.szcbrec_cb23 || c.szcbrec_cb24 || c.szcbrec_cb25 || c.szcbrec_cb26 || c.szcbrec_cb27 || '                         ' AS cb
FROM
    szcbrec c
WHERE
    c.szcbrec_gi03 = '{gi03_val}'
    AND c.szcbrec_gi01 = '{gi01_val}'
    and c.szcbrec_report_no = 'CALB1'
