import unittest
from datetime import datetime, timedelta, timezone
from dataclasses import replace
from access_pass_policy import AccessPass, Permission, authorize


class AccessPassPolicyTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 20, tzinfo=timezone.utc)
        self.record = AccessPass(26, 25, frozenset({Permission.BUSINESS_MAIL}), self.now + timedelta(days=1))

    def allowed(self, record=None, **kwargs):
        params = dict(owner_id=26, sender_id=25, permission=Permission.BUSINESS_MAIL, now=self.now)
        params.update(kwargs)
        return authorize(self.record if record is None else record, **params)

    def test_mail_only_does_not_grant_calls_or_chat(self):
        self.assertTrue(self.allowed())
        for action in (Permission.CHAT, Permission.VOICE_CALL, Permission.VIDEO_CALL):
            self.assertFalse(self.allowed(permission=action))

    def test_wrong_sender_or_owner_denied(self):
        self.assertFalse(self.allowed(sender_id=27))
        self.assertFalse(self.allowed(owner_id=27))

    def test_expiry_and_revocation(self):
        self.assertFalse(self.allowed(now=self.now + timedelta(days=1)))
        self.assertFalse(self.allowed(replace(self.record, revoked=True)))

    def test_bad_timestamp_or_permission_denied(self):
        self.assertFalse(self.allowed(now=self.now.replace(tzinfo=None)))
        self.assertFalse(self.allowed(permission='business_mail'))
        self.assertFalse(self.allowed(replace(self.record, expires_at=self.now.replace(tzinfo=None))))

    def test_no_expiry_is_explicitly_supported(self):
        self.assertTrue(self.allowed(replace(self.record, expires_at=None)))


if __name__ == '__main__':
    unittest.main()
