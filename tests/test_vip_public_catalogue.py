import unittest
from vip_public_catalogue import FEATURED_VIP_IDS, visible_featured_ids


class FakeConn:
    def __init__(self, issued):
        self.issued = issued
        self.calls = []
    def execute(self, sql, params):
        self.calls.append((sql, params))
        return self
    def fetchall(self):
        return [(n,) for n in self.issued]


class VipPublicCatalogueTests(unittest.TestCase):
    def test_issued_cards_are_removed(self):
        conn = FakeConn([2, 7, 786])
        visible = visible_featured_ids(conn)
        for number in (2, 7, 786):
            self.assertNotIn(number, visible)
        self.assertIn(3, visible)
        self.assertIn(1000, visible)
        self.assertEqual(conn.calls[0][1], (list(FEATURED_VIP_IDS),))

    def test_all_issued_yields_empty_list(self):
        self.assertEqual(visible_featured_ids(FakeConn(FEATURED_VIP_IDS)), [])

    def test_company_reserved_not_featured(self):
        self.assertNotIn(1, FEATURED_VIP_IDS)
        self.assertNotIn(11, FEATURED_VIP_IDS)

    def test_query_does_not_mutate_data(self):
        conn = FakeConn([])
        visible_featured_ids(conn)
        self.assertTrue(conn.calls[0][0].startswith("SELECT "))
        self.assertNotIn("email", conn.calls[0][0])


if __name__ == "__main__":
    unittest.main()
