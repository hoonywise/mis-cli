WITH
    cte_sx07 AS (
        SELECT
            '0' AS szsxrec_sx07
        FROM
            dual
    )
SELECT
    c.szsxrec_gi90,
    c.szsxrec_gi01,
    c.szsxrec_gi03,
    c.szsxrec_sb02,
    c.szsxrec_sb00,
    c.szsxrec_cb01,
    c.szsxrec_xb00,
    c.szsxrec_sx01,
    c.szsxrec_sx02,
    c.szsxrec_sx03,
    c.szsxrec_sx04,
    c.szsxrec_sx05,
    c.szsxrec_cb00,
    c.szsxrec_sx06,
    cc.szsxrec_sx07
FROM
    szsxrec c
    CROSS JOIN cte_sx07 cc
WHERE
    c.szsxrec_gi03 = '{gi03_val}'
    AND (
        c.szsxrec_gi01 <> '863'
        OR (c.szsxrec_gi03 = '863' AND c.szsxrec_report_no = 'TEST1')
    )