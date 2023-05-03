-- Add table of unique strings. These can be used when testing how different collations order strings.

BEGIN;

CREATE TABLE validity_test_strings (
    string VARCHAR(64) NOT NULL,
    PRIMARY KEY(string)
    );

COMMIT;