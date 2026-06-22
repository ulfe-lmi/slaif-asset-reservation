from __future__ import annotations

from pathlib import Path

from django.core.management import call_command


def test_api_v1_namespace_exists(client) -> None:
    response = client.get("/api/v1/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "SLAIF Asset Reservation API",
        "version": "v1",
        "endpoints": {},
    }


def test_openapi_schema_generation_succeeds(tmp_path: Path) -> None:
    schema_path = tmp_path / "openapi.yaml"

    call_command("spectacular", file=str(schema_path), validate=True, fail_on_warn=True)

    schema = schema_path.read_text(encoding="utf-8")
    assert "SLAIF Asset Reservation API" in schema
    assert "/api/v1/" in schema
