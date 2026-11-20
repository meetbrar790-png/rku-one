"""Isolated, read-only RKU Numeric ID password authentication prototype.

No production API route, OTP delivery, database migration, or writes.
Existing email login remains untouched.
"""
from pwdlib import PasswordHash

_hasher = PasswordHash.recommended()

def validate_numeric_id(value):
    """Reject reserved/invalid identifiers; IDs must already exist in users."""
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return None
    raw = str(value)
    if not raw.isascii() or not raw.isdecimal() or raw.startswith("0"):
        return None
    number = int(raw)
    return number if 1 <= number <= 9223372036854775807 else None

def verify_numeric_id_password(conn, numeric_id, password):
    """Read-only check; NOT a public login endpoint. Caller must enforce\n    per-ID and per-IP rate limits, generic errors and secure token issuance.\n    """
    number = validate_numeric_id(numeric_id)
    if number is None or not isinstance(password, str) or len(password) > 256:
        return None
    row = conn.execute(
        "SELECT password_hash FROM users WHERE rku_id = %s", (number,)
    ).fetchone()
    if row and _hasher.verify(password, row[0]):
        return {"rku_id": number}
    return None
