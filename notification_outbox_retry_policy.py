"""Pure staging-only retry policy for notification outbox workers.

Does not send push notifications. Real workers require DB leases with fencing,
transactional state updates, dead-letter handling and provider idempotency.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum


class RetryDecision(str, Enum):
    RETRY = "retry"
    WAIT = "wait"
    DEAD_LETTER = "dead_letter"
    COMPLETE = "complete"


@dataclass(frozen=True)
class OutboxAttempt:
    attempts: int
    next_attempt_at: datetime
    delivered: bool = False


def retry_decision(attempt: OutboxAttempt, now: datetime, *, max_attempts: int = 5) -> RetryDecision:
    if not isinstance(attempt, OutboxAttempt):
        return RetryDecision.DEAD_LETTER
    if attempt.delivered is True:
        return RetryDecision.COMPLETE
    if not isinstance(attempt.attempts, int) or isinstance(attempt.attempts, bool) or attempt.attempts < 0:
        return RetryDecision.DEAD_LETTER
    if not isinstance(max_attempts, int) or isinstance(max_attempts, bool) or max_attempts < 1:
        return RetryDecision.DEAD_LETTER
    if attempt.attempts >= max_attempts:
        return RetryDecision.DEAD_LETTER
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        return RetryDecision.DEAD_LETTER
    due = attempt.next_attempt_at
    if not isinstance(due, datetime) or due.tzinfo is None or due.utcoffset() is None:
        return RetryDecision.DEAD_LETTER
    return RetryDecision.RETRY if now.astimezone(timezone.utc) >= due.astimezone(timezone.utc) else RetryDecision.WAIT


def next_backoff(attempts_after_failure: int) -> timedelta:
    """Exponential retry delay capped at one hour; caller adds jitter."""
    if not isinstance(attempts_after_failure, int) or isinstance(attempts_after_failure, bool) or attempts_after_failure < 1:
        raise ValueError('Positive integer attempt count required')
    return timedelta(seconds=min(3600, 30 * (2 ** min(attempts_after_failure - 1, 8))))
