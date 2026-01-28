WITH
    cte_sb AS (
        SELECT
            c.szsbrec_pidm,
            c.szsbrec_gi01,
            c.szsbrec_gi03,
            c.szsbrec_sb00
        FROM
            szsbrec c
        WHERE
            c.szsbrec_report_no = 'CALB1'
    ),
    cte_stvterm AS (
        SELECT
            a.stvterm_code,
            a.stvterm_desc,
            a.stvterm_start_date,
            a.stvterm_end_date,
            LAG(a.stvterm_end_date) OVER (
                PARTITION BY
                    SUBSTR(a.stvterm_code, -1, 1)
                ORDER BY
                    a.stvterm_code
            ) + 1 AS prev_term_end_date_plus_1,
            a.STVTERM_MIS_TERM_ID
        FROM
            stvterm a
        WHERE
            SUBSTR(a.stvterm_code, -1, 1) = '0'
    ),
    cte_scbsupp AS (
        SELECT
            scbsupp_subj_code,
            scbsupp_crse_numb,
            scbsupp_eff_term,
            scbsupp_perm_dist_ind,
            scbsupp_tops_code
        FROM
            saturn.scbsupp scbsupp
        WHERE
            (
                scbsupp.scbsupp_eff_term = (
                    SELECT
                        MAX(scbsupp1.scbsupp_eff_term) "Max_SCBSUPP_EFF_TERM"
                    FROM
                        saturn.scbsupp scbsupp1
                        INNER JOIN cte_stvterm stvterm1 ON (scbsupp1.scbsupp_eff_term = stvterm1.stvterm_code)
                    WHERE
                        scbsupp1.scbsupp_subj_code = scbsupp.scbsupp_subj_code
                        AND scbsupp1.scbsupp_crse_numb = scbsupp.scbsupp_crse_numb
                        AND stvterm1.stvterm_mis_term_id <= '{gi03_val}'
                )
            )
    ),
    cte_main AS (
        SELECT
            e.stvterm_code AS term_code,
            CASE
                WHEN SUBSTR(a.shrtrce_levl_code, 1, 1) = '1' THEN 'Cypress'
                WHEN SUBSTR(a.shrtrce_levl_code, 1, 1) = '2' THEN 'Fullerton'
                WHEN SUBSTR(a.shrtrce_levl_code, 1, 1) = '3' THEN 'NOCE'
            END AS college,
            c.spriden_id AS id,
            c.spriden_last_name AS last_name,
            c.spriden_first_name AS first_name,
            b.shrtrit_sbgi_code AS institution_code,
            a.shrtrce_activity_date AS assess_date,
            e.prev_term_end_date_plus_1,
            e.stvterm_end_date AS current_term_end_date,
            d.scbsupp_perm_dist_ind AS crse_ctrl_no,
            a.shrtrce_subj_code AS subj_code,
            a.shrtrce_crse_numb AS crse_numb,
            a.shrtrce_crse_title AS crse_title,
            a.shrtrce_credit_hours AS credit_hrs,
            a.shrtrce_grde_code AS grade_code,
            'SY' AS GI90,
            CASE
                WHEN SUBSTR(a.shrtrce_levl_code, 1, 1) = '1' THEN '861'
                WHEN SUBSTR(a.shrtrce_levl_code, 1, 1) = '2' THEN '862'
                WHEN SUBSTR(a.shrtrce_levl_code, 1, 1) = '3' THEN '863'
            END AS GI01,
            e.stvterm_mis_term_id AS GI03,
            f.szsbrec_sb00 AS SB00,
            RPAD(d.scbsupp_perm_dist_ind, 12, ' ') AS CB00,
            RPAD(a.shrtrce_subj_code || a.shrtrce_crse_numb, 12, ' ') AS CB01,
            TO_CHAR(a.shrtrce_activity_date, 'YYMMDD') AS SY01,
            CASE
                WHEN b.shrtrit_sbgi_code = 'CPLPFO' THEN 'A'
                WHEN b.shrtrit_sbgi_code = 'CRBYEX' THEN 'B'
                WHEN b.shrtrit_sbgi_code IN ('APCR', 'APEXAM', 'APEXM2') THEN 'C'
                WHEN b.shrtrit_sbgi_code IN ('IB', 'IBEXAM', 'IBEXM1') THEN 'D'
                WHEN b.shrtrit_sbgi_code IN ('CLEPCR', 'CLEPEX') THEN 'E'
                WHEN b.shrtrit_sbgi_code = 'CPLCRT' THEN 'F'
                WHEN b.shrtrit_sbgi_code IN ('MILCR1', 'MILICR', 'CPLJST') THEN 'G'
                WHEN b.shrtrit_sbgi_code = 'CPLCTE' THEN 'H'
                WHEN b.shrtrit_sbgi_code = 'CPLDLPT' THEN 'I'
                WHEN b.shrtrit_sbgi_code = 'CPLSTEX' THEN 'J'
                WHEN b.shrtrit_sbgi_code = 'CRPRL' THEN 'Z'
            END AS SY02,
            LPAD(TO_CHAR(TRUNC(a.shrtrce_credit_hours * 100)), 4, '0') AS SY03,
            RPAD(
                CASE
                    WHEN REGEXP_LIKE (a.shrtrce_grde_code, '^T?[ABCDP]$') THEN
                    -- Remove leading 'T' if present, else return as is
                    CASE
                        WHEN SUBSTR(a.shrtrce_grde_code, 1, 1) = 'T' THEN SUBSTR(a.shrtrce_grde_code, 2, 1)
                        ELSE a.shrtrce_grde_code
                    END
                    ELSE NULL
                END,
                3,
                ' '
            ) AS SY04
        FROM
            shrtrce a
            INNER JOIN shrtrit b ON (
                a.shrtrce_pidm = b.shrtrit_pidm
                AND a.shrtrce_trit_seq_no = b.shrtrit_seq_no
            )
            INNER JOIN spriden c ON (
                a.shrtrce_pidm = c.spriden_pidm
                AND c.spriden_change_ind IS NULL
            )
            LEFT JOIN cte_scbsupp d ON (
                a.shrtrce_subj_code = d.scbsupp_subj_code
                AND a.shrtrce_crse_numb = d.scbsupp_crse_numb
            )
            LEFT JOIN cte_stvterm e ON (
                a.shrtrce_activity_date >= e.prev_term_end_date_plus_1
                AND a.shrtrce_activity_date <= e.stvterm_end_date
            )
            LEFT JOIN cte_sb f ON (
                a.shrtrce_pidm = f.szsbrec_pidm
                AND e.stvterm_mis_term_id = f.szsbrec_gi03
                AND (
                    CASE
                        WHEN SUBSTR(a.shrtrce_levl_code, 1, 1) = '1' THEN '861'
                        WHEN SUBSTR(a.shrtrce_levl_code, 1, 1) = '2' THEN '862'
                        WHEN SUBSTR(a.shrtrce_levl_code, 1, 1) = '3' THEN '863'
                    END
                ) = f.szsbrec_gi01
            )
        WHERE
            b.shrtrit_sbgi_code IN (
                'APEXAM',
                'CLEPCR',
                'CLEPEX', -- stop using after 253  
                'CPLCRT',
                'CPLCTE',
                'CPLDLPT',
                'CPLJST',
                'CPLPFO',
                'CPLSTEX',
                'CRBYEX',
                'CRPRL',
                'IBEXAM',
                'IBEXM1', -- stop using after 253  
                'MILCR1', -- stop using after 253             
                'IB',
                'APCR',
                'APEXM2', -- stop using after 253  
                'CLEPCR',
                'MILICR'
            )
            AND d.scbsupp_perm_dist_ind IS NOT NULL
            AND a.shrtrce_activity_date IS NOT NULL
            AND f.szsbrec_sb00 IS NOT NULL
    )
SELECT
    GI90,
    GI01,
    GI03,
    SB00,
    CB00,
    CB01,
    SY01,
    SY02,
    SY03,
    CASE
        WHEN SY03 = '0000'
        AND SY04 IS NULL THEN 'NA'
        ELSE SY04
    END AS SY04
FROM
    cte_main
WHERE
    gi03 = '{gi03_val}'
    AND gi01 = '{gi01_val}'