import unittest
from vip_shop_preview import parse_numeric_id, number_preview, featured_previews


class VipShopPreviewTests(unittest.TestCase):
    def test_canonical_numbers(self):
        self.assertEqual(parse_numeric_id("786"), 786)
        for value in ("0", "01", "-2", "+2", " 2", "2 ", "1.5", "1" * 19, "", True, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_numeric_id(value)

    def test_reserved_founder_is_not_for_sale(self):
        for number in (1, 11):
            entry = number_preview(number)
            self.assertIsNone(entry["list_price_usd"])
            self.assertFalse(entry["sale_enabled"])

    def test_preview_never_claims_availability(self):
        for entry in featured_previews():
            self.assertEqual(entry["availability"], "not_verified")
            self.assertFalse(entry["sale_enabled"])
            self.assertFalse(entry["request_enabled"])

    def test_free_number_is_not_vip_sale(self):
        entry = number_preview("1001")
        self.assertEqual(entry["list_price_usd"], 0)
        self.assertEqual(entry["category"], "Free")
        self.assertFalse(entry["sale_enabled"])

    def test_1000_price(self):
        self.assertEqual(number_preview("1000")["list_price_usd"], 999)


if __name__ == "__main__":
    unittest.main()
