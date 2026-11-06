"""Profile API route regression tests with mocked storage."""
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from api import ProfileData, my_profile, update_profile, public_profile


class ProfileRouteTests(unittest.TestCase):
    def test_private_profile_requires_login(self):
        with self.assertRaises(HTTPException) as error:
            my_profile(authorization=None)
        self.assertEqual(error.exception.status_code, 401)

    def test_private_profile_uses_authenticated_id(self):
        with patch("api.authenticated_id", return_value=1), patch("api.get_profile", return_value={"name": "Test"}) as get:
            result = my_profile(authorization="Bearer mock")
        self.assertEqual(result["name"], "Test")
        get.assert_called_once_with(1, True)

    def test_public_profile_rejects_invalid_id(self):
        with patch("api.get_profile") as get:
            with self.assertRaises(HTTPException) as error:
                public_profile(0)
        self.assertEqual(error.exception.status_code, 400)
        get.assert_not_called()

    def test_public_profile_queries_public_view(self):
        with patch("api.get_profile", return_value={}) as get:
            public_profile(2)
        get.assert_called_once_with(2)

    def test_profile_update_trims_fields_and_preserves_consent(self):
        with patch("api.authenticated_id", return_value=1), patch("api.save_profile", return_value={"saved": True}) as save:
            result = update_profile(ProfileData(name="  Name  ", company="  Company  ", public=False), authorization="Bearer mock")
        self.assertEqual(result, {"saved": True})
        save.assert_called_once_with(1, "Name", "Company", "", False)

    def test_profile_rejects_insecure_logo_url(self):
        with patch("api.authenticated_id", return_value=1), patch("api.save_profile") as save:
            with self.assertRaises(HTTPException) as error:
                update_profile(ProfileData(logo_url="http://example.com/logo.png"), authorization="Bearer mock")
        self.assertEqual(error.exception.status_code, 400)
        save.assert_not_called()

    def test_profile_rejects_oversized_name(self):
        with patch("api.authenticated_id", return_value=1), patch("api.save_profile") as save:
            with self.assertRaises(HTTPException) as error:
                update_profile(ProfileData(name="x" * 81), authorization="Bearer mock")
        self.assertEqual(error.exception.status_code, 400)
        save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
