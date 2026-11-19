"""Static safety checks for the international-language homepage preview.

These do not replace real browser, Android, or translation QA.
"""
from html.parser import HTMLParser
from pathlib import Path
import unittest


class LanguageMarkupParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = {}
        self.options = []
        self._in_option = False
        self._option_value = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids[a["id"]] = (tag, a)
        if tag == "option":
            self._in_option = True
            self._option_value = a.get("value")

    def handle_endtag(self, tag):
        if tag == "option":
            self._in_option = False

    def handle_data(self, data):
        if self._in_option:
            self.options.append((self._option_value, data))


class GlobalLanguageMarkupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")
        cls.parser = LanguageMarkupParser()
        cls.parser.feed(cls.html)

    def test_menu_is_closed_by_default(self):
        tag, attrs = self.parser.ids["languagePanel"]
        self.assertEqual(tag, "div")
        self.assertIn("hidden", attrs)
        self.assertEqual(self.parser.ids["languageTrigger"][1]["aria-expanded"], "false")

    def test_search_is_accessible(self):
        tag, attrs = self.parser.ids["languageSearch"]
        self.assertEqual(tag, "input")
        self.assertEqual(attrs["type"], "search")
        self.assertIn("aria-label", attrs)

    def test_country_choices_and_no_punjabi_option(self):
        codes = [code for code, _ in self.parser.options]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertNotIn("pa", codes)
        for code in ("en", "en-GB", "en-AU", "en-NZ", "en-CA", "en-US", "en-IN", "hi", "zh-CN", "fr", "de", "es"):
            self.assertIn(code, codes)

    def test_partial_translation_is_disclosed(self):
        self.assertIn("Full translation is not yet available.", self.html)
        self.assertIn('previewNotice.style.display=preview?"block":"none"', self.html)

    def test_menu_has_escape_and_outside_click_handlers(self):
        self.assertIn('event.key==="Escape"', self.html)
        self.assertIn('event.target.closest(".language-picker")', self.html)


if __name__ == "__main__":
    unittest.main()
