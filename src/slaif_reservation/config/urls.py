"""URL configuration for the scaffold application."""

from __future__ import annotations

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny, IsAdminUser

from slaif_reservation.config.views import health_live, health_ready

schema_permission_classes = [AllowAny] if settings.API_DOCS_PUBLIC else [IsAdminUser]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/live", health_live, name="health-live"),
    path("health/ready", health_ready, name="health-ready"),
    path("api/v1/", include("slaif_reservation.api.urls", namespace="api-v1")),
]

if settings.API_DOCS_ENABLED:
    urlpatterns += [
        path(
            "api/schema/",
            SpectacularAPIView.as_view(permission_classes=schema_permission_classes),
            name="api-schema",
        ),
        path(
            "api/docs/",
            SpectacularSwaggerView.as_view(url_name="api-schema"),
            name="api-docs",
        ),
    ]
