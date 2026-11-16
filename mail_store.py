from registration import get_connection

def setup_mail():
    with get_connection() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS messages (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            sender BIGINT NOT NULL REFERENCES users(rku_id),
            recipient BIGINT NOT NULL REFERENCES users(rku_id),
            subject VARCHAR(200) NOT NULL,
            body TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_recipient_id ON messages(recipient, id DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender, id DESC)")

def deliver(sender, recipient, subject, body):
    with get_connection() as conn:
        row = conn.execute("SELECT rku_id FROM users WHERE rku_id=%s", (recipient,)).fetchone()
        if not row:
            raise ValueError("Recipient ID not found")
        conn.execute("INSERT INTO messages(sender,recipient,subject,body) VALUES (%s,%s,%s,%s)",
                     (sender,recipient,subject,body))

def mailbox(owner, sent=False, before=None):
    field = "sender" if sent else "recipient"
    if before is not None and (type(before) is not int or before < 1):
        raise ValueError("Invalid mail cursor")
    query = "SELECT id,sender,recipient,subject,body,created_at FROM messages WHERE "+field+"=%s"
    params = [owner]
    if before is not None:
        query += " AND id < %s"
        params.append(before)
    query += " ORDER BY id DESC LIMIT 50"
    with get_connection() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
    message_ids = [r[0] for r in rows]
    attachments = {}
    if message_ids:
        with get_connection() as conn:
            links = conn.execute(
                """SELECT ma.message_id,a.id,a.filename,a.mime_type,a.byte_size
                   FROM message_attachments ma JOIN private_attachments a ON a.id=ma.attachment_id
                   WHERE ma.message_id = ANY(%s)""", (message_ids,)
            ).fetchall()
        for msg_id, att_id, filename, mime, size in links:
            attachments.setdefault(msg_id, []).append(
                {"id": att_id, "filename": filename, "mime": mime, "size": size}
            )
    return [{"id":r[0],"from":r[1],"to":r[2],"subject":r[3],"body":r[4],"date":r[5].isoformat(),
             "attachments":attachments.get(r[0],[])} for r in rows]

def deliver_many(sender, recipients, subject, body, attachment_id=None):
    recipients = list(dict.fromkeys(recipients))
    if not 1 <= len(recipients) <= 25 or any(type(r) is not int or r < 1 for r in recipients):
        raise ValueError("Enter 1 to 25 valid RKU IDs")
    with get_connection() as conn:
        # Serialize sends from this RKU ID to avoid parallel requests bypassing limits.
        conn.execute("SELECT pg_advisory_xact_lock(%s)", (sender,))
        recent = conn.execute("""SELECT COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '1 minute'),
                                        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '1 hour')
                                 FROM messages WHERE sender=%s AND created_at >= NOW() - INTERVAL '1 hour'""", (sender,)).fetchone()
        if recent[0] + len(recipients) > 20 or recent[1] + len(recipients) > 100:
            raise ValueError("Sending limit reached. Please wait before sending more mail.")
        rows = conn.execute("SELECT rku_id FROM users WHERE rku_id = ANY(%s)", (recipients,)).fetchall()
        found = {row[0] for row in rows}
        missing = [r for r in recipients if r not in found]
        if missing:
            raise ValueError("Unknown RKU ID: " + ", ".join(map(str, missing)))
        if attachment_id is not None:
            owned = conn.execute(
                "SELECT 1 FROM private_attachments WHERE id=%s AND owner=%s",
                (attachment_id, sender)
            ).fetchone()
            if not owned:
                raise ValueError("Attachment not found or not owned by sender")
        for recipient in recipients:
            row = conn.execute(
                "INSERT INTO messages(sender,recipient,subject,body) VALUES (%s,%s,%s,%s) RETURNING id",
                (sender,recipient,subject,body)
            ).fetchone()
            if attachment_id is not None:
                conn.execute(
                    "INSERT INTO message_attachments(message_id,attachment_id) VALUES (%s,%s)",
                    (row[0],attachment_id)
                )
    return len(recipients)
