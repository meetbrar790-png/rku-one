"""RKU ID policy checks. No live database access or number allocation.

Existing numeric IDs must never be reassigned. VIP reservation must be
introduced only after an inventory audit and an explicit migration review.
"""
import unittest
from unittest.mock import patch

from registration import register_user


class NumericIdPolicyTests(unittest.TestCase):
    def test_invalid_email_does_not_allocate_an_id(self):
        with patch("registration.get_connection") as connect:
            with self.assertRaises(ValueError):
                register_user("", "secure-password-123")
            connect.assert_not_called()

    def test_too_long_email_does_not_allocate_an_id(self):
        with patch("registration.get_connection") as connect:
            with self.assertRaises(ValueError):
                register_user("x" * 255, "secure-password-123")
            connect.assert_not_called()

    def test_issued_ids_are_returned_unchanged(self):
        # A fake database response ensures registration does not rewrite
        # previously assigned IDs or force a specific VIP number.
        from unittest.mock import MagicMock
        conn = MagicMock()
        conn.execute.return_value.fetchone.return_value = (9001,)
        manager = MagicMock()
        manager.__enter__.return_value = conn
        with patch("registration.get_connection", return_value=manager), patch(
            "registration.password_hash.hash", return_value="fake-hash"
        ):
            result = register_user("USER@example.com", "secure-password-123")
        self.assertEqual(result, {"rku_id": 9001, "email": "user@example.com"})
        sql = conn.execute.call_args.args[0]
        self.assertIn("RETURNING rku_id", sql)
        self.assertNotIn("OVERRIDING SYSTEM VALUE", sql)


if __name__ == "__main__":
    unittest.main()
