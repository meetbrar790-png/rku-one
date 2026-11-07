"""Disposable PostgreSQL: repeated verified payment event allocates once.

No real provider webhooks are accepted. This is a transaction/idempotency
rehearsal using fake payment references in an isolated test database.
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

from vip_allocator_prototype import ALLOCATION_LOCK_KEY


@unittest.skipUnless(os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
                     "Disposable PostgreSQL VIP test DB not configured")
class VipPaymentIdempotencyTests(unittest.TestCase):
    def test_duplicate_payment_event_changes_state_once(self):
        url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        table = "rku_vip_idempotency_" + uuid.uuid4().hex
        with psycopg.connect(url) as conn:
            if not conn.info.dbname.endswith("_vip_test"):
                self.fail("Refusing non-test database")
            conn.execute(sql.SQL(
                "CREATE TABLE {} (rku_id BIGINT PRIMARY KEY, owner_id BIGINT NOT NULL, "
                "state TEXT NOT NULL, payment_ref TEXT UNIQUE NOT NULL, "
                "allocation_count INTEGER NOT NULL DEFAULT 0)"
            ).format(sql.Identifier(table)))
        try:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL(
                    "INSERT INTO {} (rku_id,owner_id,state,payment_ref) "
                    "VALUES (2,1,'reserved','fake-ref-001')"
                ).format(sql.Identifier(table)))
            results = []
            for _ in range(3):
                with psycopg.connect(url) as conn:
                    conn.execute("SELECT pg_advisory_xact_lock(%s)", (ALLOCATION_LOCK_KEY,))
                    changed = conn.execute(sql.SQL(
                        "UPDATE {} SET state='allocated', allocation_count=allocation_count+1 "
                        "WHERE rku_id=2 AND owner_id=1 AND payment_ref=%s "
                        "AND state='reserved' RETURNING rku_id"
                    ).format(sql.Identifier(table)), ("fake-ref-001",)).fetchone()
                    results.append(changed)
            self.assertEqual(results, [(2,), None, None])
            with psycopg.connect(url) as conn:
                self.assertEqual(conn.execute(sql.SQL(
                    "SELECT state,allocation_count FROM {} WHERE rku_id=2"
                ).format(sql.Identifier(table))).fetchone(), ("allocated", 1))
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table)))


if __name__ == "__main__":
    unittest.main()
