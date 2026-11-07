"""Opt-in PostgreSQL rollback tests for shared VIP allocation lock.

Uses disposable *_vip_test database only. Never production.
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

from vip_allocator_prototype import allocate_free_id


@unittest.skipUnless(
    os.getenv("RKU_VIP_TEST_DATABASE_URL") and psycopg,
    "Disposable PostgreSQL VIP database not configured",
)
class VipAllocatorRollbackTests(unittest.TestCase):
    def test_failed_registration_rolls_back_issued_id(self):
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
            with psycopg.connect(url) as conn:
                candidate = allocate_free_id(conn, users, reserved, seq)
                self.assertEqual(candidate, 1)
                conn.rollback()
            with psycopg.connect(url) as conn:
                self.assertEqual(
                    conn.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(users))).fetchone()[0], 0
                )
                next_candidate = allocate_free_id(conn, users, reserved, seq)
                # PostgreSQL sequences are intentionally non-transactional.
                self.assertEqual(next_candidate, 2)
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(users)))
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(reserved)))
                conn.execute(sql.SQL("DROP SEQUENCE IF EXISTS {}").format(sql.Identifier(seq)))


if __name__ == "__main__":
    unittest.main()
