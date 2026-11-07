"""API registration contract tests; no database or external HTTP calls."""
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from psycopg.errors import UniqueViolation

from api import UserData, register


class RegistrationApiContractTests(unittest.TestCase):
    def test_success_returns_allocated_id_and_email(self):
        with patch("api.register_user", return_value={
            "rku_id": 42, "email": "new@example.invalid"
        }) as mocked:
            result = register(UserData(email="new@example.invalid",
                                       password="long-test-password"))
        self.assertEqual(result, {"rku_id": 42, "email": "new@example.invalid"})
        mocked.assert_called_once_with("new@example.invalid", "long-test-password")

    def test_invalid_registration_returns_400(self):
        with patch("api.register_user", side_effect=ValueError("Invalid registration")):
            with self.assertRaises(HTTPException) as ctx:
                register(UserData(email="new@example.invalid",
                                  password="long-test-password"))
        self.assertEqual(ctx.exception.status_code, 400)

    def test_duplicate_email_returns_409(self):
        with patch("api.register_user", side_effect=UniqueViolation("duplicate")):
            with self.assertRaises(HTTPException) as ctx:
                register(UserData(email="new@example.invalid",
                                  password="long-test-password"))
        self.assertEqual(ctx.exception.status_code, 409)

    def test_internal_error_hides_details(self):
        with patch("api.register_user", side_effect=RuntimeError("private DB detail")):
            with self.assertRaises(HTTPException) as ctx:
                register(UserData(email="new@example.invalid",
                                  password="long-test-password"))
        self.assertEqual(ctx.exception.status_code, 500)
        self.assertNotIn("private DB detail", str(ctx.exception.detail))


if __name__ == "__main__":
    unittest.main()
