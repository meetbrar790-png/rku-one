"""Offline unit tests for private attachment cleanup. No production credentials."""
import unittest
from unittest.mock import patch, MagicMock

from private_attachments import delete_private, StorageError


class CleanupTests(unittest.TestCase):
    @patch("private_attachments.storage_config", return_value=("https://example.supabase.co", "sb_secret_test"))
    @patch("private_attachments.httpx.Client")
    def test_cleanup_uses_private_object_endpoint(self, client_class, config):
        client = client_class.return_value.__enter__.return_value
        client.delete.return_value.raise_for_status.return_value = None
        path = "1001/" + "a" * 48 + ".pdf"
        delete_private(path)
        args, kwargs = client.delete.call_args
        self.assertEqual(args[0], "https://example.supabase.co/storage/v1/object/rku-one-test-attachments/" + path)
        self.assertEqual(kwargs["headers"], {"apikey": "sb_secret_test"})

    def test_cleanup_rejects_invalid_path(self):
        with self.assertRaises(ValueError):
            delete_private("../secret.pdf")

    @patch("private_attachments.storage_config", return_value=("https://example.supabase.co", "sb_secret_test"))
    @patch("private_attachments.httpx.Client")
    def test_cleanup_surfaces_http_failure(self, client_class, config):
        import httpx
        client = client_class.return_value.__enter__.return_value
        client.delete.side_effect = httpx.ConnectError("offline")
        with self.assertRaises(StorageError):
            delete_private("1001/" + "b" * 48 + ".png")


if __name__ == "__main__":
    unittest.main()
