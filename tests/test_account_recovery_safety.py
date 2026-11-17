"""Offline tests for password recovery primitives; never contact production."""
from datetime import datetime, timedelta, timezone

from account_recovery_policy import (
    RESET_TTL, hash_reset_token, new_reset_token,
    recovery_request_public_message, reset_token_usable, token_matches,
)


def test_token_is_random_and_only_digest_matches():
    a, b = new_reset_token(), new_reset_token()
    assert a != b
    assert len(a) >= 32
    digest = hash_reset_token(a)
    assert a != digest
    assert token_matches(a, digest)
    assert not token_matches(b, digest)
    assert not token_matches("invalid", digest)


def test_expired_and_used_tokens_are_rejected():
    now = datetime.now(timezone.utc)
    assert reset_token_usable(issued_at=now, now=now, consumed=False)
    assert not reset_token_usable(issued_at=now - RESET_TTL, now=now, consumed=False)
    assert not reset_token_usable(issued_at=now, now=now, consumed=True)
    assert not reset_token_usable(issued_at=now + timedelta(seconds=1), now=now, consumed=False)


def test_public_response_does_not_reveal_account_existence():
    message = recovery_request_public_message()
    assert "If this email is registered" in message
    assert "RKU ID" not in message
