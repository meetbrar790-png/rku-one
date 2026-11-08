import unittest

from vip_tier_policy import (vip_tier, is_paid_premium_id,
                             is_available_for_sale, VIP_PRICE_CURRENCY, FREE_ID_START)


class VipTierPolicyTests(unittest.TestCase):
    def test_usd_and_free_boundary(self):
        self.assertEqual(VIP_PRICE_CURRENCY, 'USD')
        self.assertEqual(FREE_ID_START, 1001)
        self.assertEqual(vip_tier(FREE_ID_START), 'normal')

    def test_tier_boundaries(self):
        cases = {1: "founder", 2: "vvip", 10: "vvip",
                 11: "company_reserved", 12: "vip_gold",
                 13: "special_vvip", 14: "vip_gold", 100: "vip_gold",
                 101: "vip_silver", 785: "vip_silver",
                 786: "special_vvip", 787: "vip_silver", 999: "vip_silver", 1000: "vip_silver",
                 1001: "normal", 999999999: "normal"}
        for number, expected in cases.items():
            with self.subTest(number=number):
                self.assertEqual(vip_tier(number), expected)

    def test_premium_only_2_to_1000(self):
        for number in (2, 10, 13, 100, 101, 786, 999, 1000):
            self.assertTrue(is_paid_premium_id(number))
        for number in (1, 1001, 100000):
            self.assertFalse(is_paid_premium_id(number))

    def test_issued_reserved_founder_and_normal_not_sellable(self):
        self.assertFalse(is_available_for_sale(1, set(), set()))
        self.assertFalse(is_available_for_sale(11, set(), set()))
        self.assertFalse(is_paid_premium_id(11))
        self.assertFalse(is_available_for_sale(2, {2}, set()))
        self.assertFalse(is_available_for_sale(3, set(), {3}))
        self.assertTrue(is_available_for_sale(4, {1, 2}, {3}))
        self.assertFalse(is_available_for_sale(1001, set(), set()))

    def test_invalid_ids(self):
        for value in (0, -1, True, 1.2, "2"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    vip_tier(value)


if __name__ == "__main__":
    unittest.main()
