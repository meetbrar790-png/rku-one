"""Isolated anti-harassment request guard prototype; no production integration.

A pending request cannot be repeated, and rejected/blocked recipients cannot
be contacted by the sender. Rate-limit counters and enforcement must be stored
atomically in the server/database before public deployment.
"""
from datetime import datetime, timedelta, timezone
from permission_first_policy import ContactStatus

WINDOW = timedelta(hours=24)
MAX_DISTINCT_RECIPIENTS = 10


def may_request(status: ContactStatus, recipient_requests_in_window: int,
                sender_distinct_recipients_in_window: int) -> bool:
    """Fail closed unless the relationship is unknown and quotas allow it."""
    if status is not ContactStatus.UNKNOWN:
        return False
    if any(isinstance(n, bool) or not isinstance(n, int) or n < 0
           for n in (recipient_requests_in_window, sender_distinct_recipients_in_window)):
        return False
    return (recipient_requests_in_window == 0
            and sender_distinct_recipients_in_window < MAX_DISTINCT_RECIPIENTS)


def within_window(occurred_at: datetime, now: datetime) -> bool:
    """Return true for requests within the previous 24 hours, UTC aware only."""
    if any(not isinstance(t, datetime) or t.tzinfo is None or t.utcoffset() is None
           for t in (occurred_at, now)):
        return False
    elapsed = now.astimezone(timezone.utc) - occurred_at.astimezone(timezone.utc)
    return timedelta(0) <= elapsed < WINDOW
