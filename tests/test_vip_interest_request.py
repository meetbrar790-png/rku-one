import unittest
from vip_interest_request import prepare_interest_request


class VipInterestDraftTests(unittest.TestCase):
    def test_draft_does_not_hold_or_charge(self):
        item = prepare_interest_request("1000", 1001, "sample-key-123")
        self.assertEqual(item["status"], "draft_not_submitted")
        self.assertFalse(item["number_held"])
        self.assertFalse(item["payment_collected"])
        self.assertFalse(item["inventory_verified"])

    def test_special_ids_require_review(self):
        for number in ("13", "786"):
            self.assertTrue(prepare_interest_request(number, 1001, "sample-key-123")["requires_owner_review"])

    def test_reserved_and_free_rejected(self):
        for number in ("1", "11", "1001", "1002"):
            with self.subTest(number=number), self.assertRaises(ValueError):
                prepare_interest_request(number, 1001, "sample-key-123")

    def test_requester_and_key_validated(self):
        for owner, key in ((0, "sample-key-123"), (True, "sample-key-123"), (1001, "bad"), (1001, "not valid key")):
            with self.subTest(owner=owner, key=key), self.assertRaises(ValueError):
                prepare_interest_request("2", owner, key)


if __name__ == "__main__":
    unittest.main()
