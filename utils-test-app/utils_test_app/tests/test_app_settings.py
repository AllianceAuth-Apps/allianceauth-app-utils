from unittest.mock import Mock, patch

from django.test import TestCase

from app_utils.app_settings import clean_setting

MODULE_PATH = "app_utils.app_settings"


class TestCleanSetting(TestCase):
    @patch(MODULE_PATH + ".settings")
    def test_default_if_not_set(self, mock_settings):
        mock_settings.TEST_SETTING_DUMMY = Mock(spec=None)
        result = clean_setting("TEST_SETTING_DUMMY", False)
        self.assertEqual(result, False)

    @patch(MODULE_PATH + ".settings")
    def test_default_if_not_set_for_none(self, mock_settings):
        mock_settings.TEST_SETTING_DUMMY = Mock(spec=None)
        result = clean_setting("TEST_SETTING_DUMMY", None, required_type=int)
        self.assertEqual(result, None)

    @patch(MODULE_PATH + ".settings")
    def test_true_stays_true(self, mock_settings):
        mock_settings.TEST_SETTING_DUMMY = True
        result = clean_setting("TEST_SETTING_DUMMY", False)
        self.assertEqual(result, True)

    @patch(MODULE_PATH + ".settings")
    def test_false_stays_false(self, mock_settings):
        mock_settings.TEST_SETTING_DUMMY = False
        result = clean_setting("TEST_SETTING_DUMMY", False)
        self.assertEqual(result, False)

    @patch(MODULE_PATH + ".settings")
    def test_default_for_invalid_type_bool(self, mock_settings):
        mock_settings.TEST_SETTING_DUMMY = "invalid type"
        result = clean_setting("TEST_SETTING_DUMMY", False)
        self.assertEqual(result, False)

    @patch(MODULE_PATH + ".settings")
    def test_default_for_invalid_type_int(self, mock_settings):
        mock_settings.TEST_SETTING_DUMMY = "invalid type"
        result = clean_setting("TEST_SETTING_DUMMY", 50)
        self.assertEqual(result, 50)

    @patch(MODULE_PATH + ".settings")
    def test_none_allowed_for_type_int(self, mock_settings):
        mock_settings.TEST_SETTING_DUMMY = None
        result = clean_setting("TEST_SETTING_DUMMY", 50)
        self.assertIsNone(result)

    @patch(MODULE_PATH + ".settings")
    def test_default_if_below_minimum_1(self, mock_settings):
        """when setting is below minimum and default is > minium, then use minimum"""
        mock_settings.TEST_SETTING_DUMMY = -5
        result = clean_setting("TEST_SETTING_DUMMY", default_value=50)
        self.assertEqual(result, 0)

    @patch(MODULE_PATH + ".settings")
    def test_default_if_below_minimum_2(self, mock_settings):
        """when setting is below minimum, then use minimum"""
        mock_settings.TEST_SETTING_DUMMY = -50
        result = clean_setting("TEST_SETTING_DUMMY", default_value=50, min_value=-10)
        self.assertEqual(result, -10)

    @patch(MODULE_PATH + ".settings")
    def test_default_if_below_minimum_3(self, mock_settings):
        """when default is None and setting is below minimum, then use minimum"""
        mock_settings.TEST_SETTING_DUMMY = 10
        result = clean_setting(
            "TEST_SETTING_DUMMY", default_value=None, required_type=int, min_value=30
        )
        self.assertEqual(result, 30)

    @patch(MODULE_PATH + ".settings")
    def test_setting_if_above_maximum(self, mock_settings):
        """when setting is above maximum, then use maximum"""
        mock_settings.TEST_SETTING_DUMMY = 100
        result = clean_setting("TEST_SETTING_DUMMY", default_value=10, max_value=50)
        self.assertEqual(result, 50)

    @patch(MODULE_PATH + ".settings")
    def test_default_below_minimum(self, mock_settings):
        """when default is below minimum, then raise exception"""
        mock_settings.TEST_SETTING_DUMMY = 10
        with self.assertRaises(ValueError):
            clean_setting("TEST_SETTING_DUMMY", default_value=10, min_value=50)

    @patch(MODULE_PATH + ".settings")
    def test_default_above_maximum(self, mock_settings):
        """when default is below minimum, then raise exception"""
        mock_settings.TEST_SETTING_DUMMY = 10
        with self.assertRaises(ValueError):
            clean_setting("TEST_SETTING_DUMMY", default_value=100, max_value=50)

    @patch(MODULE_PATH + ".settings")
    def test_default_is_none_needs_required_type(self, mock_settings):
        mock_settings.TEST_SETTING_DUMMY = "invalid type"
        with self.assertRaises(ValueError):
            clean_setting("TEST_SETTING_DUMMY", default_value=None)

    @patch(MODULE_PATH + ".settings")
    def test_when_value_in_choices_return_it(self, mock_settings):
        mock_settings.TEST_SETTING_DUMMY = "bravo"
        result = clean_setting(
            "TEST_SETTING_DUMMY", default_value="alpha", choices=["alpha", "bravo"]
        )
        self.assertEqual(result, "bravo")

    @patch(MODULE_PATH + ".settings")
    def test_when_value_not_in_choices_return_default(self, mock_settings):
        mock_settings.TEST_SETTING_DUMMY = "charlie"
        result = clean_setting(
            "TEST_SETTING_DUMMY", default_value="alpha", choices=["alpha", "bravo"]
        )
        self.assertEqual(result, "alpha")
