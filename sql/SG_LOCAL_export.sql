WITH
    cte_sg26 AS (
        SELECT
            a.GI03_TERM_ID,
            a.GI01_DISTRICT_COLLEGE_ID,
            b.spriden_pidm AS pidm,
            a.sg26_1,
            a.sg26_2
        FROM
            dwh.mis_sg26@dwhdb.nocccd.edu a
            INNER JOIN spriden b ON (a.student_id = b.spriden_id)
        GROUP BY
            a.GI03_TERM_ID,
            a.GI01_DISTRICT_COLLEGE_ID,
            b.spriden_pidm,
            a.sg26_1,
            a.sg26_2
    ),
    cte_sg29 AS (
        SELECT
            a.GI03_TERM_ID,
            a.GI01_DISTRICT_COLLEGE_ID,
            b.spriden_pidm AS pidm,
            a.sg29
        FROM
            dwh.mis_sg29@dwhdb.nocccd.edu a
            INNER JOIN spriden b ON (a.student_id = b.spriden_id)
        GROUP BY
            a.GI03_TERM_ID,
            a.GI01_DISTRICT_COLLEGE_ID,
            b.spriden_pidm,
            a.sg29
    )
SELECT
    (
        c.szsgrec_gi90 || c.szsgrec_gi01 || c.szsgrec_gi03 || c.szsgrec_sb00 || c.szsgrec_sg01 || c.szsgrec_sg02 || c.szsgrec_sg03 || c.szsgrec_sg04 || c.szsgrec_sg05
    ) || (
        c.szsgrec_sg06 || c.szsgrec_sg07 || c.szsgrec_sg08 || c.szsgrec_sg09 || c.szsgrec_sg10 || c.szsgrec_sg11 || CASE
            WHEN c.szsgrec_gi01 = '863' THEN 'YYYYY'
            ELSE c.szsgrec_sg12
        END || c.szsgrec_sg13 || c.szsgrec_sg14 || c.szsgrec_sg15
    ) || (
        c.szsgrec_sg16 || c.szsgrec_sg17 || c.szsgrec_sg18 || c.szsgrec_sg19 || c.szsgrec_sg20 || c.szsgrec_sg21 || c.szsgrec_sg22 || c.szsgrec_sg23 || c.szsgrec_sg24
    ) || (
        c.szsgrec_sg25 || CASE
            WHEN a.pidm IS NOT NULL THEN a.sg26_1 || a.sg26_2
            ELSE c.szsgrec_sg26
        END || c.szsgrec_sg27 || 'XXXX' || CASE
            WHEN b.pidm IS NOT NULL THEN b.sg29
            ELSE 'X'
        END || ' '
    ) AS sg
FROM
    szsgrec c
    LEFT JOIN cte_sg26 a ON (
        c.szsgrec_pidm = a.pidm
        AND c.szsgrec_gi01 = a.GI01_DISTRICT_COLLEGE_ID
        AND c.szsgrec_gi03 = a.GI03_TERM_ID
    )
    LEFT JOIN cte_sg29 b ON (
        c.szsgrec_pidm = b.pidm
        AND c.szsgrec_gi01 = b.GI01_DISTRICT_COLLEGE_ID
        AND c.szsgrec_gi03 = b.GI03_TERM_ID
    )
WHERE
    c.szsgrec_gi03 = '{gi03_val}'
    AND c.szsgrec_gi01 = '{gi01_val}'
    AND c.szsgrec_report_no = 'CALB1'