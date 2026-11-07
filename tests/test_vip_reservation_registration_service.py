"""Cross-path disposable integration: VIP reservation and full signup."""
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
from vip_reservation_test_service import reserve_test_vip
from vip_full_registration_test_service import register_test_user


@unittest.skipUnless(os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
                     "Disposable VIP PostgreSQL DB not configured")
class ReservationRegistrationIntegration(unittest.TestCase):
    def setUp(self):
        self.url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        suffix = uuid.uuid4().hex
        self.users, self.reserved, self.seq = (
            "rku_users_" + suffix, "rku_reserved_" + suffix, "rku_seq_" + suffix)
        with psycopg.connect(self.url) as conn:
            if not conn.info.dbname.endswith("_vip_test"):
                self.fail("Refusing non-test database")
            conn.execute(sql.SQL("CREATE SEQUENCE {} START 2").format(sql.Identifier(self.seq)))
            conn.execute(sql.SQL(
                "CREATE TABLE {} (rku_id BIGINT PRIMARY KEY, email TEXT UNIQUE NOT NULL, "
                "password_hash TEXT NOT NULL)"
            ).format(sql.Identifier(self.users)))
            conn.execute(sql.SQL(
                "CREATE TABLE {} (rku_id BIGINT PRIMARY KEY, owner_id BIGINT NOT NULL)"
            ).format(sql.Identifier(self.reserved)))
            conn.execute(sql.SQL("INSERT INTO {} VALUES (1,%s,%s)").format(
                sql.Identifier(self.users)), ("owner@example.invalid", "hash"))

    def tearDown(self):
        with psycopg.connect(self.url) as conn:
            conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(self.reserved)))
            conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(self.users)))
            conn.execute(sql.SQL("DROP SEQUENCE IF EXISTS {}").format(sql.Identifier(self.seq)))

    def test_reserved_id_skipped_and_issued_id_cannot_be_reserved(self):
        with psycopg.connect(self.url) as conn:
            self.assertTrue(reserve_test_vip(conn, self.users, self.reserved, 2, 1))
            self.assertFalse(reserve_test_vip(conn, self.users, self.reserved, 2, 2))
            self.assertFalse(reserve_test_vip(conn, self.users, self.reserved, 1, 2))
        with psycopg.connect(self.url) as conn:
            result = register_test_user(conn, self.users, self.reserved, self.seq,
                                        "new@example.invalid", "hash")
            self.assertEqual(result[0], 3)
        with psycopg.connect(self.url) as conn:
            self.assertFalse(reserve_test_vip(conn, self.users, self.reserved, 3, 2))

    def test_concurrent_reservations_only_one_wins(self):
        barrier = threading.Barrier(2)
        def reserve(owner):
            barrier.wait(timeout=15)
            with psycopg.connect(self.url) as conn:
                return reserve_test_vip(conn, self.users, self.reserved, 2, owner)
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(reserve, (10, 11)))
        self.assertEqual(sorted(outcomes), [False, True])
        with psycopg.connect(self.url) as conn:
            result = register_test_user(conn, self.users, self.reserved, self.seq,
                                        "new@example.invalid", "hash")
            self.assertEqual(result[0], 3)

    def test_refuses_live_database_before_sql(self):
        from unittest.mock import MagicMock
        conn = MagicMock()
        conn.info.dbname = "rku_one_db"
        with self.assertRaises(ValueError):
            reserve_test_vip(conn, self.users, self.reserved, 2, 1)
        conn.execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
