from __future__ import annotations

import re
from datetime import timedelta
from typing import Any

import pytest
from django.contrib import admin
from django.contrib.auth import SESSION_KEY
from django.test import Client, RequestFactory, override_settings
from django.utils import timezone

from slaif_reservation.accounts.models import ApiToken, User
from slaif_reservation.accounts.services import issue_api_token
from slaif_reservation.assets.models import Asset, AssetTag
from slaif_reservation.config.admin_site import SlaifAdminSite
from slaif_reservation.reservations.models import Reservation, ReservationPolicy

BRANDING = "SLAIF Asset Reservation"
FRAMEWORK_MARKERS = (
    "Django",
    "Django administration",
    "Django site admin",
    "Django REST framework",
    "Powered by Django",
)

CANARY_USER_EMAIL = "canary-member-036a@example.test"
CANARY_USER_NAME = "Canary Member 036A"
CANARY_ASSET_NAME = "Canary GPU 036A"
CANARY_TAG = "canary-tag-036a"
CANARY_PURPOSE = "canary-purpose-036a"
CANARY_TOKEN_NAME = "canary-token-036a"


@pytest.fixture
def member_user() -> User:
    return User.objects.create_user(
        email="member@example.com",
        password="not-a-secret",
        display_name="Member User",
        timezone="Europe/Ljubljana",
    )


@pytest.fixture
def staff_user() -> User:
    return User.objects.create_user(
        email="staff@example.com",
        password="not-a-secret",
        is_staff=True,
    )


@pytest.fixture
def service_account() -> User:
    return User.objects.create_user(
        email="agent@example.com",
        password="not-a-secret",
        is_service_account=True,
    )


@pytest.fixture
def machine() -> Asset:
    return Asset.objects.create(
        slug="machine-a",
        name="Machine A",
        kind=Asset.KIND_MACHINE,
        active=True,
        reservable=False,
        verification_required=False,
    )


@pytest.fixture
def asset(machine: Asset) -> Asset:
    return Asset.objects.create(
        slug="gpu-a",
        name="GPU A",
        kind=Asset.KIND_GPU,
        parent=machine,
        active=True,
        reservable=True,
        verification_required=True,
    )


@pytest.fixture
def policy(asset: Asset) -> ReservationPolicy:
    return ReservationPolicy.objects.create(
        name="Member test policy",
        asset=asset,
        active=True,
        min_duration_minutes=30,
        max_duration_minutes=240,
        booking_horizon_days=30,
        min_lead_minutes=0,
        cancellation_cutoff_minutes=0,
        max_upcoming_per_principal=10,
        max_concurrent_per_principal=2,
        purpose_required=False,
    )


@pytest.fixture
def admin_user() -> User:
    return User.objects.create_user(
        email="admin-036a@example.test",
        password="not-a-secret",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def canary_data(member_user: User, machine: Asset, asset: Asset, policy: ReservationPolicy):
    """Private synthetic canaries that must never appear on public surfaces."""
    asset.name = CANARY_ASSET_NAME
    asset.save(update_fields=["name"])
    tag = AssetTag.objects.create(slug=CANARY_TAG, name=CANARY_TAG)
    asset.tags.add(tag)
    start = timezone.now() - timedelta(days=1)
    end = start + timedelta(hours=1)
    reservation = Reservation.objects.create(
        asset=asset,
        requested_by_user=member_user,
        source=Reservation.SOURCE_WEB,
        status=Reservation.STATUS_CONFIRMED,
        start_at=start,
        end_at=end,
        effective_end_at=end,
        purpose=CANARY_PURPOSE,
    )
    token = issue_api_token(
        owner=member_user,
        name=CANARY_TOKEN_NAME,
        scopes=["reservations:read"],
        lifetime_days=1,
    ).token
    return {"asset": asset, "tag": tag, "reservation": reservation, "token": token}


def _assert_error_response(response: Any, status_code: int) -> None:
    assert response.status_code == status_code
    content = response.content.decode()
    assert BRANDING in content
    assert "Traceback" not in content
    assert 'href="/static/web/brand/slaif-logo.svg"' in content


def _assert_no_framework_branding(content: str) -> None:
    lowered = content.lower()
    for marker in FRAMEWORK_MARKERS:
        assert marker not in content
    assert "django-rest-framework.org" not in lowered


def _assert_no_canaries(content: str, canary_data: Any, member_user: User) -> None:
    for marker in (
        CANARY_USER_EMAIL,
        CANARY_USER_NAME,
        CANARY_ASSET_NAME,
        CANARY_TAG,
        CANARY_PURPOSE,
        CANARY_TOKEN_NAME,
        str(member_user.id),
    ):
        assert marker not in content


@pytest.mark.django_db
def test_anonymous_landing_shows_product_identity_and_ctas(client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    content = response.content.decode()
    assert f"<title>{BRANDING}</title>" in content
    assert 'src="/static/web/brand/slaif-logo.svg"' in content
    assert BRANDING in content
    # Obvious actions with exact targets.
    assert '<a class="button" href="/login/">Log in</a>' in content
    assert '<a class="button button-secondary" href="/admin/">Administration</a>' in content
    # No member workflow menu for anonymous visitors.
    assert "My reservations" not in content
    assert "API tokens" not in content
    assert 'href="/assets/"' not in content
    _assert_no_framework_branding(content)


@pytest.mark.django_db
def test_anonymous_landing_discloses_no_private_canaries(
    client, canary_data: Any, member_user: User
) -> None:
    response = client.get("/")
    assert response.status_code == 200
    _assert_no_canaries(response.content.decode(), canary_data, member_user)


@pytest.mark.django_db
def test_root_dispatches_by_role_without_redirect_loops(
    client, member_user: User, staff_user: User, admin_user: User
) -> None:
    # Anonymous: landing directly.
    response = client.get("/")
    assert response.status_code == 200

    # Ordinary active human: dashboard, member menu, no staff entries.
    client.force_login(member_user)
    response = client.get("/", follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == []
    content = response.content.decode()
    for label in ("Dashboard", "Assets", "My reservations", "API tokens", "Profile", "Logout"):
        assert label in content
    assert "Management" not in content
    assert "Administration" not in content

    # Staff: member menu plus Management and Administration.
    client.force_login(staff_user)
    response = client.get("/")
    assert response.status_code == 200
    content = response.content.decode()
    assert 'href="/manage/"' in content
    assert 'href="/admin/"' in content

    # Permitted administrator: same navigation reaches administration.
    client.force_login(admin_user)
    response = client.get("/")
    assert response.status_code == 200
    assert 'href="/admin/"' in response.content.decode()


@pytest.mark.django_db
def test_disallowed_sessions_still_terminate_on_root(client, service_account: User) -> None:
    client.force_login(service_account)
    response = client.get("/", follow=True)

    assert response.status_code == 200
    assert response.request["PATH_INFO"] == "/login/"
    assert SESSION_KEY not in client.session
    content = response.content.decode()
    assert "Dashboard" not in content
    # Public entry navigation is shown to the terminated visitor.
    assert 'href="/admin/"' in content


@pytest.mark.django_db
def test_admin_login_rejects_non_human_identities(
    client, staff_user: User, service_account: User, admin_user: User
) -> None:
    # Anonymous reaches the branded administration login.
    response = client.get("/admin/")
    assert response.status_code == 302
    assert response["Location"] == "/admin/login/?next=/admin/"

    response = client.get("/admin/login/")
    assert response.status_code == 200
    login_content = response.content.decode()
    assert BRANDING + " administration" in login_content
    assert 'name="csrfmiddlewaretoken"' in login_content
    _assert_no_framework_branding(login_content)

    # Service account: generic denial, no specific wording, session cleared.
    client.force_login(service_account)
    response = client.post(
        "/admin/login/",
        {"username": service_account.email, "password": "not-a-secret"},
    )
    assert response.status_code == 200
    assert b"Enter a valid email address and password" in response.content
    assert b"service" not in response.content.lower()
    assert SESSION_KEY not in client.session

    # Inactive staff: same generic denial.
    staff_user.is_active = False
    staff_user.save(update_fields=["is_active"])
    client.force_login(staff_user)
    response = client.post(
        "/admin/login/",
        {"username": staff_user.email, "password": "not-a-secret"},
    )
    assert response.status_code == 200
    assert b"Enter a valid email address and password" in response.content
    assert SESSION_KEY not in client.session

    # Active staff: admission preserved, with the default post-login
    # redirect semantics (explicit next target, or LOGIN_REDIRECT_URL).
    staff_user.is_active = True
    staff_user.save(update_fields=["is_active"])
    client.force_login(staff_user)
    response = client.post(
        "/admin/login/",
        {
            "username": staff_user.email,
            "password": "not-a-secret",
            "next": "/admin/",
        },
    )
    assert response.status_code == 302
    assert response["Location"] == "/admin/"
    response = client.post(
        "/admin/login/",
        {"username": staff_user.email, "password": "not-a-secret"},
    )
    assert response.status_code == 302
    assert response["Location"] == "/"


@pytest.mark.django_db
def test_admin_login_rejects_non_staff_members(client, member_user: User) -> None:
    # A valid active member credential must not create an administration
    # session: generic denial, no session, no credential-class wording.
    response = client.post(
        "/admin/login/",
        {"username": member_user.email, "password": "not-a-secret"},
    )

    assert response.status_code == 200
    assert b"Enter a valid email address and password" in response.content
    lowered = response.content.decode().lower()
    assert "staff" not in lowered
    assert "service" not in lowered
    assert SESSION_KEY not in client.session

    # Normal member-login access is preserved.
    client.force_login(member_user)
    assert client.get("/").status_code == 200


@pytest.mark.django_db
def test_admin_routes_deny_and_terminate_service_account_session(
    client, service_account: User
) -> None:
    # A staff service-account session is denied on every admin route and
    # terminated on the login view, not only at login time.
    service_account.is_staff = True
    service_account.save(update_fields=["is_staff"])

    for path in (
        "/admin/",
        "/admin/accounts/user/",
        "/admin/assets/asset/",
        "/admin/reservations/reservation/",
    ):
        client.force_login(service_account)
        response = client.get(path, follow=True)

        assert response.status_code == 200, path
        assert response.redirect_chain, path
        assert response.request["PATH_INFO"] == "/admin/login/", path
        # The disallowed session is terminated, not merely denied.
        assert SESSION_KEY not in client.session, path
        # No administration model content on the resulting page.
        assert "Api tokens" not in response.content.decode(), path


@pytest.mark.django_db
def test_admin_access_denied_after_account_flags_change(client, staff_user: User) -> None:
    # A previously valid human session loses every admin route as soon as
    # the operator changes the account flags.
    client.force_login(staff_user)
    assert client.get("/admin/").status_code == 200

    staff_user.is_service_account = True
    staff_user.save(update_fields=["is_service_account"])
    response = client.get("/admin/", follow=True)
    assert response.status_code == 200
    assert response.request["PATH_INFO"] == "/admin/login/"
    assert SESSION_KEY not in client.session
    assert "Api tokens" not in response.content.decode()

    # Inactive variant on a fresh valid human session, checked on a model
    # changelist as well as the index.
    staff_user.is_service_account = False
    staff_user.save(update_fields=["is_service_account"])
    client.force_login(staff_user)
    assert client.get("/admin/").status_code == 200

    staff_user.is_active = False
    staff_user.save(update_fields=["is_active"])
    response = client.get("/admin/accounts/user/", follow=True)
    assert response.status_code == 200
    assert response.request["PATH_INFO"] == "/admin/login/"
    assert SESSION_KEY not in client.session


@pytest.mark.django_db
def test_non_staff_member_denied_administration_without_session_loss(
    client, member_user: User
) -> None:
    client.force_login(member_user)
    response = client.get("/admin/", follow=True)

    assert response.status_code == 200
    assert response.request["PATH_INFO"] == "/admin/login/"
    # A valid member session is denied, not terminated.
    assert SESSION_KEY in client.session
    content = client.get("/").content.decode()
    assert "Dashboard" in content


@pytest.mark.django_db
def test_valid_staff_admin_matrix_preserved(
    client, rf: RequestFactory, staff_user: User, admin_user: User
) -> None:
    from slaif_reservation.audit.models import AuditEvent
    from slaif_reservation.reservations.models import MaintenanceBlackout, Reservation

    # Permitted administrator: full site admission, all apps, protected
    # models stay read-only.
    client.force_login(admin_user)
    response = client.get("/admin/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "<h1>Administration</h1>" in content
    for app in ("Accounts", "Assets", "Audit", "Reservations"):
        assert app in content

    for path in (
        "/admin/accounts/user/",
        "/admin/accounts/apitoken/",
        "/admin/audit/auditevent/",
        "/admin/reservations/reservation/",
    ):
        response = client.get(path)
        assert response.status_code == 200, path
        assert "Add API token" not in response.content.decode(), path

    # Active staff without model permissions: admitted to the site, model
    # content still follows the existing per-model permission checks.
    client.force_login(staff_user)
    response = client.get("/admin/")
    assert response.status_code == 200
    assert "Api tokens" not in response.content.decode()
    assert client.get("/admin/accounts/apitoken/").status_code == 403

    # Protected read-only mutation boundaries stay unchanged.
    request = rf.get("/admin/accounts/apitoken/")
    request.user = admin_user
    for model in (ApiToken, AuditEvent, Reservation, MaintenanceBlackout):
        model_admin = admin.site._registry[model]
        assert model_admin.has_add_permission(request) is False, model
        assert model_admin.has_change_permission(request) is False, model
        assert model_admin.has_delete_permission(request) is False, model


@pytest.mark.django_db
def test_custom_admin_site_identity_and_surfaces(client, admin_user: User) -> None:
    from django.apps import apps

    assert apps.get_app_config("admin").default_site == (
        "slaif_reservation.config.admin_site.SlaifAdminSite"
    )
    _ = admin.site.site_header  # force lazy setup
    assert isinstance(admin.site._wrapped, SlaifAdminSite)
    assert admin.site.site_title == BRANDING + " administration"
    assert admin.site.site_header == BRANDING + " administration"
    assert admin.site.index_title == "Administration"

    client.force_login(admin_user)
    response = client.get("/admin/")
    assert response.status_code == 200
    content = response.content.decode()
    assert BRANDING + " administration" in content
    assert "<h1>Administration</h1>" in content
    assert 'href="/static/web/brand/slaif-logo.svg"' in content
    # Registered app surfaces remain visible.
    assert "Assets" in content
    _assert_no_framework_branding(content)

    # Breadcrumb identity on model pages (the index has none by design).
    response = client.get("/admin/accounts/user/")
    assert response.status_code == 200
    changelist = response.content.decode()
    assert '<a href="/admin/">Administration</a>' in changelist
    _assert_no_framework_branding(changelist)


@pytest.mark.django_db
def test_no_framework_branding_on_browser_surfaces(
    client, member_user: User, staff_user: User, admin_user: User
) -> None:
    pages: list[tuple[str, Any]] = [
        ("/", None),
        ("/login/", None),
        ("/admin/login/", None),
    ]
    for path, user in pages:
        if user is not None:
            client.force_login(user)
        response = client.get(path)
        assert response.status_code == 200, path
        _assert_no_framework_branding(response.content.decode())

    client.force_login(member_user)
    for path in ("/", "/assets/", "/reservations/", "/tokens/"):
        _assert_no_framework_branding(client.get(path).content.decode())

    client.force_login(staff_user)
    _assert_no_framework_branding(client.get("/manage/").content.decode())

    client.force_login(admin_user)
    _assert_no_framework_branding(client.get("/admin/").content.decode())


@pytest.mark.django_db
def test_branded_generic_error_handlers(rf: RequestFactory, client) -> None:
    from slaif_reservation.config.views import (
        handler400,
        handler403,
        handler404,
        handler500,
    )

    for status_code, handler in [
        (400, handler400),
        (403, handler403),
        (404, handler404),
    ]:
        response = handler(rf.get("/anything/"), exception=None)
        _assert_error_response(response, status_code)
    response = handler500(rf.get("/anything/"))
    _assert_error_response(response, 500)

    # A real missing route serves the branded 404.
    response = client.get("/definitely-not-a-route-036a/")
    assert response.status_code == 404
    content = response.content.decode()
    assert BRANDING in content
    assert "Traceback" not in content
    _assert_no_framework_branding(content)


@pytest.mark.django_db
def test_csrf_failure_is_branded_without_reason(client) -> None:
    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.get("/login/")  # establish the CSRF cookie
    response = csrf_client.post(
        "/login/", {"username": "nobody@example.test", "password": "not-a-secret"}
    )

    assert response.status_code == 403
    content = response.content.decode()
    assert BRANDING in content
    assert "CSRF" not in content
    assert "Traceback" not in content
    _assert_no_framework_branding(content)


@pytest.mark.django_db
def test_error_rendering_is_safe_when_db_is_unavailable(rf: RequestFactory):
    from django.db import connections
    from django.test import Client as TestClient

    from slaif_reservation.config.views import handler404, handler500

    with override_settings(
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "sar036a-unreachable",
                "USER": "slaif",
                "PASSWORD": "slaif",
                "HOST": "127.0.0.1",
                "PORT": "1",
            }
        }
    ):
        connections.close_all()
        for handler in (handler404, handler500):
            response = handler(rf.get("/whatever/"))
        assert response.status_code in (404, 500)
        content = response.content.decode()
        assert BRANDING in content
        assert "Traceback" not in content

        # A fresh anonymous browser request without a session cookie renders
        # the branded 404 even though no database is reachable.
        fresh = TestClient()
        response = fresh.get("/definitely-not-a-route-036a/")
        assert response.status_code == 404
        assert BRANDING in response.content.decode()


@pytest.mark.django_db
def test_browsable_api_identity_and_json_compatibility(
    client, staff_user: User, asset: Asset
) -> None:
    from django.conf import settings

    renderers = settings.REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"]
    assert renderers[0] == "rest_framework.renderers.JSONRenderer"
    assert renderers[-1] == "slaif_reservation.api.renderers.SlaifBrowsableAPIRenderer"

    # JSON contract is unchanged.
    response = client.get("/api/v1/")
    assert response.status_code == 200
    assert response.json()["name"] == BRANDING + " API"
    assert response.json()["endpoints"]["reservations"] == "/api/v1/reservations/"

    # HTML representation carries the product identity.
    response = client.get("/api/v1/", HTTP_ACCEPT="text/html")
    assert response.status_code == 200
    content = response.content.decode()
    assert "SLAIF Asset Reservation API" in content
    _assert_no_framework_branding(content)

    # Anonymous permission boundary stays a branded 403, JSON or HTML.
    assert client.get("/api/v1/assets/", HTTP_ACCEPT="text/html").status_code == 403
    anonymous_html = client.get("/api/v1/assets/", HTTP_ACCEPT="text/html").content.decode()
    _assert_no_framework_branding(anonymous_html)

    # Staff session still renders the existing HTML controls with data.
    client.force_login(staff_user)
    response = client.get(f"/api/v1/assets/{asset.id}/", HTTP_ACCEPT="text/html")
    assert response.status_code == 200
    staff_html = response.content.decode()
    assert asset.name in staff_html
    assert "GET" in staff_html
    _assert_no_framework_branding(staff_html)

    # JSON remains available to the same staff session.
    response = client.get(f"/api/v1/assets/{asset.id}/")
    assert response.status_code == 200
    assert response.json()["slug"] == asset.slug


@pytest.mark.django_db
def test_token_pages_carry_current_scoped_api_guidance(client, member_user: User) -> None:
    client.force_login(member_user)

    for path in ("/tokens/", "/tokens/new/"):
        response = client.get(path)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Work Order 0006" not in content
        assert "not enabled" not in content
        assert "/api/v1/" in content

    # Creation keeps one-time secrecy semantics and the new guidance.
    response = client.post(
        "/tokens/new/",
        {
            "name": "Guidance token",
            "scopes": ["reservations:read"],
            "lifetime_days": "7",
        },
    )
    assert response.status_code == 200
    content = response.content.decode()
    assert "Work Order 0006" not in content
    assert "/api/v1/" in content
    match = re.search(r"sar_[0-9a-f]{32}_[A-Za-z0-9_-]+", content)
    assert match is not None
    bearer_token = match.group(0)
    assert content.count(bearer_token) == 1
    assert response["Cache-Control"] == "no-store, private"
    assert response["Pragma"] == "no-cache"
    assert response["Referrer-Policy"] == "no-referrer"
    assert response.content.count(bearer_token.encode()) == 1

    token = ApiToken.objects.get(owner=member_user)
    assert token.display_prefix in content
    assert token.verifier not in content

    list_response = client.get("/tokens/")
    assert list_response.status_code == 200
    assert bearer_token not in list_response.content.decode()
    assert token.verifier not in list_response.content.decode()
