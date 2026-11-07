"""Verify a disposable PostgreSQL connection before running staging tests.

This check performs only read-only identity queries. It must never be used
as permission to run migrations against production.
"""
import os
import psycopg
from staging_db_preflight import assert_disposable_staging_url


def verify_disposable_connection(url: str) -> dict:
    assert_disposable_staging_url(url)
    with psycopg.connect(url, connect_timeout=5) as conn:
        dbname, username, address, port = conn.execute(
            "SELECT current_database(), current_user, inet_server_addr()::text, "
            "inet_server_port()"
        ).fetchone()
        if not dbname.endswith("_vip_test"):
            raise ValueError("Connected database is not disposable")
        if conn.info.dbname != dbname:
            raise ValueError("Connected database identity mismatch")
        if address not in ("127.0.0.1", "::1", None):
            raise ValueError("Connected server is not loopback")
        if not username or port is None:
            raise ValueError("Connected server identity incomplete")
        return {"database": dbname, "user": username, "loopback": True}


if __name__ == "__main__":
    result = verify_disposable_connection(os.environ["RKU_VIP_TEST_DATABASE_URL"])
    print("Verified disposable PostgreSQL connection:", result["database"])
