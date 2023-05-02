-- alter unicode table

BEGIN;

-- Add unique constraint on code_point column
ALTER TABLE unicode_characters ADD CONSTRAINT unicode_characters_code_point_unique UNIQUE (code_point);

COMMIT;