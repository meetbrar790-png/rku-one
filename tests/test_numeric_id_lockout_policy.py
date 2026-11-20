import unittest
from datetime import datetime, timedelta, timezone
from numeric_id_lockout_policy import (
    LoginFailureState, record_failed_attempt, is_blocked, clear_after_success,
)


class NumericIdLockoutPolicyTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 20, 10, 0, tzinfo=timezone.utc)

    def test_blocks_at_fifth_failure_and_expires(self):
        state = LoginFailureState()
        for i in range(4):
            state = record_failed_attempt(state, self.now + timedelta(seconds=i))
            self.assertFalse(is_blocked(state, self.now + timedelta(seconds=i)))
        state = record_failed_attempt(state, self.now + timedelta(seconds=4))
        self.assertEqual(state.failures, 5)
        self.assertTrue(is_blocked(state, self.now + timedelta(seconds=5)))
        self.assertFalse(is_blocked(state, self.now + timedelta(minutes=15, seconds=4)))

    def test_blocked_attempts_do_not_extend_lockout(self):
        state = LoginFailureState()
        for _ in range(5):
            state = record_failed_attempt(state, self.now)
        self.assertEqual(record_failed_attempt(state, self.now + timedelta(minutes=1)), state)

    def test_window_reset_and_post_lockout_reset(self):
        state = record_failed_attempt(LoginFailureState(), self.now)
        state = record_failed_attempt(state, self.now + timedelta(minutes=15))
        self.assertEqual(state.failures, 1)
        for _ in range(4):
            state = record_failed_attempt(state, self.now + timedelta(minutes=15))
        state = record_failed_attempt(state, self.now + timedelta(minutes=30))
        self.assertEqual(state.failures, 1)

    def test_success_clears_state(self):
        self.assertEqual(clear_after_success(), LoginFailureState())

    def test_naive_datetime_rejected(self):
        with self.assertRaises(ValueError):
            record_failed_attempt(LoginFailureState(), datetime(2026, 1, 1))


if __name__ == '__main__':
    unittest.main()
