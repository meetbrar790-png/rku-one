"""Regression tests for the isolated numeric ID PostgreSQL lockout helpers.

Uses mocks only; no live database or production credentials are accessed.
"""
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

from numeric_id_db_lockout_staging import record_failure, check_blocked


class NumericDbLockoutRegressionTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)
        self.conn = Mock()

    def test_fifth_failure_is_saved_as_blocked(self):
        self.conn.execute.return_value.fetchone.return_value = (
            4, self.now - timedelta(minutes=1), None,
        )
        result = record_failure(self.conn, 1001, self.now)
        self.assertEqual(result.failures, 5)
        self.assertEqual(result.blocked_until, self.now + timedelta(minutes=15))
        sql, params = self.conn.execute.call_args.args
        self.assertIn('ON CONFLICT', sql)
        self.assertEqual(params[0], 1001)
        self.assertEqual(params[3], self.now + timedelta(minutes=15))
        self.conn.commit.assert_not_called()

    def test_blocked_login_does_not_extend_lockout(self):
        expires = self.now + timedelta(minutes=9)
        self.conn.execute.return_value.fetchone.return_value = (
            5, self.now - timedelta(minutes=6), expires,
        )
        result = record_failure(self.conn, 1001, self.now)
        self.assertEqual(result.blocked_until, expires)

    def test_blocked_check_is_read_only(self):
        self.conn.execute.return_value.fetchone.return_value = (
            5, self.now - timedelta(minutes=2), self.now + timedelta(minutes=13),
        )
        self.assertTrue(check_blocked(self.conn, 1001, self.now))
        statements = [call.args[0] for call in self.conn.execute.call_args_list]
        self.assertEqual(len(statements), 2)
        self.assertTrue(all('INSERT' not in sql and 'DELETE' not in sql for sql in statements))


if __name__ == '__main__':
    unittest.main()
