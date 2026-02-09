WITH
    cte_sb AS (
              SELECT
                  c.szsbrec_pidm,
                  c.szsbrec_gi01,
                  c.szsbrec_gi03,
                  c.szsbrec_sb00
              FROM
                  szsbrec c
              WHERE c.szsbrec_report_no = 'CALB1'
              ),
    cte_vr AS (
              SELECT
                  gi90,
                  gi01,
                  gi03,
                  szsbrec_sb00 AS sb00,
                  vr01,
                  vr02,
                  SUM(vr03) AS vr03
              FROM
                  dwh.mis_vr_ext@dwhdb.nocccd.edu
                      INNER JOIN cte_sb
                          ON (
                          cte_sb.szsbrec_pidm = fw_get_pidm(dwh.mis_vr_ext.sb00)
                              AND cte_sb.szsbrec_gi01 = dwh.mis_vr_ext.gi01
                              AND cte_sb.szsbrec_gi03 = dwh.mis_vr_ext.gi03
                          )
              WHERE gi03 = '{gi03_val}'
                AND gi01 = '{gi01_val}'
              GROUP BY
                  gi90,
                  gi01,
                  gi03,
                  szsbrec_sb00,
                  vr01,
                  vr02
              )
SELECT
    (
        RPAD(gi90, 2, ' ') ||
        RPAD(gi01, 3, ' ') ||
        RPAD(gi03, 3, ' ') ||
        RPAD(sb00, 9, ' ') ||
        RPAD(vr01, 2, ' ') ||
        RPAD(vr02, 3, ' ') ||
        LPAD(vr03, 6, '0')) AS vr
FROM
    cte_vr