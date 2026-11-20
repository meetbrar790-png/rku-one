import unittest
from datetime import datetime, timezone
from unittest.mock import Mock
from numeric_id_db_lockout_staging import record_failure, clear_failure_after_success, check_blocked


class NumericDbLockoutStagingTests(unittest.TestCase):
    def setUp(self):
        self.conn = Mock()
        self.conn.execute.return_value.fetchone.return_value = None
        self.now = datetime(2026, 11, 20, tzinfo=timezone.utc)

    def test_first_failure_uses_parameterized_statements(self):
        state = record_failure(self.conn, 1001, self.now)
        self.assertEqual(state.failures, 1)
        sql = [call.args[0] for call in self.conn.execute.call_args_list]
        self.assertTrue(any('pg_advisory_xact_lock' in s for s in sql))
        self.assertTrue(any('ON CONFLICT' in s for s in sql))
        self.assertFalse(self.conn.commit.called)

    def test_success_clears_only_one_id(self):
        clear_failure_after_success(self.conn, 1001)
        self.conn.execute.assert_any_call('DELETE FROM numeric_login_failures WHERE rku_id=%s', (1001,))

    def test_invalid_ids_rejected_before_db_access(self):
        for invalid in (0, -1, True, '1001', 9223372036854775808):
            with self.subTest(invalid=invalid):
                self.conn.reset_mock()
                with self.assertRaises(ValueError):
                    check_blocked(self.conn, invalid, self.now)
                self.conn.execute.assert_not_called()


if __name__ == '__main__':
    unittest.main()
