"""Staging-only atomic digest aggregation for unknown connection requests.

Caller must authenticate recipient and enforce admission control before calling.
This does NOT send notifications, guarantee delivery, or provide anti-DDoS.
Use within a caller-owned database transaction; never call on production.
"""
from datetime import datetime, timezone


def _window_start(now: datetime) -> datetime:
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Timezone-aware timestamp required")
    utc = now.astimezone(timezone.utc)
    return utc.replace(hour=0, minute=0, second=0, microsecond=0)


def _validate_recipient(recipient_id: int) -> None:
    if isinstance(recipient_id, bool) or not isinstance(recipient_id, int) or not 1 <= recipient_id <= 9223372036854775807:
        raise ValueError("Invalid recipient ID")


def count_unknown_request(conn, recipient_id: int, now: datetime) -> int:
    """Atomic increment; return current daily count, not a push decision."""
    _validate_recipient(recipient_id)
    window = _window_start(now)
    row = conn.execute(
        "INSERT INTO notification_digest_staging (recipient_rku_id, window_start, unknown_request_count) "
        "VALUES (%s, %s, 1) ON CONFLICT (recipient_rku_id, window_start) "
        "DO UPDATE SET unknown_request_count = notification_digest_staging.unknown_request_count + 1 "
        "RETURNING unknown_request_count",
        (recipient_id, window),
    ).fetchone()
    return row[0]


def claim_digest_once(conn, recipient_id: int, now: datetime) -> bool:
    """Atomically claim one digest for an existing recipient/day row.

    Claiming is NOT delivery. A real worker needs a transactional outbox and
    retry/idempotency strategy to avoid lost notifications after worker crashes.
    """
    _validate_recipient(recipient_id)
    window = _window_start(now)
    row = conn.execute(
        "UPDATE notification_digest_staging SET digest_claimed = TRUE "
        "WHERE recipient_rku_id = %s AND window_start = %s AND digest_claimed = FALSE "
        "RETURNING unknown_request_count",
        (recipient_id, window),
    ).fetchone()
    return row is not None
