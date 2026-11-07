"""Disposable full-registration service: concurrency and rollback tests."""
import os
import threading
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor

try:
    import psycopg
    from psycopg import sql
except ImportError:
    psycopg = None
    sql = None

from vip_full_registration_test_service import register_test_user


@unittest.skipUnless(os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
                     "Disposable VIP PostgreSQL DB not configured")
class FullRegistrationServiceTransactions(unittest.TestCase):
    def setUp(self):
        self.url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        suffix = uuid.uuid4().hex
        self.users = "rku_users_" + suffix
        self.reserved = "rku_reserved_" + suffix
        self.seq = "rku_seq_" + suffix
        with psycopg.connect(self.url) as conn:
            if not conn.info.dbname.endswith("_vip_test"):
                self.fail("Refusing non-test DB")
            conn.execute(sql.SQL("CREATE SEQUENCE {} START 2").format(sql.Identifier(self.seq)))
            conn.execute(sql.SQL(
                "CREATE TABLE {} (rku_id BIGINT PRIMARY KEY, email TEXT UNIQUE NOT NULL, "
                "password_hash TEXT NOT NULL)"
            ).format(sql.Identifier(self.users)))
            conn.execute(sql.SQL("CREATE TABLE {} (rku_id BIGINT PRIMARY KEY)").format(
                sql.Identifier(self.reserved)))
            conn.execute(sql.SQL("INSERT INTO {} VALUES (1,%s,%s)").format(
                sql.Identifier(self.users)), ("owner@example.invalid", "existing-hash"))
            conn.execute(sql.SQL("INSERT INTO {} VALUES (2)").format(
                sql.Identifier(self.reserved)))

    def tearDown(self):
        with psycopg.connect(self.url) as conn:
            conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(self.reserved)))
            conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(self.users)))
            conn.execute(sql.SQL("DROP SEQUENCE IF EXISTS {}").format(sql.Identifier(self.seq)))

    def test_two_concurrent_registrations_receive_unique_ids(self):
        barrier = threading.Barrier(2)
        def create(index):
            barrier.wait(timeout=15)
            with psycopg.connect(self.url) as conn:
                return register_test_user(conn, self.users, self.reserved, self.seq,
                                          f"user{index}@example.invalid", f"hash-{index}")
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(create, (1, 2)))
        self.assertEqual(sorted(result[0] for result in results), [3, 4])
        with psycopg.connect(self.url) as conn:
            ids = conn.execute(sql.SQL("SELECT rku_id FROM {} ORDER BY rku_id").format(
                sql.Identifier(self.users))).fetchall()
            self.assertEqual(ids, [(1,), (3,), (4,)])

    def test_failed_transaction_rolls_back_user_without_reusing_id(self):
        with self.assertRaises(RuntimeError):
            with psycopg.connect(self.url) as conn:
                first = register_test_user(conn, self.users, self.reserved, self.seq,
                                           "failed@example.invalid", "hash")
                self.assertEqual(first[0], 3)
                raise RuntimeError("Simulated failure before commit")
        with psycopg.connect(self.url) as conn:
            count = conn.execute(sql.SQL(
                "SELECT COUNT(*) FROM {} WHERE email=%s"
            ).format(sql.Identifier(self.users)), ("failed@example.invalid",)).fetchone()[0]
            self.assertEqual(count, 0)
            result = register_test_user(conn, self.users, self.reserved, self.seq,
                                        "success@example.invalid", "hash")
            self.assertEqual(result[0], 4)
        with psycopg.connect(self.url) as conn:
            ids = conn.execute(sql.SQL("SELECT rku_id FROM {} ORDER BY rku_id").format(
                sql.Identifier(self.users))).fetchall()
            self.assertEqual(ids, [(1,), (4,)])


if __name__ == "__main__":
    unittest.main()
