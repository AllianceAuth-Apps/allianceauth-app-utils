import datetime as dt
import logging
import random
from time import sleep
from typing import Optional

import requests

from django.utils.timezone import now

from app_utils.logging import LoggerAddTag

from . import __title__, __version__
from ._app_settings import (
    APPUTILS_ESI_DAILY_DOWNTIME_END,
    APPUTILS_ESI_DAILY_DOWNTIME_START,
    APPUTILS_ESI_ERROR_LIMIT_THRESHOLD,
)

logger = LoggerAddTag(logging.getLogger(__name__), __title__)


class EsiStatusException(Exception):
    """EsiStatus base exception."""

    def __init__(self, message):
        super().__init__()
        self.message = message


class EsiOffline(EsiStatusException):
    """ESI is offline error."""

    def __init__(self):
        super().__init__("ESI appears to be offline.")


class EsiErrorLimitExceeded(EsiStatusException):
    """ESI error limit exceeded error."""

    def __init__(self, retry_in: float) -> None:
        super().__init__("The ESI error limit has been exceeded.")
        self._retry_in = float(retry_in)

    @property
    def retry_in(self) -> float:
        """Time until next error window in seconds."""
        return self._retry_in


class EsiStatus:
    """Current status of ESI (immutable)."""

    MAX_JITTER = 20

    def __init__(
        self,
        is_online: bool,
        error_limit_remain: int = None,
        error_limit_reset: int = None,
    ) -> None:
        self._is_online = bool(is_online)
        if error_limit_remain is None or error_limit_reset is None:
            self._error_limit_remain = None
            self._error_limit_reset = None
        else:
            self._error_limit_remain = int(error_limit_remain)
            self._error_limit_reset = int(error_limit_reset)

    @property
    def is_ok(self) -> bool:
        """True if ESI is online and below error limit, else False."""
        return self.is_online and not self.is_error_limit_exceeded

    @property
    def is_online(self) -> bool:
        """True if ESI is online, else False."""
        return self._is_online

    @property
    def error_limit_remain(self) -> Optional[int]:
        """Amount of remaining errors in current window."""
        return self._error_limit_remain

    @property
    def error_limit_reset(self) -> Optional[int]:
        """Seconds until current error window resets."""
        return self._error_limit_reset

    @property
    def is_error_limit_exceeded(self) -> bool:
        """True when remain is below the threshold, else False.

        Will also return False if remain/reset are not defined
        """
        return bool(
            self.error_limit_remain
            and self.error_limit_reset
            and self.error_limit_remain <= APPUTILS_ESI_ERROR_LIMIT_THRESHOLD
        )

    def error_limit_reset_w_jitter(self, max_jitter: int = None) -> int:
        """Calc seconds to retry in order to reach next error window incl. jitter."""
        if self.error_limit_reset is None:
            return 0
        if not max_jitter or max_jitter < 1:
            max_jitter = self.MAX_JITTER
        return self.error_limit_reset + int(random.uniform(1, max_jitter))

    def raise_for_status(self):
        """Raise an exception if ESI if offline or the error limit is exceeded."""
        if not self.is_online:
            raise EsiOffline()
        if self.is_error_limit_exceeded:
            raise EsiErrorLimitExceeded(retry_in=self.error_limit_reset_w_jitter())


def fetch_esi_status(ignore_daily_downtime: bool = False) -> EsiStatus:
    """Determine the current ESI status.

    Args:
        ignore_daily_downtime: When True will always make a request to ESI \
            even during the daily downtime
    """
    if not ignore_daily_downtime:
        downtime_start = _calc_downtime(APPUTILS_ESI_DAILY_DOWNTIME_START)
        downtime_end = _calc_downtime(APPUTILS_ESI_DAILY_DOWNTIME_END)
        if now() >= downtime_start and now() <= downtime_end:
            return EsiStatus(is_online=False)
    try:
        r = _request_esi_status()
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        logger.warning("Network error when trying to call ESI", exc_info=True)
        return EsiStatus(is_online=False)
    if not r.ok:
        is_online = False
    else:
        try:
            is_online = False if r.json().get("vip") else True
        except ValueError:
            is_online = False
    try:
        remain = int(r.headers.get("X-Esi-Error-Limit-Remain"))
        reset = int(r.headers.get("X-Esi-Error-Limit-Reset"))
    except TypeError:
        logger.warning("Failed to parse HTTP headers: %s", r.headers)
        return EsiStatus(is_online=is_online)
    logger.debug(
        "ESI status: is_online: %s, error_limit_remain = %s, error_limit_reset = %s",
        is_online,
        remain,
        reset,
    )
    return EsiStatus(
        is_online=is_online, error_limit_remain=remain, error_limit_reset=reset
    )


def _calc_downtime(hours_float: float) -> dt.datetime:
    hour, minute = _convert_float_hours(hours_float)
    return now().replace(hour=hour, minute=minute)


def _convert_float_hours(hours_float: float) -> tuple:
    """Convert float hours into int hours and int minutes for datetime."""
    h = int(hours_float)
    m = int((hours_float - h) * 60)
    return h, m


def _request_esi_status() -> requests.Response:
    """Fetch current status from ESI. Retry on common HTTP errors."""
    max_runs = 3
    for run in range(1, max_runs + 1):
        r = requests.get(
            "https://esi.evetech.net/latest/status/",
            timeout=(5, 30),
            headers={"User-Agent": f"{__package__};{__version__}"},
        )
        if r.status_code not in {
            502,  # HTTPBadGateway
            503,  # HTTPServiceUnavailable
            504,  # HTTPGatewayTimeout
        }:
            break
        logger.warning(
            "HTTP status code %s - Try %s/%s",
            r.status_code,
            run,
            max_runs,
        )
        if run < max_runs:
            wait_secs = 0.1 * (random.uniform(2, 4) ** run)
            sleep(wait_secs)
    return r


def retry_task_if_esi_is_down(self):
    """Retry current celery task if ESI is not online or error threshold is exceeded.

    This function has to be called from inside a celery task!

    Args:
        self: Current celery task from `@shared_task(bind=True)`
    """
    try:
        fetch_esi_status().raise_for_status()
    except EsiOffline as ex:
        countdown = (5 + int(random.uniform(1, 10))) * 60
        logger.warning(
            "ESI appears to be offline. Trying again in %d seconds.", countdown
        )
        raise self.retry(countdown=countdown) from ex
    except EsiErrorLimitExceeded as ex:
        logger.warning(
            "ESI error limit threshold reached. Trying again in %s seconds", ex.retry_in
        )
        raise self.retry(countdown=ex.retry_in) from ex
