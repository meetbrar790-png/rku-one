"""RKU Cloud upload intent policy, not an active upload service.

Returns validated metadata and an opaque key; no credentials, signed URLs,
database writes or file bytes are involved.
"""
from cloud_policy import validate_upload, private_object_key


def prepare_upload_intent(authenticated_owner_id, filename, size_bytes, mime_type):
    validated = validate_upload(authenticated_owner_id, filename, size_bytes, mime_type)
    return {
        **validated,
        "object_key": private_object_key(authenticated_owner_id),
        "status": "pending",
    }


def can_finalize_upload(authenticated_owner_id, pending_owner_id, expected_size, actual_size, expected_sha256, actual_sha256):
    if type(authenticated_owner_id) is not int or type(pending_owner_id) is not int or authenticated_owner_id < 1 or authenticated_owner_id != pending_owner_id:
        return False
    if type(expected_size) is not int or type(actual_size) is not int or expected_size < 1 or expected_size != actual_size:
        return False
    if not isinstance(expected_sha256, str) or not isinstance(actual_sha256, str):
        return False
    if len(expected_sha256) != 64 or len(actual_sha256) != 64:
        return False
    import hmac
    import string
    if any(c not in string.hexdigits for c in expected_sha256 + actual_sha256):
        return False
    return hmac.compare_digest(expected_sha256.lower(), actual_sha256.lower())
