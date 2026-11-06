"""Family Cloud policy tests, isolated from all production data."""
import unittest
from family_cloud_policy import validate_family_invitation, can_access_family_file, can_manage_family_members


class FamilyCloudPolicyTests(unittest.TestCase):
    def test_owner_can_invite(self):
        self.assertFalse(validate_family_invitation(1, 2, "owner")["accepted"])

    def test_adult_can_invite(self):
        self.assertEqual(validate_family_invitation(1, 2, "adult")["invitee_id"], 2)

    def test_limited_member_cannot_invite(self):
        with self.assertRaises(PermissionError):
            validate_family_invitation(1, 2, "limited")

    def test_cannot_invite_self(self):
        with self.assertRaises(ValueError):
            validate_family_invitation(1, 1, "owner")

    def test_unaccepted_invitation_cannot_access(self):
        self.assertFalse(can_access_family_file(2, {2: "adult"}, "family", False))

    def test_accepted_member_can_access_family_file(self):
        self.assertTrue(can_access_family_file(2, {2: "limited"}, "family", True))

    def test_nonmember_cannot_access(self):
        self.assertFalse(can_access_family_file(3, {2: "adult"}, "family", True))

    def test_personal_file_stays_private(self):
        self.assertFalse(can_access_family_file(2, {2: "owner"}, "personal", True))

    def test_only_owner_manages_members(self):
        self.assertTrue(can_manage_family_members("owner"))
        self.assertFalse(can_manage_family_members("adult"))

    def test_invalid_member_id_denied(self):
        self.assertFalse(can_access_family_file(0, {0: "owner"}, "family", True))


if __name__ == "__main__":
    unittest.main()
