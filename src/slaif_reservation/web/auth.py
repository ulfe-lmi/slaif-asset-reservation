from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, cast

from django.contrib.auth.views import redirect_to_login
from django.http import HttpRequest, HttpResponse


def is_active_human(user: Any) -> bool:
    return bool(user.is_authenticated and user.is_active and not user.is_service_account)


def active_human_required[
    ViewFunc: Callable[..., HttpResponse],
](view_func: ViewFunc) -> ViewFunc:
    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not is_active_human(request.user):
            return cast(HttpResponse, redirect_to_login(request.get_full_path()))
        return view_func(request, *args, **kwargs)

    return cast(ViewFunc, _wrapped)
