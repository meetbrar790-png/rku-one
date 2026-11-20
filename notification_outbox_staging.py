"""Staging-only transactional digest outbox enqueue.

Call in the SAME database transaction as the digest claim. Commit/rollback
belongs to the caller. Does not deliver notifications or guarantee exactly-once
external push delivery. Sender admission and push idempotency remain required.
"""
from notification_digest_db_staging import _validate_recipient, _window_start


def enqueue_digest_once(conn, recipient_id, now):
    """Return True if a pending digest event was newly inserted."""
    _validate_recipient(recipient_id)
    window = _window_start(now)
    row = conn.execute(
        "INSERT INTO notification_outbox_staging "
        "(recipient_rku_id, window_start, event_type) "
        "VALUES (%s, %s, 'unknown_request_digest') "
        "ON CONFLICT (recipient_rku_id, window_start, event_type) DO NOTHING "
        "RETURNING recipient_rku_id",
        (recipient_id, window),
    ).fetchone()
    return row is not None


def claim_and_enqueue_digest(conn, recipient_id, now):
    """Claim and enqueue atomically when caller commits; rollback both on failure."""
    from notification_digest_db_staging import claim_digest_once
    if not claim_digest_once(conn, recipient_id, now):
        return False
    if not enqueue_digest_once(conn, recipient_id, now):
        raise RuntimeError('Digest claimed without new outbox event; rollback transaction')
    return True
