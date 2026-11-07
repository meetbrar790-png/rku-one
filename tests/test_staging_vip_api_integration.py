"""Exercise real FastAPI registration handler with staged VIP-aware allocator."""
import os
import unittest
import uuid
from unittest.mock import patch
try:
    import psycopg
    from psycopg import sql
    from fastapi import HTTPException
    from api import register, UserData
except ImportError:
    psycopg = None
from staging_db_preflight import assert_disposable_staging_url
from staging_vip_api_adapter import staged_vip_register


@unittest.skipUnless(os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
                     "Disposable PostgreSQL DB required")
class StagedVipApiIntegrationTests(unittest.TestCase):
    def test_real_api_handler_skips_reserved_id_and_rejects_duplicate_email(self):
        url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        assert_disposable_staging_url(url)
        suffix = uuid.uuid4().hex
        users, reserved, seq = ("rku_users_" + suffix, "rku_reserved_" + suffix,
                                "rku_seq_" + suffix)
        with psycopg.connect(url) as conn:
            if not conn.info.dbname.endswith("_vip_test"):
                self.fail("Refusing production DB")
            conn.execute(sql.SQL("CREATE SEQUENCE {} START 2").format(sql.Identifier(seq)))
            conn.execute(sql.SQL(
                "CREATE TABLE {} (rku_id BIGINT PRIMARY KEY, email TEXT UNIQUE NOT NULL, "
                "password_hash TEXT NOT NULL)"
            ).format(sql.Identifier(users)))
            conn.execute(sql.SQL(
                "CREATE TABLE {} (rku_id BIGINT PRIMARY KEY, owner_id BIGINT NOT NULL)"
            ).format(sql.Identifier(reserved)))
            conn.execute(sql.SQL("INSERT INTO {} VALUES (1,%s,%s)").format(
                sql.Identifier(users)), ("owner@example.com", "test-hash"))
            conn.execute(sql.SQL("INSERT INTO {} VALUES (2,1)").format(
                sql.Identifier(reserved)))
        try:
            def staging_register(email, password):
                return staged_vip_register(url, users, reserved, seq, email, password)
            with patch("api.register_user", side_effect=staging_register):
                user = UserData(email="new@example.com", password="test-password-123456")
                result = register(user)
                self.assertEqual(result, {"rku_id": 3, "email": "new@example.com"})
                with self.assertRaises(HTTPException) as err:
                    register(user)
                self.assertEqual(err.exception.status_code, 409)
            with psycopg.connect(url) as conn:
                self.assertEqual(conn.execute(sql.SQL(
                    "SELECT rku_id FROM {} WHERE email=%s"
                ).format(sql.Identifier(users)), ("new@example.com",)).fetchone()[0], 3)
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
