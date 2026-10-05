"""URL configuration for the scaffold application."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import BasePermission, IsAdminUser

# The handler* imports are intentionally unused at runtime: Django resolves
# the branded browser error handlers from the ROOT_URLCONF namespace.
from slaif_reservation.config.views import (  # noqa: F401
    handler400,
    handler403,
    handler404,
    handler500,
    health_live,
    health_ready,
)


class ApiDocumentationPermission(BasePermission):  # type: ignore[misc]
    """Apply the configured schema/docs policy consistently to both docs views."""

    def has_permission(self, request: Any, view: Any) -> bool:
        if settings.API_DOCS_PUBLIC:
            return True
        return bool(IsAdminUser().has_permission(request, view))


api_documentation_permission_classes = [ApiDocumentationPermission]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/live", health_live, name="health-live"),
    path("health/ready", health_ready, name="health-ready"),
    path("api/v1/", include("slaif_reservation.api.urls", namespace="api-v1")),
    path("manage/", include("slaif_reservation.management_ui.urls", namespace="management-ui")),
    path("", include("slaif_reservation.web.urls", namespace="web")),
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
