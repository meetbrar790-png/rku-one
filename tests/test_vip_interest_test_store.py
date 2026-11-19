import sqlite3
import tempfile
import unittest
from vip_interest_test_store import record_test_interest, initialize_disposable_store


class VipInterestStoreTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")

    def tearDown(self):
        self.db.close()

    def test_idempotent_request_not_reservation(self):
        first = record_test_interest(self.db, "1000", 1001, "request-abc123")
        second = record_test_interest(self.db, "1000", 1001, "request-abc123")
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "received_not_reserved")
        self.assertFalse(first["number_held"])
        self.assertFalse(first["payment_collected"])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM vip_interest_requests").fetchone()[0], 1)

    def test_reuse_key_different_number_rejected(self):
        record_test_interest(self.db, "2", 1001, "request-abc123")
        with self.assertRaises(ValueError):
            record_test_interest(self.db, "3", 1001, "request-abc123")

    def test_reserved_and_free_rejected(self):
        for number in ("1", "11", "1001"):
            with self.subTest(number=number), self.assertRaises(ValueError):
                record_test_interest(self.db, number, 1001, "request-abc123")

    def test_disk_db_refused(self):
        with tempfile.NamedTemporaryFile() as f:
            disk = sqlite3.connect(f.name)
            try:
                with self.assertRaises(ValueError):
                    initialize_disposable_store(disk)
            finally:
                disk.close()


if __name__ == "__main__":
    unittest.main()
