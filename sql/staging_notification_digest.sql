-- STAGING ONLY. Run manually on a disposable PostgreSQL database.
-- Do NOT run against production; not included in app startup migrations.
CREATE TABLE IF NOT EXISTS notification_digest_staging (
    recipient_rku_id BIGINT NOT NULL,
    window_start TIMESTAMPTZ NOT NULL,
    unknown_request_count BIGINT NOT NULL DEFAULT 0 CHECK (unknown_request_count >= 0),
    digest_claimed BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (recipient_rku_id, window_start)
);
