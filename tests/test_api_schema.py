from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from django.contrib.staticfiles import finders
from django.core.management import call_command
from django.test import override_settings

from slaif_reservation.accounts.models import User


@pytest.mark.django_db
def test_api_v1_namespace_exists(client) -> None:
    response = client.get("/api/v1/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "SLAIF Asset Reservation API",
        "version": "v1",
        "endpoints": {
            "assets": "/api/v1/assets/",
            "availability": "/api/v1/assets/{asset_id}/availability/",
            "me": "/api/v1/me/",
            "reservations": "/api/v1/reservations/",
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
    assert "/api/v1/me/" in schema
    assert "/api/v1/assets/{asset_id}/availability/" in schema
    assert "/api/v1/reservations/" in schema
    assert "/api/v1/reservations/{reservation_id}/" in schema
    assert "/api/v1/reservations/{reservation_id}/cancel/" in schema
    assert "/api/v1/reservations/{reservation_id}/release/" in schema

    parsed_schema = yaml.safe_load(schema)
    assert "/api/v1/assets/" in parsed_schema["paths"]
    assert "/api/v1/assets/{asset_id}/" in parsed_schema["paths"]
    assert "Bearer" in parsed_schema.get("components", {}).get("securitySchemes", {})

    list_operation = parsed_schema["paths"]["/api/v1/assets/"]["get"]
    detail_operation = parsed_schema["paths"]["/api/v1/assets/{asset_id}/"]["get"]
    list_parameters = {parameter["name"]: parameter for parameter in list_operation["parameters"]}
    assert {
        "kind",
        "parent",
        "tag",
        "active",
        "reservable",
        "q",
        "limit",
        "offset",
    } <= set(list_parameters)
    assert list_parameters["parent"]["schema"]["format"] == "uuid"
    assert detail_operation["parameters"][0]["name"] == "asset_id"
    assert detail_operation["parameters"][0]["schema"]["format"] == "uuid"
    assert "Staff-session-authenticated" in list_operation["description"]
    assert (
        "Bearer/API-token authentication is intentionally deferred" in list_operation["description"]
    )
    assert "Staff-session-authenticated" in detail_operation["description"]
    assert "/api/v1/me/" in parsed_schema["paths"]
    assert "/api/v1/reservations/" in parsed_schema["paths"]
    create_parameters = {
        parameter["name"]
        for parameter in parsed_schema["paths"]["/api/v1/reservations/"]["post"]["parameters"]
    }
    assert {"Idempotency-Key", "X-Request-ID"} <= create_parameters
    assert "/api/v1/tokens/" not in parsed_schema["paths"]
    assert "/api/v1/reservations/{reservation_id}/cancel/" in parsed_schema["paths"]


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


@pytest.mark.django_db
def test_token_lifecycle_routes_are_not_exposed_as_api(client) -> None:
    root_response = client.get("/api/v1/")
    assert root_response.status_code == 200
    assert "reservations" in root_response.json()["endpoints"]

    assert client.post("/api/v1/tokens/", {}).status_code == 404
    assert client.get("/api/v1/me/").status_code == 401
