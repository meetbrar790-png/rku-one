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

def deliver(sender, recipient, subject, body):
    with get_connection() as conn:
        row = conn.execute("SELECT rku_id FROM users WHERE rku_id=%s", (recipient,)).fetchone()
        if not row:
            raise ValueError("Recipient ID not found")
        conn.execute("INSERT INTO messages(sender,recipient,subject,body) VALUES (%s,%s,%s,%s)",
                     (sender,recipient,subject,body))

def mailbox(owner, sent=False):
    field = "sender" if sent else "recipient"
    with get_connection() as conn:
        rows = conn.execute("SELECT id,sender,recipient,subject,body,created_at FROM messages WHERE "+field+"=%s ORDER BY id DESC LIMIT 50", (owner,)).fetchall()
    return [{"id":r[0],"from":r[1],"to":r[2],"subject":r[3],"body":r[4],"date":r[5].isoformat()} for r in rows]
