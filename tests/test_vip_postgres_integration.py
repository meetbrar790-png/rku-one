"""Opt-in PostgreSQL tests, ONLY for a disposable database ending '_vip_test'.

No Render production URL or restored backup should ever be used here.
Set RKU_VIP_TEST_DATABASE_URL to a dedicated throwaway database URL.
The test creates a randomly named table and removes it in finally.
"""
import os
import uuid
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

try:
    import psycopg
    from psycopg import sql
except ImportError:
    psycopg = None
    sql = None


@unittest.skipUnless(
    os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
    "Dedicated disposable PostgreSQL test database not configured",
)
class VipPostgresIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        with psycopg.connect(self.url) as conn:
            dbname = conn.info.dbname
            if not dbname.endswith("_vip_test"):
                self.fail("Refusing to modify database not ending in _vip_test")
        self.table = "rku_vip_test_" + uuid.uuid4().hex
        with psycopg.connect(self.url) as conn:
            conn.execute(sql.SQL("CREATE TABLE {} (rku_id BIGINT PRIMARY KEY, owner TEXT NOT NULL)").format(sql.Identifier(self.table)))

    def tearDown(self):
        if hasattr(self, "table"):
            with psycopg.connect(self.url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(self.table)))

    def reserve(self, owner, number=2):
        with psycopg.connect(self.url) as conn:
            row = conn.execute(
                sql.SQL("INSERT INTO {} (rku_id, owner) VALUES (%s, %s) ON CONFLICT DO NOTHING RETURNING rku_id").format(sql.Identifier(self.table)),
                (number, owner),
            ).fetchone()
            return row is not None

    def test_duplicate_cannot_be_allocated(self):
        self.assertTrue(self.reserve("A"))
        self.assertFalse(self.reserve("B"))

    def test_concurrent_buyers_only_one_succeeds(self):
        gate = Barrier(2, timeout=10)

        def attempt(owner):
            gate.wait()
            return self.reserve(owner)

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(attempt, ("A", "B")))
        self.assertEqual(sorted(outcomes), [False, True])

    def test_rollback_does_not_hold_number(self):
        with psycopg.connect(self.url) as conn:
            conn.execute(
                sql.SQL("INSERT INTO {} (rku_id, owner) VALUES (3, 'A')").format(sql.Identifier(self.table))
            )
            conn.rollback()
        self.assertTrue(self.reserve("B", 3))


if __name__ == "__main__":
    unittest.main()
