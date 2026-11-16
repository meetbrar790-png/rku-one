"""No-database unit tests for mail attachment access boundaries."""
import unittest
from unittest.mock import patch
import attachment_store


class FakeConnection:
    def __init__(self, row):
        self.row = row
        self.query = ""
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query, params):
        self.query = query
        self.params = params
        return self

    def fetchone(self):
        return self.row


class AttachmentAccessTests(unittest.TestCase):
    def test_download_checks_owner_or_message_recipient(self):
        conn = FakeConnection(None)
        with patch.object(attachment_store, "get_connection", return_value=conn):
            result = attachment_store.get_accessible_attachment(1002, 19)
        self.assertIsNone(result)
        self.assertEqual(conn.params, (19, 1002, 1002))
        self.assertIn("a.owner=%s", conn.query)
        self.assertIn("m.recipient=%s", conn.query)
        self.assertIn("ma.attachment_id=a.id", conn.query)

    def test_no_match_returns_no_attachment(self):
        with patch.object(attachment_store, "get_connection", return_value=FakeConnection(None)):
            self.assertIsNone(attachment_store.get_accessible_attachment(9999, 19))

    def test_sender_owned_attachment_required_before_mail_link(self):
        conn = FakeConnection(None)
        with patch.object(attachment_store, "get_connection", return_value=conn):
            self.assertIsNone(attachment_store.attachment_for_mail(1002, 55))
        self.assertEqual(conn.params, (55, 1002))
        self.assertIn("owner=%s", conn.query)


if __name__ == "__main__":
    unittest.main()
