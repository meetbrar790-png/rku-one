import sqlite3
import unittest
from vip_interest_checked_test_store import record_checked_test_interest


class CheckedVipInterestTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")

    def tearDown(self):
        self.db.close()

    def record(self, number, **snapshots):
        return record_checked_test_interest(
            self.db, str(number), 1001, "checked-test-key-001", **snapshots
        )

    def count(self):
        return self.db.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='vip_interest_requests'"
        ).fetchone()[0]

    def test_missing_snapshot_fails_closed_without_write(self):
        with self.assertRaisesRegex(ValueError, "unverified"):
            self.record(1000)
        self.assertEqual(self.count(), 0)

    def test_issued_and_held_block_without_write(self):
        for number, issued, held in ((2, {2}, set()), (3, set(), {3})):
            with self.subTest(number=number), self.assertRaises(ValueError):
                self.record(number, issued_ids=issued, held_ids=held)
        self.assertEqual(self.count(), 0)

    def test_special_ids_need_owner_review(self):
        for number in (13, 786):
            with self.subTest(number=number), self.assertRaisesRegex(ValueError, "owner_review"):
                self.record(number, issued_ids=set(), held_ids=set())
        self.assertEqual(self.count(), 0)

    def test_clean_disposable_snapshot_allows_nonbinding_interest(self):
        result = self.record(1000, issued_ids=set(), held_ids=set())
        self.assertEqual(result["status"], "received_not_reserved")
        self.assertFalse(result["inventory_verified"])
        self.assertFalse(result["number_held"])
        self.assertFalse(result["payment_collected"])


if __name__ == "__main__":
    unittest.main()
