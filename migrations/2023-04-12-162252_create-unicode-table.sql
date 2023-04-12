-- create unicode table
BEGIN;

-- Add table of all characters in Unicode to test ordering them
CREATE TABLE unicode_characters (
  code_point INTEGER NOT NULL,
  char_value VARCHAR(255) NOT NULL
);

COMMIT;