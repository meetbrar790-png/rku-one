"""Additional offline safety tests for VIP inventory proposals.

These do not connect to Render or reserve any real numbers.
"""
import unittest

from vip_policy import MAX_RKU_ID, proposed_vip_inventory


class VipInventoryEdgeCaseTests(unittest.TestCase):
    def test_existing_ids_always_excluded(self):
        self.assertEqual(proposed_vip_inventory([1, 2, 3, 4, 5], [1, 3, 5]), (2, 4))

    def test_all_candidates_issued(self):
        self.assertEqual(proposed_vip_inventory([1, 2], [1, 2]), ())

    def test_bigint_boundary_supported(self):
        self.assertEqual(proposed_vip_inventory([MAX_RKU_ID], []), (MAX_RKU_ID,))

    def test_invalid_candidate_rejected_even_if_issued(self):
        with self.assertRaises(ValueError):
            proposed_vip_inventory([0], [0])

    def test_invalid_candidate_type_rejected(self):
        with self.assertRaises(ValueError):
            proposed_vip_inventory([True, 2], [1])

    def test_empty_issued_snapshot_is_not_live_availability(self):
        # Result is a proposal only; it must never trigger a sale or reservation.
        self.assertEqual(proposed_vip_inventory([1, 2], []), (1, 2))


if __name__ == "__main__":
    unittest.main()
