-- create-test-table
BEGIN;

CREATE TABLE test_table (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

COMMIT;