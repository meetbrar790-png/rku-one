"""Offline tests for attachment upload failure and orphan cleanup."""
import io
import unittest
from unittest.mock import patch
from fastapi import UploadFile
from api import attachment_upload
from private_attachments import StorageError
import asyncio


class AttachmentUploadCleanupTests(unittest.TestCase):
    def make_file(self):
        return UploadFile(filename="receipt.pdf", file=io.BytesIO(b"%PDF-1.7\n"), headers={"content-type": "application/pdf"})

    def test_metadata_failure_triggers_object_cleanup(self):
        with patch("api.authenticated_id", return_value=1001), \
             patch("api.upload_private", return_value="1001/" + "a" * 48 + ".pdf"), \
             patch("api.save_attachment", side_effect=RuntimeError("database unavailable")), \
             patch("api.delete_private") as cleanup:
            with self.assertRaises(RuntimeError):
                asyncio.run(attachment_upload(self.make_file(), authorization="Bearer mock"))
        cleanup.assert_called_once_with("1001/" + "a" * 48 + ".pdf")

    def test_cleanup_failure_does_not_hide_original_metadata_error(self):
        with patch("api.authenticated_id", return_value=1001), \
             patch("api.upload_private", return_value="1001/" + "a" * 48 + ".pdf"), \
             patch("api.save_attachment", side_effect=RuntimeError("metadata write failed")), \
             patch("api.delete_private", side_effect=StorageError("cleanup failed")):
            with self.assertRaisesRegex(RuntimeError, "metadata write failed"):
                asyncio.run(attachment_upload(self.make_file(), authorization="Bearer mock"))


if __name__ == "__main__":
    unittest.main()
