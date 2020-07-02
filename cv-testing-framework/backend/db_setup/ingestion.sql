-- This file sets up various table used for ingestion.

--create a saperate schema for ingestion tables
CREATE SCHEMA IF NOT EXISTS uploads;

-- Grant privilage to backend and backend readonly users
-- These privilages enable the user to crate and drop the temp staging tables
GRANT ALL ON SCHEMA uploads TO backend;

-- table to store upload audits
CREATE TABLE uploads.uploads_audit (
    tablename TEXT NOT NULL PRIMARY KEY,
    entrydate DATE NOT NULL,
    table_exist BOOLEAN NOT NULL
);
ALTER TABLE uploads.uploads_audit OWNER to backend;
GRANT ALL ON TABLE uploads.uploads_audit TO backend;
GRANT SELECT ON TABLE uploads.uploads_audit TO backend_readonly;