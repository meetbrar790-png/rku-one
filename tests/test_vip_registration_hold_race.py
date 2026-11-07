"""Disposable cross-path race between VIP hold and full registration."""
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
from vip_full_registration_test_service import register_test_user
from vip_reservation_test_service import reserve_test_vip


@unittest.skipUnless(os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
                     "Disposable VIP test DB not configured")
class VipRegistrationReservationRaceTests(unittest.TestCase):
    def test_concurrent_hold_and_signup_never_issue_same_id(self):
        url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        suffix = uuid.uuid4().hex
        users = "rku_users_" + suffix
        reserved = "rku_reserved_" + suffix
        seq = "rku_seq_" + suffix
        with psycopg.connect(url) as conn:
            if not conn.info.dbname.endswith("_vip_test"):
                self.fail("Refusing non-test database")
            conn.execute(sql.SQL("CREATE SEQUENCE {} START 2").format(sql.Identifier(seq)))
            conn.execute(sql.SQL(
                "CREATE TABLE {} (rku_id BIGINT PRIMARY KEY, email TEXT UNIQUE NOT NULL, "
                "password_hash TEXT NOT NULL)"
            ).format(sql.Identifier(users)))
            conn.execute(sql.SQL(
                "CREATE TABLE {} (rku_id BIGINT PRIMARY KEY, owner_id BIGINT NOT NULL)"
            ).format(sql.Identifier(reserved)))
            conn.execute(sql.SQL("INSERT INTO {} VALUES (1,%s,%s)").format(
                sql.Identifier(users)), ("owner@example.com", "hash"))
        try:
            barrier = threading.Barrier(2)
            def signup():
                barrier.wait(timeout=15)
                with psycopg.connect(url) as conn:
                    return register_test_user(conn, users, reserved, seq,
                                              "new@example.com", "hash")[0]
            def hold():
                barrier.wait(timeout=15)
                with psycopg.connect(url) as conn:
                    return reserve_test_vip(conn, users, reserved, 2, 1)
            with ThreadPoolExecutor(max_workers=2) as pool:
                signup_future = pool.submit(signup)
                hold_future = pool.submit(hold)
                allocated_id = signup_future.result(timeout=30)
                hold_success = hold_future.result(timeout=30)
            self.assertIn(allocated_id, (2, 3))
            self.assertEqual(hold_success, allocated_id != 2)
            with psycopg.connect(url) as conn:
                overlap = conn.execute(sql.SQL(
                    "SELECT COUNT(*) FROM {} u JOIN {} r USING (rku_id)"
                ).format(sql.Identifier(users), sql.Identifier(reserved))).fetchone()[0]
                self.assertEqual(overlap, 0)
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(reserved)))
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(users)))
                conn.execute(sql.SQL("DROP SEQUENCE IF EXISTS {}").format(sql.Identifier(seq)))


if __name__ == "__main__":
    unittest.main()
