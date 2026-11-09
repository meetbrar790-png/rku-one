"""Configuration for a private S3-compatible attachment bucket.

No bucket is provisioned and no upload/download endpoints are enabled here.
Use short-lived, authenticated server-generated grants when implementing access.
"""
from dataclasses import dataclass
from urllib.parse import urlparse

@dataclass(frozen=True)
class PrivateObjectStorageConfig:
    endpoint_url: str
    bucket_name: str
    region: str
    access_key_id: str
    secret_access_key: str
    server_side_encryption: bool = True

    def validate(self) -> None:
        parsed = urlparse(self.endpoint_url)
        if (parsed.scheme != "https" or not parsed.hostname or
                parsed.username is not None or parsed.password is not None or
                parsed.query or parsed.fragment or parsed.path not in ("", "/")):
            raise ValueError("Storage endpoint must be a bare HTTPS URL")
        if not self.bucket_name or len(self.bucket_name) > 63 or not all(
            c.islower() or c.isdigit() or c in ".-" for c in self.bucket_name
        ):
            raise ValueError("Invalid storage bucket name")
        if not self.region or not self.access_key_id or not self.secret_access_key:
            raise ValueError("Missing private storage credentials")
        if self.server_side_encryption is not True:
            raise ValueError("Encryption must be enabled")

def required_storage_environment() -> tuple[str, ...]:
    """Environment variable names only. Never log their values."""
    return (
        "RKU_ATTACHMENTS_S3_ENDPOINT",
        "RKU_ATTACHMENTS_S3_BUCKET",
        "RKU_ATTACHMENTS_S3_REGION",
        "RKU_ATTACHMENTS_S3_ACCESS_KEY_ID",
        "RKU_ATTACHMENTS_S3_SECRET_ACCESS_KEY",
    )
