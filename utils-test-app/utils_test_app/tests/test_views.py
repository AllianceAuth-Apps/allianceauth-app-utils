from django.test import TestCase
from django.utils import translation
from django.utils.html import mark_safe

from app_utils.views import (
    HttpResponseNoContent,
    bootstrap_glyph_html,
    bootstrap_label_html,
    bootstrap_link_button_html,
    humanize_value,
    link_html,
    no_wrap_html,
    yesno_str,
)

MODULE_PATH = "app_utils"
CURRENT_PATH = "utils_test_app.tests.test_all"


class TestHttpResponseNoContent(TestCase):
    def test_can_create_objects(self):
        # when
        res = HttpResponseNoContent()
        # then
        self.assertEqual(res.status_code, 204)
        if hasattr(res, "_headers"):  # Django<3.2
            self.assertNotIn("content-type", res._headers)
        elif hasattr(res, "headers"):  # Django>=3.2
            self.assertNotIn("content-type", res.headers)
        else:
            self.fail("No headers found")


class TestHtmlHelper(TestCase):
    def test_add_no_wrap_html(self):
        expected = '<span class="text-nowrap;">Dummy</span>'
        self.assertEqual(no_wrap_html("Dummy"), expected)

    def test_yesno_str(self):
        with translation.override("en"):
            self.assertEqual(yesno_str(True), "yes")
            self.assertEqual(yesno_str(False), "no")
            self.assertEqual(yesno_str(None), "no")
            self.assertEqual(yesno_str(123), "no")
            self.assertEqual(yesno_str("xxxx"), "no")

    def test_add_bs_label_html(self):
        expected = '<span class="label label-danger">Dummy</span>'
        self.assertEqual(bootstrap_label_html("Dummy", "danger"), expected)

    def test_create_link_html_default(self):
        expected = (
            '<a href="https://www.example.com" target="_blank">' "Example Link</a>"
        )
        self.assertEqual(link_html("https://www.example.com", "Example Link"), expected)

    def test_create_link_html(self):
        expected = '<a href="https://www.example.com">Example Link</a>'
        self.assertEqual(
            link_html("https://www.example.com", "Example Link", False), expected
        )
        expected = (
            '<a href="https://www.example.com">' "<strong>Example Link</strong></a>"
        )
        self.assertEqual(
            link_html(
                "https://www.example.com",
                mark_safe("<strong>Example Link</strong>"),
                False,
            ),
            expected,
        )

    def test_create_bs_button_html_default(self):
        expected = (
            '<a href="https://www.example.com" class="btn btn-info">'
            '<span class="glyphicon glyphicon-example"></span></a>'
        )
        self.assertEqual(
            bootstrap_link_button_html("https://www.example.com", "example", "info"),
            expected,
        )

    def test_create_bs_button_html_disabled(self):
        expected = (
            '<a href="https://www.example.com" class="btn btn-info"'
            ' disabled="disabled">'
            '<span class="glyphicon glyphicon-example"></span></a>'
        )
        self.assertEqual(
            bootstrap_link_button_html(
                "https://www.example.com", "example", "info", True
            ),
            expected,
        )


class TestBootstrapGlyphHtml(TestCase):
    def test_should_return_simply_glyph(self):
        expected = '<span class="glyphicon glyphicon-example"></span>'
        self.assertEqual(bootstrap_glyph_html("example"), expected)


class TestFormatIskValue(TestCase):
    def test_defaults(self):
        self.assertEqual(humanize_value(0.9), "0.90")
        self.assertEqual(humanize_value(1), "1.00")
        self.assertEqual(humanize_value(1.1), "1.10")
        self.assertEqual(humanize_value(1000), "1.00k")
        self.assertEqual(humanize_value(1100), "1.10k")
        self.assertEqual(humanize_value(551100), "551.10k")
        self.assertEqual(humanize_value(1000000), "1.00m")
        self.assertEqual(humanize_value(1000000000), "1.00b")
        self.assertEqual(humanize_value(1000000000000), "1.00t")

    def test_precision(self):
        self.assertEqual(humanize_value(12340000000, 1), "12.3b")
