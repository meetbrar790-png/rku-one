import unittest
from stripe_sandbox_checkout_plan import build_sandbox_checkout_spec, assert_stripe_test_key

class StripeSandboxCheckoutPlanTests(unittest.TestCase):
    def test_price_is_in_us_cents_and_sales_disabled(self):
        for number, cents in [(2,999900),(13,499900),(100,149900),(101,19900),(786,499900),(1000,99900)]:
            with self.subTest(number=number):
                spec=build_sandbox_checkout_spec(number,issued_ids=set(),reserved_ids=set())
                self.assertEqual(spec.unit_amount,cents)
                self.assertEqual(spec.currency,"usd")
                self.assertTrue(spec.test_mode_only)
                self.assertFalse(spec.fulfillment_enabled)
                self.assertTrue(spec.adaptive_pricing_requested)

    def test_reserved_issued_and_free_ids_rejected(self):
        for number in (1,11,1001,100000):
            with self.assertRaises(ValueError):
                build_sandbox_checkout_spec(number,issued_ids=set(),reserved_ids=set())
        with self.assertRaises(ValueError):
            build_sandbox_checkout_spec(786,issued_ids={786},reserved_ids=set())
        with self.assertRaises(ValueError):
            build_sandbox_checkout_spec(786,issued_ids=set(),reserved_ids={786})

    def test_live_stripe_key_is_rejected(self):
        for key in ("", "sk_live_example", "rk_test_example", "pk_test_example", "sk_test_"):
            with self.assertRaises(ValueError):
                assert_stripe_test_key(key)
        assert_stripe_test_key("sk_test_example")

if __name__ == "__main__":
    unittest.main()
