"""RKU ONE authentication and mail input regression tests.

Run with: python -m unittest discover -s tests
These tests use mocks and do not touch production accounts or database.
"""
import unittest
from unittest.mock import patch, MagicMock

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


if __name__ == "__main__":
    unittest.main()
