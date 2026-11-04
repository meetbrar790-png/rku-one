"""Private RKU ONE contacts, owned by the authenticated account."""
from registration import get_connection


def setup_contacts():
    with get_connection() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS contacts (
            owner BIGINT NOT NULL REFERENCES users(rku_id),
            contact_id BIGINT NOT NULL REFERENCES users(rku_id),
            nickname VARCHAR(80) NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY(owner, contact_id)
        )""")


def list_contacts(owner):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT contact_id,nickname FROM contacts WHERE owner=%s ORDER BY contact_id LIMIT 500",
            (owner,)
        ).fetchall()
    return [{"rku_id": row[0], "nickname": row[1]} for row in rows]


def save_contact(owner, contact_id, nickname):
    if type(contact_id) is not int or contact_id < 1 or contact_id > 9223372036854775807 or contact_id == owner:
        raise ValueError("Enter another valid RKU ID")
    if not isinstance(nickname, str) or len(nickname) > 80:
        raise ValueError("Contact name must be 80 characters or fewer")
    with get_connection() as conn:
        exists = conn.execute("SELECT 1 FROM users WHERE rku_id=%s", (contact_id,)).fetchone()
        if not exists:
            raise ValueError("RKU ID not found")
        # Serialize additions per owner so the per-account cap is enforced even under concurrent requests.
        conn.execute("SELECT pg_advisory_xact_lock(%s)", (owner,))
        existing = conn.execute("SELECT 1 FROM contacts WHERE owner=%s AND contact_id=%s", (owner, contact_id)).fetchone()
        if not existing:
            total = conn.execute("SELECT COUNT(*) FROM contacts WHERE owner=%s", (owner,)).fetchone()[0]
            if total >= 500:
                raise ValueError("Contact limit reached (500)")
        conn.execute("""INSERT INTO contacts(owner,contact_id,nickname) VALUES(%s,%s,%s)
            ON CONFLICT(owner,contact_id) DO UPDATE SET nickname=EXCLUDED.nickname""",
            (owner, contact_id, nickname.strip()))
    return {"rku_id": contact_id, "nickname": nickname.strip()}


def delete_contact(owner, contact_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM contacts WHERE owner=%s AND contact_id=%s", (owner, contact_id))
    return {"success": True}
