from __future__ import annotations

from django.urls import path

from slaif_reservation.api.read_all_views import (
    AllReservationDetailAPIView,
    AllReservationListAPIView,
)
from slaif_reservation.api.reservation_views import (
    AvailabilityAPIView,
    MeAPIView,
    ReservationCancelAPIView,
    ReservationDetailAPIView,
    ReservationListCreateAPIView,
    ReservationReleaseAPIView,
)
from slaif_reservation.api.views import ApiRootView
from slaif_reservation.assets import api_urls as asset_api_urls

app_name = "api-v1"

urlpatterns = [
    path("", ApiRootView.as_view(), name="root"),
    path("me/", MeAPIView.as_view(), name="me"),
    path(
        "assets/<uuid:asset_id>/availability/",
        AvailabilityAPIView.as_view(),
        name="asset-availability",
    ),
    path("reservations/", ReservationListCreateAPIView.as_view(), name="reservation-list"),
    path(
        "reservations/<uuid:reservation_id>/",
        ReservationDetailAPIView.as_view(),
        name="reservation-detail",
    ),
    path(
        "reservations/<uuid:reservation_id>/cancel/",
        ReservationCancelAPIView.as_view(),
        name="reservation-cancel",
    ),
    path(
        "reservations/<uuid:reservation_id>/release/",
        ReservationReleaseAPIView.as_view(),
        name="reservation-release",
    ),
    path("all-reservations/", AllReservationListAPIView.as_view(), name="all-reservation-list"),
    path(
        "all-reservations/<uuid:reservation_id>/",
        AllReservationDetailAPIView.as_view(),
        name="all-reservation-detail",
    ),
    *asset_api_urls.urlpatterns,
]
