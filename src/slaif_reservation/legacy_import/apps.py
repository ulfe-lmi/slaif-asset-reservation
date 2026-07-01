from __future__ import annotations

from django.apps import AppConfig


class LegacyImportConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "slaif_reservation.legacy_import"
