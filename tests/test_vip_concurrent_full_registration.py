"""Concurrent full-user registration in isolated PostgreSQL.

Tests shared transaction lock and VIP skip with realistic user records.
No production data or credentials are used.
"""
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

from vip_allocator_prototype import ALLOCATION_LOCK_KEY


@unittest.skipUnless(os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
                     "Disposable PostgreSQL VIP test DB not configured")
class ConcurrentFullRegistrationTests(unittest.TestCase):
    def test_two_users_get_distinct_ids_and_skip_vip(self):
        url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        suffix = uuid.uuid4().hex
        users, reserved, sequence = ("rku_users_" + suffix, "rku_reserved_" + suffix,
                                     "rku_seq_" + suffix)
        with psycopg.connect(url) as conn:
            if not conn.info.dbname.endswith("_vip_test"):
                self.fail("Refusing non-test database")
            conn.execute(sql.SQL("CREATE SEQUENCE {} START 2").format(sql.Identifier(sequence)))
            conn.execute(sql.SQL(
                "CREATE TABLE {} (rku_id BIGINT PRIMARY KEY, email TEXT UNIQUE NOT NULL, "
                "password_hash TEXT NOT NULL)"
            ).format(sql.Identifier(users)))
            conn.execute(sql.SQL("CREATE TABLE {} (rku_id BIGINT PRIMARY KEY)").format(
                sql.Identifier(reserved)))
        try:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("INSERT INTO {} VALUES (1,%s,%s)").format(
                    sql.Identifier(users)), ("owner@example.invalid", "owner-hash"))
                conn.execute(sql.SQL("INSERT INTO {} VALUES (2)").format(
                    sql.Identifier(reserved)))
            barrier = threading.Barrier(2)

            def register(index):
                barrier.wait(timeout=15)
                with psycopg.connect(url) as conn:
                    conn.execute("SELECT pg_advisory_xact_lock(%s)", (ALLOCATION_LOCK_KEY,))
                    for _ in range(10):
                        candidate = conn.execute("SELECT nextval(%s::regclass)", (sequence,)).fetchone()[0]
                        blocked = conn.execute(sql.SQL(
                            "SELECT EXISTS(SELECT 1 FROM {} WHERE rku_id=%s) "
                            "OR EXISTS(SELECT 1 FROM {} WHERE rku_id=%s)"
                        ).format(sql.Identifier(users), sql.Identifier(reserved)),
                            (candidate, candidate)).fetchone()[0]
                        if not blocked:
                            return conn.execute(sql.SQL(
                                "INSERT INTO {} (rku_id,email,password_hash) "
                                "VALUES (%s,%s,%s) RETURNING rku_id"
                            ).format(sql.Identifier(users)),
                                (candidate, f"user{index}@example.invalid", f"hash{index}")).fetchone()[0]
                    raise RuntimeError("No free ID found")

            with ThreadPoolExecutor(max_workers=2) as pool:
                ids = list(pool.map(register, (1, 2)))
            self.assertEqual(sorted(ids), [3, 4])
            with psycopg.connect(url) as conn:
                rows = conn.execute(sql.SQL(
                    "SELECT rku_id FROM {} ORDER BY rku_id"
                ).format(sql.Identifier(users))).fetchall()
                self.assertEqual(rows, [(1,), (3,), (4,)])
                self.assertEqual(conn.execute(sql.SQL(
                    "SELECT rku_id FROM {}"
                ).format(sql.Identifier(reserved))).fetchall(), [(2,)])
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(reserved)))
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(users)))
                conn.execute(sql.SQL("DROP SEQUENCE IF EXISTS {}").format(sql.Identifier(sequence)))


if __name__ == "__main__":
    unittest.main()
