"""Disposable SQLite storage for VIP expressions of interest.

This is a local development/test component, NOT a production reservation store.
It never allocates IDs, checks live inventory, or takes payment.
"""
import sqlite3
from vip_interest_request import prepare_interest_request

SCHEMA = """
CREATE TABLE IF NOT EXISTS vip_interest_requests (
  requester_id INTEGER NOT NULL,
  request_key TEXT NOT NULL,
  number_id INTEGER NOT NULL,
  status TEXT NOT NULL CHECK(status='received_not_reserved'),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (requester_id, request_key)
);
"""


def initialize_disposable_store(connection):
    """Only allow ephemeral in-memory SQLite, never a disk or live database."""
    databases = connection.execute("PRAGMA database_list").fetchall()
    if len(databases) != 1 or databases[0][2] != "":
        raise ValueError("In-memory disposable SQLite connection required")
    connection.execute(SCHEMA)


def record_test_interest(connection, number_input, requester_id, request_key):
    """Record a nonbinding request with idempotency; caller owns transaction."""
    draft = prepare_interest_request(number_input, requester_id, request_key)
    if draft["number_id"] > 1000:
        raise ValueError("Not a VIP number")
    initialize_disposable_store(connection)
    existing = connection.execute(
        "SELECT number_id,status FROM vip_interest_requests "
        "WHERE requester_id=? AND request_key=?",
        (requester_id, request_key),
    ).fetchone()
    if existing:
        if existing[0] != draft["number_id"]:
            raise ValueError("Idempotency key reused for a different number")
        return {"number_id": existing[0], "status": existing[1],
                "number_held": False, "payment_collected": False}
    connection.execute(
        "INSERT INTO vip_interest_requests(requester_id,request_key,number_id,status) "
        "VALUES(?,?,?,'received_not_reserved')",
        (requester_id, request_key, draft["number_id"]),
    )
    return {"number_id": draft["number_id"], "status": "received_not_reserved",
            "number_held": False, "payment_collected": False}
