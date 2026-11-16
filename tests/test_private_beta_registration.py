"""Private beta signup allowlist tests. No live accounts or database."""
import unittest
from unittest.mock import patch
from fastapi import HTTPException
from api import register, UserData


class PrivateBetaRegistrationTests(unittest.TestCase):
    def user(self, email):
        return UserData(email=email, password="long-test-password")

    def test_invited_email_can_register(self):
        with patch.dict("os.environ", {"RKU_BETA_ALLOWED_EMAILS": "Friend@Example.com,other@example.com"}), \
             patch("api.register_user", return_value={"rku_id": 1003, "email": "friend@example.com"}) as create:
            self.assertEqual(register(self.user("friend@example.com"))["rku_id"], 1003)
        create.assert_called_once()

    def test_uninvited_email_is_rejected_before_database(self):
        with patch.dict("os.environ", {"RKU_BETA_ALLOWED_EMAILS": "friend@example.com"}), \
             patch("api.register_user") as create:
            with self.assertRaises(HTTPException) as error:
                register(self.user("stranger@example.com"))
        self.assertEqual(error.exception.status_code, 403)
        create.assert_not_called()

    def test_unset_allowlist_keeps_existing_registration_behavior(self):
        with patch.dict("os.environ", {"RKU_BETA_ALLOWED_EMAILS": ""}), \
             patch("api.register_user", return_value={"rku_id": 1004, "email": "new@example.com"}) as create:
            self.assertEqual(register(self.user("new@example.com"))["rku_id"], 1004)
        create.assert_called_once()


if __name__ == "__main__":
    unittest.main()
