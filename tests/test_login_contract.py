"""Isolated RKU ONE login contract tests.

Uses mocked credential lookup and token issuance; no production users,
external requests, or database connections are accessed.
"""
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from api import UserData, login


class LoginContractTests(unittest.TestCase):
    def setUp(self):
        self.user = UserData(email="staging@example.com", password="test-password-12345")

    def test_valid_login_returns_id_and_token(self):
        with patch("api.verify_login", return_value={"rku_id": 1001, "email": "staging@example.com"}) as verify, patch(
            "api.issue_token", return_value="isolated-test-token"
        ) as token:
            result = login(self.user)
        self.assertEqual(result["rku_id"], 1001)
        self.assertEqual(result["token"], "isolated-test-token")
        verify.assert_called_once_with("staging@example.com", "test-password-12345")
        token.assert_called_once_with(1001)

    def test_invalid_credentials_return_401_without_token(self):
        with patch("api.verify_login", return_value=None), patch("api.issue_token") as token:
            with self.assertRaises(HTTPException) as error:
                login(self.user)
        self.assertEqual(error.exception.status_code, 401)
        token.assert_not_called()

    def test_internal_login_error_is_not_disclosed(self):
        with patch("api.verify_login", side_effect=RuntimeError("secret production detail")), patch(
            "api.issue_token"
        ) as token:
            with self.assertRaises(HTTPException) as error:
                login(self.user)
        self.assertEqual(error.exception.status_code, 500)
        self.assertNotIn("secret production detail", str(error.exception.detail))
        token.assert_not_called()


if __name__ == "__main__":
    unittest.main()
