import unittest
from vip_search_preview import vip_search_preview


class VipSearchPreviewTests(unittest.TestCase):
    def test_reserved_never_available(self):
        for number in (1, 11):
            result = vip_search_preview(number, lambda _: False)
            self.assertEqual(result["status"], "reserved_not_for_sale")
            self.assertIsNone(result["list_price_usd"])

    def test_issued_never_available(self):
        result = vip_search_preview(13, lambda _: True)
        self.assertEqual(result["status"], "issued_not_for_sale")
        self.assertEqual(result["list_price_usd"], 4999)

    def test_unissued_is_unverified_not_available(self):
        result = vip_search_preview(786, lambda _: False)
        self.assertEqual(result["status"], "unverified")
        self.assertFalse(result["availability_verified"])
        self.assertFalse(result["payment_enabled"])
        self.assertFalse(result["reservation_enabled"])
        self.assertFalse(result["allocation_enabled"])

    def test_price_policy_preserved(self):
        self.assertEqual(vip_search_preview(2, lambda _: False)["list_price_usd"], 9999)
        self.assertEqual(vip_search_preview(1000, lambda _: False)["list_price_usd"], 999)

    def test_invalid_inputs_rejected(self):
        for value in (0, -1, 1001, True, "786", 3.5):
            with self.assertRaises(ValueError):
                vip_search_preview(value, lambda _: False)


if __name__ == "__main__":
    unittest.main()
