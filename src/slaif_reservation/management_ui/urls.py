from __future__ import annotations

from django.urls import path

from slaif_reservation.management_ui import views

app_name = "management-ui"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("policies/", views.policy_list, name="policy-list"),
    path("policies/new/", views.policy_create, name="policy-create"),
    path("policies/<uuid:policy_id>/", views.policy_detail, name="policy-detail"),
    path("policies/<uuid:policy_id>/edit/", views.policy_update, name="policy-update"),
    path(
        "policies/<uuid:policy_id>/deactivate/",
        views.policy_deactivate,
        name="policy-deactivate",
    ),
    path("blackouts/", views.blackout_list, name="blackout-list"),
    path("blackouts/new/", views.blackout_create, name="blackout-create"),
    path("blackouts/<uuid:blackout_id>/", views.blackout_detail, name="blackout-detail"),
    path(
        "blackouts/<uuid:blackout_id>/deactivate/",
        views.blackout_deactivate,
        name="blackout-deactivate",
    ),
    path("reservations/", views.reservation_list, name="reservation-list"),
    path(
        "reservations/calendar/<uuid:asset_id>/",
        views.reservation_calendar,
        name="reservation-calendar",
    ),
    path(
        "reservations/<uuid:reservation_id>/",
        views.reservation_detail,
        name="reservation-detail",
    ),
    path(
        "reservations/<uuid:reservation_id>/cancel/",
        views.reservation_cancel,
        name="reservation-cancel",
    ),
    path(
        "reservations/<uuid:reservation_id>/release/",
        views.reservation_release,
        name="reservation-release",
    ),
    path("audit/", views.audit_list, name="audit-list"),
    path("audit/export.csv", views.audit_export, name="audit-export"),
    path("audit/<uuid:event_id>/", views.audit_detail, name="audit-detail"),
]
