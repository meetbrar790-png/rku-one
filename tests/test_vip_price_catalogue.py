import unittest

from vip_price_catalogue import catalogue_entry, catalogue_summary


class VipPriceCatalogueTests(unittest.TestCase):
    def test_all_catalogue_items_are_nontransactional(self):
        for number in range(1, 1002):
            with self.subTest(rku_id=number):
                entry = catalogue_entry(number)
                self.assertEqual(entry["currency"], "USD")
                self.assertFalse(entry["sale_enabled"])
                self.assertEqual(entry["availability"], "not_verified")
                if number in (1, 11):
                    self.assertIsNone(entry["list_price_usd"])
                elif number >= 1001:
                    self.assertEqual(entry["list_price_usd"], 0)
                else:
                    self.assertGreater(entry["list_price_usd"], 0)

    def test_summary_reservations_and_free_start(self):
        summary = catalogue_summary()
        self.assertEqual(summary["founder_id"], 1)
        self.assertEqual(summary["company_reserved_id"], 11)
        self.assertEqual(summary["special_vvip_ids"], [13, 786])
        self.assertEqual(summary["free_id_start"], 1001)
        self.assertFalse(summary["sale_enabled"])
        self.assertEqual(summary["inventory_status"], "not_verified")


if __name__ == "__main__":
    unittest.main()
