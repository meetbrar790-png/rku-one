"""Pure VIP hold expiry policy. No database writes or live checkout."""
from datetime import datetime

def may_release_hold(*, state, paid, issued, expires_at, now):
    """Eligibility only; caller must recheck payment and ID under DB lock."""
    if state not in {"reserved", "allocated", "cancelled"}:
        raise ValueError("Unknown reservation state")
    if type(paid) is not bool or type(issued) is not bool:
        raise ValueError("paid and issued must be boolean")
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    if expires_at is not None and (
        not isinstance(expires_at, datetime)
        or expires_at.tzinfo is None
        or expires_at.utcoffset() is None
    ):
        raise ValueError("expires_at must be timezone-aware")
    if paid or issued or state == "allocated":
        return False
    if state == "cancelled":
        return True
    return expires_at is not None and expires_at <= now
