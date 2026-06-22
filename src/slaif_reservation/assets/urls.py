from __future__ import annotations

from django.urls import path

from slaif_reservation.assets import views

app_name = "assets"

urlpatterns = [
    path("", views.asset_list, name="list"),
    path("<uuid:asset_id>/", views.asset_detail, name="detail"),
]
