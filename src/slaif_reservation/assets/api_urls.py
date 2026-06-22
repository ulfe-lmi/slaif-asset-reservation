from __future__ import annotations

from django.urls import path

from slaif_reservation.assets.api import AssetDetailAPIView, AssetListAPIView

urlpatterns = [
    path("assets/", AssetListAPIView.as_view(), name="asset-list"),
    path("assets/<uuid:asset_id>/", AssetDetailAPIView.as_view(), name="asset-detail"),
]
