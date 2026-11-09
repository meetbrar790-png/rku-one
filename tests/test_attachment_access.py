import unittest
from attachment_access import (
    AttachmentRecord, require_attachment_access,
    new_private_object_key, require_private_storage_configuration,
)

class AttachmentAccessTests(unittest.TestCase):
    def setUp(self):
        self.record = AttachmentRecord("mail-attachments/random", 42, 1002, 1)

    def test_sender_and_recipient_can_access(self):
        for requester in (1, 1002):
            self.assertIsNone(require_attachment_access(self.record, requester_id=requester, message_id=42))

    def test_other_users_and_other_messages_denied(self):
        for requester, message in ((1003, 42), (1, 43), (0, 42), (True, 42), (1, 0)):
            with self.assertRaises(PermissionError):
                require_attachment_access(self.record, requester_id=requester, message_id=message)

    def test_keys_are_opaque_and_unique(self):
        a, b = new_private_object_key(), new_private_object_key()
        self.assertNotEqual(a, b)
        self.assertTrue(a.startswith("mail-attachments/"))
        self.assertNotIn("1002", a)

    def test_private_encrypted_storage_required(self):
        for private, encrypted in ((False, True), (True, False), (False, False)):
            with self.assertRaises(RuntimeError):
                require_private_storage_configuration(bucket_is_private=private, encryption_enabled=encrypted)
        require_private_storage_configuration(bucket_is_private=True, encryption_enabled=True)

if __name__ == "__main__":
    unittest.main()
