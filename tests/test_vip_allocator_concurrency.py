"""Isolated PostgreSQL tests for vip_allocator_prototype; no production access."""
import os
import uuid
import unittest
from concurrent.futures import ThreadPoolExecutor

try:
    import psycopg
    from psycopg import sql
except ImportError:
    psycopg = None
    sql = None

from vip_allocator_prototype import allocate_free_id


@unittest.skipUnless(
    os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
    "Disposable VIP PostgreSQL database not configured",
)
class VipAllocatorConcurrencyTests(unittest.TestCase):
    def setUp(self):
        self.url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        with psycopg.connect(self.url) as conn:
            if not conn.info.dbname.endswith("_vip_test"):
                self.fail("Refusing database not ending _vip_test")
        suffix = uuid.uuid4().hex
        self.users = "rku_users_" + suffix
        self.reservations = "rku_reserved_" + suffix
        self.sequence = "rku_seq_" + suffix
        with psycopg.connect(self.url) as conn:
            conn.execute(sql.SQL("CREATE SEQUENCE {} START 1").format(sql.Identifier(self.sequence)))
            conn.execute(sql.SQL("CREATE TABLE {} (rku_id BIGINT PRIMARY KEY)").format(sql.Identifier(self.users)))
            conn.execute(sql.SQL("CREATE TABLE {} (rku_id BIGINT PRIMARY KEY)").format(sql.Identifier(self.reservations)))
            conn.execute(sql.SQL("INSERT INTO {} VALUES (1)").format(sql.Identifier(self.users)))
            conn.execute(sql.SQL("INSERT INTO {} VALUES (2)").format(sql.Identifier(self.reservations)))
            conn.execute("SELECT nextval(%s::regclass)", (self.sequence,))

    def tearDown(self):
        with psycopg.connect(self.url) as conn:
            conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(self.users)))
            conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(self.reservations)))
            conn.execute(sql.SQL("DROP SEQUENCE IF EXISTS {}").format(sql.Identifier(self.sequence)))

    def _allocate(self):
        with psycopg.connect(self.url) as conn:
            return allocate_free_id(conn, self.users, self.reservations, self.sequence)

    def test_skips_issued_and_reserved(self):
        self.assertEqual(self._allocate(), 3)
        self.assertEqual(self._allocate(), 4)

    def test_two_concurrent_registrations_get_distinct_ids(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            ids = list(pool.map(lambda _: self._allocate(), range(2)))
        self.assertEqual(sorted(ids), [3, 4])

    def test_rejects_non_test_table_names(self):
        with psycopg.connect(self.url) as conn:
            with self.assertRaises(ValueError):
                allocate_free_id(conn, "users", self.reservations, self.sequence)


if __name__ == "__main__":
    unittest.main()
