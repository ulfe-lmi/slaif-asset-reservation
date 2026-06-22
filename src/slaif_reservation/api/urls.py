from __future__ import annotations

from django.urls import path

from slaif_reservation.api.views import ApiRootView
from slaif_reservation.assets import api_urls as asset_api_urls

app_name = "api-v1"

urlpatterns = [
    path("", ApiRootView.as_view(), name="root"),
    *asset_api_urls.urlpatterns,
]
