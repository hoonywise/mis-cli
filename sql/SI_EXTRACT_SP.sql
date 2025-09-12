SELECT DISTINCT
    (
        'SI' || a.gi01_district_college_id || a.sb00_student_id || a.sb01_id_status || p.szsprec_sb00 || CASE
            WHEN (
                SUBSTR(p.szsprec_sb00, 1, 1) IN ('@')
                OR SUBSTR(p.szsprec_sb00, 1, 3) IN ('000', '666')
                OR SUBSTR(p.szsprec_sb00, 1, 3) BETWEEN 900 AND 999
                OR SUBSTR(p.szsprec_sb00, 4, 2) = '00'
                OR SUBSTR(p.szsprec_sb00, 6, 4) = '0000'
            ) THEN 'C'
            ELSE 'S'
        END
    ) AS SI
FROM
    dwh.mis_sb@dwhdb.nocccd.edu a
    JOIN szsprec p ON (
        fw_get_pidm (a.sb00_student_id) = p.szsprec_pidm
        AND p.szsprec_report_no = 'CALB1'
    )
    JOIN dwh.mis_error_reports@dwhdb.nocccd.edu e ON (
        fw_get_pidm (a.sb00_student_id) = fw_get_pidm (e.info_1)
        AND TRIM(e.error_description) LIKE 'STUDENT ID HAS NEVER BEEN REPORTED TO MIS%'
    )
WHERE
    a.gi03_term_id IN ({gi03_val})
    AND a.sb00_student_id <> p.szsprec_sb00
ORDER BY
    (
        'SI' || a.gi01_district_college_id || a.sb00_student_id || a.sb01_id_status || p.szsprec_sb00 || CASE
            WHEN (
                SUBSTR(p.szsprec_sb00, 1, 1) IN ('@')
                OR SUBSTR(p.szsprec_sb00, 1, 3) IN ('000', '666')
                OR SUBSTR(p.szsprec_sb00, 1, 3) BETWEEN 900 AND 999
                OR SUBSTR(p.szsprec_sb00, 4, 2) = '00'
                OR SUBSTR(p.szsprec_sb00, 6, 4) = '0000'
            ) THEN 'C'
            ELSE 'S'
        END
    )