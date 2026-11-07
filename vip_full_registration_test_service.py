"""Disposable-only full registration allocator.

NOT wired to live registration. Caller provides a transaction and a password
hash; no plaintext passwords are accepted or stored here.
"""
import re
from psycopg import sql

from vip_allocator_prototype import ALLOCATION_LOCK_KEY

def register_test_user(conn, users_table, reservations_table, sequence_name,
                       email, password_hash, *, max_attempts=100):
    dbname = getattr(getattr(conn, "info", None), "dbname", None)
    if not isinstance(dbname, str) or not dbname.endswith("_vip_test"):
        raise ValueError("Disposable *_vip_test database required")
    names = ((users_table, "rku_users_"), (reservations_table, "rku_reserved_"),
             (sequence_name, "rku_seq_"))
    suffixes = []
    for value, prefix in names:
        if not isinstance(value, str) or re.fullmatch(prefix + r"[0-9a-f]{32}", value) is None:
            raise ValueError("Randomly named disposable test objects required")
        suffixes.append(value[len(prefix):])
    if len(set(suffixes)) != 1:
        raise ValueError("Test objects must share a random suffix")
    if not isinstance(email, str) or not email.strip() or len(email) > 254:
        raise ValueError("Valid email required")
    if not isinstance(password_hash, str) or not password_hash:
        raise ValueError("Password hash required")
    if type(max_attempts) is not int or not 1 <= max_attempts <= 10000:
        raise ValueError("Invalid max_attempts")
    normalized = email.strip().lower()
    conn.execute("SELECT pg_advisory_xact_lock(%s)", (ALLOCATION_LOCK_KEY,))
    for _ in range(max_attempts):
        candidate = conn.execute("SELECT nextval(%s::regclass)", (sequence_name,)).fetchone()[0]
        if candidate < 1:
            raise ValueError("Invalid ID")
        blocked = conn.execute(sql.SQL(
            "SELECT EXISTS(SELECT 1 FROM {} WHERE rku_id=%s) "
            "OR EXISTS(SELECT 1 FROM {} WHERE rku_id=%s)"
        ).format(sql.Identifier(users_table), sql.Identifier(reservations_table)),
            (candidate, candidate)).fetchone()[0]
        if not blocked:
            return conn.execute(sql.SQL(
                "INSERT INTO {} (rku_id,email,password_hash) "
                "VALUES (%s,%s,%s) RETURNING rku_id,email"
            ).format(sql.Identifier(users_table)),
                (candidate, normalized, password_hash)).fetchone()
    raise RuntimeError("No free ID within attempt limit")
