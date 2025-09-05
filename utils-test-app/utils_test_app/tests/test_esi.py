import datetime as dt
from unittest.mock import Mock, patch

import requests
import requests_mock
from celery.exceptions import Retry as CeleryRetry

from app_utils.esi import (
    EsiDailyDowntime,
    EsiErrorLimitExceeded,
    EsiOffline,
    EsiStatus,
    fetch_esi_status,
    retry_task_if_esi_is_down,
)
from app_utils.testing import NoSocketsTestCase

MODULE_PATH = "app_utils.esi"


class TestEsiStatusExceptions(NoSocketsTestCase):
    def test_can_create_exceptions(self):
        # given
        params = [EsiOffline, EsiDailyDowntime, EsiErrorLimitExceeded]
        for exception_class in params:
            with self.subTest(exception=exception_class):
                # when
                obj = exception_class()
                # then
                self.assertIsInstance(obj, exception_class)


class TestEsiErrorLimitExceeded(NoSocketsTestCase):
    def test_can_create_exception_without_params(self):
        # when
        obj = EsiErrorLimitExceeded()
        # then
        self.assertEqual(obj.retry_in, 60)

    def test_can_create_exception_with_param(self):
        # when
        obj = EsiErrorLimitExceeded(42)
        # then
        self.assertEqual(obj.retry_in, 42)
        self.assertIn("ESI error limit has been exceeded", obj.message)


class TestEsiStatus(NoSocketsTestCase):
    def test_create_1(self):
        obj = EsiStatus(True)
        self.assertTrue(obj.is_online)
        self.assertIsNone(obj.error_limit_remain)
        self.assertIsNone(obj.error_limit_reset)

    def test_create_2(self):
        obj = EsiStatus(False, 1)
        self.assertFalse(obj.is_online)
        self.assertIsNone(obj.error_limit_remain)
        self.assertIsNone(obj.error_limit_reset)

    def test_create_3(self):
        obj = EsiStatus(True, None, 1)
        self.assertTrue(obj.is_online)
        self.assertIsNone(obj.error_limit_remain)
        self.assertIsNone(obj.error_limit_reset)

    def test_create_4(self):
        obj = EsiStatus(True, 10, 20)
        self.assertTrue(obj.is_online)
        self.assertEqual(obj.error_limit_remain, 10)
        self.assertEqual(obj.error_limit_reset, 20)

    def test_create_5(self):
        obj = EsiStatus(True, "10", "20")
        self.assertTrue(obj.is_online)
        self.assertEqual(obj.error_limit_remain, 10)
        self.assertEqual(obj.error_limit_reset, 20)

    @patch(MODULE_PATH + ".APPUTILS_ESI_ERROR_LIMIT_THRESHOLD", 25)
    def test_is_ok_should_be_true(self):
        obj = EsiStatus(True, error_limit_remain=30, error_limit_reset=20)
        self.assertTrue(obj.is_ok)

    @patch(MODULE_PATH + ".APPUTILS_ESI_ERROR_LIMIT_THRESHOLD", 25)
    def test_is_ok_should_be_false_1(self):
        obj = EsiStatus(False, error_limit_remain=30, error_limit_reset=20)
        self.assertFalse(obj.is_ok)

    @patch(MODULE_PATH + ".APPUTILS_ESI_ERROR_LIMIT_THRESHOLD", 25)
    def test_is_ok_should_be_false_2(self):
        obj = EsiStatus(True, error_limit_remain=20, error_limit_reset=20)
        self.assertFalse(obj.is_ok)

    @patch(MODULE_PATH + ".APPUTILS_ESI_ERROR_LIMIT_THRESHOLD", 25)
    def test_is_error_limit_exceeded_1(self):
        obj = EsiStatus(True, error_limit_remain=30, error_limit_reset=20)
        self.assertFalse(obj.is_error_limit_exceeded)

    @patch(MODULE_PATH + ".APPUTILS_ESI_ERROR_LIMIT_THRESHOLD", 25)
    def test_is_error_limit_exceeded_2(self):
        obj = EsiStatus(True, error_limit_remain=10, error_limit_reset=20)
        self.assertTrue(obj.is_error_limit_exceeded)

    @patch(MODULE_PATH + ".APPUTILS_ESI_ERROR_LIMIT_THRESHOLD", 25)
    def test_is_error_limit_exceeded_3(self):
        obj = EsiStatus(True, error_limit_remain=10)
        self.assertFalse(obj.is_error_limit_exceeded)

    @patch(MODULE_PATH + ".EsiStatus.MAX_JITTER", 20)
    def test_error_limit_reset_w_jitter_1(self):
        # given
        obj = EsiStatus(True, error_limit_remain=30, error_limit_reset=20)
        # when/then
        for _ in range(1000):
            result = obj.error_limit_reset_w_jitter()
            self.assertGreaterEqual(result, 21)
            self.assertLessEqual(result, 41)

    @patch(MODULE_PATH + ".EsiStatus.MAX_JITTER", 20)
    def test_error_limit_reset_w_jitter_2(self):
        # given
        obj = EsiStatus(True, error_limit_remain=30, error_limit_reset=20)
        # when/then
        for _ in range(1000):
            result = obj.error_limit_reset_w_jitter(10)
            self.assertGreaterEqual(result, 11)
            self.assertLessEqual(result, 31)

    @patch(MODULE_PATH + ".EsiStatus.MAX_JITTER", 20)
    def test_error_limit_reset_w_jitter_3(self):
        # given
        obj = EsiStatus(True)
        # when
        result = obj.error_limit_reset_w_jitter(10)
        # then
        self.assertEqual(result, 0)

    def test_raise_for_status_1(self):
        """When no error condition is met, do nothing"""
        obj = EsiStatus(True, error_limit_remain=99, error_limit_reset=20)
        try:
            obj.raise_for_status()
        except Exception:
            self.fail("raise_for_status() raised Exception unexpectedly!")

    @patch(MODULE_PATH + ".APPUTILS_ESI_ERROR_LIMIT_THRESHOLD", 25)
    def test_raise_for_status_2(self):
        """When ESI is offline, then raise exception"""
        obj = EsiStatus(False, error_limit_remain=99, error_limit_reset=20)
        with self.assertRaises(EsiOffline):
            obj.raise_for_status()

    @patch(MODULE_PATH + ".APPUTILS_ESI_ERROR_LIMIT_THRESHOLD", 25)
    def test_raise_for_status_3(self):
        """When ESI is offline, then raise exception"""
        obj = EsiStatus(
            False, error_limit_remain=99, error_limit_reset=20, is_daily_downtime=True
        )
        with self.assertRaises(EsiDailyDowntime):
            obj.raise_for_status()

    @patch(MODULE_PATH + ".APPUTILS_ESI_ERROR_LIMIT_THRESHOLD", 25)
    def test_should_raise_for_status_3a(self):
        """When ESI is offline, then raise offline type exception"""
        obj = EsiStatus(
            False, error_limit_remain=99, error_limit_reset=20, is_daily_downtime=True
        )
        with self.assertRaises(EsiOffline):
            obj.raise_for_status()

    @patch(MODULE_PATH + ".APPUTILS_ESI_ERROR_LIMIT_THRESHOLD", 25)
    def test_raise_for_status_4(self):
        """When ESI error limit is exceeded, then raise exception"""
        obj = EsiStatus(True, error_limit_remain=15, error_limit_reset=20)
        with self.assertRaises(EsiErrorLimitExceeded):
            obj.raise_for_status()


@requests_mock.Mocker()
class TestFetchEsiStatus(NoSocketsTestCase):
    @patch(MODULE_PATH + ".APPUTILS_ESI_DAILY_DOWNTIME_START", 11.0)
    @patch(MODULE_PATH + ".APPUTILS_ESI_DAILY_DOWNTIME_END", 11.25)
    def test_normal(self, requests_mocker):
        """When ESI is online and header is complete, then report status accordingly"""
        # given
        requests_mocker.register_uri(
            "GET",
            url="https://esi.evetech.net/latest/status/",
            headers={
                "X-Esi-Error-Limit-Remain": "40",
                "X-Esi-Error-Limit-Reset": "30",
            },
            json={
                "players": 12345,
                "server_version": "1132976",
                "start_time": "2017-01-02T12:34:56Z",
            },
        )
        # when
        my_now = dt.datetime(2021, 6, 29, 10, 0)
        with patch(MODULE_PATH + ".now") as mock_now:
            mock_now.return_value = my_now
            status = fetch_esi_status()
        # then
        self.assertTrue(status.is_online)
        self.assertEqual(status.error_limit_remain, 40)
        self.assertEqual(status.error_limit_reset, 30)

    def test_esi_offline(self, requests_mocker):
        """When ESI is offline and header is complete, then report status accordingly"""
        requests_mocker.register_uri(
            "GET",
            url="https://esi.evetech.net/latest/status/",
            headers={
                "X-Esi-Error-Limit-Remain": "40",
                "X-Esi-Error-Limit-Reset": "30",
            },
            status_code=404,  # HTTPNotFound
        )
        status = fetch_esi_status()
        self.assertFalse(status.is_online)
        self.assertEqual(status.error_limit_remain, 40)
        self.assertEqual(status.error_limit_reset, 30)

    def test_esi_vip(self, requests_mocker):
        """When ESI is offline and header is complete, then report status accordingly"""
        requests_mocker.register_uri(
            "GET",
            url="https://esi.evetech.net/latest/status/",
            headers={
                "X-Esi-Error-Limit-Remain": "40",
                "X-Esi-Error-Limit-Reset": "30",
            },
            json={
                "vip": True,
                "players": 12345,
                "server_version": "1132976",
                "start_time": "2017-01-02T12:34:56Z",
            },
        )
        status = fetch_esi_status()
        self.assertFalse(status.is_online)
        self.assertEqual(status.error_limit_remain, 40)
        self.assertEqual(status.error_limit_reset, 30)

    def test_esi_invalid_json(self, requests_mocker):
        """When ESI response JSON can not be parse, then report as offline"""
        requests_mocker.register_uri(
            "GET",
            url="https://esi.evetech.net/latest/status/",
            headers={
                "X-Esi-Error-Limit-Remain": "40",
                "X-Esi-Error-Limit-Reset": "30",
            },
            text="this is not json",
        )
        status = fetch_esi_status()
        self.assertFalse(status.is_online)
        self.assertEqual(status.error_limit_remain, 40)
        self.assertEqual(status.error_limit_reset, 30)

    def test_headers_missing(self, requests_mocker):
        """When header is incomplete, then report error limits with None"""
        requests_mocker.register_uri(
            "GET",
            url="https://esi.evetech.net/latest/status/",
            headers={
                "X-Esi-Error-Limit-Remain": "40",
            },
            json={
                "players": 12345,
                "server_version": "1132976",
                "start_time": "2017-01-02T12:34:56Z",
            },
        )
        status = fetch_esi_status()
        self.assertTrue(status.is_online)
        self.assertIsNone(status.error_limit_remain)
        self.assertIsNone(status.error_limit_reset)

    @patch(MODULE_PATH + ".sleep", lambda x: None)
    def test_retry_on_specific_http_errors_1(self, requests_mocker):
        """When specific HTTP code occurred, then retry until HTTP OK is received"""

        counter = 0

        def response_callback(request, context) -> str:
            nonlocal counter
            counter += 1
            if counter == 2:
                context.status_code = 200
                return {
                    "players": 12345,
                    "server_version": "1132976",
                    "start_time": "2017-01-02T12:34:56Z",
                }
            else:
                context.status_code = 504
                return "[]"

        requests_mocker.register_uri(
            "GET",
            url="https://esi.evetech.net/latest/status/",
            headers={
                "X-Esi-Error-Limit-Remain": "40",
                "X-Esi-Error-Limit-Reset": "30",
            },
            json=response_callback,
        )
        fetch_esi_status()
        self.assertEqual(requests_mocker.call_count, 2)

    @patch(MODULE_PATH + ".sleep", lambda x: None)
    def test_retry_on_specific_http_errors_2(self, requests_mocker):
        """When specific HTTP code occurred, then retry up to maximum retries"""
        requests_mocker.register_uri(
            "GET",
            url="https://esi.evetech.net/latest/status/",
            headers={
                "X-Esi-Error-Limit-Remain": "40",
                "X-Esi-Error-Limit-Reset": "30",
            },
            status_code=504,
        )
        status = fetch_esi_status()
        self.assertEqual(requests_mocker.call_count, 4)
        self.assertFalse(status.is_online)

    @patch(MODULE_PATH + ".sleep", lambda x: None)
    def test_retry_on_specific_http_errors_3(self, requests_mocker):
        """When specific HTTP code occurred, then retry up to maximum retries"""
        requests_mocker.register_uri(
            "GET",
            url="https://esi.evetech.net/latest/status/",
            headers={
                "X-Esi-Error-Limit-Remain": "40",
                "X-Esi-Error-Limit-Reset": "30",
            },
            status_code=502,
        )
        status = fetch_esi_status()
        self.assertEqual(requests_mocker.call_count, 4)
        self.assertFalse(status.is_online)

    @patch(MODULE_PATH + ".sleep", lambda x: None)
    def test_retry_on_specific_http_errors_4(self, requests_mocker):
        """Do not repeat on other HTTP errors"""
        requests_mocker.register_uri(
            "GET",
            url="https://esi.evetech.net/latest/status/",
            headers={
                "X-Esi-Error-Limit-Remain": "40",
                "X-Esi-Error-Limit-Reset": "30",
            },
            status_code=404,
        )
        status = fetch_esi_status()
        self.assertEqual(requests_mocker.call_count, 1)
        self.assertFalse(status.is_online)

    @patch(MODULE_PATH + ".APPUTILS_ESI_DAILY_DOWNTIME_START", 11.0)
    @patch(MODULE_PATH + ".APPUTILS_ESI_DAILY_DOWNTIME_END", 11.25)
    def test_should_report_offline_during_esi_downtime(self, requests_mocker):
        """When during ESI daily downtime, report ESI as offline."""
        # when
        with patch(MODULE_PATH + ".now") as mock_now:
            mock_now.return_value = dt.datetime(
                2021, 6, 29, 11, 1, tzinfo=dt.timezone.utc
            )
            status = fetch_esi_status()
        # then
        self.assertFalse(status.is_online)
        self.assertTrue(status.is_daily_downtime)

    @patch(MODULE_PATH + ".APPUTILS_ESI_DAILY_DOWNTIME_START", 11.0)
    @patch(MODULE_PATH + ".APPUTILS_ESI_DAILY_DOWNTIME_END", 11.25)
    def test_should_ignore_daily_downtime(self, requests_mocker):
        # given
        requests_mocker.register_uri(
            "GET",
            url="https://esi.evetech.net/latest/status/",
            headers={
                "X-Esi-Error-Limit-Remain": "40",
                "X-Esi-Error-Limit-Reset": "30",
            },
            json={
                "players": 12345,
                "server_version": "1132976",
                "start_time": "2017-01-02T12:34:56Z",
            },
        )
        # when
        my_now = dt.datetime(2021, 6, 29, 11, 1)
        with patch(MODULE_PATH + ".now") as mock_now:
            mock_now.return_value = my_now
            status = fetch_esi_status(ignore_daily_downtime=True)
        # then
        self.assertTrue(status.is_online)
        self.assertTrue(status.is_daily_downtime)

    def test_should_report_offline_on_connection_timeout(self, requests_mocker):
        # given
        requests_mocker.register_uri(
            "GET",
            url="https://esi.evetech.net/latest/status/",
            exc=requests.exceptions.ConnectTimeout,
        )
        # when
        status = fetch_esi_status()
        # then
        self.assertFalse(status.is_online)

    def test_should_report_offline_on_connection_error(self, requests_mocker):
        # given
        requests_mocker.register_uri(
            "GET",
            url="https://esi.evetech.net/latest/status/",
            exc=requests.exceptions.ConnectionError,
        )
        # when
        status = fetch_esi_status()
        # then
        self.assertFalse(status.is_online)


class TestRetryTaskIfEsiIsDown(NoSocketsTestCase):
    @patch(MODULE_PATH + ".fetch_esi_status", lambda: EsiStatus(True, 99, 60))
    def test_should_do_nothing_if_esi_is_ok(self):
        # given
        task = Mock()
        # when
        retry_task_if_esi_is_down(task)
        # then
        self.assertFalse(task.retry.called)

    @patch(MODULE_PATH + ".fetch_esi_status", lambda: EsiStatus(False, 99, 60))
    def test_should_retry_when_esi_is_offline(self):
        # given
        task = Mock()
        task.retry.side_effect = CeleryRetry()
        # when
        with self.assertRaises(CeleryRetry):
            retry_task_if_esi_is_down(task)
        # then
        self.assertTrue(task.retry.called)
        _, kwargs = task.retry.call_args
        self.assertTrue(kwargs["countdown"])

    @patch(MODULE_PATH + ".fetch_esi_status", lambda: EsiStatus(True, 1, 60))
    def test_should_retry_if_esi_error_threshold_exceeded(self):
        # given
        task = Mock()
        task.retry.side_effect = CeleryRetry()
        # when
        with self.assertRaises(CeleryRetry):
            retry_task_if_esi_is_down(task)
        # then
        self.assertTrue(task.retry.called)
        _, kwargs = task.retry.call_args
        self.assertGreaterEqual(kwargs["countdown"], 60)
