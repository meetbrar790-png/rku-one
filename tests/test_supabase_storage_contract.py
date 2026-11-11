"""Isolated Supabase Storage contract tests: no network or real credentials."""
import unittest
from unittest.mock import patch, MagicMock

import private_attachments as storage


class SupabaseStorageContractTests(unittest.TestCase):
    def test_upload_is_private_unique_path_without_upsert(self):
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        with patch.object(storage, "storage_config", return_value=("https://example.supabase.co", "sb_secret_fake")), patch.object(storage.httpx, "Client", return_value=client):
            path = storage.upload_private(1002, b"%PDF-1.7\n", "application/pdf")
        self.assertTrue(path.startswith("1002/"))
        self.assertTrue(path.endswith(".pdf"))
        args, kwargs = client.post.call_args
        self.assertIn("/storage/v1/object/rku-one-test-attachments/1002/", args[0])
        self.assertEqual(kwargs["headers"]["x-upsert"], "false")
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/pdf")
        self.assertEqual(kwargs["content"], b"%PDF-1.7\n")
        client.post.return_value.raise_for_status.assert_called_once()

    def test_download_uses_authenticated_private_endpoint(self):
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        client.get.return_value.content = b"%PDF-1.7\n"
        path = "1002/" + "a" * 48 + ".pdf"
        with patch.object(storage, "storage_config", return_value=("https://example.supabase.co", "sb_secret_fake")), patch.object(storage.httpx, "Client", return_value=client):
            result = storage.download_private(path)
        self.assertEqual(result, b"%PDF-1.7\n")
        self.assertIn("/storage/v1/object/authenticated/rku-one-test-attachments/", client.get.call_args.args[0])

    def test_download_rejects_oversized_response(self):
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        client.get.return_value.content = b"x" * (storage.MAX_BYTES + 1)
        path = "1002/" + "a" * 48 + ".pdf"
        with patch.object(storage, "storage_config", return_value=("https://example.supabase.co", "sb_secret_fake")), patch.object(storage.httpx, "Client", return_value=client):
            with self.assertRaises(storage.StorageError):
                storage.download_private(path)

    def test_http_failure_is_generic_storage_error(self):
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        client.post.return_value.raise_for_status.side_effect = storage.httpx.HTTPError("secret provider details")
        with patch.object(storage, "storage_config", return_value=("https://example.supabase.co", "sb_secret_fake")), patch.object(storage.httpx, "Client", return_value=client):
            with self.assertRaisesRegex(storage.StorageError, "^Private attachment upload failed$"):
                storage.upload_private(1, b"%PDF-1.7\n", "application/pdf")


if __name__ == "__main__":
    unittest.main()
