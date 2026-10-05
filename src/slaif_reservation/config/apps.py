"""Application configuration for the configured administration site."""

from __future__ import annotations

from django.contrib.admin.apps import AdminConfig as DjangoAdminConfig


class AdminConfig(DjangoAdminConfig):
    """Admin app configuration bound to the SLAIF administration site."""

    default_site = "slaif_reservation.config.admin_site.SlaifAdminSite"
