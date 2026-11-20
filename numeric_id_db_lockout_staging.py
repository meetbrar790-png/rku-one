"""Staging-only PostgreSQL-backed numeric-ID failure tracking.

Not wired to a public route. The caller must run these functions within ONE
transaction, with the per-ID advisory lock acquired first. No schema is created
or modified by importing this module.
"""
from datetime import datetime, timezone
from numeric_id_lockout_policy import LoginFailureState, is_blocked, record_failed_attempt


def _lock(conn, numeric_id):
    if isinstance(numeric_id, bool) or not isinstance(numeric_id, int) or not 1 <= numeric_id <= 9223372036854775807:
        raise ValueError("Invalid numeric ID")
    # Namespace this lock separately from free/VIP allocation locks.
    conn.execute("SELECT pg_advisory_xact_lock(%s, %s)", (27182, numeric_id % 2147483647))


def load_failure_state(conn, numeric_id):
    """Caller must already hold the per-ID advisory transaction lock."""
    row = conn.execute(
        "SELECT failures, first_failure, blocked_until FROM numeric_login_failures WHERE rku_id=%s",
        (numeric_id,),
    ).fetchone()
    return LoginFailureState(*row) if row else LoginFailureState()


def check_blocked(conn, numeric_id, now):
    """Read under a transaction-scoped lock; returns current block status."""
    _lock(conn, numeric_id)
    return is_blocked(load_failure_state(conn, numeric_id), now)


def record_failure(conn, numeric_id, now):
    """Atomically record failure within caller-owned transaction.

    Must not be used as an alternative to separate IP-based rate limiting.
    """
    _lock(conn, numeric_id)
    next_state = record_failed_attempt(load_failure_state(conn, numeric_id), now)
    conn.execute(
        "INSERT INTO numeric_login_failures (rku_id, failures, first_failure, blocked_until) "
        "VALUES (%s,%s,%s,%s) ON CONFLICT (rku_id) DO UPDATE SET "
        "failures=EXCLUDED.failures, first_failure=EXCLUDED.first_failure, "
        "blocked_until=EXCLUDED.blocked_until",
        (numeric_id, next_state.failures, next_state.first_failure, next_state.blocked_until),
    )
    return next_state


def clear_failure_after_success(conn, numeric_id):
    """Only call after a verified password, in the same locked transaction."""
    _lock(conn, numeric_id)
    conn.execute("DELETE FROM numeric_login_failures WHERE rku_id=%s", (numeric_id,))
