"""Health check views."""

from __future__ import annotations

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET

from slaif_reservation.config.operational import database_is_ready


@require_GET
def health_live(_request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


@require_GET
def health_ready(_request: HttpRequest) -> JsonResponse:
    if not database_is_ready():
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})
