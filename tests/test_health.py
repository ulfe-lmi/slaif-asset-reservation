from __future__ import annotations

from django.db import connection


def test_liveness_does_not_require_database(client, monkeypatch) -> None:
    def fail_if_called() -> None:
        raise AssertionError("liveness must not touch the database")

    monkeypatch.setattr(connection, "ensure_connection", fail_if_called)

    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_success(client, db) -> None:
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_failure_is_privacy_safe(client, monkeypatch) -> None:
    def fail_connection() -> None:
        raise RuntimeError("postgres://user:password@db.example/internal")

    monkeypatch.setattr(connection, "ensure_connection", fail_connection)

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert "password" not in response.content.decode()
