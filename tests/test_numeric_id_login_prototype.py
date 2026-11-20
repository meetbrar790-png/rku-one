import unittest
from unittest.mock import Mock
from pwdlib import PasswordHash
from numeric_id_login_prototype import validate_numeric_id, verify_numeric_id_password

class NumericLoginPrototypeTests(unittest.TestCase):
    def test_validation(self):
        for invalid in ("", "0", "0002", "-2", "2.0", "٢", "9223372036854775808", True, None):
            self.assertIsNone(validate_numeric_id(invalid))
        self.assertEqual(validate_numeric_id("1001"), 1001)
        self.assertEqual(validate_numeric_id(2), 2)

    def test_correct_password_read_only(self):
        conn = Mock()
        conn.execute.return_value.fetchone.return_value = (PasswordHash.recommended().hash("secure-password-123"),)
        self.assertEqual(verify_numeric_id_password(conn, "1001", "secure-password-123"), {"rku_id": 1001})
        conn.execute.assert_called_once_with("SELECT password_hash FROM users WHERE rku_id = %s", (1001,))

    def test_incorrect_password(self):
        conn = Mock()
        conn.execute.return_value.fetchone.return_value = (PasswordHash.recommended().hash("secure-password-123"),)
        self.assertIsNone(verify_numeric_id_password(conn, "1001", "incorrect"))

    def test_missing_user(self):
        conn = Mock()
        conn.execute.return_value.fetchone.return_value = None
        self.assertIsNone(verify_numeric_id_password(conn, "1001", "secure-password-123"))

    def test_invalid_input_no_query(self):
        conn = Mock()
        self.assertIsNone(verify_numeric_id_password(conn, "0001", "pass"))
        conn.execute.assert_not_called()

if __name__ == "__main__":
    unittest.main()
