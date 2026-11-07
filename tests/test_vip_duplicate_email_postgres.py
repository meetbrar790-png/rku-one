"""Disposable PostgreSQL test: concurrent duplicate email cannot create two users.

Models a future full registration path; does not modify production registration.
"""
import os
import threading
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor

try:
    import psycopg
    from psycopg import sql
    from psycopg.errors import UniqueViolation
except ImportError:
    psycopg = None
    sql = None
    UniqueViolation = None

from vip_allocator_prototype import ALLOCATION_LOCK_KEY


@unittest.skipUnless(os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
                     "Disposable PostgreSQL VIP test DB not configured")
class DuplicateEmailRegistrationTests(unittest.TestCase):
    def test_concurrent_same_email_only_one_account(self):
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

            def register(_):
                barrier.wait(timeout=15)
                try:
                    with psycopg.connect(url) as conn:
                        conn.execute("SELECT pg_advisory_xact_lock(%s)", (ALLOCATION_LOCK_KEY,))
                        candidate = conn.execute("SELECT nextval(%s::regclass)", (sequence,)).fetchone()[0]
                        if candidate == 2:
                            candidate = conn.execute("SELECT nextval(%s::regclass)", (sequence,)).fetchone()[0]
                        conn.execute(sql.SQL(
                            "INSERT INTO {} (rku_id,email,password_hash) VALUES (%s,%s,%s)"
                        ).format(sql.Identifier(users)),
                            (candidate, "same@example.invalid", "test-hash"))
                        return "created"
                except UniqueViolation:
                    return "duplicate"

            with ThreadPoolExecutor(max_workers=2) as pool:
                outcomes = list(pool.map(register, (1, 2)))
            self.assertEqual(sorted(outcomes), ["created", "duplicate"])
            with psycopg.connect(url) as conn:
                rows = conn.execute(sql.SQL(
                    "SELECT rku_id,email FROM {} ORDER BY rku_id"
                ).format(sql.Identifier(users))).fetchall()
                self.assertEqual(rows, [(1, "owner@example.invalid"),
                                        (3, "same@example.invalid")])
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(reserved)))
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(users)))
                conn.execute(sql.SQL("DROP SEQUENCE IF EXISTS {}").format(sql.Identifier(sequence)))


if __name__ == "__main__":
    unittest.main()
