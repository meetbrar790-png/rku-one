import unittest
from datetime import datetime, timedelta, timezone
from email_verification_policy import (
    VERIFICATION_TTL, create_verification_token, verification_digest,
    verification_matches, verification_usable, verification_request_public_message,
)


class EmailVerificationPolicyTests(unittest.TestCase):
    def test_random_tokens_and_digest_only(self):
        first, second = create_verification_token(), create_verification_token()
        self.assertNotEqual(first, second)
        digest = verification_digest(first)
        self.assertEqual(len(digest), 64)
        self.assertTrue(verification_matches(first, digest))
        self.assertFalse(verification_matches(second, digest))
        self.assertFalse(verification_matches("invalid", digest))

    def test_expiry_one_use_and_future_rejection(self):
        issued = datetime(2026, 11, 8, tzinfo=timezone.utc)
        self.assertTrue(verification_usable(issued_at=issued, now=issued, consumed=False))
        self.assertTrue(verification_usable(
            issued_at=issued, now=issued + VERIFICATION_TTL - timedelta(microseconds=1),
            consumed=False))
        self.assertFalse(verification_usable(
            issued_at=issued, now=issued + VERIFICATION_TTL, consumed=False))
        self.assertFalse(verification_usable(
            issued_at=issued, now=issued + timedelta(minutes=1), consumed=True))
        self.assertFalse(verification_usable(
            issued_at=issued, now=issued - timedelta(seconds=1), consumed=False))

    def test_naive_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            verification_usable(
                issued_at=datetime(2026, 11, 8),
                now=datetime(2026, 11, 8, tzinfo=timezone.utc),
                consumed=False)

    def test_neutral_response(self):
        self.assertIn("If this account is eligible", verification_request_public_message())


if __name__ == "__main__":
    unittest.main()
