"""Offline VIP reservation race model, not a production allocator.

The real implementation must use PostgreSQL constraints, transactional
locking, verified payments and a live ID inventory before enabling sales.
"""
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

from vip_policy import validate_numeric_id


class InMemoryReservationLedger:
    def __init__(self, issued_ids=()):
        self._issued = frozenset(validate_numeric_id(i) for i in issued_ids)
        self._reserved = {}
        self._lock = threading.Lock()

    def reserve(self, rku_id, owner):
        validate_numeric_id(rku_id)
        if not isinstance(owner, str) or not owner:
            raise ValueError("owner required")
        with self._lock:
            if rku_id in self._issued or rku_id in self._reserved:
                return False
            self._reserved[rku_id] = owner
            return True


class VipReservationRaceTests(unittest.TestCase):
    def test_two_buyers_only_one_wins(self):
        ledger = InMemoryReservationLedger(issued_ids=[1])
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda owner: ledger.reserve(2, owner), ["A", "B"]))
        self.assertEqual(sorted(results), [False, True])

    def test_issued_id_one_cannot_be_reserved(self):
        ledger = InMemoryReservationLedger(issued_ids=[1])
        self.assertFalse(ledger.reserve(1, "buyer"))

    def test_repeated_reservation_fails(self):
        ledger = InMemoryReservationLedger()
        self.assertTrue(ledger.reserve(5, "buyer"))
        self.assertFalse(ledger.reserve(5, "buyer"))

    def test_invalid_id_cannot_be_reserved(self):
        ledger = InMemoryReservationLedger()
        with self.assertRaises(ValueError):
            ledger.reserve(0, "buyer")


if __name__ == "__main__":
    unittest.main()
