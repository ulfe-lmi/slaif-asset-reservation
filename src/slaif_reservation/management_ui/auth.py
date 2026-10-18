from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from django.contrib.auth.views import redirect_to_login
from django.http import HttpRequest, HttpResponseBase, HttpResponseForbidden

from slaif_reservation.accounts.authorization import (
    has_any_reservation_permission,
)
from slaif_reservation.accounts.authorization import (
    is_management_user as _is_management_user,
)

__all__ = ["is_management_user", "management_required"]


def is_management_user(user: Any) -> bool:
    """Management-dashboard admission: any of the nine application capabilities.

    ``is_staff`` alone confers nothing (staff is /admin/ admission only); an
    active non-service-account human holding at least one of the documented
    management permissions through groups, individual grants or superuser
    semantics is admitted to the management dashboard. Individual routes
    check their own narrower capability set with :func:`management_required`.
    """
    return _is_management_user(user)


def management_required(
    *codenames: str,
) -> Callable[[Callable[..., HttpResponseBase]], Callable[..., HttpResponseBase]]:
    """Authorize a management route by its explicit application capabilities.

    Every route names the capability set it requires (the documented
    reservations-namespace permissions; manage capabilities include their
    module's read interface by naming both). Anonymous callers are redirected
    to login; any authenticated caller missing every named capability
    receives 403 BEFORE the view body runs, so direct GET/POST cannot be
    authorized by a hidden button and no protected record is fetched for a
    denied principal. Staff status alone confers nothing; Django superuser
    permission semantics are retained. An empty codename list never admits
    (fail closed).
    """

    def decorator(view_func: Callable[..., HttpResponseBase]) -> Callable[..., HttpResponseBase]:
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not has_any_reservation_permission(request.user, codenames):
                return HttpResponseForbidden("Management access is restricted.")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
