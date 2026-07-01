from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from slaif_reservation.accounts.models import ApiToken
from slaif_reservation.api.problem import InsufficientScope


class HasApiTokenScope(BasePermission):  # type: ignore[misc]
    def has_permission(self, request: Request, view: Any) -> bool:
        required = tuple(getattr(view, "required_scopes", ()))
        token = request.auth
        if not isinstance(token, ApiToken):
            raise InsufficientScope()
        if all(token.has_scope(scope) for scope in required):
            return True
        raise InsufficientScope()
