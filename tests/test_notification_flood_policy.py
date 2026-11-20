import unittest
from notification_flood_policy import Delivery, NotificationContext, NotificationKind, PrivacyMode, delivery_for


class NotificationFloodPolicyTests(unittest.TestCase):
    def test_unknown_request_never_gets_individual_push(self):
        for mode in PrivacyMode:
            for digest in (False, True):
                result = delivery_for(NotificationContext(mode, NotificationKind.UNKNOWN_REQUEST, False, digest))
                self.assertNotEqual(result, Delivery.PUSH)

    def test_protected_digest_only_once_per_scheduling_window(self):
        first = NotificationContext(PrivacyMode.PROTECTED, NotificationKind.UNKNOWN_REQUEST, False)
        second = NotificationContext(PrivacyMode.PROTECTED, NotificationKind.UNKNOWN_REQUEST, False, True)
        self.assertEqual(delivery_for(first), Delivery.DIGEST)
        self.assertEqual(delivery_for(second), Delivery.SILENT_INBOX)

    def test_strict_mode_silences_unknown(self):
        self.assertEqual(delivery_for(NotificationContext(PrivacyMode.STRICT, NotificationKind.UNKNOWN_REQUEST, False)), Delivery.SILENT_INBOX)

    def test_verified_mail_does_not_bypass_consent(self):
        for kind in (NotificationKind.VERIFIED_BUSINESS_MAIL, NotificationKind.VERIFIED_OFFICIAL_MAIL):
            self.assertEqual(delivery_for(NotificationContext(PrivacyMode.PROTECTED, kind, False)), Delivery.SILENT_INBOX)

    def test_allowed_contacts_can_notify(self):
        self.assertEqual(delivery_for(NotificationContext(PrivacyMode.PROTECTED, NotificationKind.TRUSTED_MESSAGE, True)), Delivery.PUSH)

    def test_bad_inputs_fail_closed(self):
        self.assertEqual(delivery_for(None), Delivery.SILENT_INBOX)
        self.assertEqual(delivery_for(NotificationContext('protected', NotificationKind.UNKNOWN_REQUEST, False)), Delivery.SILENT_INBOX)
        self.assertEqual(delivery_for(NotificationContext(PrivacyMode.PROTECTED, NotificationKind.UNKNOWN_REQUEST, 'false')), Delivery.SILENT_INBOX)


if __name__ == '__main__':
    unittest.main()
