"""Disposable PostgreSQL: realistic full user registration skips VIP-held ID.

No production tables or credentials are used. Test objects are dropped.
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

from vip_allocator_prototype import ALLOCATION_LOCK_KEY


@unittest.skipUnless(os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
                     "Disposable PostgreSQL VIP test DB not configured")
class FullRegistrationVipIntegrationTests(unittest.TestCase):
    def test_full_registration_skips_reserved_id_and_preserves_existing_id(self):
        url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        suffix = uuid.uuid4().hex
        users = "rku_users_" + suffix
        reservations = "rku_reserved_" + suffix
        sequence = "rku_seq_" + suffix
        with psycopg.connect(url) as conn:
            if not conn.info.dbname.endswith("_vip_test"):
                self.fail("Refusing non-test database")
            conn.execute(sql.SQL("CREATE SEQUENCE {} START 2").format(sql.Identifier(sequence)))
            conn.execute(sql.SQL(
                "CREATE TABLE {} (rku_id BIGINT PRIMARY KEY, email TEXT UNIQUE NOT NULL, "
                "password_hash TEXT NOT NULL)"
            ).format(sql.Identifier(users)))
            conn.execute(sql.SQL(
                "CREATE TABLE {} (rku_id BIGINT PRIMARY KEY)"
            ).format(sql.Identifier(reservations)))
        try:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("INSERT INTO {} VALUES (1, %s, %s)").format(
                    sql.Identifier(users)), ("owner@example.invalid", "existing-hash"))
                conn.execute(sql.SQL("INSERT INTO {} VALUES (2)").format(
                    sql.Identifier(reservations)))
            with psycopg.connect(url) as conn:
                conn.execute("SELECT pg_advisory_xact_lock(%s)", (ALLOCATION_LOCK_KEY,))
                candidate = None
                for _ in range(10):
                    proposed = conn.execute("SELECT nextval(%s::regclass)", (sequence,)).fetchone()[0]
                    blocked = conn.execute(sql.SQL(
                        "SELECT EXISTS(SELECT 1 FROM {} WHERE rku_id=%s) "
                        "OR EXISTS(SELECT 1 FROM {} WHERE rku_id=%s)"
                    ).format(sql.Identifier(users), sql.Identifier(reservations)),
                        (proposed, proposed)).fetchone()[0]
                    if not blocked:
                        candidate = proposed
                        break
                self.assertEqual(candidate, 3)
                result = conn.execute(sql.SQL(
                    "INSERT INTO {} (rku_id,email,password_hash) "
                    "VALUES (%s,%s,%s) RETURNING rku_id"
                ).format(sql.Identifier(users)),
                    (candidate, "new@example.invalid", "test-hash")).fetchone()
                self.assertEqual(result, (3,))
            with psycopg.connect(url) as conn:
                rows = conn.execute(sql.SQL(
                    "SELECT rku_id,email,password_hash FROM {} ORDER BY rku_id"
                ).format(sql.Identifier(users))).fetchall()
                self.assertEqual(rows, [
                    (1, "owner@example.invalid", "existing-hash"),
                    (3, "new@example.invalid", "test-hash"),
                ])
                held = conn.execute(sql.SQL("SELECT rku_id FROM {}").format(
                    sql.Identifier(reservations))).fetchall()
                self.assertEqual(held, [(2,)])
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(reservations)))
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(users)))
                conn.execute(sql.SQL("DROP SEQUENCE IF EXISTS {}").format(sql.Identifier(sequence)))


if __name__ == "__main__":
    unittest.main()
