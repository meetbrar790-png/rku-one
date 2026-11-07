"""Disposable PostgreSQL integration tests for VIP hold release eligibility.

These tests use a temporary test table, NOT real VIP reservations. Release
must be guarded by current payment, allocation and expiry state in the same
transaction. No payment processing is performed.
"""
import os
import uuid
import unittest
from datetime import datetime, timedelta, timezone

try:
    import psycopg
    from psycopg import sql
except ImportError:
    psycopg = None
    sql = None


@unittest.skipUnless(
    os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
    "Disposable PostgreSQL VIP test DB not configured",
)
class VipHoldExpiryPostgresTests(unittest.TestCase):
    def test_expired_unpaid_hold_can_cancel_but_paid_hold_cannot(self):
        url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        with psycopg.connect(url) as conn:
            if not conn.info.dbname.endswith("_vip_test"):
                self.fail("Refusing non-test database")
        table = "rku_vip_expiry_" + uuid.uuid4().hex
        try:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL(
                    "CREATE TABLE {} (rku_id BIGINT PRIMARY KEY, state TEXT NOT NULL, "
                    "paid BOOLEAN NOT NULL, issued BOOLEAN NOT NULL, expires_at TIMESTAMPTZ)"
                ).format(sql.Identifier(table)))
                conn.execute(sql.SQL(
                    "INSERT INTO {} VALUES "
                    "(2, 'reserved', FALSE, FALSE, NOW() - INTERVAL '1 hour'), "
                    "(3, 'reserved', TRUE, FALSE, NOW() - INTERVAL '1 hour'), "
                    "(4, 'reserved', FALSE, TRUE, NOW() - INTERVAL '1 hour'), "
                    "(5, 'reserved', FALSE, FALSE, NOW() + INTERVAL '1 hour')"
                ).format(sql.Identifier(table)))
            with psycopg.connect(url) as conn:
                conn.execute("SELECT pg_advisory_xact_lock(78112026)")
                changed = conn.execute(sql.SQL(
                    "UPDATE {} SET state='cancelled' "
                    "WHERE state='reserved' AND paid=FALSE AND issued=FALSE "
                    "AND expires_at IS NOT NULL AND expires_at <= NOW() "
                    "RETURNING rku_id"
                ).format(sql.Identifier(table))).fetchall()
                self.assertEqual(changed, [(2,)])
                states = dict(conn.execute(sql.SQL(
                    "SELECT rku_id, state FROM {} ORDER BY rku_id"
                ).format(sql.Identifier(table))).fetchall())
                self.assertEqual(states, {2: "cancelled", 3: "reserved", 4: "reserved", 5: "reserved"})
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table)))


if __name__ == "__main__":
    unittest.main()
