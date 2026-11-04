"""RKU ONE authentication and mail input regression tests.

Run with: python -m unittest discover -s tests
These tests use mocks and do not touch production accounts or database.
"""
import unittest
from unittest.mock import patch
from fastapi import HTTPException
from mail_auth import issue_token, authenticated_id

from registration import register_user, verify_login
from mail_store import deliver_many, mailbox


class RegistrationInputTests(unittest.TestCase):
    def test_short_password_rejected_without_database(self):
        with patch("registration.get_connection") as connect:
            with self.assertRaises(ValueError):
                register_user("user@example.com", "short")
            connect.assert_not_called()

    def test_oversized_password_rejected_without_database(self):
        with patch("registration.get_connection") as connect:
            with self.assertRaises(ValueError):
                register_user("user@example.com", "x" * 257)
            connect.assert_not_called()

    def test_oversized_login_rejected_without_database(self):
        with patch("registration.get_connection") as connect:
            self.assertIsNone(verify_login("user@example.com", "x" * 257))
            connect.assert_not_called()


class MailInputTests(unittest.TestCase):
    def test_empty_recipients_rejected(self):
        with patch("mail_store.get_connection") as connect:
            with self.assertRaises(ValueError):
                deliver_many(1, [], "Subject", "Body")
            connect.assert_not_called()

    def test_more_than_25_recipients_rejected(self):
        with patch("mail_store.get_connection") as connect:
            with self.assertRaises(ValueError):
                deliver_many(1, list(range(1, 27)), "Subject", "Body")
            connect.assert_not_called()

    def test_invalid_cursor_rejected(self):
        with patch("mail_store.get_connection") as connect:
            with self.assertRaises(ValueError):
                mailbox(1, before=0)
            connect.assert_not_called()


class SessionTokenTests(unittest.TestCase):
    def test_valid_signed_token(self):
        with patch.dict("os.environ", {"RKU_SESSION_SECRET": "test-only-secret"}):
            token = issue_token(1)
            self.assertEqual(authenticated_id("Bearer " + token), 1)

    def test_modified_signature_rejected(self):
        with patch.dict("os.environ", {"RKU_SESSION_SECRET": "test-only-secret"}):
            token = issue_token(1)
            payload, signature = token.split(".")
            changed = ("0" if signature[0] != "0" else "1") + signature[1:]
            with self.assertRaises(HTTPException) as error:
                authenticated_id("Bearer " + payload + "." + changed)
            self.assertEqual(error.exception.status_code, 401)

    def test_expired_token_rejected(self):
        with patch.dict("os.environ", {"RKU_SESSION_SECRET": "test-only-secret"}):
            with patch("mail_auth.time.time", return_value=1000):
                token = issue_token(1)
            with patch("mail_auth.time.time", return_value=1000 + 86401):
                with self.assertRaises(HTTPException) as error:
                    authenticated_id("Bearer " + token)
            self.assertEqual(error.exception.status_code, 401)

    def test_oversized_bearer_token_rejected(self):
        with self.assertRaises(HTTPException) as error:
            authenticated_id("Bearer " + "a" * 5000)
        self.assertEqual(error.exception.status_code, 401)

    def test_missing_bearer_token_rejected(self):
        with self.assertRaises(HTTPException) as error:
            authenticated_id(None)
        self.assertEqual(error.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
