"""Offline tests for VIP payment confirmation policy."""
import unittest
from vip_payment_policy import may_allocate_paid_vip


class VipPaymentPolicyTests(unittest.TestCase):
    def check(self, **changes):
        values = dict(reservation_state="reserved", payment_verified=True,
                      payment_reference_matches=True, reservation_owner_matches=True,
                      issued=False, expired=False)
        values.update(changes)
        return may_allocate_paid_vip(**values)

    def test_verified_payment_and_matching_reservation(self):
        self.assertTrue(self.check())

    def test_unverified_payment_rejected(self):
        self.assertFalse(self.check(payment_verified=False))

    def test_wrong_payment_reference_rejected(self):
        self.assertFalse(self.check(payment_reference_matches=False))

    def test_wrong_owner_rejected(self):
        self.assertFalse(self.check(reservation_owner_matches=False))

    def test_issued_id_rejected(self):
        self.assertFalse(self.check(issued=True))

    def test_expired_hold_rejected(self):
        self.assertFalse(self.check(expired=True))

    def test_cancelled_hold_rejected(self):
        self.assertFalse(self.check(reservation_state="cancelled"))

    def test_allocated_hold_not_reallocated(self):
        self.assertFalse(self.check(reservation_state="allocated"))

    def test_unknown_state_rejected(self):
        with self.assertRaises(ValueError):
            self.check(reservation_state="unknown")

    def test_non_boolean_verification_rejected(self):
        with self.assertRaises(ValueError):
            self.check(payment_verified="yes")


if __name__ == "__main__":
    unittest.main()
