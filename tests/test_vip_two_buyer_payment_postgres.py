"""Disposable PostgreSQL test: two buyers cannot claim one VIP number.

Payment verification is simulated. No real payment gateway or live IDs.
"""
import os
import threading
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor

try:
    import psycopg
    from psycopg import sql
except ImportError:
    psycopg = None
    sql = None

from vip_allocator_prototype import ALLOCATION_LOCK_KEY
from vip_payment_policy import may_allocate_paid_vip


@unittest.skipUnless(os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
                     "Disposable PostgreSQL VIP test DB not configured")
class VipTwoBuyerPaymentTests(unittest.TestCase):
    def test_only_reservation_owner_can_claim_number(self):
        url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        table = "rku_vip_buyers_" + uuid.uuid4().hex
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
                    "INSERT INTO {} VALUES (2,10,'reserved','fake-payment-owner')"
                ).format(sql.Identifier(table)))
            barrier = threading.Barrier(2)

            def attempt(owner_id, payment_ref):
                barrier.wait(timeout=15)
                with psycopg.connect(url) as conn:
                    conn.execute("SELECT pg_advisory_xact_lock(%s)", (ALLOCATION_LOCK_KEY,))
                    row = conn.execute(sql.SQL(
                        "SELECT owner_id,state,payment_ref FROM {} WHERE rku_id=2 FOR UPDATE"
                    ).format(sql.Identifier(table))).fetchone()
                    allowed = may_allocate_paid_vip(
                        reservation_state=row[1], payment_verified=True,
                        payment_reference_matches=(row[2] == payment_ref),
                        reservation_owner_matches=(row[0] == owner_id),
                        issued=False, expired=False)
                    if not allowed:
                        return False
                    return conn.execute(sql.SQL(
                        "UPDATE {} SET state='allocated' "
                        "WHERE rku_id=2 AND owner_id=%s AND payment_ref=%s "
                        "AND state='reserved' RETURNING rku_id"
                    ).format(sql.Identifier(table)),
                        (owner_id, payment_ref)).fetchone() is not None

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda pair: attempt(*pair),
                                        [(10, "fake-payment-owner"),
                                         (11, "fake-payment-other")]))
            self.assertEqual(results, [True, False])
            with psycopg.connect(url) as conn:
                self.assertEqual(conn.execute(sql.SQL(
                    "SELECT owner_id,state FROM {} WHERE rku_id=2"
                ).format(sql.Identifier(table))).fetchone(), (10, "allocated"))
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table)))


if __name__ == "__main__":
    unittest.main()
