-- rename table

BEGIN;

ALTER TABLE validity_test_strings RENAME TO test_strings;

COMMIT;