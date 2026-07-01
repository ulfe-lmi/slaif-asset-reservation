from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from django.contrib.auth.views import redirect_to_login
from django.http import HttpRequest, HttpResponseBase, HttpResponseForbidden


def is_management_user(user: Any) -> bool:
    return bool(
        getattr(user, "is_authenticated", False)
        and getattr(user, "is_active", False)
        and getattr(user, "is_staff", False)
        and not getattr(user, "is_service_account", False)
    )


def management_required(
    view_func: Callable[..., HttpResponseBase],
) -> Callable[..., HttpResponseBase]:
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not is_management_user(request.user):
            return HttpResponseForbidden("Management access is restricted.")
        return view_func(request, *args, **kwargs)

    return wrapper
