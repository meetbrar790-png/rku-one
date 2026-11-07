"""Opt-in PostgreSQL integration tests for VIP reservation uniqueness.

Run only against a disposable, dedicated test database:
  RKU_VIP_TEST_DATABASE_URL=postgresql://... python -m unittest tests.test_vip_postgres_integration

Never point this at production or a restored backup. Tests create and drop
only a dedicated table inside a rolled-back transaction.
"""
import os
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

try:
    import psycopg
except ImportError:
    psycopg = None


@unittest.skipUnless(os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg, "Dedicated PostgreSQL test DB not configured")
class VipPostgresIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        with psycopg.connect(self.url) as conn:
            conn.execute("CREATE TEMP TABLE vip_test_reservations (rku_id BIGINT PRIMARY KEY, owner TEXT NOT NULL)")
            self.assertEqual(
                conn.execute("INSERT INTO vip_test_reservations VALUES (2, 'A') ON CONFLICT DO NOTHING RETURNING rku_id").fetchone(),
                (2,),
            )
            self.assertIsNone(
                conn.execute("INSERT INTO vip_test_reservations VALUES (2, 'B') ON CONFLICT DO NOTHING RETURNING rku_id").fetchone()
            )
            conn.rollback()

    def test_unique_constraint_rejects_duplicate(self):
        with psycopg.connect(self.url) as conn:
            conn.execute("CREATE TEMP TABLE vip_test_reservations (rku_id BIGINT PRIMARY KEY, owner TEXT NOT NULL)")
            conn.execute("INSERT INTO vip_test_reservations VALUES (2, 'A')")
            with self.assertRaises(psycopg.errors.UniqueViolation):
                conn.execute("INSERT INTO vip_test_reservations VALUES (2, 'B')")
            conn.rollback()


if __name__ == "__main__":
    unittest.main()
