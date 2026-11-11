"""Offline safety checks: no Supabase credentials or production DB needed."""
import os
import unittest
from unittest.mock import patch
from private_attachments import (
    ALLOWED_TYPES, MAX_BYTES, StorageError, new_object_path,
    storage_config, validate_attachment, download_private,
)


class PrivateAttachmentTests(unittest.TestCase):
    def test_unique_unpredictable_owner_paths(self):
        a = new_object_path(1, "application/pdf")
        b = new_object_path(1, "application/pdf")
        self.assertNotEqual(a, b)
        self.assertTrue(a.startswith("1/"))
        self.assertTrue(a.endswith(".pdf"))

    def test_reject_unsupported_type(self):
        with self.assertRaises(ValueError):
            validate_attachment(b"hello", "text/html")

    def test_reject_empty_and_oversize(self):
        with self.assertRaises(ValueError):
            validate_attachment(b"", "application/pdf")
        with self.assertRaises(ValueError):
            validate_attachment(b"%PDF-" + b"x" * MAX_BYTES, "application/pdf")

    def test_reject_mismatched_signature(self):
        with self.assertRaises(ValueError):
            validate_attachment(b"<script>hello</script>", "image/png")

    def test_accept_valid_signatures(self):
        samples = {
            "application/pdf": b"%PDF-1.7\n",
            "image/png": bytes.fromhex("89504e470d0a1a0a") + b"test",
            "image/jpeg": bytes.fromhex("ffd8ff") + b"test",
            "image/webp": b"RIFF1234WEBPtest",
        }
        for mime, data in samples.items():
            with self.subTest(mime=mime):
                validate_attachment(data, mime)

    def test_missing_secret_fails_closed(self):
        with patch.dict(os.environ, {"SUPABASE_URL": "https://example.supabase.co",
                                     "SUPABASE_SECRET_KEY": ""}):
            with self.assertRaises(StorageError):
                storage_config()

    def test_reject_untrusted_download_paths(self):
        for path in ("../secrets", "1/../../other.pdf", "2/example.pdf", "https://evil.test"):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    download_private(path)


if __name__ == "__main__":
    unittest.main()
