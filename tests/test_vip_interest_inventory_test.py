import unittest
from vip_interest_inventory_test import evaluate_vip_interest


class VipInventoryTests(unittest.TestCase):
    def evaluate(self, number, **kwargs):
        return evaluate_vip_interest(str(number), 1001, "inventory-key-001", **kwargs)

    def test_missing_inventory_fails_closed(self):
        result = self.evaluate(1000)
        self.assertEqual(result["inventory_status"], "unverified")
        self.assertFalse(result["may_submit"])

    def test_issued_and_held_are_blocked(self):
        self.assertEqual(self.evaluate(2, issued_ids={2}, held_ids=set())["inventory_status"], "issued")
        self.assertFalse(self.evaluate(2, issued_ids={2}, held_ids=set())["may_submit"])
        self.assertEqual(self.evaluate(3, issued_ids=set(), held_ids={3})["inventory_status"], "held")
        self.assertFalse(self.evaluate(3, issued_ids=set(), held_ids={3})["may_submit"])

    def test_special_numbers_require_review(self):
        for number in (13, 786):
            result = self.evaluate(number, issued_ids=set(), held_ids=set())
            self.assertEqual(result["inventory_status"], "owner_review_required")
            self.assertFalse(result["may_submit"])

    def test_clean_test_snapshot_is_not_live_availability(self):
        result = self.evaluate(1000, issued_ids=set(), held_ids=set())
        self.assertTrue(result["may_submit"])
        self.assertFalse(result["inventory_verified"])
        self.assertFalse(result["number_held"])


if __name__ == "__main__":
    unittest.main()
