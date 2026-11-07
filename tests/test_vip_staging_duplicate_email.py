"""Disposable staging rehearsal: duplicate email cannot create another account.

This exercises the test-only full registration service, not the live API.
"""
import os
import unittest
import uuid

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
                     "Disposable PostgreSQL test DB not configured")
class StagingRegistrationDuplicateEmailTests(unittest.TestCase):
    def test_duplicate_email_rolls_back_and_does_not_consume_reserved_id(self):
        url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        suffix = uuid.uuid4().hex
        users = "rku_users_" + suffix
        reserved = "rku_reserved_" + suffix
        seq = "rku_seq_" + suffix
        with psycopg.connect(url) as conn:
            if not conn.info.dbname.endswith("_vip_test"):
                self.fail("Refusing non-test DB")
            conn.execute(sql.SQL("CREATE SEQUENCE {} START 2").format(sql.Identifier(seq)))
            conn.execute(sql.SQL(
                "CREATE TABLE {} (rku_id BIGINT PRIMARY KEY, email TEXT UNIQUE NOT NULL, "
                "password_hash TEXT NOT NULL)"
            ).format(sql.Identifier(users)))
            conn.execute(sql.SQL("CREATE TABLE {} (rku_id BIGINT PRIMARY KEY)").format(
                sql.Identifier(reserved)))
            conn.execute(sql.SQL("INSERT INTO {} VALUES (2)").format(sql.Identifier(reserved)))
        try:
            with psycopg.connect(url) as conn:
                first = register_test_user(conn, users, reserved, seq,
                                           "first@example.com", "hash-one")
                self.assertEqual(first, (3, "first@example.com"))
            with self.assertRaises(UniqueViolation):
                with psycopg.connect(url) as conn:
                    register_test_user(conn, users, reserved, seq,
                                       " FIRST@EXAMPLE.COM ", "hash-two")
            with psycopg.connect(url) as conn:
                result = register_test_user(conn, users, reserved, seq,
                                            "second@example.com", "hash-three")
                self.assertEqual(result, (5, "second@example.com"))
                rows = conn.execute(sql.SQL(
                    "SELECT rku_id,email,password_hash FROM {} ORDER BY rku_id"
                ).format(sql.Identifier(users))).fetchall()
                self.assertEqual(rows, [(3, "first@example.com", "hash-one"),
                                        (5, "second@example.com", "hash-three")])
                self.assertEqual(conn.execute(sql.SQL(
                    "SELECT rku_id FROM {}"
                ).format(sql.Identifier(reserved))).fetchall(), [(2,)])
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(reserved)))
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(users)))
                conn.execute(sql.SQL("DROP SEQUENCE IF EXISTS {}").format(sql.Identifier(seq)))


if __name__ == "__main__":
    unittest.main()
