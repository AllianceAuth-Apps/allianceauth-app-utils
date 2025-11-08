"""Helpers for working with ESI."""

import datetime as dt
import logging
import random
import warnings
from contextlib import contextmanager
from http import HTTPStatus
from typing import Optional

from bravado.exception import HTTPError
from celery import Task

from django.utils.timezone import now
from esi.clients import EsiClientProvider
from esi.exceptions import ESIBucketLimitException, ESIErrorLimitException

from app_utils import __title__, __version__
from app_utils._app_settings import (
    APPUTILS_ESI_DAILY_DOWNTIME_END,
    APPUTILS_ESI_DAILY_DOWNTIME_START,
)
from app_utils.logging import LoggerAddTag

logger = LoggerAddTag(logging.getLogger(__name__), __title__)

_esi = EsiClientProvider(ua_appname="allianceauth-app-utils", ua_version=__version__)


class EsiStatusException(Exception):
    """EsiStatus base exception."""

    def __init__(self, message):
        super().__init__()
        self.message = message


class EsiOffline(EsiStatusException):
    """ESI is offline error."""

    def __init__(self):
        """:meta private:"""
        super().__init__("ESI appears to be offline.")


class EsiDailyDowntime(EsiOffline):
    """ESI is offline due to daily downtime."""

    def __init__(self):
        """:meta private:"""
        super().__init__()
        self.message = "Assuming ESI is offline during it's daily downtime."


class EsiErrorLimitExceeded(EsiStatusException):
    """ESI error limit exceeded error.

    DEPRECATED: This feature no longer works due to recent changes
    of the status endpoint. This class will be removed in future versions.
    """

    def __init__(self, retry_in: float = 60) -> None:
        """:meta private:"""
        warnings.warn(
            "EsiErrorLimitExceeded is deprecated and will be removed in future versions.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        super().__init__("The ESI error limit has been exceeded.")
        self._retry_in = float(retry_in)

    @property
    def retry_in(self) -> float:
        """Time until next error window in seconds."""
        return self._retry_in


class EsiStatus:
    """Represents the current online status of ESI
    and can report whether the current time is within th the planned daily downtime.
    """

    def __init__(
        self,
        is_online: bool,
        error_limit_remain: Optional[int] = None,
        error_limit_reset: Optional[int] = None,
        is_daily_downtime: bool = False,
    ) -> None:
        self._is_online = bool(is_online)
        self._is_daily_downtime = is_daily_downtime
        if error_limit_remain:
            warnings.warn(
                "error_limit_remain is deprecated and will be removed in future versions.",
                category=DeprecationWarning,
                stacklevel=2,
            )
        if error_limit_reset:
            warnings.warn(
                "error_limit_reset is deprecated and will be removed in future versions.",
                category=DeprecationWarning,
                stacklevel=2,
            )

    @property
    def is_ok(self) -> bool:
        """True if ESI was online when this object was created."""
        return self.is_online

    @property
    def is_daily_downtime(self) -> bool:
        """True if status was created during daily downtime time frame."""
        return self._is_daily_downtime

    @property
    def is_online(self) -> bool:
        """True if ESI was online when this object was created."""
        return self._is_online

    @property
    def error_limit_remain(self) -> Optional[int]:
        """Amount of remaining errors in current window.

        DEPRECATED: This feature no longer works due to recent changes
        of the status endpoint. This property will be removed in future versions.
        """
        warnings.warn(
            "error_limit_remain is deprecated and will be removed in future versions.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        return None

    @property
    def error_limit_reset(self) -> Optional[int]:
        """Seconds until current error window resets.

        DEPRECATED: This feature no longer works due to recent changes
        of the status endpoint. This property will be removed in future versions.
        """
        warnings.warn(
            "error_limit_reset is deprecated and will be removed in future versions.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        return None

    @property
    def is_error_limit_exceeded(self) -> bool:
        """True when remain is below the threshold, else False.
        Will also return False if remain/reset are not defined.

        DEPRECATED: This feature no longer works due to recent changes
        of the status endpoint. This property will be removed in future versions.
        """
        warnings.warn(
            "is_error_limit_exceeded is deprecated and will be removed in future versions.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        return False

    def raise_for_status(self):
        """Raise an exception if ESI if offline or the error limit is exceeded."""
        if not self.is_online:
            if self.is_daily_downtime:
                raise EsiDailyDowntime()
            raise EsiOffline()


def fetch_esi_status(ignore_daily_downtime: bool = False) -> EsiStatus:
    """Determine and return the current ESI status.

    Args:
        ignore_daily_downtime: When True will always make a request to ESI \
            even during the daily downtime
    """
    is_daily_downtime = _is_daily_downtime()
    if not ignore_daily_downtime and is_daily_downtime:
        return EsiStatus(is_online=False, is_daily_downtime=True)

    try:
        status = _esi.client.Status.get_status().result(retries=1)
    except ConnectionError:
        logger.warning("Network error when trying to call ESI", exc_info=True)
        return EsiStatus(is_online=False, is_daily_downtime=is_daily_downtime)
    except HTTPError:  # Will usually return http error 502 when offline
        logger.warning("HTTP error when trying to call ESI", exc_info=True)
        return EsiStatus(is_online=False, is_daily_downtime=is_daily_downtime)

    is_online = status.get("vip") is None
    logger.debug("ESI status: is_online: %s", is_online)
    return EsiStatus(is_online=is_online, is_daily_downtime=is_daily_downtime)


def _is_daily_downtime() -> bool:
    """Determine if we currently are in the daily downtime period."""
    downtime_start = _calc_downtime(APPUTILS_ESI_DAILY_DOWNTIME_START)
    downtime_end = _calc_downtime(APPUTILS_ESI_DAILY_DOWNTIME_END)
    return now() >= downtime_start and now() <= downtime_end


def _calc_downtime(hours_float: float) -> dt.datetime:
    hour, minute = _convert_float_hours(hours_float)
    return now().replace(hour=hour, minute=minute)


def _convert_float_hours(hours_float: float) -> tuple:
    """Convert float hours into int hours and int minutes for datetime."""
    hours = int(hours_float)
    minutes = int((hours_float - hours) * 60)
    return hours, minutes


def retry_task_if_esi_is_down(task: Task):
    """Retry current celery task if ESI is not online.

    This function has to be called from inside a celery task!

    Args:
        task: Current celery task from `@shared_task(bind=True)`
    """
    try:
        fetch_esi_status().raise_for_status()
    except EsiOffline as ex:
        countdown = (5 + int(random.uniform(1, 10))) * 60
        logger.warning(
            "ESI appears to be offline. Trying again in %d seconds.", countdown
        )
        raise task.retry(countdown=countdown) from ex


@contextmanager
def retry_task_on_esi_error_and_offline(task: Task, info: str):
    """Context manager that retries a task when the error error limit has been exceeded
    or when ESI appears to be offline.

    DEPRECATED: This context manager is deprecated and will be removed in future version.
    Please switch to retry_task_on_esi_issue.

    Args:
        task: current celery task
        info: text describing what is being retried

    Example:

    .. code-block:: python

        from app_utils.esi import retry_task_on_esi_error_and_offline

        @shared_task(bind=True)
        def my_task(self):
             with retry_task_on_esi_error_and_offline(self, "my_task"):
                # work that might trigger an HTTPError

    '''
    """

    def retry(exc: Exception, retry_after: float, issue: str):
        backoff_jitter = int(random.uniform(2, 4) ** task.request.retries)
        countdown = retry_after + backoff_jitter
        logger.warning(
            "%s: %s. Trying again in %s seconds",
            info,
            issue,
            countdown,
        )
        raise task.retry(countdown=countdown, exc=exc)

    warnings.warn(
        "retry_task_on_esi_error_and_offline() is deprecated "
        "and will be removed in future versions.",
        category=DeprecationWarning,
        stacklevel=2,
    )
    try:
        yield
    except ESIErrorLimitException as exc:
        retry(exc, exc.reset or 60, "ESI error limit exceeded")
    except HTTPError as exc:
        if exc.status_code in {
            HTTPStatus.BAD_GATEWAY,
            HTTPStatus.SERVICE_UNAVAILABLE,
        }:
            retry(exc, 60, "ESI appears to be offline")
        raise exc


@contextmanager
def retry_task_on_esi_issue(task: Task):
    """Retries task when a recoverable ESI issue is encountered
    in the wrapped code block.

    Retries on:
        * Error limit is exceeded
        * Rate limit is exceeded for the current rate limit group
        * Temporary outage (HTTP 502, 503)

    Args:
        task: current celery task

    Example:

    .. code-block:: python

        from app_utils.esi import retry_task_on_esi_error_and_offline

        @shared_task(bind=True)
        def my_task(self):
            ...
            with retry_task_on_esi_error_and_offline(self):
                # Code that makes ESI requests via django-esi

    '''
    """

    def retry(exc: Exception, retry_after: float, issue: str):
        backoff_jitter = int(random.uniform(2, 4) ** task.request.retries)
        countdown = retry_after + backoff_jitter
        logger.warning(
            "%s: %s. Trying again in %s seconds",
            task.name,
            issue,
            countdown,
        )
        raise task.retry(countdown=countdown, exc=exc)

    try:
        yield
    except ESIErrorLimitException as exc:
        retry(exc, exc.reset or 60, "ESI error limit exceeded")
    except ESIBucketLimitException as exc:
        try:
            retry_after = exc.reset or exc.bucket.window
        except AttributeError:
            retry_after = 900
        try:
            slug = exc.bucket.slug
        except AttributeError:
            slug = "?"
        retry(exc, retry_after, f"ESI rate limit exceeded for {slug}")
    except HTTPError as exc:
        if exc.status_code in {
            HTTPStatus.BAD_GATEWAY,
            HTTPStatus.SERVICE_UNAVAILABLE,
        }:
            retry(exc, 60, "ESI appears to be offline")
        raise exc
