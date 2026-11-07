import unittest
from datetime import datetime, timedelta, timezone

from account_recovery_policy import (
    RESET_TTL, new_reset_token, hash_reset_token, token_matches,
    reset_token_usable, recovery_request_public_message,
)


class AccountRecoveryPolicyTests(unittest.TestCase):
    def test_tokens_random_and_only_digest_needed_for_validation(self):
        a, b = new_reset_token(), new_reset_token()
        self.assertNotEqual(a, b)
        self.assertGreaterEqual(len(a), 32)
        digest = hash_reset_token(a)
        self.assertEqual(len(digest), 64)
        self.assertNotEqual(a, digest)
        self.assertTrue(token_matches(a, digest))
        self.assertFalse(token_matches(b, digest))
        self.assertFalse(token_matches("bad", digest))

    def test_one_use_and_expiry_boundaries(self):
        issued = datetime(2026, 11, 8, tzinfo=timezone.utc)
        self.assertTrue(reset_token_usable(issued_at=issued, now=issued, consumed=False))
        self.assertTrue(reset_token_usable(
            issued_at=issued, now=issued + RESET_TTL - timedelta(microseconds=1), consumed=False
        ))
        self.assertFalse(reset_token_usable(
            issued_at=issued, now=issued + RESET_TTL, consumed=False
        ))
        self.assertFalse(reset_token_usable(
            issued_at=issued, now=issued + timedelta(seconds=1), consumed=True
        ))
        self.assertFalse(reset_token_usable(
            issued_at=issued, now=issued - timedelta(seconds=1), consumed=False
        ))

    def test_naive_timestamps_rejected(self):
        with self.assertRaises(ValueError):
            reset_token_usable(
                issued_at=datetime(2026, 11, 8),
                now=datetime(2026, 11, 8, tzinfo=timezone.utc),
                consumed=False,
            )

    def test_neutral_public_message(self):
        self.assertEqual(
            recovery_request_public_message(),
            "If this email is registered, recovery instructions will be sent.",
        )


if __name__ == "__main__":
    unittest.main()
