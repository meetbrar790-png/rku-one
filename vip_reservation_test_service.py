"""Test-only VIP reservation service; never call on production databases."""
import re
from psycopg import sql
from vip_allocator_prototype import ALLOCATION_LOCK_KEY


def reserve_test_vip(conn, users_table, reservations_table, rku_id, owner_id):
    if not str(getattr(getattr(conn, "info", None), "dbname", "")).endswith("_vip_test"):
        raise ValueError("Disposable *_vip_test database required")
    names = ((users_table, "rku_users_"), (reservations_table, "rku_reserved_"))
    suffixes = []
    for name, prefix in names:
        if not isinstance(name, str) or re.fullmatch(prefix + r"[0-9a-f]{32}", name) is None:
            raise ValueError("Random disposable test table names required")
        suffixes.append(name[len(prefix):])
    if suffixes[0] != suffixes[1]:
        raise ValueError("Test table suffix mismatch")
    if type(rku_id) is not int or rku_id < 1 or type(owner_id) is not int or owner_id < 1:
        raise ValueError("Positive integer IDs required")
    conn.execute("SELECT pg_advisory_xact_lock(%s)", (ALLOCATION_LOCK_KEY,))
    issued = conn.execute(sql.SQL(
        "SELECT EXISTS(SELECT 1 FROM {} WHERE rku_id=%s)"
    ).format(sql.Identifier(users_table)), (rku_id,)).fetchone()[0]
    if issued:
        return False
    inserted = conn.execute(sql.SQL(
        "INSERT INTO {} (rku_id,owner_id) VALUES (%s,%s) "
        "ON CONFLICT (rku_id) DO NOTHING RETURNING rku_id"
    ).format(sql.Identifier(reservations_table)), (rku_id, owner_id)).fetchone()
    return inserted is not None
