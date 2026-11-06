"""Mail route checks using mocks only; no live accounts or database."""
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from api import MailData, send_message, inbox, sent


class MailRouteTests(unittest.TestCase):
    def test_send_success_uses_logged_in_sender(self):
        with patch("api.authenticated_id", return_value=1), patch("api.deliver_many", return_value=2) as deliver:
            result = send_message(MailData(to=[2, 3], subject="  Hello  ", body="  Message  "), authorization="Bearer mock")
        self.assertEqual(result, {"success": True, "delivered": 2})
        deliver.assert_called_once_with(1, [2, 3], "Hello", "Message")

    def test_invalid_recipients_return_400(self):
        with patch("api.authenticated_id", return_value=1), patch("api.deliver_many", side_effect=ValueError("Invalid RKU ID")):
            with self.assertRaises(HTTPException) as error:
                send_message(MailData(to=2, subject="Hello", body="Message"), authorization="Bearer mock")
        self.assertEqual(error.exception.status_code, 400)

    def test_oversized_message_rejected_before_delivery(self):
        with patch("api.authenticated_id", return_value=1), patch("api.deliver_many") as deliver:
            with self.assertRaises(HTTPException) as error:
                send_message(MailData(to=2, subject="Hello", body="x" * 10001), authorization="Bearer mock")
        self.assertEqual(error.exception.status_code, 400)
        deliver.assert_not_called()

    def test_inbox_uses_authenticated_owner_and_cursor(self):
        with patch("api.authenticated_id", return_value=1), patch("api.mailbox", return_value=[]) as mailbox:
            self.assertEqual(inbox(before=100, authorization="Bearer mock"), [])
        mailbox.assert_called_once_with(1, before=100)

    def test_sent_uses_authenticated_owner_and_cursor(self):
        with patch("api.authenticated_id", return_value=1), patch("api.mailbox", return_value=[]) as mailbox:
            self.assertEqual(sent(before=100, authorization="Bearer mock"), [])
        mailbox.assert_called_once_with(1, True, before=100)

    def test_sent_requires_login(self):
        with self.assertRaises(HTTPException) as error:
            sent(before=None, authorization=None)
        self.assertEqual(error.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
