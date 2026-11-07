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
    if not all(isinstance(v, str) and v.startswith("rku_") for v in
               (users_table, reservations_table, sequence_name)):
        raise ValueError("Only isolated rku_ test objects supported")
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
