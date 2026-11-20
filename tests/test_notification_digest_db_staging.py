import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
from notification_digest_db_staging import count_unknown_request, claim_digest_once


class NotificationDigestDbStagingTests(unittest.TestCase):
    def setUp(self):
        self.conn = Mock()
        self.now = datetime(2026, 11, 20, 23, 59, tzinfo=timezone.utc)

    def test_atomic_increment_returns_count(self):
        self.conn.execute.return_value.fetchone.return_value = (100000,)
        self.assertEqual(count_unknown_request(self.conn, 25, self.now), 100000)
        sql, params = self.conn.execute.call_args.args
        self.assertIn('ON CONFLICT', sql)
        self.assertIn('unknown_request_count + 1', sql)
        self.assertEqual(params[0], 25)
        self.assertEqual(params[1], datetime(2026, 11, 20, tzinfo=timezone.utc))
        self.conn.commit.assert_not_called()

    def test_claim_once_is_atomic(self):
        self.conn.execute.return_value.fetchone.side_effect = [(50,), None]
        self.assertTrue(claim_digest_once(self.conn, 25, self.now))
        self.assertFalse(claim_digest_once(self.conn, 25, self.now))
        sql = self.conn.execute.call_args.args[0]
        self.assertIn('digest_claimed = FALSE', sql)
        self.assertIn('RETURNING', sql)

    def test_next_day_has_new_window(self):
        self.conn.execute.return_value.fetchone.return_value = (1,)
        count_unknown_request(self.conn, 25, self.now + timedelta(minutes=2))
        self.assertEqual(self.conn.execute.call_args.args[1][1], datetime(2026, 11, 21, tzinfo=timezone.utc))

    def test_bad_ids_and_naive_times_rejected(self):
        for bad in (0, -1, True, '25'):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    count_unknown_request(self.conn, bad, self.now)
        with self.assertRaises(ValueError):
            claim_digest_once(self.conn, 25, self.now.replace(tzinfo=None))


if __name__ == '__main__':
    unittest.main()
