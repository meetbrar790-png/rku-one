"""API route regression tests; all database operations are mocked."""
import unittest
from unittest.mock import patch
from fastapi import HTTPException
from api import send_message, inbox, contacts_list, contacts_save, contacts_remove, MailData, ContactData


class ApiRouteTests(unittest.TestCase):
    def test_send_requires_login(self):
        with self.assertRaises(HTTPException) as caught:
            send_message(MailData(to=2, subject="Hello", body="Hi"), authorization=None)
        self.assertEqual(caught.exception.status_code, 401)

    def test_send_rate_limit_returns_429(self):
        with patch("api.authenticated_id", return_value=1), patch(
            "api.deliver_many", side_effect=ValueError("Sending limit reached. Please wait before sending more mail.")
        ):
            with self.assertRaises(HTTPException) as caught:
                send_message(MailData(to=2, subject="Hello", body="Hi"), authorization="Bearer mock")
        self.assertEqual(caught.exception.status_code, 429)
        self.assertEqual(caught.exception.headers["Retry-After"], "60")

    def test_send_rejects_blank_subject_before_database(self):
        with patch("api.authenticated_id", return_value=1), patch("api.deliver_many") as deliver:
            with self.assertRaises(HTTPException) as caught:
                send_message(MailData(to=2, subject=" ", body="Hi"), authorization="Bearer mock")
            self.assertEqual(caught.exception.status_code, 400)
            deliver.assert_not_called()

    def test_inbox_rejects_bad_cursor(self):
        with patch("api.mailbox") as mailbox:
            with self.assertRaises(HTTPException) as caught:
                inbox(before=0, authorization="Bearer mock")
            self.assertEqual(caught.exception.status_code, 400)
            mailbox.assert_not_called()

    def test_contacts_require_login(self):
        with self.assertRaises(HTTPException) as caught:
            contacts_list(authorization=None)
        self.assertEqual(caught.exception.status_code, 401)

    def test_contacts_save_uses_authenticated_owner(self):
        with patch("api.authenticated_id", return_value=1), patch(
            "api.save_contact", return_value={"rku_id": 2, "nickname": "Friend"}
        ) as save:
            result = contacts_save(ContactData(rku_id=2, nickname="Friend"), authorization="Bearer mock")
        save.assert_called_once_with(1, 2, "Friend")
        self.assertEqual(result["rku_id"], 2)

    def test_contacts_remove_rejects_invalid_id(self):
        with patch("api.authenticated_id", return_value=1), patch("api.delete_contact") as delete:
            with self.assertRaises(HTTPException) as caught:
                contacts_remove(ContactData(rku_id=0), authorization="Bearer mock")
            self.assertEqual(caught.exception.status_code, 400)
            delete.assert_not_called()


if __name__ == "__main__":
    unittest.main()
