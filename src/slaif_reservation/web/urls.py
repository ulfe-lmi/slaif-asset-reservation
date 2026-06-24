from __future__ import annotations

from django.urls import path

from slaif_reservation.web import views

app_name = "web"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", views.HumanLoginView.as_view(), name="login"),
    path("logout/", views.HumanLogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("tokens/", views.token_list, name="token-list"),
    path("tokens/new/", views.token_create, name="token-create"),
    path("tokens/<uuid:token_id>/revoke/", views.revoke_own_token, name="token-revoke"),
    path("assets/", views.asset_list, name="asset-list"),
    path("assets/<uuid:asset_id>/", views.asset_detail, name="asset-detail"),
    path("assets/<uuid:asset_id>/reserve/", views.reserve_asset, name="reserve"),
    path("reservations/", views.reservation_list, name="reservation-list"),
    path(
        "reservations/<uuid:reservation_id>/",
        views.reservation_detail,
        name="reservation-detail",
    ),
    path(
        "reservations/<uuid:reservation_id>/cancel/",
        views.cancel_own_reservation,
        name="reservation-cancel",
    ),
    path(
        "reservations/<uuid:reservation_id>/release/",
        views.release_own_reservation,
        name="reservation-release",
    ),
]
