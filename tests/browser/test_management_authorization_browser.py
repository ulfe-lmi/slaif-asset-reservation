"""Focused Chromium evidence for granular management authority (order 050-a).

Partial-capability, non-staff, active human sessions against real HTTP and
real PostgreSQL: the read-only All reservations browser (list, filters,
pagination, detail, no mutation controls) plus forged-POST denial; a
single-module manager whose other modules and Administration are denied;
blackout overlap privacy without read-all (safe count only); and the audit
reader / export-only split. Default and custom themes at 1440/390, visible
labels and help, mobile menu, keyboard focus, no page overflow and no
user-visible framework branding. Exactly two screenshots are captured and
retained: read-only All reservations at 1440 and partial management at 390.
"""

from __future__ import annotations

import re
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth.models import Permission
from django.test import override_settings
from django.utils import timezone
from playwright.sync_api import Page

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.reservations.models import (
    MaintenanceBlackout,
    Reservation,
)

BRANDING = "SLAIF Asset Reservation"
FRAMEWORK_MARKERS = (
    "Django",
    "Django REST framework",
    "Django administration",
    "Django site admin",
    "Powered by Django",
)

DESKTOP = {"width": 1440, "height": 900}
MOBILE = {"width": 390, "height": 844}
CUSTOM_BRANDING = Path(__file__).resolve().parents[1] / "fixtures/branding/custom"
DISPLAY_TZ = ZoneInfo("Europe/Ljubljana")


def _login(page: Page, live_server, user: User) -> None:
    page.goto(f"{live_server.url}/login/")
    page.get_by_label("Email").fill(user.email)
    page.get_by_label("Password").fill("not-a-secret")
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server.url}/")


def _assert_no_framework_branding(page: Page) -> None:
    for marker in FRAMEWORK_MARKERS:
        assert marker not in page.content(), marker
        assert marker not in page.title()


def _assert_no_horizontal_overflow(page: Page) -> None:
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), (
        "horizontal page overflow"
    )


def _csrf_token(page: Page) -> str:
    """Read the session CSRF token from the always-rendered logout form."""
    return page.locator('form[action$="/logout/"] input[name="csrfmiddlewaretoken"]').input_value()


def _post_form(page: Page, url: str, token: str) -> int:
    """Same-origin form POST with a valid CSRF token, as a forged browser."""
    return page.evaluate(
        """async (args) => {
            const res = await fetch(args.url, {
                method: "POST",
                headers: {"Content-Type": "application/x-www-form-urlencoded"},
                body: "csrfmiddlewaretoken=" + args.token,
                credentials: "same-origin",
                redirect: "manual",
            });
            return res.status;
        }""",
        {"url": url, "token": token},
    )


def _screenshot(page: Page, output_path, name: str) -> None:
    page.screenshot(path=f"{output_path}/{name}.png")


def _make_user(email: str, display_name: str, **extra: object) -> User:
    return User.objects.create_user(
        email=email, password="not-a-secret", display_name=display_name, **extra
    )


def _grant(user: User, codenames: list[str]) -> User:
    user.user_permissions.add(
        *Permission.objects.filter(
            codename__in=list(codenames), content_type__app_label="reservations"
        )
    )
    return user


@pytest.fixture
def machine() -> Asset:
    return Asset.objects.create(
        slug="mgmt-machine",
        name="Mgmt Machine",
        kind=Asset.KIND_MACHINE,
        active=True,
        reservable=False,
        verification_required=False,
    )


@pytest.fixture
def asset_a(machine: Asset) -> Asset:
    return Asset.objects.create(
        slug="mgmt-gpu-a",
        name="Mgmt GPU A",
        kind=Asset.KIND_GPU,
        parent=machine,
        active=True,
        reservable=True,
        verification_required=False,
    )


@pytest.fixture
def asset_b(machine: Asset) -> Asset:
    return Asset.objects.create(
        slug="mgmt-gpu-b",
        name="Mgmt GPU B",
        kind=Asset.KIND_GPU,
        parent=machine,
        active=True,
        reservable=True,
        verification_required=False,
    )


@pytest.fixture
def owner_alpha() -> User:
    return _make_user("mgmt-alpha@example.com", "Alpha Owner")


@pytest.fixture
def owner_beta() -> User:
    return _make_user("mgmt-beta@example.com", "Beta Owner")


@pytest.fixture
def viewer() -> User:
    """Non-staff reader: cross-user reservation browsing only, no mutations."""
    return _grant(
        _make_user("mgmt-viewer@example.com", "Reservation Reader"), ["view_all_reservations"]
    )


@pytest.fixture
def blackout_manager() -> User:
    """Non-staff single-module manager: blackouts only, no read-all."""
    return _grant(
        _make_user("mgmt-blackout@example.com", "Blackout Manager"),
        ["manage_maintenance_blackouts"],
    )


@pytest.fixture
def audit_reader() -> User:
    return _grant(
        _make_user("mgmt-auditreader@example.com", "Audit Reader"), ["view_audit_history"]
    )


@pytest.fixture
def audit_exporter() -> User:
    return _grant(
        _make_user("mgmt-auditexport@example.com", "Audit Exporter"), ["export_audit_history"]
    )


@pytest.fixture
def bulk_reservations(
    asset_a: Asset, asset_b: Asset, owner_alpha: User, owner_beta: User
) -> list[Reservation]:
    """63 synthetic confirmed future reservations: 55 on asset A (two
    pagination pages when filtered) and 8 on asset B."""
    now = timezone.now()
    created: list[Reservation] = []
    for index in range(55):
        start = now + timedelta(days=3, hours=index)
        created.append(
            Reservation.objects.create(
                asset=asset_a,
                requested_by_user=owner_alpha if index % 2 == 0 else owner_beta,
                source=Reservation.SOURCE_WEB,
                status=Reservation.STATUS_CONFIRMED,
                start_at=start,
                end_at=start + timedelta(hours=1),
                effective_end_at=start + timedelta(hours=1),
                purpose=f"mgmt-bulk-a-{index:02d}",
            )
        )
    for index in range(8):
        start = now + timedelta(days=4, hours=index)
        created.append(
            Reservation.objects.create(
                asset=asset_b,
                requested_by_user=owner_beta if index % 2 == 0 else owner_alpha,
                source=Reservation.SOURCE_WEB,
                status=Reservation.STATUS_CONFIRMED,
                start_at=start,
                end_at=start + timedelta(hours=1),
                effective_end_at=start + timedelta(hours=1),
                purpose=f"mgmt-bulk-b-{index:02d}",
            )
        )
    return created


@pytest.fixture
def overlapping_reservation(asset_a: Asset, owner_alpha: User) -> Reservation:
    """One confirmed reservation in a window clear of the bulk fixtures."""
    start = timezone.now() + timedelta(days=1)
    return Reservation.objects.create(
        asset=asset_a,
        requested_by_user=owner_alpha,
        source=Reservation.SOURCE_WEB,
        status=Reservation.STATUS_CONFIRMED,
        start_at=start,
        end_at=start + timedelta(hours=1),
        effective_end_at=start + timedelta(hours=1),
        purpose="mgmt-blackout-canary",
    )


@pytest.fixture
def audit_events(bulk_reservations: list[Reservation]) -> list[AuditEvent]:
    reservation = bulk_reservations[0]
    created = []
    for index, action in enumerate(
        (
            AuditEvent.ACTION_RESERVATION_CREATED,
            AuditEvent.ACTION_RESERVATION_CREATED,
            AuditEvent.ACTION_POLICY_UPDATED,
        )
    ):
        created.append(
            AuditEvent.objects.create(
                occurred_at=timezone.now() - timedelta(hours=index + 1),
                actor_user=None,
                action=action,
                target_type="reservation",
                target_id=reservation.id,
                correlation_id=reservation.id,
                source=AuditEvent.SOURCE_ADMIN,
                metadata={"marker": "050-browser"},
            )
        )
    return created


@pytest.mark.django_db(transaction=True)
def test_browser_read_only_viewer_all_reservations(
    page: Page,
    live_server,
    output_path,
    viewer: User,
    asset_a: Asset,
    bulk_reservations: list[Reservation],
) -> None:
    """Read-all-only nonstaff: useful browser, no mutation controls, no
    Administration, filters and filter-preserving pagination."""
    page.set_viewport_size(DESKTOP)
    _login(page, live_server, viewer)

    # Top navigation: All reservations and Management are offered;
    # Administration is staff-only and must not appear for this user.
    assert page.get_by_role("link", name="All reservations", exact=True).is_visible()
    assert page.get_by_role("link", name="Management", exact=True).is_visible()
    assert page.get_by_role("link", name="Administration", exact=True).count() == 0

    page.get_by_role("link", name="Management", exact=True).click()
    page.wait_for_url(f"{live_server.url}/manage/")
    dashboard = page.inner_text("#content")
    # Partial dashboard: only the authorized read module is counted/linked.
    assert str(Reservation.objects.count()) in dashboard
    assert page.locator('a[href="/manage/reservations/"]').count() >= 1
    assert page.locator('a[href="/manage/policies/"]').count() == 0
    assert page.locator('a[href="/manage/blackouts/"]').count() == 0
    assert page.locator('a[href="/manage/audit/"]').count() == 0

    page.get_by_role("link", name="All reservations", exact=True).first.click()
    page.wait_for_url(f"{live_server.url}/manage/reservations/")
    assert page.get_by_role("heading", name="All reservations", exact=True).is_visible()
    # Visible labels and associated help on the existing filter controls.
    for label in ("Asset:", "Search:", "Status:", "Lifecycle:"):
        assert page.get_by_label(label, exact=True).is_visible()
    content = page.inner_text("#content")
    assert "Confirmed, cancelled or released." in content
    # Page 1 of 2: 50 rows, both owners' identities visible to the reader.
    assert page.locator("tbody tr").count() == 50
    assert "Page 1 of 2" in content
    assert "Alpha Owner" in content
    assert "Beta Owner" in content
    _assert_no_framework_branding(page)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "all-reservations-1440")

    # Filter by asset: the narrowed list still paginates and the
    # previous/next links preserve the filter.
    page.get_by_label("Asset:", exact=True).select_option(label="Mgmt Machine / Mgmt GPU A")
    page.get_by_role("button", name="Filter").click()
    page.wait_for_url(lambda url: "asset=" in url)
    assert page.locator("tbody tr").count() == 50
    assert "Page 1 of 2" in page.inner_text(".pagination")
    next_href = page.get_by_role("link", name="Next").get_attribute("href") or ""
    assert "asset=" in next_href and "page=2" in next_href
    page.get_by_role("link", name="Next").click()
    page.wait_for_url(lambda url: "page=2" in url)
    assert page.locator("tbody tr").count() == 5
    assert "mgmt-gpu-b" not in page.inner_text("table")
    prev_href = page.get_by_role("link", name="Previous").get_attribute("href") or ""
    assert "asset=" in prev_href and "page=1" in prev_href

    # A filter matching nothing is a safe empty list, not an error.
    page.get_by_label("Search:", exact=True).fill("no-such-owner-xyz")
    page.get_by_role("button", name="Filter").click()
    page.wait_for_url(lambda url: "no-such-owner-xyz" in url)
    assert "No reservations." in page.inner_text("#content")

    # Detail: authorized read-only representation without mutation controls.
    target = bulk_reservations[0]
    page.goto(f"{live_server.url}/manage/reservations/{target.id}/")
    assert page.get_by_role("heading", name="Reservation details", exact=True).is_visible()
    detail = page.inner_text("#content")
    assert str(target.id) in detail
    assert "Alpha Owner" in detail
    assert "Lifecycle" in detail and "upcoming" in detail
    assert "Effective end" in detail
    assert page.get_by_role("button", name="Cancel reservation").count() == 0
    assert page.get_by_role("button", name="Release reservation").count() == 0
    assert (
        "You can view this reservation but you do not have the management "
        "capability to cancel or release it." in detail
    )

    # Keyboard focus reaches interactive controls from the top of the page.
    page.goto(f"{live_server.url}/manage/reservations/")
    page.keyboard.press("Tab")
    focused = page.evaluate("document.activeElement && document.activeElement.tagName")
    assert focused in ("A", "BUTTON", "SKIP", "SKIP-LINK")

    # Custom theme: same surface stays clean at both widths.
    with override_settings(BRANDING_DIR=str(CUSTOM_BRANDING)):
        page.goto(f"{live_server.url}/manage/reservations/")
        _assert_no_framework_branding(page)
        _assert_no_horizontal_overflow(page)
        page.set_viewport_size(MOBILE)
        _assert_no_horizontal_overflow(page)

    # Mobile: the primary navigation collapses into the toggle menu.
    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    toggle = page.get_by_role("button", name="Menu")
    assert toggle.is_visible()
    nav_link = page.locator("#cross-user-navigation").get_by_role(
        "link", name="All reservations", exact=True
    )
    assert not nav_link.is_visible()
    toggle.click()
    assert nav_link.is_visible()
    page.keyboard.press("Escape")
    assert not nav_link.is_visible()


@pytest.mark.django_db(transaction=True)
def test_browser_read_only_viewer_forged_mutation_posts_denied(
    page: Page,
    live_server,
    viewer: User,
    bulk_reservations: list[Reservation],
) -> None:
    """A read-only viewer cannot cancel/release even with a valid CSRF
    token: 403 and no domain or audit change."""
    page.set_viewport_size(DESKTOP)
    _login(page, live_server, viewer)
    target = bulk_reservations[0]
    audits_before = AuditEvent.objects.count()

    page.goto(f"{live_server.url}/manage/reservations/{target.id}/")
    token = _csrf_token(page)
    for action in ("cancel", "release"):
        status = _post_form(
            page,
            f"{live_server.url}/manage/reservations/{target.id}/{action}/",
            token,
        )
        assert status == 403, action

    target.refresh_from_db()
    assert target.status == Reservation.STATUS_CONFIRMED
    assert AuditEvent.objects.count() == audits_before


@pytest.mark.django_db(transaction=True)
def test_browser_single_module_manager_partial_access(
    page: Page,
    live_server,
    output_path,
    blackout_manager: User,
) -> None:
    """A single-module (blackouts) nonstaff manager: their module is
    actionable, every other module and Administration are denied."""
    page.set_viewport_size(DESKTOP)
    _login(page, live_server, blackout_manager)

    assert page.get_by_role("link", name="Administration", exact=True).count() == 0
    page.get_by_role("link", name="Management", exact=True).click()
    page.wait_for_url(f"{live_server.url}/manage/")
    dashboard = page.inner_text("#content")
    assert "Active blackouts" in dashboard
    assert "Policies" not in dashboard
    assert "All reservations" not in dashboard
    assert "Audit" not in dashboard

    # Direct access to every other module is a 403, not a hidden redirect.
    for path in ("/manage/policies/", "/manage/reservations/", "/manage/audit/"):
        response = page.request.get(f"{live_server.url}{path}")
        assert response.status == 403, path
    # Administration is staff-only: a non-staff session is refused at the
    # admin login, never served the admin index.
    response = page.request.get(f"{live_server.url}/admin/")
    assert "/admin/login/" in response.url

    # The authorized module renders with its creation action.
    page.get_by_role("link", name="Blackouts", exact=True).click()
    page.wait_for_url(f"{live_server.url}/manage/blackouts/")
    assert page.get_by_role("heading", name="Maintenance blackouts", exact=True).is_visible()
    assert page.get_by_role("link", name="Create blackout").is_visible()
    _assert_no_framework_branding(page)
    _assert_no_horizontal_overflow(page)

    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "partial-management-390")


@pytest.mark.django_db(transaction=True)
def test_browser_blackout_manager_without_read_all_safe_overlap(
    page: Page,
    live_server,
    blackout_manager: User,
    asset_a: Asset,
    overlapping_reservation: Reservation,
    owner_alpha: User,
) -> None:
    """Blackout create and detail without read-all disclose only the safe
    overlap count: no owner names, UUIDs, purposes or links."""
    page.set_viewport_size(DESKTOP)
    _login(page, live_server, blackout_manager)
    page.goto(f"{live_server.url}/manage/blackouts/new/")
    assert page.get_by_role("heading", name="Create maintenance blackout", exact=True).is_visible()

    local_start = (overlapping_reservation.start_at - timedelta(minutes=15)).astimezone(DISPLAY_TZ)
    local_end = (overlapping_reservation.end_at + timedelta(minutes=15)).astimezone(DISPLAY_TZ)
    page.get_by_label("Asset:", exact=True).select_option(label="Mgmt Machine / Mgmt GPU A")
    page.get_by_label("Start:", exact=True).fill(local_start.strftime("%Y-%m-%dT%H:%M"))
    page.get_by_label("End:", exact=True).fill(local_end.strftime("%Y-%m-%dT%H:%M"))
    page.get_by_label("Reason:", exact=True).fill("planned maintenance (synthetic)")
    page.get_by_role("button", name="Create blackout").click()

    # Unconfirmed submission: the explicit overlap warning shows the safe
    # count only, and no canary may leak through any element or attribute.
    assert "Overlapping reservations" in page.inner_text("#content")
    body = page.content()
    assert "1 confirmed or released reservation overlaps this period." in body
    assert (
        "You cannot see who owns them because you do not have cross-user "
        "reservation viewing." in body
    )
    for canary in (
        owner_alpha.email,
        owner_alpha.display_name,
        str(overlapping_reservation.id),
        overlapping_reservation.purpose,
    ):
        assert canary not in body, canary

    # Explicit confirmation creates the blackout without row disclosure.
    page.get_by_label("Create despite overlapping reservations:").check()
    page.get_by_role("button", name="Create blackout").click()
    page.wait_for_url(re.compile(r"/manage/blackouts/[0-9a-f-]{36}/$"))
    assert MaintenanceBlackout.objects.count() == 1
    detail_body = page.content()
    assert page.get_by_role("heading", name="Maintenance blackout", exact=True).is_visible()
    assert "Affected reservations" in detail_body
    assert "1 confirmed or released reservation overlaps this period." in detail_body
    for canary in (owner_alpha.email, str(overlapping_reservation.id)):
        assert canary not in detail_body, canary
    # The manager keeps their own module's deactivation action.
    assert page.get_by_role("button", name="Deactivate blackout").is_visible()
    _assert_no_framework_branding(page)
    _assert_no_horizontal_overflow(page)


@pytest.mark.django_db(transaction=True)
def test_browser_audit_reader_without_export_and_export_only_download(
    page: Page,
    live_server,
    audit_reader: User,
    audit_exporter: User,
    bulk_reservations: list[Reservation],
    audit_events: list[AuditEvent],
) -> None:
    """Audit reader sees the bounded list but no export; export-only gets a
    usable filtered download on the dashboard and no audit list UI."""
    page.set_viewport_size(DESKTOP)
    _login(page, live_server, audit_reader)
    page.goto(f"{live_server.url}/manage/audit/")
    assert page.get_by_role("heading", name="Audit log", exact=True).is_visible()
    assert page.locator("tbody tr").count() == len(audit_events)
    assert page.get_by_role("link", name="Export CSV").count() == 0
    assert page.request.get(f"{live_server.url}/manage/audit/export.csv").status == 403
    _assert_no_framework_branding(page)
    _assert_no_horizontal_overflow(page)

    page.get_by_role("button", name="Logout").click()
    page.wait_for_url(f"{live_server.url}/login/")
    _login(page, live_server, audit_exporter)

    # No audit browser or detail for the exporter.
    assert page.request.get(f"{live_server.url}/manage/audit/").status == 403
    page.goto(f"{live_server.url}/manage/")
    dashboard = page.inner_text("#content")
    assert "You have limited management access" in dashboard
    assert page.get_by_role("heading", name="Export audit history", exact=True).is_visible()

    # The small dashboard form filters the existing audit CSV export.
    page.get_by_label("Action:", exact=True).select_option(label="Reservation created")
    with page.expect_download() as download_info:
        page.get_by_role("button", name="Export CSV").click()
    download = download_info.value
    assert download.suggested_filename == "slaif-audit-export.csv"
    csv_body = Path(download.path()).read_text()
    assert csv_body.startswith("occurred_at,action,target_type,")
    assert str(bulk_reservations[0].id) in csv_body
    assert "reservation.created" in csv_body
    assert "reservation_policy" not in csv_body
    # Bounded, privacy-minimized representation: no owner free text.
    assert "@example.com" not in csv_body
