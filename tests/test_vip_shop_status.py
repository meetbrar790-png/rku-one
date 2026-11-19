import unittest
from vip_shop_status import status_snapshot


class VipStatusTests(unittest.TestCase):
    def test_issued_is_not_for_sale(self):
        result = status_snapshot("2", lambda number: True)
        self.assertEqual(result["availability"], "issued")
        self.assertFalse(result["sale_enabled"])

    def test_unissued_is_unknown_not_available(self):
        result = status_snapshot("1000", lambda number: False)
        self.assertEqual(result["availability"], "unknown")
        self.assertFalse(result["request_enabled"])

    def test_reserved_not_queried(self):
        def forbidden(_):
            raise AssertionError("Reserved ID must not need DB")
        for n in ("1", "11"):
            self.assertEqual(status_snapshot(n, forbidden)["availability"], "reserved")

    def test_free_is_not_paid(self):
        result = status_snapshot("1001", lambda number: False)
        self.assertEqual(result["availability"], "free_registration_policy")
        self.assertFalse(result["sale_enabled"])

    def test_invalid(self):
        with self.assertRaises(ValueError):
            status_snapshot("001", lambda number: False)


if __name__ == "__main__":
    unittest.main()
