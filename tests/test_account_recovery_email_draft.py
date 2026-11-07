import unittest
from account_recovery_email_draft import build_reset_email
from account_recovery_policy import new_reset_token


class RecoveryEmailDraftTests(unittest.TestCase):
    def test_reset_email_contains_one_time_link_but_no_password(self):
        token = new_reset_token()
        draft = build_reset_email(
            recipient_email=" Owner@Example.com ",
            token=token,
            app_origin="https://rkuone.com",
        )
        self.assertEqual(draft["to"], "owner@example.com")
        self.assertEqual(draft["ttl_minutes"], 20)
        self.assertFalse(draft["delivery_enabled"])
        self.assertIn("https://rkuone.com/reset-password?token=", draft["text"])
        self.assertIn(token, draft["text"])
        self.assertNotIn("password_hash", draft["text"])

    def test_untrusted_or_insecure_origin_rejected(self):
        token = new_reset_token()
        for origin in (
            "http://rkuone.com", "https://rkuone.com.evil.org/path",
            "https://evil.example", "https://sub.rkuone.com",
            "https://rkuone.com:8443",
            "https://user:pass@rkuone.com", "https://rkuone.com/?next=bad",
            "https://rkuone.com/#fragment", "javascript:alert(1)",
        ):
            with self.subTest(origin=origin):
                with self.assertRaises(ValueError):
                    build_reset_email(
                        recipient_email="owner@example.com", token=token, app_origin=origin
                    )

    def test_invalid_recipient_rejected(self):
        with self.assertRaises(ValueError):
            build_reset_email(
                recipient_email="owner@example.com\r\nBcc: bad@example.com",
                token=new_reset_token(), app_origin="https://rkuone.com"
            )


if __name__ == "__main__":
    unittest.main()
