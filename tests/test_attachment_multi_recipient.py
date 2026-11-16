"""Offline multi-recipient attachment access contract tests."""
import unittest
from unittest.mock import patch
import mail_store
import attachment_store


class FakeConnection:
    def __init__(self, rows):
        self.rows = iter(rows)
        self.statements = []
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def execute(self, query, params=None):
        self.statements.append((query, params))
        return self
    def fetchone(self):
        return next(self.rows)
    def fetchall(self):
        return next(self.rows)


class MultiRecipientAttachmentTests(unittest.TestCase):
    def test_each_recipient_receives_separate_link(self):
        conn = FakeConnection([
            (0, 0), [(1002,), (1003,)], (1,), (51,), (52,)
        ])
        with patch.object(mail_store, "get_connection", return_value=conn):
            delivered = mail_store.deliver_many(1001, [1002, 1003], "Subject", "Body", 7)
        self.assertEqual(delivered, 2)
        links = [params for sql, params in conn.statements if "INSERT INTO message_attachments" in sql]
        self.assertEqual(links, [(51, 7), (52, 7)])
        checks = [params for sql, params in conn.statements if "SELECT 1 FROM private_attachments" in sql]
        self.assertEqual(checks, [(7, 1001)])

    def test_unowned_attachment_cannot_be_linked(self):
        conn = FakeConnection([(0, 0), [(1002,)], None])
        with patch.object(mail_store, "get_connection", return_value=conn):
            with self.assertRaisesRegex(ValueError, "not owned by sender"):
                mail_store.deliver_many(1001, [1002], "Subject", "Body", 7)
        self.assertFalse(any("INSERT INTO messages" in sql for sql, _ in conn.statements))

    def test_recipient_access_query_scoped_to_requesting_id(self):
        conn = FakeConnection([None])
        with patch.object(attachment_store, "get_connection", return_value=conn):
            self.assertIsNone(attachment_store.get_accessible_attachment(9999, 7))
        query, params = conn.statements[0]
        self.assertEqual(params, (7, 9999, 9999))
        self.assertIn("m.recipient=%s", query)
        self.assertIn("ma.attachment_id=a.id", query)


if __name__ == "__main__":
    unittest.main()
