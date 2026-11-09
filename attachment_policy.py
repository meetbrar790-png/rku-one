"""Attachment validation policy. No uploads or public URLs are enabled yet.

Storage must be private; downloads must authorize the sender or recipient.
Do not store attachment bytes in PostgreSQL or Render's ephemeral filesystem.
"""
from dataclasses import dataclass

MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
MAX_ATTACHMENTS_PER_MESSAGE = 5
ALLOWED_MIME_TYPES = frozenset({
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "text/plain",
})
ALLOWED_EXTENSIONS = {
    "application/pdf": frozenset({".pdf"}),
    "image/jpeg": frozenset({".jpg", ".jpeg"}),
    "image/png": frozenset({".png"}),
    "image/webp": frozenset({".webp"}),
    "text/plain": frozenset({".txt"}),
}

@dataclass(frozen=True)
class AttachmentMetadata:
    filename: str
    mime_type: str
    size_bytes: int


def validate_attachment(metadata: AttachmentMetadata) -> None:
    """Validate declared metadata; content sniffing and scanning are also required."""
    from pathlib import PurePath
    if not isinstance(metadata.filename, str) or not metadata.filename:
        raise ValueError("Attachment filename required")
    if len(metadata.filename) > 150 or "/" in metadata.filename or "\\" in metadata.filename:
        raise ValueError("Invalid attachment filename")
    if metadata.filename in {".", ".."} or PurePath(metadata.filename).name != metadata.filename:
        raise ValueError("Invalid attachment filename")
    if metadata.mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError("Unsupported attachment type")
    suffix = PurePath(metadata.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS[metadata.mime_type]:
        raise ValueError("Attachment extension does not match type")
    if type(metadata.size_bytes) is not int or not 1 <= metadata.size_bytes <= MAX_ATTACHMENT_BYTES:
        raise ValueError("Attachment must be between 1 byte and 10 MiB")
