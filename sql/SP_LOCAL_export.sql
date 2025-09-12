SELECT
  (
    c.szsprec_gi90 ||
    c.szsprec_GI01 ||
    c.szsprec_GI03 ||
    c.szsprec_sb02 ||
    c.szsprec_sb00 ||
    c.szsprec_sp01 ||
    c.szsprec_sp02 ||
    c.szsprec_sp03 ||
    c.szsprec_gi92 ||
    CASE
      WHEN trim(c.szsprec_sp04) IS NULL THEN '99999'
      ELSE c.szsprec_sp04
    END ||
    ' '
  ) AS SP
FROM
  szsprec c
WHERE
  szsprec_gi03 = '{gi03_val}'
  AND szsprec_gi01 = '{gi01_val}'
  AND c.szsprec_report_no = 'CALB1'