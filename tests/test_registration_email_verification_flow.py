"""Isolated registration-to-email-verification integration test; no live tables."""
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
class RegistrationVerificationFlowTests(unittest.TestCase):
    def test_registration_then_single_use_verification(self):
        url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        suffix = uuid.uuid4().hex
        users = "rku_verify_users_" + suffix
        tokens = "rku_verify_tokens_" + suffix
        with psycopg.connect(url) as conn:
            if not conn.info.dbname.endswith("_vip_test"):
                self.fail("Refusing non-test database")
            conn.execute(sql.SQL(
                "CREATE TABLE {} (rku_id BIGINT PRIMARY KEY, email TEXT UNIQUE NOT NULL, "
                "email_verified BOOLEAN NOT NULL DEFAULT FALSE)"
            ).format(sql.Identifier(users)))
            conn.execute(sql.SQL(
                "CREATE TABLE {} (digest TEXT PRIMARY KEY, rku_id BIGINT NOT NULL, "
                "expires_at TIMESTAMPTZ NOT NULL, consumed_at TIMESTAMPTZ)"
            ).format(sql.Identifier(tokens)))
        try:
            token = create_verification_token()
            digest = verification_digest(token)
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL(
                    "INSERT INTO {} (rku_id,email) VALUES (1001,%s)"
                ).format(sql.Identifier(users)), ("test@example.com",))
                conn.execute(sql.SQL(
                    "INSERT INTO {} (digest,rku_id,expires_at) "
                    "VALUES (%s,1001,NOW()+INTERVAL '24 hours')"
                ).format(sql.Identifier(tokens)), (digest,))
                before = conn.execute(sql.SQL(
                    "SELECT email_verified FROM {} WHERE rku_id=1001"
                ).format(sql.Identifier(users))).fetchone()
                self.assertEqual(before, (False,))

            def verify(rku_id):
                with psycopg.connect(url) as conn:
                    row = conn.execute(sql.SQL(
                        "UPDATE {} SET consumed_at=NOW() WHERE digest=%s "
                        "AND rku_id=%s AND consumed_at IS NULL AND expires_at>NOW() "
                        "RETURNING rku_id"
                    ).format(sql.Identifier(tokens)), (digest, rku_id)).fetchone()
                    if row:
                        conn.execute(sql.SQL(
                            "UPDATE {} SET email_verified=TRUE WHERE rku_id=%s"
                        ).format(sql.Identifier(users)), (rku_id,))
                    return row is not None

            self.assertFalse(verify(1002))
            self.assertTrue(verify(1001))
            self.assertFalse(verify(1001))
            with psycopg.connect(url) as conn:
                verified = conn.execute(sql.SQL(
                    "SELECT email_verified FROM {} WHERE rku_id=1001"
                ).format(sql.Identifier(users))).fetchone()
                self.assertEqual(verified, (True,))
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(tokens)))
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(users)))


if __name__ == "__main__":
    unittest.main()
