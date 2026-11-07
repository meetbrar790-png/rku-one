"""Disposable PostgreSQL test of one-use password reset tokens.

Tests atomic token consumption only. No live recovery endpoint or email sending.
"""
import os
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

try:
    import psycopg
    from psycopg import sql
except ImportError:
    psycopg = None
    sql = None

from account_recovery_policy import new_reset_token, hash_reset_token


@unittest.skipUnless(os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
                     "Disposable PostgreSQL VIP test DB not configured")
class RecoveryTokenPostgresTests(unittest.TestCase):
    def test_atomic_one_use_and_expiry(self):
        url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        table = "rku_reset_" + uuid.uuid4().hex
        token = new_reset_token()
        digest = hash_reset_token(token)
        expired_digest = hash_reset_token(new_reset_token())
        with psycopg.connect(url) as conn:
            if not conn.info.dbname.endswith("_vip_test"):
                self.fail("Refusing non-test database")
            conn.execute(sql.SQL(
                "CREATE TABLE {} (digest TEXT PRIMARY KEY, expires_at TIMESTAMPTZ NOT NULL, "
                "consumed_at TIMESTAMPTZ)"
            ).format(sql.Identifier(table)))
        try:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL(
                    "INSERT INTO {} (digest,expires_at) VALUES (%s,NOW()+INTERVAL '20 minutes'),"
                    "(%s,NOW()-INTERVAL '1 minute')"
                ).format(sql.Identifier(table)), (digest, expired_digest))

            def consume():
                with psycopg.connect(url) as conn:
                    row = conn.execute(sql.SQL(
                        "UPDATE {} SET consumed_at=NOW() WHERE digest=%s "
                        "AND consumed_at IS NULL AND expires_at>NOW() "
                        "RETURNING digest"
                    ).format(sql.Identifier(table)), (digest,)).fetchone()
                    return row is not None

            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(lambda _: consume(), range(2)))
            self.assertEqual(sorted(results), [False, True])
            self.assertFalse(consume())

            with psycopg.connect(url) as conn:
                expired = conn.execute(sql.SQL(
                    "UPDATE {} SET consumed_at=NOW() WHERE digest=%s "
                    "AND consumed_at IS NULL AND expires_at>NOW() "
                    "RETURNING digest"
                ).format(sql.Identifier(table)), (expired_digest,)).fetchone()
                self.assertIsNone(expired)
                rows = conn.execute(sql.SQL(
                    "SELECT digest, consumed_at IS NOT NULL FROM {} ORDER BY digest"
                ).format(sql.Identifier(table))).fetchall()
                self.assertEqual(
                    {row[0]: row[1] for row in rows},
                    {digest: True, expired_digest: False},
                )
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table)))


if __name__ == "__main__":
    unittest.main()
