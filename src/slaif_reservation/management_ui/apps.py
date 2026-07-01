from __future__ import annotations

from django.apps import AppConfig


class ManagementUiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "slaif_reservation.management_ui"
