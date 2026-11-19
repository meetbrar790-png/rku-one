"""Non-destructive structural checks for the RKU ONE public homepage.

This suite verifies that the language UI change keeps critical auth and mail
elements present; it does not make requests or touch production accounts.
"""
from html.parser import HTMLParser
from pathlib import Path
import unittest


class HomepageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = {}
        self.forms = set()

    def handle_starttag(self, tag, attrs):
        props = dict(attrs)
        if props.get("id"):
            self.ids[props["id"]] = (tag, props)
            if tag == "form":
                self.forms.add(props["id"])


class FunctionalHomepageStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")
        cls.page = HomepageParser()
        cls.page.feed(cls.source)

    def test_auth_forms_remain_present(self):
        self.assertTrue({"register", "login"}.issubset(self.page.forms))
        for control in ("showLogin", "showRegister", "registerCard", "loginCard"):
            self.assertIn(control, self.page.ids)

    def test_mail_and_digital_card_controls_remain_present(self):
        for control in ("mailPanel", "compose", "inboxBtn", "copyIdBtn", "profileForm", "lookupForm"):
            self.assertIn(control, self.page.ids)

    def test_language_menu_is_separate_from_auth_forms(self):
        self.assertEqual(self.page.ids["languageTrigger"][0], "button")
        self.assertEqual(self.page.ids["languageTrigger"][1].get("type"), "button")
        self.assertIn("hidden", self.page.ids["languagePanel"][1])

    def test_backend_endpoint_is_not_replaced_by_preview(self):
        self.assertIn('const API="https://rku-one-backend.onrender.com";', self.source)
        self.assertNotIn("rku-one-design-preview.onrender.com", self.source)

    def test_user_actions_still_have_handlers(self):
        for marker in (
            'getElementById("login")',
            'getElementById("register")',
            'getElementById("compose")',
            'getElementById("profileForm")',
        ):
            self.assertIn(marker, self.source)


if __name__ == "__main__":
    unittest.main()
