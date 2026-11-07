"""HTTP registration rollback test using isolated VIP-aware PostgreSQL tables."""
import os
import unittest
import uuid
from unittest.mock import patch

try:
    import psycopg
    from psycopg import sql
    from api import app
except ImportError:
    psycopg = None

from staging_db_preflight import assert_disposable_staging_url
from staging_vip_api_adapter import staged_vip_register


@unittest.skipUnless(os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
                     "Disposable PostgreSQL test DB required")
class StagedVipHttpRollbackTests(unittest.TestCase):
    def test_http_registration_failure_leaves_no_partial_user(self):
        from fastapi.testclient import TestClient

        url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        assert_disposable_staging_url(url)
        suffix = uuid.uuid4().hex
        users, reserved, seq = ("rku_users_" + suffix, "rku_reserved_" + suffix,
                                "rku_seq_" + suffix)
        with psycopg.connect(url) as conn:
            if not conn.info.dbname.endswith("_vip_test"):
                self.fail("Refusing non-test DB")
            conn.execute(sql.SQL("CREATE SEQUENCE {} START 2").format(sql.Identifier(seq)))
            conn.execute(sql.SQL(
                "CREATE TABLE {} (rku_id BIGINT PRIMARY KEY, email TEXT UNIQUE NOT NULL, "
                "password_hash TEXT NOT NULL, "
                "CONSTRAINT reject_broken_email CHECK (email <> 'broken@example.com'))"
            ).format(sql.Identifier(users)))
            conn.execute(sql.SQL(
                "CREATE TABLE {} (rku_id BIGINT PRIMARY KEY, owner_id BIGINT NOT NULL)"
            ).format(sql.Identifier(reserved)))
            conn.execute(sql.SQL("INSERT INTO {} VALUES (1,%s,%s)").format(
                sql.Identifier(users)), ("owner@example.com", "hash"))
            conn.execute(sql.SQL("INSERT INTO {} VALUES (2,1)").format(
                sql.Identifier(reserved)))
        try:
            def staged(email, password):
                return staged_vip_register(url, users, reserved, seq, email, password)
            with patch("api.register_user", side_effect=staged):
                client = TestClient(app, raise_server_exceptions=False)
                failed = client.post("/register", json={
                    "email": "broken@example.com", "password": "staging-password-123456"})
                self.assertEqual(failed.status_code, 500, failed.text)
                with psycopg.connect(url) as conn:
                    self.assertEqual(conn.execute(sql.SQL(
                        "SELECT rku_id FROM {} ORDER BY rku_id"
                    ).format(sql.Identifier(users))).fetchall(), [(1,)])
                    self.assertEqual(conn.execute(sql.SQL(
                        "SELECT rku_id FROM {}"
                    ).format(sql.Identifier(reserved))).fetchall(), [(2,)])
                recovered = client.post("/register", json={
                    "email": "recovered@example.com", "password": "staging-password-123456"})
                self.assertEqual(recovered.status_code, 200, recovered.text)
                self.assertGreaterEqual(recovered.json()["rku_id"], 3)
                self.assertNotEqual(recovered.json()["rku_id"], 2)
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(reserved)))
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(users)))
                conn.execute(sql.SQL("DROP SEQUENCE IF EXISTS {}").format(sql.Identifier(seq)))


if __name__ == "__main__":
    unittest.main()
