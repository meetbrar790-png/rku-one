import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from notification_outbox_staging import enqueue_digest_once, claim_and_enqueue_digest


class NotificationOutboxStagingTests(unittest.TestCase):
    def setUp(self):
        self.conn = Mock()
        self.now = datetime(2026, 11, 20, tzinfo=timezone.utc)

    def test_enqueue_is_idempotent(self):
        self.conn.execute.return_value.fetchone.side_effect = [(25,), None]
        self.assertTrue(enqueue_digest_once(self.conn, 25, self.now))
        self.assertFalse(enqueue_digest_once(self.conn, 25, self.now))
        sql = self.conn.execute.call_args.args[0]
        self.assertIn('ON CONFLICT', sql)
        self.assertIn('DO NOTHING', sql)

    def test_no_claim_no_enqueue(self):
        with patch('notification_digest_db_staging.claim_digest_once', return_value=False):
            self.assertFalse(claim_and_enqueue_digest(self.conn, 25, self.now))
        self.conn.execute.assert_not_called()

    def test_claim_then_enqueue(self):
        self.conn.execute.return_value.fetchone.return_value = (25,)
        with patch('notification_digest_db_staging.claim_digest_once', return_value=True):
            self.assertTrue(claim_and_enqueue_digest(self.conn, 25, self.now))
        self.conn.commit.assert_not_called()

    def test_claim_conflict_requires_rollback(self):
        self.conn.execute.return_value.fetchone.return_value = None
        with patch('notification_digest_db_staging.claim_digest_once', return_value=True):
            with self.assertRaises(RuntimeError):
                claim_and_enqueue_digest(self.conn, 25, self.now)


if __name__ == '__main__':
    unittest.main()
