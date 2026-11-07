"""Disposable PostgreSQL: simultaneous duplicate-email free registrations.

No production DB or registration handler is changed.
"""
import os
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
    UniqueViolation = Exception

from vip_full_registration_test_service import register_test_user


@unittest.skipUnless(os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
                     "Disposable PostgreSQL VIP test DB not configured")
class FreeIdDuplicateEmailRaceTests(unittest.TestCase):
    def test_duplicate_email_race_creates_one_account(self):
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
                conn.execute(sql.SQL("INSERT INTO {} VALUES (11)").format(sql.Identifier(reservations)))

            def signup(email):
                try:
                    with psycopg.connect(url) as conn:
                        row = register_test_user(
                            conn, users, reservations, sequence, email, "hashed-password"
                        )
                    return ("created", row)
                except UniqueViolation:
                    return ("duplicate", None)

            with ThreadPoolExecutor(max_workers=2) as executor:
                outcomes = list(executor.map(signup, ("Same@Example.com", " same@example.com ")))

            self.assertEqual(sorted(item[0] for item in outcomes), ["created", "duplicate"])
            self.assertEqual([item[1][0] for item in outcomes if item[0] == "created"], [1001])
            with psycopg.connect(url) as conn:
                accounts = conn.execute(sql.SQL(
                    "SELECT rku_id,email FROM {}"
                ).format(sql.Identifier(users))).fetchall()
                self.assertEqual(accounts, [(1001, "same@example.com")])
                held = conn.execute(sql.SQL(
                    "SELECT rku_id FROM {}"
                ).format(sql.Identifier(reservations))).fetchall()
                self.assertEqual(held, [(11,)])
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(reservations)))
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(users)))
                conn.execute(sql.SQL("DROP SEQUENCE IF EXISTS {}").format(sql.Identifier(sequence)))


if __name__ == "__main__":
    unittest.main()
