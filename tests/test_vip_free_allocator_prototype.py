"""Disposable PostgreSQL integration test of a *prototype* free-ID allocator.

This is NOT wired into production registration. The test requires the dedicated
RKU_VIP_TEST_DATABASE_URL database (name ending _vip_test) and uses only
randomly named tables and a sequence, all removed afterward.
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
class VipFreeAllocatorPrototypeTests(unittest.TestCase):
    def test_free_registration_skips_reserved_id_and_preserves_id_one(self):
        url = os.environ["RKU_VIP_TEST_DATABASE_URL"]
        with psycopg.connect(url) as conn:
            if not conn.info.dbname.endswith("_vip_test"):
                self.fail("Refusing database not ending in _vip_test")
        suffix = uuid.uuid4().hex
        users, reserved, seq = ("rku_users_" + suffix, "rku_reserved_" + suffix, "rku_seq_" + suffix)
        try:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("CREATE SEQUENCE {} START 1").format(sql.Identifier(seq)))
                conn.execute(sql.SQL("CREATE TABLE {} (rku_id BIGINT PRIMARY KEY)").format(sql.Identifier(users)))
                conn.execute(sql.SQL("CREATE TABLE {} (rku_id BIGINT PRIMARY KEY)").format(sql.Identifier(reserved)))
                conn.execute(sql.SQL("INSERT INTO {} VALUES (1)").format(sql.Identifier(users)))
                conn.execute(sql.SQL("INSERT INTO {} VALUES (2)").format(sql.Identifier(reserved)))
                conn.execute("SELECT nextval(%s::regclass)", (seq,))
                # A shared lock + both checks must be used by every future allocator.
                conn.execute("SELECT pg_advisory_xact_lock(78112026)")
                allocated = None
                for _ in range(10):
                    candidate = conn.execute("SELECT nextval(%s::regclass)", (seq,)).fetchone()[0]
                    exists = conn.execute(
                        sql.SQL("SELECT EXISTS (SELECT 1 FROM {} WHERE rku_id=%s) OR "
                                "EXISTS (SELECT 1 FROM {} WHERE rku_id=%s)").format(
                            sql.Identifier(users), sql.Identifier(reserved)
                        ),
                        (candidate, candidate),
                    ).fetchone()[0]
                    if not exists:
                        conn.execute(
                            sql.SQL("INSERT INTO {} VALUES (%s)").format(sql.Identifier(users)),
                            (candidate,),
                        )
                        allocated = candidate
                        break
                self.assertEqual(allocated, 3)
                self.assertEqual(
                    conn.execute(sql.SQL("SELECT rku_id FROM {} ORDER BY rku_id").format(sql.Identifier(users))).fetchall(),
                    [(1,), (3,)],
                )
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(users)))
                conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(reserved)))
                conn.execute(sql.SQL("DROP SEQUENCE IF EXISTS {}").format(sql.Identifier(seq)))


if __name__ == "__main__":
    unittest.main()
