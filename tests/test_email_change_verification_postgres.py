"""Disposable PostgreSQL regression: changed email invalidates old verification token."""
import os
import unittest
import uuid

try:
    import psycopg
    from psycopg import sql
except ImportError:
    psycopg = None
    sql = None

from email_verification_policy import create_verification_token, verification_digest


@unittest.skipUnless(os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
                     "Disposable PostgreSQL test database required")
class EmailChangeVerificationPostgresTests(unittest.TestCase):
    def test_old_email_token_cannot_verify_new_address(self):
        url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        suffix = uuid.uuid4().hex
        users = "rku_email_users_" + suffix
        tokens = "rku_email_tokens_" + suffix
        digest = verification_digest(create_verification_token())
        with psycopg.connect(url) as conn:
            if not conn.info.dbname.endswith("_vip_test"):
                self.fail("Refusing non-test database")
            conn.execute(sql.SQL(
                "CREATE TABLE {} (rku_id BIGINT PRIMARY KEY, email TEXT NOT NULL, "
                "email_verified BOOLEAN NOT NULL DEFAULT FALSE)"
            ).format(sql.Identifier(users)))
            conn.execute(sql.SQL(
                "CREATE TABLE {} (digest TEXT PRIMARY KEY, rku_id BIGINT NOT NULL, "
                "email TEXT NOT NULL, expires_at TIMESTAMPTZ NOT NULL, "
                "consumed_at TIMESTAMPTZ)"
            ).format(sql.Identifier(tokens)))
        try:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL(
                    "INSERT INTO {} (rku_id,email) VALUES (1001,'old@example.com')"
                ).format(sql.Identifier(users)))
                conn.execute(sql.SQL(
                    "INSERT INTO {} (digest,rku_id,email,expires_at) "
                    "VALUES (%s,1001,'old@example.com',NOW()+INTERVAL '24 hours')"
                ).format(sql.Identifier(tokens)), (digest,))
                conn.execute(sql.SQL(
                    "UPDATE {} SET email='new@example.com',email_verified=FALSE "
                    "WHERE rku_id=1001"
                ).format(sql.Identifier(users)))
                consumed = conn.execute(sql.SQL(
                    "UPDATE {} t SET consumed_at=NOW() FROM {} u "
                    "WHERE t.digest=%s AND t.rku_id=u.rku_id "
                    "AND t.email=u.email AND t.consumed_at IS NULL "
                    "AND t.expires_at>NOW() RETURNING t.rku_id"
                ).format(sql.Identifier(tokens), sql.Identifier(users)), (digest,)).fetchone()
                self.assertIsNone(consumed)
                state = conn.execute(sql.SQL(
                    "SELECT email,email_verified FROM {} WHERE rku_id=1001"
                ).format(sql.Identifier(users))).fetchone()
                self.assertEqual(state, ("new@example.com", False))
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(tokens)))
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(users)))


if __name__ == "__main__":
    unittest.main()
