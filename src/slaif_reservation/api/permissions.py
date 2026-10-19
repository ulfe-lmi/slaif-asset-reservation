from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from slaif_reservation.accounts.models import ApiToken
from slaif_reservation.api.problem import InsufficientScope
from slaif_reservation.web.auth import is_active_human


class HasApiTokenScope(BasePermission):  # type: ignore[misc]
    def has_permission(self, request: Request, view: Any) -> bool:
        required = tuple(getattr(view, "required_scopes", ()))
        token = request.auth
        if not isinstance(token, ApiToken):
            raise InsufficientScope()
        if all(token.has_scope(scope) for scope in required):
            return True
        raise InsufficientScope()


class IsActiveStaffHuman(BasePermission):  # type: ignore[misc]
    """Admit only current active non-service-account human staff sessions.

    Reuses the shared active-human boundary that Administration already
    applies and adds the staff flag the older staff read surfaces need.
    The check runs at DRF permission admission, before any inventory
    query, filter, detail fetch or schema work. Superuser status, model
    permissions and token scopes never replace the current human/staff
    status; nothing is cached and no authentication backend changes.
    """

    message = "Staff human access is required."

    def has_permission(self, request: Request, view: Any) -> bool:
        user = request.user
        return is_active_human(user) and bool(user.is_staff)
