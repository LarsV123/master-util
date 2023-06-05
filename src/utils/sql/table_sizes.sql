SELECT
  table_name AS `Table`,
  ROUND(((data_length + index_length) / 1024 / 1024), 2) `Size in MiB`
FROM
  information_schema.TABLES
WHERE
  table_schema = DATABASE()
  AND table_name LIKE 'test_%'
ORDER BY
  `Size in MiB` DESC;