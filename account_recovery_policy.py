"""Pure account recovery safety policy, not connected to production.

Never store raw recovery tokens. Production requires a DB-backed one-use
token, verified email delivery, atomic consumption, rate limiting and audit.
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

RESET_TOKEN_BYTES = 32
RESET_TTL = timedelta(minutes=20)


def new_reset_token() -> str:
    """Generate a high-entropy bearer token; show only in authorized email."""
    return secrets.token_urlsafe(RESET_TOKEN_BYTES)


def hash_reset_token(token: str) -> str:
    if not isinstance(token, str) or len(token) < 32 or len(token) > 512:
        raise ValueError("Invalid reset token")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def token_matches(candidate: str, expected_digest: str) -> bool:
    """Compare token digests without revealing token contents."""
    if not isinstance(expected_digest, str) or len(expected_digest) != 64:
        return False
    try:
        return hmac.compare_digest(hash_reset_token(candidate), expected_digest)
    except ValueError:
        return False


def reset_token_usable(*, issued_at: datetime, now: datetime, consumed: bool) -> bool:
    if not isinstance(issued_at, datetime) or not isinstance(now, datetime):
        raise ValueError("Timezone-aware timestamps required")
    if issued_at.tzinfo is None or now.tzinfo is None:
        raise ValueError("Timezone-aware timestamps required")
    if not isinstance(consumed, bool):
        raise ValueError("Consumed flag must be boolean")
    age = now.astimezone(timezone.utc) - issued_at.astimezone(timezone.utc)
    return not consumed and timedelta(0) <= age < RESET_TTL


def recovery_request_public_message() -> str:
    """Identical response regardless of whether the email exists."""
    return "If this email is registered, recovery instructions will be sent."
