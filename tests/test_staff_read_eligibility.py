"""Order 052-a: current-human admission on the four staff read surfaces.

ICA-GA-001 repair: the staff asset inventory list/detail and the private
schema/docs routes must deny a session whose account is no longer a current
active non-service-account human, even when the session was established by
a valid staff login. The main transition proof uses real HTTP against
``live_server`` with a genuine ``/login/`` CSRF exchange (never
``force_login``) and exercises the four REST gates before any
member/Administration page that would terminate the changed session. The
remaining boundary controls use the standard test client on real
PostgreSQL: positives, service/inactive/staff-loss transitions, unrelated
grants, bearer-only denial and the local public-docs policy.
"""

from __future__ import annotations

import re
import uuid
from http.cookiejar import CookieJar
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener

import pytest
from django.contrib.auth.models import Permission
from django.test import Client, override_settings

from slaif_reservation.accounts.models import User
from slaif_reservation.accounts.services import issue_api_token
from slaif_reservation.assets.models import Asset

LOGIN_PATH = "/login/"
PASSWORD = "synthetic-only"


def _routes(asset_id: str | uuid.UUID | None) -> dict[str, str]:
    detail = f"/api/v1/assets/{asset_id}/" if asset_id is not None else None
    routes = {
        "asset-list": "/api/v1/assets/",
        "asset-detail": detail,
        "schema": "/api/schema/",
        "docs": "/api/docs/",
    }
    return {label: path for label, path in routes.items() if path is not None}


def _open(opener, base: str, path: str) -> tuple[int, bytes]:
    try:
        response = opener.open(base + path)
        return response.status, response.read()
    except HTTPError as exc:
        return exc.code, exc.read()


def _http_login(opener, base: str, email: str, password: str) -> None:
    """Real login through /login/ with a valid CSRF token; assert success."""
    login_html = opener.open(base + LOGIN_PATH).read().decode()
    match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', login_html)
    assert match is not None
    payload = urlencode(
        {"username": email, "password": password, "csrfmiddlewaretoken": match.group(1)}
    ).encode()
    response = opener.open(
        Request(
            base + LOGIN_PATH,
            data=payload,
            headers={"Referer": base + LOGIN_PATH},
        )
    )
    # A successful staff-human login lands on the dashboard (root).
    assert response.geturl() == base + "/"


@pytest.mark.django_db(transaction=True)
def test_staff_session_marked_service_is_denied_on_all_four_via_real_http(live_server) -> None:
    staff = User.objects.create_user(
        email="staff-transition@example.invalid", password=PASSWORD, is_staff=True
    )
    asset = Asset.objects.create(
        slug="transition-gpu",
        name="Transition GPU",
        kind=Asset.KIND_GPU,
        active=True,
        reservable=True,
    )

    base = live_server.url
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    _http_login(opener, base, staff.email, PASSWORD)

    with override_settings(API_DOCS_PUBLIC=False):
        # Positive: the valid staff human reads all four surfaces first,
        # before any page that could terminate the session later.
        list_status, list_body = _open(opener, base, "/api/v1/assets/")
        assert list_status == 200
        assert "transition-gpu" in list_body.decode()
        for label, path in _routes(asset.id).items():
            if label == "asset-list":
                continue
            status, body = _open(opener, base, path)
            assert status == 200, label
            if label == "schema":
                assert b"openapi" in body

        # The operator flag change keeps the SAME session/cookies.
        User.objects.filter(pk=staff.pk).update(is_service_account=True)

        denied: dict[str, tuple[int, bytes]] = {}
        for label, path in _routes(asset.id).items():
            denied[label] = _open(opener, base, path)
        for label, (status, _body) in denied.items():
            assert status == 403, label

        # A guessed UUID for the same disallowed caller is indistinguishable.
        guessed = f"/api/v1/assets/{uuid.uuid4()}/"
        guessed_status, guessed_body = _open(opener, base, guessed)
        real_status, real_body = denied["asset-detail"]
        assert guessed_status == real_status == 403
        assert guessed_body == real_body

        # No private inventory or schema content leaks through the denials.
        leaked = b"".join(body for _status, body in denied.values()).decode("utf-8", "replace")
        assert "transition-gpu" not in leaked
        assert "openapi" not in leaked

        # Administration boundary control, only after the REST gates above.
        admin = opener.open(base + "/admin/")
        assert "/admin/login/" in admin.geturl()


@pytest.mark.django_db
def test_bearer_token_alone_never_reads_inventory_or_private_docs() -> None:
    owner = User.objects.create_user(
        email="staff-bearer@example.invalid",
        password=PASSWORD,
        is_staff=True,
        is_superuser=True,
    )
    asset = Asset.objects.create(
        slug="bearer-control-gpu",
        name="Bearer Control GPU",
        kind=Asset.KIND_GPU,
        active=True,
        reservable=True,
    )
    issued = issue_api_token(
        owner=owner,
        name="bearer control",
        scopes=[
            "assets:read",
            "availability:read",
            "reservations:read",
            "reservations:read_all",
        ],
        lifetime_days=7,
    )
    client = Client()
    with override_settings(API_DOCS_PUBLIC=False):
        for label, path in _routes(asset.id).items():
            response = client.get(path, HTTP_AUTHORIZATION=f"Bearer {issued.bearer_token}")
            assert response.status_code == 403, label
            body = response.content.decode()
            assert "bearer-control-gpu" not in body
            assert "openapi" not in body


@pytest.mark.django_db
def test_service_account_superuser_is_denied_on_all_four() -> None:
    service = User.objects.create_user(
        email="service-super@example.invalid",
        password=PASSWORD,
        is_staff=True,
        is_superuser=True,
        is_service_account=True,
    )
    asset = Asset.objects.create(
        slug="service-super-gpu",
        name="Service Super GPU",
        kind=Asset.KIND_GPU,
        active=True,
        reservable=True,
    )
    client = Client()
    client.force_login(service)
    with override_settings(API_DOCS_PUBLIC=False):
        for label, path in _routes(asset.id).items():
            response = client.get(path)
            assert response.status_code == 403, label
            body = response.content.decode()
            assert "service-super-gpu" not in body
            assert "openapi" not in body


@pytest.mark.django_db
def test_inactive_staff_session_is_denied_on_all_four() -> None:
    staff = User.objects.create_user(
        email="inactive-staff@example.invalid", password=PASSWORD, is_staff=True
    )
    staff.is_active = False
    staff.save(update_fields=["is_active"])
    asset = Asset.objects.create(
        slug="inactive-staff-gpu",
        name="Inactive Staff GPU",
        kind=Asset.KIND_GPU,
        active=True,
        reservable=True,
    )
    client = Client()
    client.force_login(staff)
    with override_settings(API_DOCS_PUBLIC=False):
        for label, path in _routes(asset.id).items():
            response = client.get(path)
            assert response.status_code == 403, label
            assert "inactive-staff-gpu" not in response.content.decode()


@pytest.mark.django_db
def test_staff_flag_removed_from_existing_session_is_denied() -> None:
    staff = User.objects.create_user(
        email="staff-removed@example.invalid", password=PASSWORD, is_staff=True
    )
    asset = Asset.objects.create(
        slug="staff-removed-gpu",
        name="Staff Removed GPU",
        kind=Asset.KIND_GPU,
        active=True,
        reservable=True,
    )
    client = Client()
    client.force_login(staff)
    with override_settings(API_DOCS_PUBLIC=False):
        for label, path in _routes(asset.id).items():
            assert client.get(path).status_code == 200, label

        User.objects.filter(pk=staff.pk).update(is_staff=False)

        for label, path in _routes(asset.id).items():
            response = client.get(path)
            assert response.status_code == 403, label
            assert "staff-removed-gpu" not in response.content.decode()

        guessed = f"/api/v1/assets/{uuid.uuid4()}/"
        guessed_status = client.get(guessed).status_code
        real_status = client.get(f"/api/v1/assets/{asset.id}/").status_code
        assert guessed_status == real_status


@pytest.mark.django_db
def test_nonstaff_with_unrelated_grants_is_denied() -> None:
    member = User.objects.create_user(email="grants-only@example.invalid", password=PASSWORD)
    view_all = Permission.objects.get(
        codename="view_all_reservations", content_type__app_label="reservations"
    )
    view_asset = Permission.objects.get(codename="view_asset", content_type__app_label="assets")
    member.user_permissions.add(view_all, view_asset)
    asset = Asset.objects.create(
        slug="grants-only-gpu",
        name="Grants Only GPU",
        kind=Asset.KIND_GPU,
        active=True,
        reservable=True,
    )
    client = Client()
    client.force_login(member)
    with override_settings(API_DOCS_PUBLIC=False):
        for label, path in _routes(asset.id).items():
            response = client.get(path)
            assert response.status_code == 403, label
            assert "grants-only-gpu" not in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize("make_user", ["staff", "superuser"])
def test_active_human_staff_and_superuser_retain_read_access(make_user: str) -> None:
    overrides = (
        {"is_staff": True, "is_superuser": True} if make_user == "superuser" else {"is_staff": True}
    )
    human = User.objects.create_user(
        email=f"active-{make_user}@example.invalid", password=PASSWORD, **overrides
    )
    asset = Asset.objects.create(
        slug=f"active-{make_user}-gpu",
        name=f"Active {make_user.title()} GPU",
        kind=Asset.KIND_GPU,
        active=True,
        reservable=True,
    )
    client = Client()
    client.force_login(human)
    with override_settings(API_DOCS_PUBLIC=False):
        for label, path in _routes(asset.id).items():
            response = client.get(path)
            assert response.status_code == 200, label
            if label == "asset-list":
                assert f"active-{make_user}-gpu" in response.content.decode()


@pytest.mark.django_db
def test_anonymous_is_denied_on_all_four_when_private() -> None:
    asset = Asset.objects.create(
        slug="anonymous-denied-gpu",
        name="Anonymous Denied GPU",
        kind=Asset.KIND_GPU,
        active=True,
        reservable=True,
    )
    client = Client()
    with override_settings(API_DOCS_PUBLIC=False):
        for label, path in _routes(asset.id).items():
            response = client.get(path)
            assert response.status_code == 403, label
            assert "anonymous-denied-gpu" not in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize("path", ["/api/schema/", "/api/docs/"])
def test_local_public_docs_remain_anonymous_readable_by_deliberate_policy(path: str) -> None:
    # The test settings keep the explicit local API_DOCS_PUBLIC=True policy;
    # the public branch is unchanged by the staff-human repair.
    assert Client().get(path).status_code == 200
