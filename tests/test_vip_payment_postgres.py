"""Disposable PostgreSQL payment confirmation and VIP allocation rehearsal.

Simulates provider verification flags only. No actual payment provider,
production database, or user entitlement is modified.
"""
import os
import unittest
import uuid

try:
    import psycopg
    from psycopg import sql
except ImportError:
    psycopg = None
    sql = None

from vip_payment_policy import may_allocate_paid_vip
from vip_allocator_prototype import ALLOCATION_LOCK_KEY


@unittest.skipUnless(os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
                     "Disposable PostgreSQL VIP test DB not configured")
class VipPaymentPostgresTests(unittest.TestCase):
    def test_verified_payment_allocates_once_unverified_does_not(self):
        url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        table = "rku_vip_payment_" + uuid.uuid4().hex
        with psycopg.connect(url) as conn:
            if not conn.info.dbname.endswith("_vip_test"):
                self.fail("Refusing non-test database")
            conn.execute(sql.SQL(
                "CREATE TABLE {} (rku_id BIGINT PRIMARY KEY, owner_id BIGINT NOT NULL, "
                "state TEXT NOT NULL, payment_ref TEXT UNIQUE NOT NULL)"
            ).format(sql.Identifier(table)))
        try:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL(
                    "INSERT INTO {} VALUES (2,1,'reserved','test-payment-1')"
                ).format(sql.Identifier(table)))
            with psycopg.connect(url) as conn:
                conn.execute("SELECT pg_advisory_xact_lock(%s)", (ALLOCATION_LOCK_KEY,))
                row = conn.execute(sql.SQL(
                    "SELECT owner_id,state,payment_ref FROM {} WHERE rku_id=2 FOR UPDATE"
                ).format(sql.Identifier(table))).fetchone()
                self.assertFalse(may_allocate_paid_vip(
                    reservation_state=row[1], payment_verified=False,
                    payment_reference_matches=True, reservation_owner_matches=True,
                    issued=False, expired=False))
                self.assertEqual(conn.execute(sql.SQL(
                    "SELECT state FROM {} WHERE rku_id=2"
                ).format(sql.Identifier(table))).fetchone()[0], "reserved")
                self.assertTrue(may_allocate_paid_vip(
                    reservation_state=row[1], payment_verified=True,
                    payment_reference_matches=(row[2] == "test-payment-1"),
                    reservation_owner_matches=(row[0] == 1),
                    issued=False, expired=False))
                updated = conn.execute(sql.SQL(
                    "UPDATE {} SET state='allocated' "
                    "WHERE rku_id=2 AND owner_id=1 AND payment_ref=%s "
                    "AND state='reserved' RETURNING rku_id"
                ).format(sql.Identifier(table)), ("test-payment-1",)).fetchone()
                self.assertEqual(updated, (2,))
            with psycopg.connect(url) as conn:
                conn.execute("SELECT pg_advisory_xact_lock(%s)", (ALLOCATION_LOCK_KEY,))
                self.assertIsNone(conn.execute(sql.SQL(
                    "UPDATE {} SET state='allocated' "
                    "WHERE rku_id=2 AND state='reserved' RETURNING rku_id"
                ).format(sql.Identifier(table))).fetchone())
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table)))


if __name__ == "__main__":
    unittest.main()
