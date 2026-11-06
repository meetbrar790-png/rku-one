"""Validate private object-storage configuration before enabling cloud uploads.

No network calls or storage operations are performed here.
"""
from urllib.parse import urlparse


def validate_storage_configuration(config):
    required = ("RKU_STORAGE_ENDPOINT", "RKU_STORAGE_BUCKET", "RKU_STORAGE_ACCESS_KEY", "RKU_STORAGE_SECRET_KEY")
    if not isinstance(config, dict) or any(not isinstance(config.get(key), str) or not config[key].strip() for key in required):
        raise ValueError("Private storage configuration is incomplete")
    endpoint = config["RKU_STORAGE_ENDPOINT"].strip()
    parsed = urlparse(endpoint)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/"):
        raise ValueError("Storage endpoint must be a private HTTPS service endpoint")
    bucket = config["RKU_STORAGE_BUCKET"].strip()
    if not 3 <= len(bucket) <= 63 or not all(c.islower() or c.isdigit() or c in ".-" for c in bucket) or bucket[0] in ".-" or bucket[-1] in ".-":
        raise ValueError("Invalid storage bucket name")
    if len(config["RKU_STORAGE_ACCESS_KEY"]) < 8 or len(config["RKU_STORAGE_SECRET_KEY"]) < 16:
        raise ValueError("Invalid storage credentials")
    # Deliberately return no credentials to prevent accidental logging.
    return {"endpoint": endpoint, "bucket": bucket, "configured": True}
