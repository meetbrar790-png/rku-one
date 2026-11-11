"""Private Supabase Storage helpers for RKU ONE mail attachments.

Server-side only. Never expose SUPABASE_SECRET_KEY to browsers or logs.
This module does not enable routes or alter production data.
"""
import os
import re
import secrets
from urllib.parse import quote

import httpx

BUCKET = "rku-one-test-attachments"
MAX_BYTES = 10 * 1024 * 1024
ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
}
PROJECT_RE = re.compile(r"^https://[a-z0-9-]+\.supabase\.co$")


class StorageError(Exception):
    pass


def storage_config():
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SECRET_KEY", "")
    if not PROJECT_RE.fullmatch(url) or not key.startswith("sb_secret_"):
        raise StorageError("Private attachment storage is not configured")
    return url, key


def new_object_path(owner_id: int, mime: str) -> str:
    if owner_id < 1 or mime not in ALLOWED_TYPES:
        raise ValueError("Invalid owner or attachment type")
    return f"{owner_id}/{secrets.token_hex(24)}{ALLOWED_TYPES[mime]}"


def validate_attachment(content: bytes, mime: str):
    if mime not in ALLOWED_TYPES:
        raise ValueError("Unsupported attachment type")
    if not content or len(content) > MAX_BYTES:
        raise ValueError("Attachment must be between 1 byte and 10 MB")
    signatures = {
        "image/jpeg": content.startswith(bytes.fromhex("ffd8ff")),
        "image/png": content.startswith(bytes.fromhex("89504e470d0a1a0a")),
        "image/webp": content.startswith(b"RIFF") and content[8:12] == b"WEBP",
        "application/pdf": content.startswith(b"%PDF-"),
    }
    if not signatures[mime]:
        raise ValueError("File content does not match declared type")


def _headers(key: str):
    return {"apikey": key, "Authorization": f"Bearer {key}"}


def upload_private(owner_id: int, content: bytes, mime: str) -> str:
    """Upload a validated file. Caller must authenticate owner and record ownership."""
    validate_attachment(content, mime)
    url, key = storage_config()
    path = new_object_path(owner_id, mime)
    endpoint = f"{url}/storage/v1/object/{BUCKET}/{quote(path, safe='/')}"
    try:
        with httpx.Client(timeout=30, follow_redirects=False) as client:
            response = client.post(endpoint, headers={**_headers(key), "Content-Type": mime, "x-upsert": "false"}, content=content)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise StorageError("Private attachment upload failed") from exc
    return path


def download_private(path: str) -> bytes:
    """Only call AFTER verifying the requesting user's access in the mail database."""
    if not re.fullmatch(r"[1-9][0-9]*/[a-f0-9]{48}\.(jpg|png|webp|pdf)", path):
        raise ValueError("Invalid object path")
    url, key = storage_config()
    endpoint = f"{url}/storage/v1/object/authenticated/{BUCKET}/{quote(path, safe='/')}"
    try:
        with httpx.Client(timeout=30, follow_redirects=False) as client:
            response = client.get(endpoint, headers=_headers(key))
            response.raise_for_status()
            if len(response.content) > MAX_BYTES:
                raise StorageError("Attachment exceeds download limit")
            return response.content
    except httpx.HTTPError as exc:
        raise StorageError("Private attachment download failed") from exc
