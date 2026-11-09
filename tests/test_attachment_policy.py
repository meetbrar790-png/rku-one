import unittest
from attachment_policy import AttachmentMetadata, validate_attachment, MAX_ATTACHMENT_BYTES

class AttachmentPolicyTests(unittest.TestCase):
    def test_valid_pdf_and_image(self):
        for filename, mime in [("file.pdf", "application/pdf"), ("photo.jpg", "image/jpeg"), ("scan.PNG", "image/png")]:
            self.assertIsNone(validate_attachment(AttachmentMetadata(filename, mime, 1024)))

    def test_reject_oversized_or_empty(self):
        for size in [0, -1, MAX_ATTACHMENT_BYTES + 1, True]:
            with self.assertRaises(ValueError):
                validate_attachment(AttachmentMetadata("file.pdf", "application/pdf", size))

    def test_reject_executable_and_mismatched_extension(self):
        for filename, mime in [("evil.exe", "application/octet-stream"), ("fake.pdf", "image/png"), ("../file.pdf", "application/pdf"), ("folder\\file.pdf", "application/pdf")]:
            with self.assertRaises(ValueError):
                validate_attachment(AttachmentMetadata(filename, mime, 123))

if __name__ == "__main__":
    unittest.main()
