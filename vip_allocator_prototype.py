"""Prototype transactional allocator for disposable PostgreSQL test schemas.

NOT connected to production registration. Caller must have created dedicated
users/reservations tables and a sequence in an isolated database. The same
transaction-scoped advisory lock MUST also be used by any future VIP checkout.
"""
from psycopg import sql

ALLOCATION_LOCK_KEY = 78112026


def allocate_free_id(conn, users_table: str, reservations_table: str, sequence_name: str, *, max_attempts=100):
    """Allocate next non-issued, non-reserved ID in caller's transaction.

    No implicit commit. Sequence gaps on rollback are expected in PostgreSQL.
    Production implementation needs a reviewed migration, authorization,
    audit logging, reservation expiry policy and concurrency tests.
    """
    dbname = getattr(getattr(conn, "info", None), "dbname", None)
    if not isinstance(dbname, str) or not dbname.endswith("_vip_test"):
        raise ValueError("Prototype allocator requires disposable *_vip_test database")
    import re
    expected = (
        (users_table, r"rku_users_[0-9a-f]{32}"),
        (reservations_table, r"rku_reserved_[0-9a-f]{32}"),
        (sequence_name, r"rku_seq_[0-9a-f]{32}"),
    )
    if any(not isinstance(value, str) or re.fullmatch(pattern, value) is None
           for value, pattern in expected):
        raise ValueError("Only randomly named disposable VIP test objects supported")
    suffixes = [value.rsplit("_", 1)[-1] for value, _ in expected]
    if len(set(suffixes)) != 1:
        raise ValueError("VIP test objects must share the same random suffix")
    if not isinstance(max_attempts, int) or isinstance(max_attempts, bool) or not 1 <= max_attempts <= 10000:
        raise ValueError("Invalid max_attempts")
    conn.execute("SELECT pg_advisory_xact_lock(%s)", (ALLOCATION_LOCK_KEY,))
    for _ in range(max_attempts):
        candidate = conn.execute("SELECT nextval(%s::regclass)", (sequence_name,)).fetchone()[0]
        if candidate < 1:
            raise ValueError("Invalid sequence value")
        blocked = conn.execute(
            sql.SQL("SELECT EXISTS (SELECT 1 FROM {} WHERE rku_id=%s) OR "
                    "EXISTS (SELECT 1 FROM {} WHERE rku_id=%s)").format(
                sql.Identifier(users_table), sql.Identifier(reservations_table)
            ),
            (candidate, candidate),
        ).fetchone()[0]
        if not blocked:
            conn.execute(
                sql.SQL("INSERT INTO {} (rku_id) VALUES (%s)").format(sql.Identifier(users_table)),
                (candidate,),
            )
            return candidate
    raise RuntimeError("No free ID found within allocation attempt limit")
