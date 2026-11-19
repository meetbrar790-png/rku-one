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
            'send("login"',
            'send("register"',
            'getElementById("compose")',
            'getElementById("profileForm")',
        ):
            self.assertIn(marker, self.source)


    def test_approved_design_has_four_feature_cards_and_globe(self):
        self.assertEqual(self.source.count('class="intro-item"'), 4)
        self.assertIn('class="trust-strip"', self.source)
        self.assertIn('/* Approved white/blue reference:', self.source)
        self.assertIn('content:"🌐"', self.source)

    def test_hero_actions_point_to_real_auth_tabs(self):
        for hero_id, target_id in (
            ("heroRegister", "showRegister"),
            ("heroLogin", "showLogin"),
        ):
            self.assertEqual(self.page.ids[hero_id][0], "a")
            self.assertEqual(self.page.ids[hero_id][1].get("href"), "#authTabs")
            self.assertIn('getElementById("'+hero_id+'").addEventListener("click"', self.source)
            self.assertIn('getElementById("'+target_id+'").click()', self.source)

    def test_vip_selector_is_request_only_and_reserved_ids_protected(self):
        for marker in ('id="vip-numbers"', 'id="vipChoiceForm"', 'id="vipChoiceInput"', 'id="vipChoiceResult"'):
            self.assertIn(marker, self.source)
        self.assertIn("n===1||n===11", self.source)
        self.assertIn("No number has been held or purchased.", self.source)
        self.assertIn("VIP payments are closed.", self.source)
        self.assertIn("<strong>13</strong><small>USD $4,999", self.source)
        self.assertIn("<strong>786</strong><small>USD $4,999", self.source)
        self.assertIn("USD $9,999 · Availability unverified", self.source)
        self.assertIn("USD $7,777 · Availability unverified", self.source)
        self.assertNotIn("<strong>1</strong><small>", self.source)
        self.assertNotIn("<strong>11</strong><small>", self.source)
        self.assertNotIn("Company IDs 1 and 11 are excluded from sale.", self.source)
        self.assertNotIn('id="vipCheckout"', self.source)

    def test_vip_catalogue_hidden_until_crown_clicked(self):
        self.assertIn('id="vip-numbers" class="vip-footer vip-catalogue" hidden', self.source)
        self.assertIn('data-vip-toggle aria-controls="vip-numbers" aria-expanded="false"', self.source)
        self.assertIn('class="vip-hero-action"', self.source)
        self.assertIn('id="vipClose"', self.source)
        self.assertIn('catalogue.hidden=!open', self.source)
        self.assertIn('if(location.hash==="#vip-numbers")setOpen(true)', self.source)
        self.assertIn("VIP payments are closed.", self.source)

if __name__ == "__main__":
    unittest.main()
