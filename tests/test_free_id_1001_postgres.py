"""Disposable PostgreSQL test: free registrations start at ID 1001.

Uses the existing guarded staging-only registration service, never live tables.
"""
import os
import unittest
import uuid

try:
    import psycopg
    from psycopg import sql
except ImportError:
    psycopg = None
    sql = None

from vip_full_registration_test_service import register_test_user


@unittest.skipUnless(os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
                     "Disposable PostgreSQL VIP test DB not configured")
class FreeId1001PostgresTests(unittest.TestCase):
    def test_free_registration_starts_1001_and_never_reuses_ids(self):
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
                conn.execute(sql.SQL("INSERT INTO {} VALUES (11)").format(
                    sql.Identifier(reservations)))
                conn.execute(sql.SQL("INSERT INTO {} VALUES (1002)").format(
                    sql.Identifier(reservations)))
            with psycopg.connect(url) as conn:
                first = register_test_user(
                    conn, users, reservations, sequence,
                    "First@Example.com", "hashed-password"
                )
                self.assertEqual(first, (1001, "first@example.com"))
            with psycopg.connect(url) as conn:
                second = register_test_user(
                    conn, users, reservations, sequence,
                    "Second@Example.com", "hashed-password"
                )
                self.assertEqual(second, (1003, "second@example.com"))
            with psycopg.connect(url) as conn:
                rows = conn.execute(sql.SQL(
                    "SELECT rku_id,email FROM {} ORDER BY rku_id"
                ).format(sql.Identifier(users))).fetchall()
                self.assertEqual(rows, [
                    (1, "founder@example.com"),
                    (1001, "first@example.com"),
                    (1003, "second@example.com"),
                ])
                holds = conn.execute(sql.SQL(
                    "SELECT rku_id FROM {} ORDER BY rku_id"
                ).format(sql.Identifier(reservations))).fetchall()
                self.assertEqual(holds, [(11,), (1002,)])
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(reservations)))
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(users)))
                conn.execute(sql.SQL("DROP SEQUENCE IF EXISTS {}").format(sql.Identifier(sequence)))


if __name__ == "__main__":
    unittest.main()
