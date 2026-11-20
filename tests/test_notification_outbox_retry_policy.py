import unittest
from datetime import datetime, timedelta, timezone
from notification_outbox_retry_policy import OutboxAttempt, RetryDecision, retry_decision, next_backoff


class OutboxRetryPolicyTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 20, tzinfo=timezone.utc)

    def test_due_retry_and_wait(self):
        self.assertEqual(retry_decision(OutboxAttempt(1, self.now), self.now), RetryDecision.RETRY)
        self.assertEqual(retry_decision(OutboxAttempt(1, self.now + timedelta(seconds=1)), self.now), RetryDecision.WAIT)

    def test_exhaustion_and_completion(self):
        self.assertEqual(retry_decision(OutboxAttempt(5, self.now), self.now), RetryDecision.DEAD_LETTER)
        self.assertEqual(retry_decision(OutboxAttempt(5, self.now, True), self.now), RetryDecision.COMPLETE)

    def test_invalid_inputs_fail_closed(self):
        self.assertEqual(retry_decision(OutboxAttempt(-1, self.now), self.now), RetryDecision.DEAD_LETTER)
        self.assertEqual(retry_decision(OutboxAttempt(True, self.now), self.now), RetryDecision.DEAD_LETTER)
        self.assertEqual(retry_decision(OutboxAttempt(1, self.now), self.now.replace(tzinfo=None)), RetryDecision.DEAD_LETTER)
        self.assertEqual(retry_decision(OutboxAttempt(1, self.now), self.now, max_attempts=0), RetryDecision.DEAD_LETTER)

    def test_backoff_capped(self):
        self.assertEqual(next_backoff(1), timedelta(seconds=30))
        self.assertEqual(next_backoff(2), timedelta(seconds=60))
        self.assertEqual(next_backoff(10), timedelta(seconds=3600))
        with self.assertRaises(ValueError):
            next_backoff(0)


if __name__ == '__main__':
    unittest.main()
