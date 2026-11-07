"""Disposable PostgreSQL test of cross-path registration / VIP locking.

This is a prototype only. Production registration.py does not yet acquire
the same lock or check VIP reservations. Do not sell or reserve VIP IDs.
"""
import os
import uuid
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

try:
    import psycopg
    from psycopg import sql
except ImportError:
    psycopg = None
    sql = None

from vip_allocator_prototype import ALLOCATION_LOCK_KEY, allocate_free_id


@unittest.skipUnless(
    os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
    "Disposable VIP PostgreSQL test DB not configured",
)
class VipCrossPathLockTests(unittest.TestCase):
    def test_registration_and_vip_checkout_share_lock(self):
        url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        with psycopg.connect(url) as conn:
            if not conn.info.dbname.endswith("_vip_test"):
                self.fail("Refusing database not ending _vip_test")
        suffix = uuid.uuid4().hex
        users, reserved, seq = ("rku_users_" + suffix, "rku_reserved_" + suffix, "rku_seq_" + suffix)
        try:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("CREATE SEQUENCE {} START 1").format(sql.Identifier(seq)))
                conn.execute(sql.SQL("CREATE TABLE {} (rku_id BIGINT PRIMARY KEY)").format(sql.Identifier(users)))
                conn.execute(sql.SQL("CREATE TABLE {} (rku_id BIGINT PRIMARY KEY)").format(sql.Identifier(reserved)))
                conn.execute(sql.SQL("INSERT INTO {} VALUES (1)").format(sql.Identifier(users)))
                conn.execute("SELECT nextval(%s::regclass)", (seq,))
            gate = Barrier(2, timeout=15)

            def vip_attempt():
                gate.wait()
                with psycopg.connect(url) as conn:
                    conn.execute("SELECT pg_advisory_xact_lock(%s)", (ALLOCATION_LOCK_KEY,))
                    already_issued = conn.execute(
                        sql.SQL("SELECT EXISTS(SELECT 1 FROM {} WHERE rku_id=2)").format(sql.Identifier(users))
                    ).fetchone()[0]
                    if already_issued:
                        return False
                    return conn.execute(
                        sql.SQL("INSERT INTO {} (rku_id) VALUES (2) ON CONFLICT DO NOTHING RETURNING rku_id").format(sql.Identifier(reserved))
                    ).fetchone() is not None

            def free_attempt():
                gate.wait()
                with psycopg.connect(url) as conn:
                    return allocate_free_id(conn, users, reserved, seq)

            with ThreadPoolExecutor(max_workers=2) as pool:
                f1 = pool.submit(vip_attempt)
                f2 = pool.submit(free_attempt)
                vip_won, free_id = f1.result(), f2.result()

            with psycopg.connect(url) as conn:
                user_ids = [r[0] for r in conn.execute(sql.SQL("SELECT rku_id FROM {}").format(sql.Identifier(users))).fetchall()]
                reserved_ids = [r[0] for r in conn.execute(sql.SQL("SELECT rku_id FROM {}").format(sql.Identifier(reserved))).fetchall()]
            self.assertIn(1, user_ids)
            self.assertNotIn(2, set(user_ids).intersection(reserved_ids))
            self.assertIn(free_id, user_ids)
            self.assertEqual(vip_won, 2 in reserved_ids)
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(users)))
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(reserved)))
                conn.execute(sql.SQL("DROP SEQUENCE IF EXISTS {}").format(sql.Identifier(seq)))


if __name__ == "__main__":
    unittest.main()
