from enum import Enum
from http import HTTPStatus
from typing import Optional

from django.http import HttpResponse, JsonResponse
from django.utils.functional import lazy
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

DEFAULT_ICON_SIZE = 32
format_html_lazy = lazy(format_html, str)


class HttpResponseNoContent(HttpResponse):
    """Special HTTP response with no content, just headers.

    The content operations are ignored.
    """

    status_code = HTTPStatus.NO_CONTENT

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # although we don't define a content-type, base class sets a
        # default one -- remove it, we're not returning content
        if hasattr(self, "_headers") and "content-type" in self._headers:  # Django<3.2
            del self._headers["content-type"]
        elif hasattr(self, "headers") and "content-type" in self.headers:  # Django>=3.2
            del self.headers["content-type"]
        else:
            raise ValueError("No header found")  # this should never be called


class JSONResponseMixin:
    """A mixin that can be used to render a JSON response for a class based view."""

    def render_to_json_response(self, context, **response_kwargs):
        """Return a JSON response, transforming 'context' to make the payload."""
        return JsonResponse(self.get_data(context), safe=False, **response_kwargs)

    def get_data(self, context):
        """Return an object that will be serialized as JSON by json.dumps()."""
        return context


class BootstrapStyle(str, Enum):
    """Bootstrap context style names, e.g. for labels"""

    DANGER = "danger"  #:
    DEFAULT = "default"  #:
    INFO = "info"  #:
    PRIMARY = "primary"  #:
    SUCCESS = "success"  #:
    WARNING = "warning"  #:

    def __str__(self) -> str:
        return self.value


# old: add_bs_label_html
def bootstrap_label_html(text: str, label: str = "default") -> str:
    """create Bootstrap label and return HTML"""
    return format_html('<span class="label label-{}">{}</span>', label, text)


# old: create_bs_glyph_html
def bootstrap_glyph_html(glyph_name: str) -> str:
    """returns a Bootstrap glyph HTML"""
    return format_html(
        '<span class="glyphicon glyphicon-{}"></span>', glyph_name.lower()
    )


# old: create_bs_glyph_2_html
def bootstrap_glyph_2_html(glyph_name, tooltip_text=None, color="initial"):
    """returns a Bootstrap glyph HTML and can also have a tool tip and a color"""
    if tooltip_text:
        tooltip_html = mark_safe(
            'aria-hidden="true" data-toggle="tooltip" data-placement="top" '
            'title="{}"'.format(tooltip_text)
        )
    else:
        tooltip_html = ""
    return format_html(
        '<span class="glyphicon glyphicon-{}"'
        ' style="color:{};"{}></span>'.format(glyph_name.lower(), color, tooltip_html)
    )


def bootstrap_icon_plus_name_html(
    icon_url,
    name,
    size: int = DEFAULT_ICON_SIZE,
    avatar: bool = False,
    url: str = None,
    text: str = None,
) -> str:
    """returns HTML to display an icon next to a name. Can also be a link."""
    name_html = link_html(url, name, new_window=False) if url else name
    if text:
        name_html = format_html("{}&nbsp;{}", name_html, text)

    return format_html(
        "{}&nbsp;&nbsp;&nbsp;{}",
        image_html(
            icon_url, classes=["ra-avatar", "img-circle"] if avatar else [], size=size
        ),
        name_html,
    )


# old: create_bs_button_html
def bootstrap_link_button_html(
    url: str, glyph_name: str, button_type: str, disabled: bool = False
) -> str:
    """returns bootstrap link button and return HTML"""
    return format_html(
        '<a href="{}" class="btn btn-{}"{}>{}</a>',
        url,
        button_type,
        mark_safe(' disabled="disabled"') if disabled else "",
        bootstrap_glyph_html(glyph_name),
    )


# old: create_fa_button_html
def fontawesome_link_button_html(
    url: str,
    fa_code: str,
    button_type: str,
    tooltip: str = None,
    disabled: bool = False,
) -> str:
    """create fontawesome button and return HTML"""
    return format_html(
        '<a href="{}" class="btn btn-{}"{}>{}{}</a>',
        url,
        button_type,
        mark_safe(f' title="{tooltip}"') if tooltip else "",
        mark_safe(' disabled="disabled"') if disabled else "",
        mark_safe(f'<i class="{fa_code}"></i>'),
    )


def fontawesome_modal_button_html(
    modal_id: str,
    fa_code: str,
    ajax_url: str = "",
    tooltip: str = "",
    style=BootstrapStyle.DEFAULT,
) -> str:
    """create fontawesome modal button and return HTML

    Args:
        modal_id: DOM ID of modal to invoke
        fa_code: fontawesome code, e.g. "fas fa-moon"
        ajax_url: URL to invoke via AJAX for loading modal content
        tooltip: text to appear as tooltip
        style: Bootstrap context style for the button
    """
    return format_html(
        '<button type="button" '
        'class="btn btn-{}" '
        'data-toggle="modal" '
        'data-target="#{}" '
        "{}"
        "{}>"
        '<i class="{}"></i>'
        "</button>",
        BootstrapStyle(style),
        modal_id,
        mark_safe(f'title="{tooltip}" ') if tooltip else "",
        mark_safe(f'data-ajax_url="{ajax_url}" ') if ajax_url else "",
        fa_code,
    )


def humanize_value(value: float, precision: int = 2) -> str:
    """returns given value in human readable and abbreviated form
    e.g. ``1234678`` -> ``1.23m``
    """
    value = float(value)
    for exponent, identifier in [(12, "t"), (9, "b"), (6, "m"), (3, "k")]:
        if value >= pow(10, exponent):
            return f"{value / pow(10, exponent):,.{precision}f}{identifier}"

    return f"{value:,.{precision}f}"


def image_html(src: str, classes: list = None, size: int = None) -> str:
    """returns the HTML for an image with optional classes and size"""
    classes_str = format_html('class="{}"', (" ".join(classes)) if classes else "")
    size_html = (
        format_html('width="{}" height="{}"', int(size), int(size)) if size else ""
    )
    return format_html('<img {} {} src="{}">', classes_str, size_html, src)


# old: create_link_html
def link_html(url: str, label: str, new_window: bool = True) -> str:
    """create html link and return HTML"""
    return format_html(
        '<a href="{}"{}>{}</a>',
        url,
        mark_safe(' target="_blank"') if new_window else "",
        label,
    )


# old: add_no_wrap_html
def no_wrap_html(text: str) -> str:
    """add no-wrap HTML to text"""
    return format_html('<span class="text-nowrap;">{}</span>', mark_safe(text))


def yesno_str(value: bool) -> str:
    """returns yes/no for boolean as string and with localization"""
    return _("yes") if value is True else _("no")


def yesnonone_str(value: Optional[bool]) -> str:
    """returns yes/no/none for boolean as string and with localization"""
    if value is True:
        return _("yes")
    elif value is False:
        return _("no")
    else:
        return ""
