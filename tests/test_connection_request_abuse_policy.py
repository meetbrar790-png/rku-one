import unittest
from datetime import datetime, timedelta, timezone
from connection_request_abuse_policy import may_request, within_window
from permission_first_policy import ContactStatus


class ConnectionRequestAbusePolicyTests(unittest.TestCase):
    def test_one_unknown_request_allowed_under_quota(self):
        self.assertTrue(may_request(ContactStatus.UNKNOWN, 0, 0))
        self.assertTrue(may_request(ContactStatus.UNKNOWN, 0, 9))

    def test_pending_rejected_blocked_cannot_repeat(self):
        for state in (ContactStatus.PENDING, ContactStatus.REJECTED, ContactStatus.BLOCKED):
            self.assertFalse(may_request(state, 0, 0))
        self.assertFalse(may_request(ContactStatus.UNKNOWN, 1, 0))

    def test_daily_sender_limit(self):
        self.assertFalse(may_request(ContactStatus.UNKNOWN, 0, 10))
        self.assertFalse(may_request(ContactStatus.UNKNOWN, 0, 100))

    def test_bad_values_fail_closed(self):
        for n in (-1, True, '0'):
            self.assertFalse(may_request(ContactStatus.UNKNOWN, n, 0))
            self.assertFalse(may_request(ContactStatus.UNKNOWN, 0, n))
        self.assertFalse(may_request('unknown', 0, 0))

    def test_window_boundaries(self):
        now = datetime(2026, 11, 20, tzinfo=timezone.utc)
        self.assertTrue(within_window(now - timedelta(hours=23), now))
        self.assertFalse(within_window(now - timedelta(hours=24), now))
        self.assertFalse(within_window(now + timedelta(seconds=1), now))
        self.assertFalse(within_window(now.replace(tzinfo=None), now))


if __name__ == '__main__':
    unittest.main()
