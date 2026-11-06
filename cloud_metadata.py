"""RKU Cloud metadata schema — design only; not deployed.

No file bytes stored in Postgres. Object storage must be private and
configured before upload/download endpoints are enabled.
"""
CLOUD_FILES_SCHEMA = """
CREATE TABLE IF NOT EXISTS cloud_files (
    file_id UUID PRIMARY KEY,
    owner_id BIGINT NOT NULL REFERENCES users(rku_id),
    object_key TEXT NOT NULL UNIQUE,
    display_name VARCHAR(180) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    size_bytes BIGINT NOT NULL CHECK (size_bytes > 0 AND size_bytes <= 26214400),
    sha256 CHAR(64),
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'ready', 'deleted')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS cloud_files_owner_created
    ON cloud_files(owner_id, created_at DESC);
"""


def metadata_for_owner(owner_id, file_id):
    """Return parameterized lookup instructions; callers must authenticate first."""
    if type(owner_id) is not int or owner_id < 1:
        raise ValueError("Invalid owner ID")
    from uuid import UUID
    try:
        parsed = UUID(str(file_id))
    except (ValueError, TypeError, AttributeError):
        raise ValueError("Invalid file ID") from None
    return (
        "SELECT file_id, object_key, display_name, mime_type, size_bytes, status "
        "FROM cloud_files WHERE owner_id = %s AND file_id = %s AND status = 'ready'",
        (owner_id, parsed),
    )
