"""Health check views and generic branded browser error handlers."""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from slaif_reservation.config.operational import database_is_ready

# Safe, fixed browser-facing error copy. Production tracebacks, exception
# text and request/private query details are never rendered.
BRANDED_ERRORS: dict[int, tuple[str, str]] = {
    400: ("Bad request", "The request could not be processed."),
    403: ("403 Forbidden", "You do not have permission to view this page."),
    404: ("404 Not found", "The page you requested could not be found."),
    500: ("Server error", "Something went wrong. Please try again later."),
}


def _render_branded_error(
    request: HttpRequest, status_code: int, *, message: str | None = None
) -> HttpResponse:
    # The template intentionally avoids user, message and session access so
    # it renders safely when the database is unavailable.
    title, default_message = BRANDED_ERRORS[status_code]
    return render(
        request,
        "web/error.html",
        {
            "status_code": status_code,
            "error_title": title,
            "error_message": message or default_message,
        },
        status=status_code,
    )


def handler400(request: HttpRequest, exception: Any = None) -> HttpResponse:
    return _render_branded_error(request, 400)


def handler403(request: HttpRequest, exception: Any = None) -> HttpResponse:
    return _render_branded_error(request, 403)


def handler404(request: HttpRequest, exception: Any = None) -> HttpResponse:
    return _render_branded_error(request, 404)


def handler500(request: HttpRequest) -> HttpResponse:
    return _render_branded_error(request, 500)


def csrf_failure(request: HttpRequest, reason: str = "") -> HttpResponse:
    """Branded CSRF rejection without revealing the internal reason."""
    return _render_branded_error(
        request,
        403,
        message=("The form could not be submitted. Go back, refresh the page, and try again."),
    )


@require_GET
def health_live(_request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


@require_GET
def health_ready(_request: HttpRequest) -> JsonResponse:
    if not database_is_ready():
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})
