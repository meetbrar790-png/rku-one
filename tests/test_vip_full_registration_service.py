"""Exercise full registration service against disposable PostgreSQL."""
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
                     "Disposable VIP PostgreSQL DB not configured")
class FullRegistrationServiceTests(unittest.TestCase):
    def test_reserved_id_skipped_and_full_user_saved(self):
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
        try:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("INSERT INTO {} VALUES (1,%s,%s)").format(
                    sql.Identifier(users)), ("owner@example.invalid", "existing-hash"))
                conn.execute(sql.SQL("INSERT INTO {} VALUES (2)").format(
                    sql.Identifier(reserved)))
            with psycopg.connect(url) as conn:
                result = register_test_user(conn, users, reserved, seq,
                                            " NEW@Example.invalid ", "hash-for-test")
                self.assertEqual(result, (3, "new@example.invalid"))
            with psycopg.connect(url) as conn:
                self.assertEqual(conn.execute(sql.SQL(
                    "SELECT rku_id,email,password_hash FROM {} ORDER BY rku_id"
                ).format(sql.Identifier(users))).fetchall(), [
                    (1, "owner@example.invalid", "existing-hash"),
                    (3, "new@example.invalid", "hash-for-test"),
                ])
                self.assertEqual(conn.execute(sql.SQL(
                    "SELECT rku_id FROM {}"
                ).format(sql.Identifier(reserved))).fetchall(), [(2,)])
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(reserved)))
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(users)))
                conn.execute(sql.SQL("DROP SEQUENCE IF EXISTS {}").format(sql.Identifier(seq)))

    def test_refuses_live_database_before_sql(self):
        from unittest.mock import MagicMock
        conn = MagicMock()
        conn.info.dbname = "rku_one_db"
        suffix = "a" * 32
        with self.assertRaises(ValueError):
            register_test_user(conn, "rku_users_"+suffix, "rku_reserved_"+suffix,
                               "rku_seq_"+suffix, "a@example.invalid", "hash")
        conn.execute.assert_not_called()

if __name__ == "__main__":
    unittest.main()
