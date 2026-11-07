"""Isolated PostgreSQL tests for transactional VIP hold expiry.

No production tables or payment provider are accessed.
"""
import os
import unittest
import uuid
from datetime import datetime, timedelta, timezone

try:
    import psycopg
    from psycopg import sql
except ImportError:
    psycopg = None
    sql = None

from vip_hold_policy import may_release_hold


@unittest.skipUnless(os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
                     "Disposable PostgreSQL VIP test DB not configured")
class VipHoldTransactionTests(unittest.TestCase):
    def test_expiry_does_not_release_paid_or_issued_id(self):
        url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        now = datetime.now(timezone.utc)
        table = "rku_hold_" + uuid.uuid4().hex
        with psycopg.connect(url) as conn:
            if not conn.info.dbname.endswith("_vip_test"):
                self.fail("Refusing non-test database")
            conn.execute(sql.SQL(
                "CREATE TABLE {} (rku_id BIGINT PRIMARY KEY, state TEXT NOT NULL, "
                "paid BOOLEAN NOT NULL, issued BOOLEAN NOT NULL, expires_at TIMESTAMPTZ)"
            ).format(sql.Identifier(table)))
        try:
            with psycopg.connect(url) as conn:
                conn.executemany(
                    sql.SQL("INSERT INTO {} VALUES (%s,%s,%s,%s,%s)").format(sql.Identifier(table)),
                    [(2, "reserved", False, False, now - timedelta(minutes=1)),
                     (3, "reserved", True, False, now - timedelta(minutes=1)),
                     (4, "reserved", False, True, now - timedelta(minutes=1)),
                     (5, "reserved", False, False, now + timedelta(hours=1)),
                     (6, "allocated", False, False, now - timedelta(minutes=1))],
                )
            with psycopg.connect(url) as conn:
                rows = conn.execute(sql.SQL(
                    "SELECT rku_id,state,paid,issued,expires_at FROM {} FOR UPDATE"
                ).format(sql.Identifier(table))).fetchall()
                eligible = [rku_id for rku_id, state, paid, issued, expiry in rows
                            if may_release_hold(state=state, paid=paid, issued=issued,
                                                expires_at=expiry, now=now)]
                self.assertEqual(eligible, [2])
                conn.execute(sql.SQL(
                    "UPDATE {} SET state='cancelled' WHERE rku_id=ANY(%s)"
                ).format(sql.Identifier(table)), (eligible,))
            with psycopg.connect(url) as conn:
                states = dict(conn.execute(sql.SQL(
                    "SELECT rku_id,state FROM {} ORDER BY rku_id"
                ).format(sql.Identifier(table))).fetchall())
                self.assertEqual(states, {2: "cancelled", 3: "reserved",
                                          4: "reserved", 5: "reserved", 6: "allocated"})
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table)))


if __name__ == "__main__":
    unittest.main()
