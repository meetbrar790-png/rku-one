"""Additional non-production security regression tests for numeric ID login."""
import unittest
from unittest.mock import Mock
from numeric_id_login_prototype import validate_numeric_id, verify_numeric_id_password

class NumericLoginSecurityTests(unittest.TestCase):
    def test_rejects_oversized_and_noncanonical_ids(self):
        invalid = ["0", "00", "01", "+1", " 1", "1 ", "1\\n", "1e3", "1.0", "１", "١", "9" * 1000, "9223372036854775808", -1, 1.0, False, None, [], {}]
        for value in invalid:
            with self.subTest(value=repr(value)[:50]):
                self.assertIsNone(validate_numeric_id(value))

    def test_accepts_boundaries(self):
        self.assertEqual(validate_numeric_id("1"), 1)
        self.assertEqual(validate_numeric_id("9223372036854775807"), 9223372036854775807)

    def test_invalid_credentials_do_not_touch_database(self):
        for user_id, password in [("0002", "pass"), ("1001", None), ("1001", "x" * 257), (True, "pass")]:
            with self.subTest(user_id=user_id):
                conn = Mock()
                self.assertIsNone(verify_numeric_id_password(conn, user_id, password))
                conn.execute.assert_not_called()

    def test_missing_id_returns_none_without_database_write(self):
        conn = Mock()
        conn.execute.return_value.fetchone.return_value = None
        self.assertIsNone(verify_numeric_id_password(conn, "1001", "password"))
        conn.execute.assert_called_once_with("SELECT password_hash FROM users WHERE rku_id = %s", (1001,))
        self.assertFalse(conn.commit.called)

if __name__ == "__main__":
    unittest.main()
