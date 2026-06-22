from __future__ import annotations

from pathlib import Path

import pytest
from django.contrib.staticfiles import finders
from django.core.management import call_command
from django.test import override_settings

from slaif_reservation.accounts.models import User


def test_api_v1_namespace_exists(client) -> None:
    response = client.get("/api/v1/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "SLAIF Asset Reservation API",
        "version": "v1",
        "endpoints": {
            "assets": "/api/v1/assets/",
        },
    }


def test_openapi_schema_generation_succeeds(tmp_path: Path) -> None:
    schema_path = tmp_path / "openapi.yaml"

    call_command("spectacular", file=str(schema_path), validate=True, fail_on_warn=True)

    schema = schema_path.read_text(encoding="utf-8")
    assert "SLAIF Asset Reservation API" in schema
    assert "/api/v1/" in schema
    assert "/api/v1/assets/" in schema
    assert "/api/v1/assets/{asset_id}/" in schema


@pytest.mark.django_db
@override_settings(API_DOCS_PUBLIC=False)
@pytest.mark.parametrize("path", ["/api/schema/", "/api/docs/"])
def test_api_documentation_denies_anonymous_access_when_private(client, path: str) -> None:
    response = client.get(path)

    assert response.status_code == 403


@pytest.mark.django_db
@override_settings(API_DOCS_PUBLIC=False)
@pytest.mark.parametrize("path", ["/api/schema/", "/api/docs/"])
def test_api_documentation_allows_staff_access_when_private(client, path: str) -> None:
    staff_user = User.objects.create_user(
        email="staff@example.com",
        password="not-a-secret",
        is_staff=True,
    )
    client.force_login(staff_user)

    response = client.get(path)

    assert response.status_code == 200


@override_settings(API_DOCS_PUBLIC=True)
@pytest.mark.parametrize("path", ["/api/schema/", "/api/docs/"])
def test_api_documentation_allows_anonymous_access_when_public(client, path: str) -> None:
    response = client.get(path)

    assert response.status_code == 200


def test_swagger_ui_uses_local_sidecar_static_assets(settings) -> None:
    assert settings.SPECTACULAR_SETTINGS["SWAGGER_UI_DIST"] == "SIDECAR"
    assert settings.SPECTACULAR_SETTINGS["SWAGGER_UI_FAVICON_HREF"] == "SIDECAR"
    assert settings.SPECTACULAR_SETTINGS["REDOC_DIST"] == "SIDECAR"
    assert finders.find("admin/css/base.css")
    assert finders.find("drf_spectacular_sidecar/swagger-ui-dist/swagger-ui-bundle.js")
