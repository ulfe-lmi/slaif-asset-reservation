"""Rendered application-capability helpers for templates (A16 / SAR-048).

Presentation only: templates may derive the same explicit
reservations-namespace capability booleans the server-side guards use, so
buttons, links and navigation reflect the checks that actually authorize the
route. No admission, validation, wire or storage behavior changes; every
call evaluates the given user instance fresh (no grant cache).
"""

from __future__ import annotations

from typing import Any

from django import template

from slaif_reservation.accounts.authorization import (
    has_any_reservation_permission,
    has_reservation_permission,
    is_management_user,
)

register = template.Library()


@register.simple_tag
def has_permission(user: Any, codename: str) -> bool:
    """Whether the user explicitly holds one documented capability."""
    return has_reservation_permission(user, codename)


@register.simple_tag
def has_any_permission(user: Any, *codenames: str) -> bool:
    """Whether the user holds at least one of the named capabilities."""
    return has_any_reservation_permission(user, codenames)


@register.simple_tag
def management_user(user: Any) -> bool:
    """Whether the user is admitted to the management dashboard (any of the
    nine management capabilities)."""
    return is_management_user(user)
