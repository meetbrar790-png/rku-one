import unittest
from vip_readonly_status import preview_vip_status, issued_id_exists_readonly


class FakeConnection:
    def __init__(self, exists):
        self.exists = exists
        self.calls = []

    def execute(self, query, params):
        self.calls.append((query, params))
        return self

    def fetchone(self):
        return (self.exists,)


class VipReadOnlyStatusTests(unittest.TestCase):
    def test_company_ids_are_not_for_sale(self):
        for number in (1, 11):
            result = preview_vip_status(number, lambda _: False)
            self.assertEqual(result["availability"], "reserved_not_for_sale")
            self.assertIsNone(result["list_price_usd"])

    def test_issued_number_is_not_for_sale(self):
        result = preview_vip_status(13, lambda _: True)
        self.assertEqual(result["availability"], "issued_not_for_sale")
        self.assertEqual(result["list_price_usd"], 4999)
        self.assertFalse(result["sale_enabled"])

    def test_unissued_number_is_not_claimed_available(self):
        result = preview_vip_status(786, lambda _: False)
        self.assertEqual(result["availability"], "unverified")
        self.assertFalse(result["request_enabled"])
        self.assertFalse(result["number_held"])

    def test_reject_invalid_number(self):
        for number in (0, -1, 1001, True, "13"):
            with self.assertRaises(ValueError):
                preview_vip_status(number, lambda _: False)

    def test_issued_lookup_is_select_only_and_parameterized(self):
        conn = FakeConnection(True)
        self.assertTrue(issued_id_exists_readonly(conn, 13))
        self.assertEqual(conn.calls, [
            ("SELECT EXISTS(SELECT 1 FROM users WHERE rku_id=%s)", (13,))
        ])


if __name__ == "__main__":
    unittest.main()
