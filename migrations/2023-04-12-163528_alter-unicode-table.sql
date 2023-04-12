-- alter-unicode-table
BEGIN;

-- Add hex char value to unicode table
ALTER TABLE
  unicode_characters
ADD
  COLUMN hex_value VARCHAR(32) NOT NULL;

COMMIT;