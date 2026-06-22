"""URL configuration for the scaffold application."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import BasePermission, IsAdminUser

from slaif_reservation.config.views import health_live, health_ready


class ApiDocumentationPermission(BasePermission):  # type: ignore[misc]
    """Apply the configured schema/docs policy consistently to both docs views."""

    def has_permission(self, request: Any, view: Any) -> bool:
        if settings.API_DOCS_PUBLIC:
            return True
        return bool(IsAdminUser().has_permission(request, view))


api_documentation_permission_classes = [ApiDocumentationPermission]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("assets/", include("slaif_reservation.assets.urls", namespace="assets")),
    path("health/live", health_live, name="health-live"),
    path("health/ready", health_ready, name="health-ready"),
    path("api/v1/", include("slaif_reservation.api.urls", namespace="api-v1")),
]

if settings.API_DOCS_ENABLED:
    urlpatterns += [
        path(
            "api/schema/",
            SpectacularAPIView.as_view(permission_classes=api_documentation_permission_classes),
            name="api-schema",
        ),
        path(
            "api/docs/",
            SpectacularSwaggerView.as_view(
                url_name="api-schema",
                permission_classes=api_documentation_permission_classes,
            ),
            name="api-docs",
        ),
    ]
