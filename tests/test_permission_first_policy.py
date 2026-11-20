import unittest
from permission_first_policy import Action, ContactStatus, may_contact, transition


class PermissionFirstPolicyTests(unittest.TestCase):
    def test_unknown_cannot_call_video_or_chat(self):
        for action in (Action.VOICE_CALL, Action.VIDEO_CALL, Action.CHAT):
            with self.subTest(action=action):
                self.assertFalse(may_contact(ContactStatus.UNKNOWN, action))

    def test_unknown_may_only_request(self):
        self.assertTrue(may_contact(ContactStatus.UNKNOWN, Action.CONNECTION_REQUEST))
        self.assertFalse(may_contact(ContactStatus.PENDING, Action.CONNECTION_REQUEST))
        self.assertFalse(may_contact(ContactStatus.REJECTED, Action.CONNECTION_REQUEST))
        self.assertFalse(may_contact(ContactStatus.BLOCKED, Action.CONNECTION_REQUEST))

    def test_receiver_can_allow_after_request(self):
        self.assertEqual(transition(ContactStatus.UNKNOWN, 'request'), ContactStatus.PENDING)
        self.assertEqual(transition(ContactStatus.PENDING, 'allow'), ContactStatus.ALLOWED)
        self.assertTrue(may_contact(ContactStatus.ALLOWED, Action.VIDEO_CALL))

    def test_revoke_and_block(self):
        self.assertEqual(transition(ContactStatus.ALLOWED, 'reject'), ContactStatus.REJECTED)
        self.assertFalse(may_contact(ContactStatus.REJECTED, Action.CHAT))
        self.assertEqual(transition(ContactStatus.ALLOWED, 'block'), ContactStatus.BLOCKED)
        with self.assertRaises(ValueError):
            transition(ContactStatus.BLOCKED, 'allow')

    def test_unknown_values_fail_closed(self):
        self.assertFalse(may_contact('allowed', Action.CHAT))
        self.assertFalse(may_contact(ContactStatus.ALLOWED, 'chat'))


if __name__ == '__main__':
    unittest.main()
