import unittest
from identity_only_connection_request import make_connection_notice, validate_request_payload


class IdentityOnlyConnectionRequestTests(unittest.TestCase):
    def test_fixed_notice(self):
        notice = make_connection_notice(25, 26)
        self.assertEqual(notice.message, 'RKU ID 25 wants to connect with you.')
        self.assertEqual(notice.recipient_rku_id, 26)

    def test_reject_all_sender_content(self):
        forbidden = ('message', 'text', 'photo', 'video', 'attachment', 'link', 'url', 'media', 'sender_rku_id')
        for field in forbidden:
            with self.subTest(field=field):
                self.assertFalse(validate_request_payload({'recipient_rku_id': 26, field: ''}))

    def test_only_recipient_id_accepted(self):
        self.assertTrue(validate_request_payload({'recipient_rku_id': 26}))
        for payload in ({}, {'recipient_rku_id': '26'}, {'recipient_rku_id': True}, {'recipient_rku_id': 0}, None):
            with self.subTest(payload=payload):
                self.assertFalse(validate_request_payload(payload))

    def test_no_self_request_or_invalid_sender(self):
        for sender, receiver in ((25, 25), (0, 26), (True, 26), (25, '26')):
            with self.subTest(sender=sender, receiver=receiver):
                with self.assertRaises(ValueError):
                    make_connection_notice(sender, receiver)


if __name__ == '__main__':
    unittest.main()
