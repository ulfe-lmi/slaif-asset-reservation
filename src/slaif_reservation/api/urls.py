from __future__ import annotations

from django.urls import path

from slaif_reservation.api.views import ApiRootView

app_name = "api-v1"

urlpatterns = [
    path("", ApiRootView.as_view(), name="root"),
]
