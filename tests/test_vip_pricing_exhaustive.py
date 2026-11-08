"""Exhaustive proposed VIP pricing coverage for all IDs 1 through 1001."""
import unittest

from vip_pricing_policy import CURRENCY, proposed_price_usd, sale_quote_usd
from vip_tier_policy import vip_tier


class ExhaustiveVipPriceTests(unittest.TestCase):
    def test_every_premium_number_has_positive_usd_price_except_reserved(self):
        self.assertEqual(CURRENCY, "USD")
        for number in range(1, 1002):
            with self.subTest(rku_id=number):
                price = proposed_price_usd(number)
                if number in {1, 11}:
                    self.assertIsNone(price)
                    self.assertIsNone(sale_quote_usd(number, set(), set()))
                elif number >= 1000:
                    self.assertEqual(price, 0)
                    self.assertIsNone(sale_quote_usd(number, set(), set()))
                else:
                    self.assertIsInstance(price, int)
                    self.assertGreater(price, 0)
                    self.assertEqual(sale_quote_usd(number, set(), set()), price)
                    self.assertIsNone(sale_quote_usd(number, {number}, set()))
                    self.assertIsNone(sale_quote_usd(number, set(), {number}))

    def test_special_and_boundary_numbers(self):
        expected = {
            1: ("founder", None), 2: ("vvip", 9999),
            10: ("vvip", 5999), 11: ("company_reserved", None),
            12: ("vip_gold", 499), 13: ("special_vvip", 4999),
            14: ("vip_gold", 499), 99: ("vip_gold", 499),
            100: ("vip_gold", 1499), 101: ("vip_silver", 199),
            785: ("vip_silver", 199), 786: ("special_vvip", 4999),
            787: ("vip_silver", 199), 999: ("vip_silver", 199),
            1000: ("normal", 0), 1001: ("normal", 0),
        }
        for number, (tier, price) in expected.items():
            with self.subTest(rku_id=number):
                self.assertEqual(vip_tier(number), tier)
                self.assertEqual(proposed_price_usd(number), price)

    def test_large_normal_numbers_remain_free(self):
        for number in (1002, 9999, 1000000, 9999999999):
            self.assertEqual(proposed_price_usd(number), 0)


if __name__ == "__main__":
    unittest.main()
