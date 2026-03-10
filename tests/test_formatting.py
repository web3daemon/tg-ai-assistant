import unittest

from src.utils.formatting import render_telegram_html, strip_markup


class FormattingTests(unittest.TestCase):
    def test_render_telegram_html_formats_basic_markup(self) -> None:
        rendered = render_telegram_html("**Жирный** и `код` и *курсив*")
        self.assertIn("<b>Жирный</b>", rendered)
        self.assertIn("<code>код</code>", rendered)
        self.assertIn("<i>курсив</i>", rendered)

    def test_strip_markup_removes_simple_wrappers(self) -> None:
        stripped = strip_markup("**Жирный** и `код`")
        self.assertEqual(stripped, "Жирный и код")


if __name__ == "__main__":
    unittest.main()
