"""Pure RKU Cloud upload policy helpers.

No storage credentials, database writes, upload endpoints or automatic backups
are enabled by this module. It can be tested without real user files.
"""
import secrets
from pathlib import PurePath

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
ALLOWED_MIME_TYPES = frozenset({
    "image/jpeg", "image/png", "image/webp",
    "application/pdf", "text/plain",
})


def validate_upload(owner_id, filename, size_bytes, mime_type):
    if type(owner_id) is not int or not 1 <= owner_id <= 9223372036854775807:
        raise ValueError("Valid authenticated RKU ID required")
    if not isinstance(filename, str) or not filename or len(filename) > 180:
        raise ValueError("Invalid filename")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in filename):
        raise ValueError("Invalid filename")
    if "/" in filename or "\\" in filename or filename in (".", ".."):
        raise ValueError("Invalid filename")
    if type(size_bytes) is not int or not 1 <= size_bytes <= MAX_UPLOAD_BYTES:
        raise ValueError("File size exceeds upload policy")
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError("File type is not supported")
    return {"owner_id": owner_id, "filename": filename, "size_bytes": size_bytes, "mime_type": mime_type}


def private_object_key(owner_id):
    if type(owner_id) is not int or not 1 <= owner_id <= 9223372036854775807:
        raise ValueError("Valid authenticated RKU ID required")
    # Never incorporate user-supplied filenames in object keys.
    return f"owners/{owner_id}/{secrets.token_hex(24)}"


def require_owner(authenticated_owner_id, file_owner_id):
    if type(authenticated_owner_id) is not int or type(file_owner_id) is not int or authenticated_owner_id < 1 or file_owner_id < 1:
        raise PermissionError("File access denied")
    if not secrets.compare_digest(str(authenticated_owner_id), str(file_owner_id)):
        raise PermissionError("File access denied")
    return True
