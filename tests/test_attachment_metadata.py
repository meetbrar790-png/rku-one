import unittest
from attachment_metadata import authorized_attachment_lookup, AUTHORIZED_ATTACHMENT_LOOKUP_SQL, ATTACHMENTS_SCHEMA_SQL

class FakeConnection:
    def __init__(self, row):
        self.row = row
        self.calls = []
    def execute(self, sql, params):
        self.calls.append((sql, params))
        return self
    def fetchone(self):
        return self.row

class AttachmentMetadataTests(unittest.TestCase):
    def test_requires_matching_requester_for_both_message_roles(self):
        self.assertIn("m.sender = %s OR m.recipient = %s", AUTHORIZED_ATTACHMENT_LOOKUP_SQL)
        self.assertIn("REFERENCES messages(id)", ATTACHMENTS_SCHEMA_SQL)
        conn = FakeConnection(("private/key", "x.pdf", "application/pdf", 100, 1002, 1, 42))
        result = authorized_attachment_lookup(conn, attachment_id=9, message_id=42, requester_id=1002)
        self.assertEqual(result[0], "private/key")
        self.assertEqual(conn.calls[0][1], (9, 42, 1002, 1002))

    def test_fail_closed_when_no_matching_row(self):
        with self.assertRaises(PermissionError):
            authorized_attachment_lookup(FakeConnection(None), attachment_id=9, message_id=42, requester_id=1003)

    def test_invalid_ids_rejected_without_db_query(self):
        conn = FakeConnection(None)
        for requester in (0, -1, True, "1"):
            with self.assertRaises(PermissionError):
                authorized_attachment_lookup(conn, attachment_id=9, message_id=42, requester_id=requester)
        self.assertEqual(conn.calls, [])

if __name__ == "__main__":
    unittest.main()
