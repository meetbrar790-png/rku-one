"""Disposable PostgreSQL test: VIP reservation is durable across sessions.

This verifies a *test-only* reservation table, not production VIP checkout.
"""
import os
import uuid
import unittest

try:
    import psycopg
    from psycopg import sql
except ImportError:
    psycopg = None
    sql = None


@unittest.skipUnless(
    os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
    "Dedicated PostgreSQL VIP test DB not configured",
)
class VipReservationDurabilityTests(unittest.TestCase):
    def test_committed_hold_persists_and_duplicate_is_rejected(self):
        url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        with psycopg.connect(url) as conn:
            if not conn.info.dbname.endswith("_vip_test"):
                self.fail("Refusing non-test database")
        table = "rku_vip_durable_" + uuid.uuid4().hex
        try:
            with psycopg.connect(url) as conn:
                conn.execute(
                    sql.SQL("CREATE TABLE {} (rku_id BIGINT PRIMARY KEY, reservation_key UUID UNIQUE NOT NULL)").format(
                        sql.Identifier(table)
                    )
                )
                conn.execute(
                    sql.SQL("INSERT INTO {} VALUES (%s, %s)").format(sql.Identifier(table)),
                    (2, uuid.uuid4()),
                )
            # A new database session must still see the committed hold.
            with psycopg.connect(url) as conn:
                self.assertEqual(
                    conn.execute(
                        sql.SQL("SELECT COUNT(*) FROM {} WHERE rku_id=2").format(sql.Identifier(table))
                    ).fetchone()[0],
                    1,
                )
                duplicate = conn.execute(
                    sql.SQL(
                        "INSERT INTO {} VALUES (%s, %s) "
                        "ON CONFLICT (rku_id) DO NOTHING RETURNING rku_id"
                    ).format(sql.Identifier(table)),
                    (2, uuid.uuid4()),
                ).fetchone()
                self.assertIsNone(duplicate)
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table)))


if __name__ == "__main__":
    unittest.main()
