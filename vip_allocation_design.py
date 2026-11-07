"""Proposed SQL primitives for a future transactional VIP allocator.

This module is deliberately NOT imported by registration.py or api.py.
No schema migration or production allocation is performed.
"""
from psycopg import sql

# A single advisory transaction lock must be used by BOTH registration
# and VIP checkout before any allocation. Lock alone is insufficient:
# availability must be checked and enforced inside the same transaction.
ALLOCATION_LOCK_SQL = "SELECT pg_advisory_xact_lock(78112026)"

# Reference DDL only. Applying it alone does NOT reserve any number.
VIP_RESERVATION_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS vip_number_reservations (
    rku_id BIGINT PRIMARY KEY CHECK (rku_id > 0),
    state TEXT NOT NULL CHECK (state IN ('reserved', 'allocated', 'cancelled')),
    reservation_key UUID NOT NULL UNIQUE,
    reserved_for BIGINT REFERENCES users(rku_id),
    reserved_until TIMESTAMPTZ,
    payment_reference TEXT UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""


def proposed_reservation_insert_sql():
    """A conflict-safe insert shape for isolated tests; not a full allocator."""
    return sql.SQL(
        "INSERT INTO vip_number_reservations "
        "(rku_id, state, reservation_key) VALUES (%s, 'reserved', %s) "
        "ON CONFLICT (rku_id) DO NOTHING RETURNING rku_id"
    )
