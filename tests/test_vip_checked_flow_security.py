"""Security regression tests for isolated, nonbinding VIP inventory flow."""
import sqlite3
import unittest

from vip_interest_checked_test_store import record_checked_test_interest


class CheckedFlowSecurityTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")

    def tearDown(self):
        self.db.close()

    def submit(self, number, key="security-key-001", **inventory):
        return record_checked_test_interest(
            self.db, str(number), 1001, key, **inventory
        )

    def stored_rows(self):
        exists = self.db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='vip_interest_requests'"
        ).fetchone()
        if not exists:
            return []
        return self.db.execute(
            "SELECT requester_id,request_key,number_id,status FROM vip_interest_requests"
        ).fetchall()

    def test_incomplete_snapshots_fail_closed_without_storage(self):
        for inventory in ({}, {"issued_ids": set()}, {"held_ids": set()}):
            with self.subTest(inventory=inventory), self.assertRaisesRegex(ValueError, "unverified"):
                self.submit(1000, **inventory)
            self.assertEqual(self.stored_rows(), [])

    def test_assigned_held_and_protected_numbers_cannot_be_recorded(self):
        cases = [
            (2, {"issued_ids": {2}, "held_ids": set()}),
            (3, {"issued_ids": set(), "held_ids": {3}}),
            (1, {"issued_ids": set(), "held_ids": set()}),
            (11, {"issued_ids": set(), "held_ids": set()}),
            (13, {"issued_ids": set(), "held_ids": set()}),
            (786, {"issued_ids": set(), "held_ids": set()}),
        ]
        for number, inventory in cases:
            with self.subTest(number=number), self.assertRaises(ValueError):
                self.submit(number, **inventory)
            self.assertEqual(self.stored_rows(), [])

    def test_duplicate_request_is_idempotent_and_nonbinding(self):
        inventory = {"issued_ids": set(), "held_ids": set()}
        first = self.submit(1000, **inventory)
        second = self.submit(1000, **inventory)
        self.assertEqual(first, second)
        self.assertEqual(len(self.stored_rows()), 1)
        self.assertEqual(first["status"], "received_not_reserved")
        self.assertFalse(first["inventory_verified"])
        self.assertFalse(first["number_held"])
        self.assertFalse(first["payment_collected"])

    def test_idempotency_key_cannot_switch_number(self):
        inventory = {"issued_ids": set(), "held_ids": set()}
        self.submit(1000, **inventory)
        with self.assertRaisesRegex(ValueError, "Idempotency key reused"):
            self.submit(999, **inventory)
        self.assertEqual(len(self.stored_rows()), 1)

    def test_invalid_key_never_persists(self):
        with self.assertRaises(ValueError):
            self.submit(1000, key="bad key", issued_ids=set(), held_ids=set())
        self.assertEqual(self.stored_rows(), [])


if __name__ == "__main__":
    unittest.main()
