"""Disposable PostgreSQL concurrency test for proposed free-ID range 1001+.

This does not modify the production registration handler or any live DB.
"""
import os
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
                     "Disposable PostgreSQL VIP test DB not configured")
class ConcurrentFree1001Tests(unittest.TestCase):
    def test_parallel_free_registrations_are_unique_and_skip_holds(self):
        url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        suffix = uuid.uuid4().hex
        users = "rku_users_" + suffix
        reservations = "rku_reserved_" + suffix
        sequence = "rku_seq_" + suffix
        with psycopg.connect(url) as conn:
            if not conn.info.dbname.endswith("_vip_test"):
                self.fail("Refusing non-test database")
            conn.execute(sql.SQL("CREATE SEQUENCE {} START 1001").format(sql.Identifier(sequence)))
            conn.execute(sql.SQL(
                "CREATE TABLE {} (rku_id BIGINT PRIMARY KEY, email TEXT UNIQUE NOT NULL, "
                "password_hash TEXT NOT NULL)"
            ).format(sql.Identifier(users)))
            conn.execute(sql.SQL(
                "CREATE TABLE {} (rku_id BIGINT PRIMARY KEY)"
            ).format(sql.Identifier(reservations)))
        try:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("INSERT INTO {} VALUES (1,%s,%s)").format(
                    sql.Identifier(users)), ("founder@example.com", "hash"))
                for held_id in (11, 1002, 1005):
                    conn.execute(sql.SQL("INSERT INTO {} VALUES (%s)").format(
                        sql.Identifier(reservations)), (held_id,))

            def signup(index):
                with psycopg.connect(url) as conn:
                    return register_test_user(
                        conn, users, reservations, sequence,
                        f"User{index}@Example.com", "hashed-password"
                    )

            with ThreadPoolExecutor(max_workers=4) as executor:
                results = list(executor.map(signup, range(4)))

            assigned = sorted(row[0] for row in results)
            self.assertEqual(assigned, [1001, 1003, 1004, 1006])
            self.assertEqual(len(set(assigned)), 4)
            with psycopg.connect(url) as conn:
                persisted = conn.execute(sql.SQL(
                    "SELECT rku_id FROM {} WHERE rku_id>=1001 ORDER BY rku_id"
                ).format(sql.Identifier(users))).fetchall()
                self.assertEqual([r[0] for r in persisted], assigned)
                reserved = conn.execute(sql.SQL(
                    "SELECT rku_id FROM {} ORDER BY rku_id"
                ).format(sql.Identifier(reservations))).fetchall()
                self.assertEqual([r[0] for r in reserved], [11, 1002, 1005])
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(reservations)))
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(users)))
                conn.execute(sql.SQL("DROP SEQUENCE IF EXISTS {}").format(sql.Identifier(sequence)))


if __name__ == "__main__":
    unittest.main()
