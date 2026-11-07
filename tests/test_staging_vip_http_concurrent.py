"""Concurrent HTTP /register requests with a disposable VIP-aware adapter.

This test does not start FastAPI lifespan, deploy a server, or connect to
production. The registration dependency is replaced only inside this test.
"""
import os
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
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
class ConcurrentVipHttpRegistrationTests(unittest.TestCase):
    def test_two_http_signups_skip_reserved_id(self):
        from fastapi.testclient import TestClient  # only installed in PostgreSQL CI

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
                "password_hash TEXT NOT NULL)"
            ).format(sql.Identifier(users)))
            conn.execute(sql.SQL(
                "CREATE TABLE {} (rku_id BIGINT PRIMARY KEY, owner_id BIGINT NOT NULL)"
            ).format(sql.Identifier(reserved)))
            conn.execute(sql.SQL("INSERT INTO {} VALUES (1,%s,%s)").format(
                sql.Identifier(users)), ("owner@example.com", "hash"))
            conn.execute(sql.SQL("INSERT INTO {} VALUES (2,1)").format(
                sql.Identifier(reserved)))
        try:
            barrier = Barrier(2)
            def staged(email, password):
                return staged_vip_register(url, users, reserved, seq, email, password)
            def signup(email):
                barrier.wait(timeout=20)
                client = TestClient(app)  # no lifespan or production schema setup
                return client.post("/register", json={
                    "email": email, "password": "staging-password-123456"})
            with patch("api.register_user", side_effect=staged):
                with ThreadPoolExecutor(max_workers=2) as pool:
                    futures = [pool.submit(signup, "alpha@example.com"),
                               pool.submit(signup, "beta@example.com")]
                    responses = [future.result(timeout=45) for future in futures]
            self.assertTrue(all(r.status_code == 200 for r in responses),
                            [r.text for r in responses])
            self.assertEqual({r.json()["rku_id"] for r in responses}, {3, 4})
            with psycopg.connect(url) as conn:
                self.assertEqual(conn.execute(sql.SQL(
                    "SELECT rku_id FROM {} ORDER BY rku_id"
                ).format(sql.Identifier(users))).fetchall(), [(1,), (3,), (4,)])
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
