SELECT DISTINCT
    'VE' || '{gi03_val}' || c.spbpers_ssn AS pdis
FROM
    sfrstcr a
    INNER JOIN spriden b ON (
        b.spriden_pidm = a.sfrstcr_pidm
        AND b.spriden_change_ind IS NULL
    )
    INNER JOIN spbpers c ON (
        b.spriden_pidm = c.spbpers_pidm
        AND c.spbpers_ssn IS NOT NULL
    )
    INNER JOIN stvterm s ON (s.stvterm_code = a.sfrstcr_term_code)
WHERE
    a.sfrstcr_rsts_code LIKE 'R%'
    AND s.stvterm_mis_term_id = '{gi03_val}'
    AND a.sfrstcr_camp_code LIKE SUBSTR('{gi01_val}', 3, 1) || '%'
    AND NOT EXISTS (
        SELECT
            1
        FROM
            spbpers cc
        WHERE
            c.spbpers_ssn = cc.spbpers_ssn
            AND cc.spbpers_ssn IS NOT NULL
            AND cc.spbpers_pidm <> c.spbpers_pidm
    )