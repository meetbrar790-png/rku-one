"""Route tests use FastAPI route callables directly; no production DB required."""
import unittest
from fastapi import HTTPException
from api import vip_featured_preview, vip_number_preview


class VipPreviewRouteTests(unittest.TestCase):
    def test_featured_read_only(self):
        result = vip_featured_preview()
        self.assertFalse(result["sale_enabled"])
        self.assertFalse(result["inventory_connected"])
        self.assertTrue(result["items"])
        self.assertTrue(all(item["availability"] == "not_verified" for item in result["items"]))

    def test_number_preview(self):
        item = vip_number_preview("1000")
        self.assertEqual(item["list_price_usd"], 999)
        self.assertFalse(item["request_enabled"])

    def test_invalid_number(self):
        for value in ("0", "01", "-1", "abc"):
            with self.subTest(value=value), self.assertRaises(HTTPException) as ctx:
                vip_number_preview(value)
            self.assertEqual(ctx.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
