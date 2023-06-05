SELECT
  CASE
    WHEN inner_query.collation_type = 'ICU'
    AND inner_query.ICU_FROZEN = 1
    AND inner_query.ICU_EXTRA_TAILORING = 1 THEN 'ICU_tailoring'
    WHEN inner_query.collation_type = 'ICU'
    AND inner_query.ICU_FROZEN = 1
    AND inner_query.ICU_EXTRA_TAILORING = 0 THEN 'ICU_frozen'
    WHEN inner_query.collation_type = 'ICU'
    AND inner_query.ICU_FROZEN = 0
    AND inner_query.ICU_EXTRA_TAILORING = 0 THEN 'ICU_locale'
    ELSE 'MySQL'
  END AS config,
  COUNT(*),
  ROUND(AVG(order_by_asc), 2),
  ROUND(AVG(order_by_desc), 2),
  ROUND(AVG(equals), 2)
FROM
  (
    SELECT
      ICU_FROZEN,
      ICU_EXTRA_TAILORING,
      CASE
        WHEN SUBSTR(collation, 9, 3) = 'icu' THEN 'ICU'
        ELSE 'MySQL'
      END AS collation_type,
      order_by_asc,
      order_by_desc,
      equals
    FROM
      benchmarks
  ) AS inner_query
GROUP BY
  config;