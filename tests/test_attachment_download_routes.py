"""Offline authorization checks for private attachment API routes."""
import unittest
from unittest.mock import patch
from fastapi import HTTPException
from api import attachment_download


class AttachmentDownloadRouteTests(unittest.TestCase):
    def test_unrelated_id_is_denied_before_storage_access(self):
        with patch("api.authenticated_id", return_value=9999), \
             patch("api.get_accessible_attachment", return_value=None) as lookup, \
             patch("api.download_private") as storage:
            with self.assertRaises(HTTPException) as error:
                attachment_download(25, authorization="Bearer fake")
        self.assertEqual(error.exception.status_code, 404)
        lookup.assert_called_once_with(9999, 25)
        storage.assert_not_called()

    def test_authorized_recipient_can_download(self):
        row = ("1001/" + "a" * 48 + ".pdf", "application/pdf", "file.pdf")
        with patch("api.authenticated_id", return_value=1002), \
             patch("api.get_accessible_attachment", return_value=row) as lookup, \
             patch("api.download_private", return_value=b"%PDF-1.7\n") as storage:
            response = attachment_download(25, authorization="Bearer fake")
        lookup.assert_called_once_with(1002, 25)
        storage.assert_called_once_with(row[0])
        self.assertEqual(response.body, b"%PDF-1.7\n")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertTrue(response.headers["content-disposition"].startswith("attachment;"))

    def test_invalid_attachment_id_never_reaches_database_or_storage(self):
        with patch("api.authenticated_id", return_value=1001), \
             patch("api.get_accessible_attachment") as lookup, \
             patch("api.download_private") as storage:
            with self.assertRaises(HTTPException) as error:
                attachment_download(0, authorization="Bearer fake")
        self.assertEqual(error.exception.status_code, 404)
        lookup.assert_not_called()
        storage.assert_not_called()


if __name__ == "__main__":
    unittest.main()
