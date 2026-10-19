"""Rendered form guidance helpers (SAR-044).

Presentation only: nearby help elements with deterministic IDs for
``aria-describedby`` wiring, human-readable token-scope labels/effects, and
humanized duration display. No validation, permission, admission, wire or
storage behavior changes.
"""

from __future__ import annotations

from typing import Any

from django import template
from django.utils.html import format_html
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

register = template.Library()

SCOPE_LABELS = {
    "assets:read": _("Asset inventory (reserved)"),
    "availability:read": _("Read availability"),
    "reservations:read": _("Read your reservations"),
    "reservations:create": _("Create reservations"),
    "reservations:cancel": _("Cancel reservations"),
    "reservations:release": _("Release reservations"),
    "reservations:read_all": _("Read other people's reservations (read-only)"),
}

SCOPE_EFFECTS = {
    "assets:read": _(
        "Reserved for future use. It grants nothing today: bearer tokens still cannot "
        "list or read assets — the asset endpoints remain staff-session only."
    ),
    "availability:read": _(
        "Lets the token check which times are free on an asset (advisory availability). "
        "It changes nothing."
    ),
    "reservations:read": _("Lets the token read this person's own reservations."),
    "reservations:create": _(
        "Lets the token create reservations under the current policy and limits. "
        "You can only create this scope while your account currently has the booking "
        "capability; restricted assets still need group eligibility at booking time."
    ),
    "reservations:cancel": _("Lets the token cancel this person's upcoming reservations."),
    "reservations:release": _("Lets the token release this person's active reservation early."),
    "reservations:read_all": _(
        "Read-only: lets the token list and inspect other people's reservations with "
        "the minimal shared fields. You can only create this scope while your account "
        "currently has the view-all-reservations capability; if that capability is "
        "removed, the scope stops working on the token's next request while its other "
        "scopes keep working."
    ),
}


@register.filter
def scope_label(scope: str) -> str:
    """Human label for a stored scope value (wire value is unchanged)."""
    return SCOPE_LABELS.get(scope, scope)


@register.filter
def scope_effect(scope: str) -> str:
    """Plain-language effect of one scope, or empty for unknown values."""
    return SCOPE_EFFECTS.get(scope, "")


@register.filter
def human_duration(value: Any) -> str:
    """Human-readable length for display; stored units stay minutes.

    30 -> "30 minutes"; 90 -> "1 hour, 30 minutes"; 1440 -> "1 day";
    1441 -> "1 day, 1 minute"; 1501 -> "1 day, 1 hour, 1 minute";
    2880 -> "2 days"; 2890 -> "2 days, 10 minutes".
    """
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        return ""
    if minutes < 0:
        return ""
    hours, rem = divmod(minutes, 60)
    days, leftover_hours = divmod(hours, 24)
    parts: list[str] = []
    if days:
        parts.append(ngettext("%(count)d day", "%(count)d days", days) % {"count": days})
    if leftover_hours:
        parts.append(
            ngettext("%(count)d hour", "%(count)d hours", leftover_hours)
            % {"count": leftover_hours}
        )
    if rem:
        parts.append(ngettext("%(count)d minute", "%(count)d minutes", rem) % {"count": rem})
    if not parts:
        parts.append("0 minutes")
    return ", ".join(parts)


@register.simple_tag
def field_guidance(field: object) -> str:
    """Render the bound field's nearby help paragraph with a stable ID.

    The ID is ``<auto_id>-help``; forms set the matching ``aria-describedby``
    widget attribute. Renders nothing when the field carries no help text.
    """
    help_text = getattr(getattr(field, "field", None), "help_text", "") or ""
    auto_id = getattr(field, "auto_id", "") or ""
    if not help_text or not auto_id:
        return ""
    return format_html('<p class="help" id="{}">{}</p>', f"{auto_id}-help", help_text)
