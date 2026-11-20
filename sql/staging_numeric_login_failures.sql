-- STAGING ONLY: execute against a disposable PostgreSQL database, NOT production.
-- This migration is not invoked by application startup or deployment.
CREATE TABLE IF NOT EXISTS numeric_login_failures (
    rku_id BIGINT PRIMARY KEY,
    failures INTEGER NOT NULL CHECK (failures >= 0),
    first_failure TIMESTAMPTZ,
    blocked_until TIMESTAMPTZ
);
-- Do not add a foreign key until deletion/retention behavior is reviewed.
