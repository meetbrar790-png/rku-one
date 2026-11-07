"""Verify email tokens are bound to an account and consumed once in disposable PostgreSQL."""
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

from email_verification_policy import create_verification_token, verification_digest


@unittest.skipUnless(os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
                     "Disposable PostgreSQL test database required")
class EmailVerificationPostgresTests(unittest.TestCase):
    def test_token_is_account_bound_atomic_and_expires(self):
        url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        table = "rku_verify_" + uuid.uuid4().hex
        token_digest = verification_digest(create_verification_token())
        expired_digest = verification_digest(create_verification_token())
        with psycopg.connect(url) as conn:
            if not conn.info.dbname.endswith("_vip_test"):
                self.fail("Refusing non-test database")
            conn.execute(sql.SQL(
                "CREATE TABLE {} (digest TEXT PRIMARY KEY, user_id BIGINT NOT NULL, "
                "expires_at TIMESTAMPTZ NOT NULL, consumed_at TIMESTAMPTZ)"
            ).format(sql.Identifier(table)))
        try:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL(
                    "INSERT INTO {} (digest,user_id,expires_at) VALUES "
                    "(%s,1001,NOW()+INTERVAL '24 hours'),"
                    "(%s,1002,NOW()-INTERVAL '1 second')"
                ).format(sql.Identifier(table)), (token_digest, expired_digest))

            def consume(user_id, digest):
                with psycopg.connect(url) as conn:
                    return conn.execute(sql.SQL(
                        "UPDATE {} SET consumed_at=NOW() "
                        "WHERE digest=%s AND user_id=%s AND consumed_at IS NULL "
                        "AND expires_at>NOW() RETURNING user_id"
                    ).format(sql.Identifier(table)), (digest, user_id)).fetchone()

            self.assertIsNone(consume(1002, token_digest))
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: consume(1001, token_digest), range(2)))
            self.assertEqual(sum(result is not None for result in results), 1)
            self.assertIsNone(consume(1001, token_digest))
            self.assertIsNone(consume(1002, expired_digest))
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table)))


if __name__ == "__main__":
    unittest.main()
