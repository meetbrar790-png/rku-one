import unittest

from vip_pricing_policy import CURRENCY, proposed_price_usd, sale_quote_usd


class VipPricingPolicyTests(unittest.TestCase):
    def test_currency_and_short_ids(self):
        self.assertEqual(CURRENCY, "USD")
        expected = {2: 9999, 3: 7999, 4: 5999, 5: 4999,
                    6: 3999, 7: 7777, 8: 6999, 9: 4999,
                    10: 5999}
        for number, price in expected.items():
            with self.subTest(number=number):
                self.assertEqual(proposed_price_usd(number), price)

    def test_special_and_boundaries(self):
        expected = {1: None, 11: None, 12: 499, 13: 4999,
                    14: 499, 99: 499, 100: 1499, 101: 199,
                    785: 199, 786: 4999, 787: 199, 999: 199,
                    1000: 999, 1001: 0, 1000000: 0}
        for number, price in expected.items():
            with self.subTest(number=number):
                self.assertEqual(proposed_price_usd(number), price)

    def test_not_sellable_if_issued_reserved_or_company(self):
        self.assertIsNone(sale_quote_usd(1, set(), set()))
        self.assertIsNone(sale_quote_usd(11, set(), set()))
        self.assertIsNone(sale_quote_usd(2, {2}, set()))
        self.assertIsNone(sale_quote_usd(13, set(), {13}))
        self.assertIsNone(sale_quote_usd(1001, set(), set()))
        self.assertEqual(sale_quote_usd(786, set(), set()), 4999)


if __name__ == "__main__":
    unittest.main()
