"""Private attachment metadata and owner-only retrieval (draft feature)."""
from registration import get_connection


def setup_attachment_table():
    with get_connection() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS private_attachments (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            owner BIGINT NOT NULL REFERENCES users(rku_id),
            object_path TEXT NOT NULL UNIQUE,
            mime_type VARCHAR(40) NOT NULL,
            filename VARCHAR(150) NOT NULL,
            byte_size INTEGER NOT NULL CHECK (byte_size BETWEEN 1 AND 10485760),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_private_attachments_owner ON private_attachments(owner,id DESC)")


def save_attachment(owner, path, mime, filename, size):
    with get_connection() as conn:
        row = conn.execute(
            "INSERT INTO private_attachments(owner,object_path,mime_type,filename,byte_size) "
            "VALUES (%s,%s,%s,%s,%s) RETURNING id",
            (owner, path, mime, filename, size)
        ).fetchone()
    return row[0]


def get_owned_attachment(owner, attachment_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT object_path,mime_type,filename FROM private_attachments "
            "WHERE id=%s AND owner=%s", (attachment_id, owner)
        ).fetchone()
    return row
