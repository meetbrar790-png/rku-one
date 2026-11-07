"""Offline policy tests: no connection to live Render or local databases."""
import unittest
from vip_policy import MAX_RKU_ID, proposed_vip_inventory, validate_numeric_id


class VipPolicyTests(unittest.TestCase):
    def test_preserves_existing_id_one(self):
        self.assertEqual(proposed_vip_inventory([1, 2, 3], [1]), (2, 3))

    def test_deduplicates_and_sorts(self):
        self.assertEqual(proposed_vip_inventory([10, 2, 10, 3], [3]), (2, 10))

    def test_does_not_change_input(self):
        candidates = [1, 2]
        issued = [1]
        proposed_vip_inventory(candidates, issued)
        self.assertEqual(candidates, [1, 2])
        self.assertEqual(issued, [1])

    def test_rejects_zero_negative_bool_and_overflow(self):
        for invalid in [0, -1, True, False, MAX_RKU_ID + 1, "2", 2.0]:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    validate_numeric_id(invalid)

    def test_rejects_invalid_issued_id(self):
        with self.assertRaises(ValueError):
            proposed_vip_inventory([2], [0])

    def test_empty_inventory(self):
        self.assertEqual(proposed_vip_inventory([], [1]), ())


if __name__ == "__main__":
    unittest.main()
