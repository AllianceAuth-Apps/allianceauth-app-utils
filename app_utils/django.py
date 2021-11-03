import logging
from typing import Any

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.db import models
from django.utils.html import format_html

from . import __title__
from .logging import LoggerAddTag
from .urls import static_file_absolute_url

logger = LoggerAddTag(logging.getLogger(__name__), __title__)


def app_labels() -> set:
    """returns set of all current app labels"""
    return {x for x in apps.app_configs.keys()}


def clean_setting(
    name: str,
    default_value: object,
    min_value: int = None,
    max_value: int = None,
    required_type: type = None,
    choices: list = None,
) -> Any:
    """cleans the user input for an app's setting in the Django settings file

    Will use default_value if setting is not defined.
    Will use minimum or maximum value if respective boundary is exceeded.

    Args:
        default_value: value to use if setting is not defined
        min_value: minimum allowed value (0 assumed for int)
        max_value: maximum value value
        required_type: Mandatory if `default_value` is `None`,
        otherwise derived from default_value

    Returns:
        cleaned value for setting

    This function is designed to be used in a dedicated module like ``app_settings.py``
    as layer between the actual settings and all other modules.
    ``app_settings.py`` will import and clean all settings and all other modules are supposed to import the settings it.

    Example for app_settings:

    .. code-block:: python

        from app_utils.django import clean_setting

        EXAMPLE_SETTING = clean_setting("EXAMPLE_SETTING", 10)
    """
    if default_value is None and not required_type:
        raise ValueError("You must specify a required_type for None defaults")

    if not required_type:
        required_type = type(default_value)

    if min_value is None and issubclass(required_type, int):
        min_value = 0

    if issubclass(required_type, int) and default_value is not None:
        if min_value is not None and default_value < min_value:
            raise ValueError("default_value can not be below min_value")
        if max_value is not None and default_value > max_value:
            raise ValueError("default_value can not be above max_value")

    if not hasattr(settings, name):
        cleaned_value = default_value
    else:
        dirty_value = getattr(settings, name)
        if dirty_value is None or (
            isinstance(dirty_value, required_type)
            and (min_value is None or dirty_value >= min_value)
            and (max_value is None or dirty_value <= max_value)
            and (choices is None or dirty_value in choices)
        ):
            cleaned_value = dirty_value
        elif (
            isinstance(dirty_value, required_type)
            and min_value is not None
            and dirty_value < min_value
        ):
            logger.warning(
                "You setting for {} it not valid. Please correct it. "
                "Using minimum value for now: {}".format(name, min_value)
            )
            cleaned_value = min_value
        elif (
            isinstance(dirty_value, required_type)
            and max_value is not None
            and dirty_value > max_value
        ):
            logger.warning(
                "You setting for {} it not valid. Please correct it. "
                "Using maximum value for now: {}".format(name, max_value)
            )
            cleaned_value = max_value
        else:
            logger.warning(
                "You setting for {} it not valid. Please correct it. "
                "Using default for now: {}".format(name, default_value)
            )
            cleaned_value = default_value
    return cleaned_value


def users_with_permission(
    permission: Permission, include_superusers=True
) -> models.QuerySet:
    """returns queryset of users that have the given Django permission

    Args:
        permission: required permission
        include_superusers: whether superusers are included in the returned list
    """
    users_qs = (
        permission.user_set.all()
        | User.objects.filter(
            groups__in=list(permission.group_set.values_list("pk", flat=True))
        )
        | User.objects.select_related("profile").filter(
            profile__state__in=list(permission.state_set.values_list("pk", flat=True))
        )
    )
    if include_superusers:
        users_qs |= User.objects.filter(is_superuser=True)
    return users_qs.distinct()


def admin_boolean_icon_html(value) -> str:
    """Variation of the admin boolean type, which returns the HTML for creating
    the usual `True` and `False` icons.
    But returns `None` for `None`, instead of the question mark."""

    def make_html(icon_url: str, alt: str) -> str:
        return format_html(f'<img src="{icon_url}" alt="{alt}">')

    if value is True:
        icon_url = static_file_absolute_url("admin/img/icon-yes.svg")
        return make_html(icon_url, "True")
    elif value is False:
        icon_url = static_file_absolute_url("admin/img/icon-no.svg")
        return make_html(icon_url, "False")
    return None
