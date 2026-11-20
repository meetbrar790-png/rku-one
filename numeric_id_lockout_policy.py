"""Pure, isolated lockout policy prototype for RKU numeric ID login.

This module has NO persistence, API route, or production enforcement. A public
login requires transactional PostgreSQL state, trusted IP throttling, and review.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

WINDOW = timedelta(minutes=15)
LOCKOUT = timedelta(minutes=15)
MAX_FAILURES = 5


@dataclass(frozen=True)
class LoginFailureState:
    failures: int = 0
    first_failure: datetime | None = None
    blocked_until: datetime | None = None


def _utc(instant: datetime) -> datetime:
    if not isinstance(instant, datetime) or instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("An aware datetime is required")
    return instant.astimezone(timezone.utc)


def is_blocked(state: LoginFailureState, now: datetime) -> bool:
    now = _utc(now)
    return state.blocked_until is not None and now < _utc(state.blocked_until)


def record_failed_attempt(state: LoginFailureState, now: datetime) -> LoginFailureState:
    """Calculate next failure state; caller MUST persist it atomically.

    Repeated attempts during a lockout do not extend its expiration.
    """
    now = _utc(now)
    if is_blocked(state, now):
        return state
    if state.first_failure is None or now - _utc(state.first_failure) >= WINDOW:
        return LoginFailureState(failures=1, first_failure=now)
    failures = state.failures + 1
    return LoginFailureState(
        failures=failures,
        first_failure=state.first_failure,
        blocked_until=now + LOCKOUT if failures >= MAX_FAILURES else None,
    )


def clear_after_success() -> LoginFailureState:
    """Return a clean state; caller must persist atomically after valid login."""
    return LoginFailureState()
