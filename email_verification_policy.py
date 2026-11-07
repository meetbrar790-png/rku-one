"""Offline email verification token policy for future RKU ONE onboarding.

No emails sent and no production database changes. Persist only token digest;
consume it atomically and bind it to a specific account/email server-side.
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

VERIFICATION_TTL = timedelta(hours=24)


def create_verification_token() -> str:
    return secrets.token_urlsafe(32)


def verification_digest(token: str) -> str:
    if not isinstance(token, str) or not 32 <= len(token) <= 512:
        raise ValueError("Invalid verification token")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verification_matches(candidate: str, stored_digest: str) -> bool:
    if not isinstance(stored_digest, str) or len(stored_digest) != 64:
        return False
    try:
        return hmac.compare_digest(verification_digest(candidate), stored_digest)
    except ValueError:
        return False


def verification_usable(*, issued_at: datetime, now: datetime, consumed: bool) -> bool:
    if not isinstance(issued_at, datetime) or not isinstance(now, datetime):
        raise ValueError("Timezone-aware timestamps required")
    if issued_at.tzinfo is None or now.tzinfo is None or not isinstance(consumed, bool):
        raise ValueError("Timezone-aware timestamps and boolean consumed required")
    age = now.astimezone(timezone.utc) - issued_at.astimezone(timezone.utc)
    return not consumed and timedelta(0) <= age < VERIFICATION_TTL


def verification_request_public_message() -> str:
    return "If this account is eligible, verification instructions will be sent."
