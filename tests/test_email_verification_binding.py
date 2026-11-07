import unittest
from email_verification_binding import may_verify_email, normalize_verification_email


class EmailVerificationBindingTests(unittest.TestCase):
    def test_same_account_and_email_can_verify(self):
        self.assertTrue(may_verify_email(
            token_user_id=1001, current_user_id=1001,
            token_email=" Owner@Example.com ", current_email="owner@example.com",
            token_is_usable=True))

    def test_changed_email_cannot_reuse_old_token(self):
        self.assertFalse(may_verify_email(
            token_user_id=1001, current_user_id=1001,
            token_email="old@example.com", current_email="new@example.com",
            token_is_usable=True))

    def test_other_account_cannot_claim_token(self):
        self.assertFalse(may_verify_email(
            token_user_id=1001, current_user_id=1002,
            token_email="owner@example.com", current_email="owner@example.com",
            token_is_usable=True))

    def test_expired_or_used_token_cannot_verify(self):
        self.assertFalse(may_verify_email(
            token_user_id=1001, current_user_id=1001,
            token_email="owner@example.com", current_email="owner@example.com",
            token_is_usable=False))

    def test_invalid_email_and_ids_rejected(self):
        for email in ("", "bad", "owner@example.com\nBcc: bad@example.com"):
            with self.subTest(email=email):
                with self.assertRaises(ValueError):
                    normalize_verification_email(email)
        self.assertFalse(may_verify_email(
            token_user_id=True, current_user_id=1,
            token_email="a@example.com", current_email="a@example.com",
            token_is_usable=True))


if __name__ == "__main__":
    unittest.main()
