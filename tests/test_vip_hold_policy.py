"""Offline VIP hold expiry and cancellation policy tests."""
import unittest
from datetime import datetime, timedelta, timezone
from vip_hold_policy import may_release_hold

class VipHoldPolicyTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 8, tzinfo=timezone.utc)

    def check(self, **overrides):
        args = dict(state="reserved", paid=False, issued=False,
                    expires_at=self.now - timedelta(seconds=1), now=self.now)
        args.update(overrides)
        return may_release_hold(**args)

    def test_expired_unpaid_hold_eligible(self):
        self.assertTrue(self.check())

    def test_active_hold_not_eligible(self):
        self.assertFalse(self.check(expires_at=self.now + timedelta(hours=1)))

    def test_paid_hold_protected(self):
        self.assertFalse(self.check(paid=True))

    def test_issued_id_protected(self):
        self.assertFalse(self.check(issued=True))

    def test_allocated_id_protected(self):
        self.assertFalse(self.check(state="allocated"))

    def test_cancelled_unpaid_hold_eligible(self):
        self.assertTrue(self.check(state="cancelled", expires_at=None))

    def test_missing_expiry_not_eligible(self):
        self.assertFalse(self.check(expires_at=None))

    def test_invalid_state_rejected(self):
        with self.assertRaises(ValueError):
            self.check(state="unknown")

    def test_naive_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            self.check(now=datetime(2026, 11, 8))

if __name__ == "__main__":
    unittest.main()
