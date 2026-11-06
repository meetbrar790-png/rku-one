"""Registration and login route regression tests without production database access."""
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from psycopg.errors import UniqueViolation
from api import UserData, register, login


class AccountRouteTests(unittest.TestCase):
    def setUp(self):
        self.user = UserData(email="test@example.com", password="safe-password-123")

    def test_registration_returns_allocated_id(self):
        with patch("api.register_user", return_value={"rku_id": 42, "email": "test@example.com"}) as create:
            result = register(self.user)
        self.assertEqual(result["rku_id"], 42)
        create.assert_called_once_with("test@example.com", "safe-password-123")

    def test_registration_validation_error_is_400(self):
        with patch("api.register_user", side_effect=ValueError("Invalid password")):
            with self.assertRaises(HTTPException) as error:
                register(self.user)
        self.assertEqual(error.exception.status_code, 400)

    def test_duplicate_registration_is_409(self):
        with patch("api.register_user", side_effect=UniqueViolation("duplicate")):
            with self.assertRaises(HTTPException) as error:
                register(self.user)
        self.assertEqual(error.exception.status_code, 409)

    def test_invalid_login_does_not_issue_token(self):
        with patch("api.verify_login", return_value=None), patch("api.issue_token") as issue:
            with self.assertRaises(HTTPException) as error:
                login(self.user)
            self.assertEqual(error.exception.status_code, 401)
            issue.assert_not_called()

    def test_valid_login_issues_token_for_authenticated_id(self):
        with patch("api.verify_login", return_value={"rku_id": 42}), patch(
            "api.issue_token", return_value="test-token"
        ) as issue:
            result = login(self.user)
        self.assertEqual(result, {"rku_id": 42, "token": "test-token"})
        issue.assert_called_once_with(42)

    def test_login_database_error_is_500_without_leaking_details(self):
        with patch("api.verify_login", side_effect=RuntimeError("private database detail")), patch("api.logging.exception"):
            with self.assertRaises(HTTPException) as error:
                login(self.user)
        self.assertEqual(error.exception.status_code, 500)
        self.assertNotIn("private database detail", str(error.exception.detail))


if __name__ == "__main__":
    unittest.main()
