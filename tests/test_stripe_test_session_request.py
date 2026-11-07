import unittest
from stripe_test_session_request import build_test_checkout_request

BASE = {
    "issued_ids": set(), "reserved_ids": set(),
    "test_secret_key": "sk_test_example",
    "success_url": "http://127.0.0.1:8000/test/success",
    "cancel_url": "http://127.0.0.1:8000/test/cancel",
    "test_order_reference": "test_order_123",
}

class StripeTestSessionRequestTests(unittest.TestCase):
    def test_safe_test_session_request(self):
        payload = build_test_checkout_request(786, **BASE)
        self.assertEqual(payload["mode"], "payment")
        self.assertEqual(payload["line_items"][0]["price_data"]["currency"], "usd")
        self.assertEqual(payload["line_items"][0]["price_data"]["unit_amount"], 499900)
        self.assertEqual(payload["metadata"]["environment"], "test")
        self.assertEqual(payload["metadata"]["rku_id"], "786")
        self.assertNotIn("test_secret_key", str(payload))
        self.assertNotIn("sk_test_", str(payload))

    def test_production_key_and_remote_urls_rejected(self):
        for changes in (
            {"test_secret_key": "sk_live_example"},
            {"success_url": "https://rkuone.com/success"},
            {"cancel_url": "https://example.com/cancel"},
            {"success_url": "http://localhost.evil.com:8000/success"},
            {"success_url": "http://127.0.0.1:8000/success?next=remote"},
            {"test_order_reference": "real_order_123"},
        ):
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    build_test_checkout_request(786, **{**BASE, **changes})

    def test_issued_reserved_and_free_rejected(self):
        for number, changes in (
            (786, {"issued_ids": {786}}),
            (786, {"reserved_ids": {786}}),
            (11, {}),
            (1001, {}),
        ):
            with self.subTest(number=number):
                with self.assertRaises(ValueError):
                    build_test_checkout_request(number, **{**BASE, **changes})

if __name__ == "__main__":
    unittest.main()
