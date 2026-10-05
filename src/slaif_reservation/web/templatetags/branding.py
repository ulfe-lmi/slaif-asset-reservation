"""Presentation helpers for the optional operator branding slots (SAR-045).

Each helper renders the operator override when that exact slot currently
resolves to a valid file, otherwise the packaged default, so a missing or
invalid asset can never break the page or another slot.
"""

from __future__ import annotations

from django.template import Library
from django.templatetags.static import static
from django.utils.safestring import SafeText, mark_safe

from slaif_reservation.web.branding import (
    DEFAULT_BRAND_STATIC,
    STYLE_CSS,
    asset_url,
    resolve_slot,
)

register = Library()


@register.simple_tag
def branding_src(slot: str) -> str:
    """Image ``src`` for a slot: the override URL or the packaged default."""
    return asset_url(slot) if resolve_slot(slot) is not None else static(DEFAULT_BRAND_STATIC)


@register.simple_tag
def branding_css_link() -> SafeText:
    """The override stylesheet link, emitted only when the slot is valid."""
    if resolve_slot(STYLE_CSS) is not None:
        return mark_safe(f'<link rel="stylesheet" href="{asset_url(STYLE_CSS)}">')
    return mark_safe("")


@register.simple_tag
def branding_icon_link() -> SafeText:
    """The ``<link rel="icon">`` element with the correct type for the slot."""
    resolved = resolve_slot("favicon")
    if resolved is not None:
        mime = resolved.content_type.split(";", 1)[0]
        return mark_safe(f'<link rel="icon" type="{mime}" href="{asset_url("favicon")}">')
    return mark_safe(
        f'<link rel="icon" type="image/svg+xml" href="{static(DEFAULT_BRAND_STATIC)}">'
    )
