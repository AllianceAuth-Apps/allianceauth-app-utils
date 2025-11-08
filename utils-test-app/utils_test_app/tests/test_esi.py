import datetime as dt
from unittest.mock import Mock, patch

from bravado.exception import HTTPError
from celery import Task
from celery.exceptions import Retry as CeleryRetry

from esi.exceptions import ESIBucketLimitException, ESIErrorLimitException
from esi.rate_limiting import ESIRateLimitBucket

from app_utils.esi import (
    EsiDailyDowntime,
    EsiErrorLimitExceeded,
    EsiOffline,
    EsiStatus,
    fetch_esi_status,
    retry_task_if_esi_is_down,
    retry_task_on_esi_error_and_offline,
)
from app_utils.esi_testing import EsiClientStub, EsiEndpoint, build_http_error
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

    def test_create_2(self):
        obj = EsiStatus(False, 1)
        self.assertFalse(obj.is_online)

    def test_create_3(self):
        obj = EsiStatus(True, None, 1)
        self.assertTrue(obj.is_online)

    def test_create_4(self):
        obj = EsiStatus(True, 10, 20)
        self.assertTrue(obj.is_online)

    def test_create_5(self):
        obj = EsiStatus(True, "10", "20")
        self.assertTrue(obj.is_online)

    def test_is_ok_should_be_true(self):
        obj = EsiStatus(True, error_limit_remain=30, error_limit_reset=20)
        self.assertTrue(obj.is_ok)

    def test_is_ok_should_be_false_1(self):
        obj = EsiStatus(False, error_limit_remain=30, error_limit_reset=20)
        self.assertFalse(obj.is_ok)

    def test_raise_for_status_1(self):
        """When no error condition is met, do nothing"""
        obj = EsiStatus(True, error_limit_remain=99, error_limit_reset=20)
        try:
            obj.raise_for_status()
        except Exception:
            self.fail("raise_for_status() raised Exception unexpectedly!")

    def test_raise_for_status_2(self):
        """When ESI is offline, then raise exception"""
        obj = EsiStatus(False, error_limit_remain=99, error_limit_reset=20)
        with self.assertRaises(EsiOffline):
            obj.raise_for_status()

    def test_raise_for_status_3(self):
        """When ESI is offline, then raise exception"""
        obj = EsiStatus(
            False, error_limit_remain=99, error_limit_reset=20, is_daily_downtime=True
        )
        with self.assertRaises(EsiDailyDowntime):
            obj.raise_for_status()

    def test_should_raise_for_status_3a(self):
        """When ESI is offline, then raise offline type exception"""
        obj = EsiStatus(
            False, error_limit_remain=99, error_limit_reset=20, is_daily_downtime=True
        )
        with self.assertRaises(EsiOffline):
            obj.raise_for_status()


@patch(MODULE_PATH + "._esi")
class TestFetchEsiStatus(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        return super().setUpClass()

    @patch(MODULE_PATH + ".APPUTILS_ESI_DAILY_DOWNTIME_START", 11.0)
    @patch(MODULE_PATH + ".APPUTILS_ESI_DAILY_DOWNTIME_END", 11.25)
    def test_should_report_online_when_online(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub(
            testdata={
                "Status": {
                    "get_status": {
                        "players": 12345,
                        "server_version": "1132976",
                        "start_time": "2017-01-02T12:34:56Z",
                    }
                }
            },
            endpoints=[EsiEndpoint("Status", "get_status")],
        )
        # when
        my_now = dt.datetime(2021, 6, 29, 10, 0)
        with patch(MODULE_PATH + ".now") as mock_now:
            mock_now.return_value = my_now
            status = fetch_esi_status()
        # then
        self.assertTrue(status.is_online)
        self.assertIsNone(status.error_limit_remain)
        self.assertIsNone(status.error_limit_reset)

    def test_should_report_offline_when_in_vip_mode(self, mock_esi):
        mock_esi.client = EsiClientStub(
            testdata={
                "Status": {
                    "get_status": {
                        "vip": True,
                        "players": 0,
                        "server_version": "1132976",
                        "start_time": "2017-01-02T12:34:56Z",
                    }
                }
            },
            endpoints=[EsiEndpoint("Status", "get_status")],
        )
        status = fetch_esi_status()
        self.assertFalse(status.is_online)
        self.assertIsNone(status.error_limit_remain)
        self.assertIsNone(status.error_limit_reset)

    @patch(MODULE_PATH + ".APPUTILS_ESI_DAILY_DOWNTIME_START", 11.0)
    @patch(MODULE_PATH + ".APPUTILS_ESI_DAILY_DOWNTIME_END", 11.25)
    def test_should_report_offline_during_esi_downtime(self, mock_esi):
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
    def test_should_ignore_daily_downtime(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub(
            testdata={
                "Status": {
                    "get_status": {
                        "players": 12345,
                        "server_version": "1132976",
                        "start_time": "2017-01-02T12:34:56Z",
                    }
                }
            },
            endpoints=[EsiEndpoint("Status", "get_status")],
        )
        # when
        my_now = dt.datetime(2021, 6, 29, 11, 1)
        with patch(MODULE_PATH + ".now") as mock_now:
            mock_now.return_value = my_now
            status = fetch_esi_status(ignore_daily_downtime=True)
        # then
        self.assertTrue(status.is_online)
        self.assertTrue(status.is_daily_downtime)

    def test_should_report_offline_on_server_error(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub(
            testdata={
                "Status": {
                    "get_status": {
                        "players": 12345,
                        "server_version": "1132976",
                        "start_time": "2017-01-02T12:34:56Z",
                    }
                }
            },
            endpoints=[EsiEndpoint("Status", "get_status")],
            http_error=502,
        )
        # when
        status = fetch_esi_status()
        # then
        self.assertFalse(status.is_online)

    def test_should_report_offline_on_connection_error(self, mock_esi):
        # given
        mock_esi.client.Status.get_status.side_effect = ConnectionError
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


class TestRetryTaskOnEsiIssues(NoSocketsTestCase):
    def test_should_complete_normally_when_no_issue(self):
        task = Mock(spec=Task)
        with retry_task_on_esi_error_and_offline(task):
            pass

    def test_should_retry_when_esi_is_offline_1(self):
        task = Mock(spec=Task)
        task.name = "task_name"
        task.request.retries = 1
        task.retry.side_effect = CeleryRetry
        with self.assertRaises(CeleryRetry):
            with retry_task_on_esi_error_and_offline(task):
                raise build_http_error(502)

    def test_should_retry_when_esi_is_offline_2(self):
        task = Mock(spec=Task)
        task.request.retries = 1
        task.retry.side_effect = CeleryRetry
        with self.assertRaises(CeleryRetry):
            with retry_task_on_esi_error_and_offline(task):
                raise build_http_error(503)

    def test_should_retry_when_error_limit_is_exceeded(self):
        task = Mock(spec=Task)
        task.request.retries = 1
        task.retry.side_effect = CeleryRetry
        with self.assertRaises(CeleryRetry):
            with retry_task_on_esi_error_and_offline(task):
                raise ESIErrorLimitException(reset=30)

    def test_should_retry_when_rate_limit_is_exceeded(self):
        task = Mock(spec=Task)
        task.request.retries = 1
        task.retry.side_effect = CeleryRetry
        bucket = Mock(spec=ESIRateLimitBucket)
        bucket.slug = "bucket-slug"
        bucket.window = 300
        with self.assertRaises(CeleryRetry):
            with retry_task_on_esi_error_and_offline(task):
                raise ESIBucketLimitException(bucket=bucket, reset=30)

    def test_should_reraise_other_http_errors(self):
        task = Mock(spec=Task)
        task.request.retries = 1
        task.retry.side_effect = CeleryRetry

        with self.assertRaises(HTTPError):
            with retry_task_on_esi_error_and_offline(task):
                raise build_http_error(400)
