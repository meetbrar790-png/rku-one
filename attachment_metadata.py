"""Private mail attachment metadata schema (not enabled in the live API).

Object bytes belong in a private encrypted object-store bucket, never in the
Render ephemeral filesystem. Message ownership is checked again on every read.
"""
from attachment_policy import MAX_ATTACHMENT_BYTES

ATTACHMENTS_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS mail_attachments (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    message_id BIGINT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    object_key TEXT NOT NULL UNIQUE,
    original_filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes BIGINT NOT NULL CHECK (size_bytes BETWEEN 1 AND 10485760),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT mail_attachments_key_private
      CHECK (object_key LIKE 'mail-attachments/%')
);
CREATE INDEX IF NOT EXISTS idx_mail_attachments_message
    ON mail_attachments(message_id);
"""

# This SELECT must run with an authenticated requester_id; it never returns
# an object key for a user who is not the sender or recipient of the message.
AUTHORIZED_ATTACHMENT_LOOKUP_SQL = """
SELECT a.object_key, a.original_filename, a.mime_type, a.size_bytes,
       m.sender, m.recipient, m.id
FROM mail_attachments AS a
JOIN messages AS m ON m.id = a.message_id
WHERE a.id = %s AND m.id = %s
  AND (m.sender = %s OR m.recipient = %s)
"""

def authorized_attachment_lookup(conn, *, attachment_id: int, message_id: int, requester_id: int):
    """Return metadata only after database-level ownership authorization."""
    if any(type(x) is not int or x < 1 for x in (attachment_id, message_id, requester_id)):
        raise PermissionError("Invalid attachment access")
    row = conn.execute(
        AUTHORIZED_ATTACHMENT_LOOKUP_SQL,
        (attachment_id, message_id, requester_id, requester_id),
    ).fetchone()
    if row is None:
        raise PermissionError("Attachment not found or access denied")
    return row
