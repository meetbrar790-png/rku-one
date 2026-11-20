-- STAGING ONLY. Apply manually to disposable PostgreSQL, never production.
-- Idempotent per-recipient/day digest enqueue. Delivery worker is NOT included.
CREATE TABLE IF NOT EXISTS notification_outbox_staging (
    recipient_rku_id BIGINT NOT NULL,
    window_start TIMESTAMPTZ NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type = 'unknown_request_digest'),
    state TEXT NOT NULL DEFAULT 'pending' CHECK (state IN ('pending', 'sending', 'sent')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (recipient_rku_id, window_start, event_type)
);
