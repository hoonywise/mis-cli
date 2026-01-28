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
    )
SELECT
    GI90,
    GI01,
    GI03,
    szsbrec_sb00 AS SB00,
    VR01,
    VR02,
    VR03
FROM
    dwh.mis_vr_ext@dwhdb.nocccd.edu
    INNER JOIN cte_sb ON (
        cte_sb.szsbrec_pidm = fw_get_pidm (dwh.mis_vr_ext.SB00)
        AND cte_sb.szsbrec_gi01 = dwh.mis_vr_ext.GI01
        AND cte_sb.szsbrec_gi03 = dwh.mis_vr_ext.GI03
    )
WHERE
    GI03 = '{gi03_val}'
    AND GI01 = '{gi01_val}'