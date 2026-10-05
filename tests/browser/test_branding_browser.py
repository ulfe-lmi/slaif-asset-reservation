"""038-a — browser qualification of the optional operator branding (SAR-045).

Default (packaged identity) and one meaningful institutional override fixture
are qualified at 1440 and 390 for the landing, member login, admin login,
member dashboard + form, staff page and admin index. Assertions target the
actual asset requests, the selected imagery, computed CSS, stylesheet order,
the safe invalid-override fallback, and the preserved product/accessibility
contract. Screenshots are privacy-safe (no token/credential surfaces).

Runs from an owned disposable source copy against an owned PostgreSQL 17
project with cleared OAP_ROLE (see TESTING.md).
"""

from __future__ import annotations

import re
from datetime import timedelta
from pathlib import Path

import pytest
from django.test import override_settings
from django.utils import timezone
from playwright.sync_api import Page

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.models import Asset, AssetTag
from slaif_reservation.reservations.models import Reservation, ReservationPolicy

REPO_ROOT = Path(__file__).resolve().parents[2]
CUSTOM = REPO_ROOT / "tests" / "fixtures" / "branding" / "custom"
FALLBACK = REPO_ROOT / "tests" / "fixtures" / "branding" / "fallback"
STATIC_LOGO = "/static/web/brand/slaif-logo.svg"

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


# --- environment control for the live server ---------------------------------


def _branding(value: str | None):
    """Override the setting in-process: the live server thread shares it."""
    return override_settings(BRANDING_DIR=value)


@pytest.fixture
def branding_custom():
    with _branding(str(CUSTOM)):
        yield


@pytest.fixture
def branding_fallback():
    with _branding(str(FALLBACK)):
        yield


@pytest.fixture
def branding_off():
    with _branding(None):
        yield


# --- shared fixtures -----------------------------------------------------------


@pytest.fixture
def member_user() -> User:
    return User.objects.create_user(
        email="brand-member@example.com",
        password="not-a-secret",
        timezone="Europe/Ljubljana",
    )


@pytest.fixture
def staff_user() -> User:
    return User.objects.create_user(
        email="brand-staff@example.com",
        password="not-a-secret",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def machine() -> Asset:
    return Asset.objects.create(
        slug="brand-machine",
        name="Brand Machine",
        kind=Asset.KIND_MACHINE,
        active=True,
        reservable=False,
        verification_required=False,
    )


@pytest.fixture
def asset(machine: Asset) -> Asset:
    child = Asset.objects.create(
        slug="brand-gpu",
        name="Brand GPU",
        kind=Asset.KIND_GPU,
        parent=machine,
        active=True,
        reservable=True,
        verification_required=True,
    )
    child.tags.add(AssetTag.objects.create(slug="brand-tag", name="Brand Tag"))
    return child


@pytest.fixture
def policy(asset: Asset) -> ReservationPolicy:
    return ReservationPolicy.objects.create(
        name="Brand Policy",
        asset=asset,
        active=True,
        min_duration_minutes=30,
        max_duration_minutes=2880,
        booking_horizon_days=7,
        min_lead_minutes=0,
        cancellation_cutoff_minutes=0,
        purpose_required=False,
        max_upcoming_per_principal=50,
        max_concurrent_per_principal=8,
    )


def _login(page: Page, live_server, user: User) -> None:
    page.goto(f"{live_server.url}/login/")
    page.get_by_label("Email").fill(user.email)
    page.get_by_label("Password").fill("not-a-secret")
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server.url}/")


def _screenshot(page: Page, output_path, name: str) -> None:
    path = f"{output_path}/{name}.png"
    page.wait_for_function(
        "Array.from(document.images).every(i => "
        "i.complete && i.naturalWidth > 0 && i.naturalHeight > 0)"
    )
    page.screenshot(path=path)


def _assert_no_framework_branding(page: Page) -> None:
    text = page.locator("body").inner_text()
    for marker in FRAMEWORK_MARKERS:
        assert marker not in text, f"framework branding visible: {marker}"


def _assert_no_horizontal_overflow(page: Page) -> None:
    overflow = page.evaluate(
        "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
    )
    assert not overflow, "horizontal overflow detected"


def _stylesheet_index(page: Page, fragment: str) -> int:
    hrefs = page.evaluate(
        """() => Array.from(document.styleSheets).map(
              (sheet) => sheet.href || "")"""
    )
    for index, href in enumerate(hrefs):
        if fragment in href:
            return index
    return -1


def _css_var(page: Page, name: str) -> str:
    return page.evaluate(
        """(name) => getComputedStyle(document.documentElement)
                .getPropertyValue(name).trim()""",
        name,
    )


def _assert_logo_slot(page: Page, *, compact_visible: bool) -> None:
    primary = page.locator("img.brand-logo").first
    compact = page.locator("img.brand-logo-compact").first
    assert primary.count() >= 1 and compact.count() >= 1
    assert primary.is_visible() is not compact_visible
    assert compact.is_visible() is compact_visible


def _assert_selected_assets(
    page: Page,
    live_server,
    *,
    hero: str | None = None,
    favicon_type: str = "image/svg+xml",
) -> None:
    """The selected imagery is actually requested and served successfully."""
    icon = page.locator('link[rel="icon"]').first
    assert icon.get_attribute("type") == favicon_type
    if hero == "/branding/hero":
        hero_img = page.locator("img.landing-logo")
        assert hero_img.get_attribute("src") == "/branding/hero"
        with page.expect_response(
            lambda response: "/branding/hero" in response.url
            and response.request.resource_type == "image"
        ) as info:
            page.reload()
        assert info.value.status == 200
    else:
        assert page.locator("img.landing-logo").get_attribute("src") == STATIC_LOGO


def _assert_css_loaded_after_defaults(
    page: Page, *, custom: bool, default_fragment: str = "site.css"
) -> None:
    if not custom:
        assert _stylesheet_index(page, "/branding/style.css") == -1
        return
    default_index = _stylesheet_index(page, default_fragment)
    custom_index = _stylesheet_index(page, "/branding/style.css")
    assert default_index != -1 and custom_index != -1
    assert custom_index > default_index
    # The operator tokens actually apply (custom CSS wins over defaults).
    assert _css_var(page, "--background") == "#10233f"


# --- landing -------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_landing_default_identity(page: Page, branding_off, live_server, output_path) -> None:
    page.set_viewport_size(DESKTOP)
    page.goto(live_server.url + "/")
    assert page.title() == BRANDING
    _assert_selected_assets(page, live_server, hero=None, favicon_type="image/svg+xml")
    _assert_css_loaded_after_defaults(page, custom=False)
    _assert_logo_slot(page, compact_visible=False)
    _assert_no_framework_branding(page)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-default-landing-1440")
    page.set_viewport_size(MOBILE)
    _assert_logo_slot(page, compact_visible=True)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-default-landing-390")


@pytest.mark.django_db(transaction=True)
def test_landing_custom_branding(page: Page, branding_custom, live_server, output_path) -> None:
    page.set_viewport_size(DESKTOP)
    page.goto(live_server.url + "/")
    assert page.title() == BRANDING
    _assert_selected_assets(page, live_server, hero="/branding/hero", favicon_type="image/png")
    _assert_css_loaded_after_defaults(page, custom=True)
    _assert_logo_slot(page, compact_visible=False)
    assert page.locator("img.brand-logo").get_attribute("src") == "/branding/logo"
    assert page.locator("img.brand-logo-compact").get_attribute("src") == "/branding/logo-compact"
    _assert_no_framework_branding(page)
    _assert_no_horizontal_overflow(page)
    # Screenshots first (unfocused), then the keyboard check, so the captures
    # are representative of the resting state (the focused skip link is a
    # pre-existing focus style that would cover the header in the capture).
    _screenshot(page, output_path, "branding-custom-landing-1440")
    page.keyboard.press("Tab")
    focused = page.evaluate("document.activeElement && document.activeElement.tagName")
    assert focused in ("A", "BUTTON", "SKIP", "SKIP-LINK")
    page.evaluate("document.activeElement.blur()")
    page.set_viewport_size(MOBILE)
    _assert_logo_slot(page, compact_visible=True)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-custom-landing-390")


# --- member login ----------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_member_login_default(page: Page, branding_off, live_server, output_path) -> None:
    page.set_viewport_size(DESKTOP)
    page.goto(live_server.url + "/login/")
    assert page.title() == "Log in — SLAIF Asset Reservation"
    assert page.locator('input[name="csrfmiddlewaretoken"]').count() == 1
    assert page.locator("img.brand-logo").get_attribute("src") == STATIC_LOGO
    _assert_css_loaded_after_defaults(page, custom=False)
    _assert_logo_slot(page, compact_visible=False)
    _assert_no_framework_branding(page)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-default-member-login-1440")
    page.set_viewport_size(MOBILE)
    _assert_logo_slot(page, compact_visible=True)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-default-member-login-390")


@pytest.mark.django_db(transaction=True)
def test_member_login_custom(page: Page, branding_custom, live_server, output_path) -> None:
    page.set_viewport_size(DESKTOP)
    page.goto(live_server.url + "/login/")
    assert page.title() == "Log in — SLAIF Asset Reservation"
    assert page.locator('input[name="csrfmiddlewaretoken"]').count() == 1
    icon = page.locator('link[rel="icon"]').first
    assert icon.get_attribute("href") == "/branding/favicon"
    assert icon.get_attribute("type") == "image/png"
    assert page.locator("img.brand-logo").get_attribute("src") == "/branding/logo"
    _assert_css_loaded_after_defaults(page, custom=True)
    _assert_logo_slot(page, compact_visible=False)
    _assert_no_framework_branding(page)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-custom-member-login-1440")
    page.set_viewport_size(MOBILE)
    _assert_logo_slot(page, compact_visible=True)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-custom-member-login-390")


# --- admin login -----------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_admin_login_default(page: Page, branding_off, live_server, output_path) -> None:
    page.set_viewport_size(DESKTOP)
    page.goto(live_server.url + "/admin/login/")
    assert page.locator("#site-name img.admin-brand-logo").get_attribute("src") == STATIC_LOGO
    assert page.locator('link[rel="icon"]').first.get_attribute("type") == "image/svg+xml"
    _assert_css_loaded_after_defaults(page, custom=False, default_fragment="admin-identity.css")
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-default-admin-login-1440")
    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-default-admin-login-390")


@pytest.mark.django_db(transaction=True)
def test_admin_login_custom(page: Page, branding_custom, live_server, output_path) -> None:
    page.set_viewport_size(DESKTOP)
    page.goto(live_server.url + "/admin/login/")
    assert page.locator("#site-name img.admin-brand-logo").get_attribute("src") == "/branding/logo"
    icon = page.locator('link[rel="icon"]').first
    assert icon.get_attribute("href") == "/branding/favicon"
    assert icon.get_attribute("type") == "image/png"
    _assert_css_loaded_after_defaults(page, custom=True, default_fragment="admin-identity.css")
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-custom-admin-login-1440")
    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-custom-admin-login-390")


# --- member dashboard + form -------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_member_dashboard_and_form_default(
    page: Page,
    branding_off,
    live_server,
    output_path,
    member_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    now = timezone.now()
    Reservation.objects.create(
        asset=asset,
        requested_by_user=member_user,
        source=Reservation.SOURCE_WEB,
        status=Reservation.STATUS_CONFIRMED,
        start_at=now + timedelta(hours=3),
        end_at=now + timedelta(hours=4),
        effective_end_at=now + timedelta(hours=4),
    )
    page.set_viewport_size(DESKTOP)
    _login(page, live_server, member_user)
    _assert_css_loaded_after_defaults(page, custom=False)
    _assert_no_framework_branding(page)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-default-member-dashboard-1440")
    page.goto(f"{live_server.url}/assets/{asset.id}/reserve/")
    assert page.locator("form").count() >= 1
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-default-member-form-1440")
    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    assert page.get_by_label(re.compile(r"^Start:?$")).is_visible()
    assert page.locator("#id_start-help").is_visible()
    _screenshot(page, output_path, "branding-default-member-form-390")
    page.goto(f"{live_server.url}/")
    _assert_logo_slot(page, compact_visible=True)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-default-member-dashboard-390")


@pytest.mark.django_db(transaction=True)
def test_member_dashboard_and_form_custom(
    page: Page,
    branding_custom,
    live_server,
    output_path,
    member_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    now = timezone.now()
    Reservation.objects.create(
        asset=asset,
        requested_by_user=member_user,
        source=Reservation.SOURCE_WEB,
        status=Reservation.STATUS_CONFIRMED,
        start_at=now + timedelta(hours=3),
        end_at=now + timedelta(hours=4),
        effective_end_at=now + timedelta(hours=4),
    )
    page.set_viewport_size(DESKTOP)
    _login(page, live_server, member_user)
    _assert_css_loaded_after_defaults(page, custom=True)
    assert page.locator("img.brand-logo").get_attribute("src") == "/branding/logo"
    _assert_no_framework_branding(page)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-custom-member-dashboard-1440")
    page.goto(f"{live_server.url}/assets/{asset.id}/reserve/")
    assert page.locator("form").count() >= 1
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-custom-member-form-1440")
    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    assert page.get_by_label(re.compile(r"^Start:?$")).is_visible()
    assert page.locator("#id_start-help").is_visible()
    _screenshot(page, output_path, "branding-custom-member-form-390")
    page.goto(f"{live_server.url}/")
    _assert_logo_slot(page, compact_visible=True)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-custom-member-dashboard-390")


# --- staff page --------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_staff_page_default(
    page: Page, branding_off, live_server, output_path, staff_user: User, policy: ReservationPolicy
) -> None:
    page.set_viewport_size(DESKTOP)
    _login(page, live_server, staff_user)
    page.goto(f"{live_server.url}/manage/")
    assert "/manage/" in page.url
    _assert_css_loaded_after_defaults(page, custom=False)
    _assert_no_framework_branding(page)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-default-staff-1440")
    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-default-staff-390")


@pytest.mark.django_db(transaction=True)
def test_staff_page_custom(
    page: Page,
    branding_custom,
    live_server,
    output_path,
    staff_user: User,
    policy: ReservationPolicy,
) -> None:
    page.set_viewport_size(DESKTOP)
    _login(page, live_server, staff_user)
    page.goto(f"{live_server.url}/manage/")
    assert "/manage/" in page.url
    _assert_css_loaded_after_defaults(page, custom=True)
    assert page.locator("img.brand-logo").get_attribute("src") == "/branding/logo"
    _assert_no_framework_branding(page)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-custom-staff-1440")
    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-custom-staff-390")


# --- admin index ---------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_admin_index_default(
    page: Page, branding_off, live_server, output_path, staff_user: User, policy: ReservationPolicy
) -> None:
    page.set_viewport_size(DESKTOP)
    _login(page, live_server, staff_user)
    page.goto(f"{live_server.url}/admin/")
    assert page.url.endswith("/admin/")
    _assert_css_loaded_after_defaults(page, custom=False, default_fragment="admin-identity.css")
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-default-admin-index-1440")
    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-default-admin-index-390")


@pytest.mark.django_db(transaction=True)
def test_admin_index_custom(
    page: Page,
    branding_custom,
    live_server,
    output_path,
    staff_user: User,
    policy: ReservationPolicy,
) -> None:
    page.set_viewport_size(DESKTOP)
    _login(page, live_server, staff_user)
    page.goto(f"{live_server.url}/admin/")
    assert page.url.endswith("/admin/")
    _assert_css_loaded_after_defaults(page, custom=True, default_fragment="admin-identity.css")
    assert page.locator("#site-name img.admin-brand-logo").get_attribute("src") == "/branding/logo"
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-custom-admin-index-1440")
    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-custom-admin-index-390")


# --- safe invalid-override fallback ----------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_invalid_compact_override_falls_back_safely(
    page: Page, branding_fallback, live_server, output_path
) -> None:
    """One invalid slot must not break the page or the valid overrides."""
    page.set_viewport_size(MOBILE)
    response = page.goto(live_server.url + "/login/")
    assert response is not None and response.status == 200
    # Valid slots stay selected...
    assert page.locator("img.brand-logo").get_attribute("src") == "/branding/logo"
    _assert_css_loaded_after_defaults(page, custom=True)
    # ...the invalid compact slot falls back to the packaged default.
    assert page.locator("img.brand-logo-compact").get_attribute("src") == STATIC_LOGO
    assert page.locator("img.brand-logo-compact").is_visible()
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "branding-fallback-compact-390")
    page.set_viewport_size(DESKTOP)
    _screenshot(page, output_path, "branding-fallback-compact-1440")


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "css",
    [
        r'@\69mport "http://branding-probe.invalid/slot.css";',
        'body {background-image:image-set("http://branding-probe.invalid/image.png" 1x)}',
    ],
)
def test_resource_gate_has_browser_sensitivity(
    page: Page, live_server, tmp_path: Path, css: str
) -> None:
    attempted: list[str] = []

    def intercept(route):
        attempted.append(route.request.url)
        route.abort()

    page.route("http://branding-probe.invalid/**", intercept)
    # The actual browser recognizes the unsafe construct; no external request
    # leaves the intercepted context.
    page.set_content(f"<style>{css}</style><body>Owned fixture</body>")
    page.wait_for_function("document.readyState === 'complete'")
    page.wait_for_timeout(150)
    assert attempted, "negative control did not exercise a browser resource load"
    attempted.clear()
    (tmp_path / "style.css").write_text(css)
    with override_settings(BRANDING_DIR=str(tmp_path)):
        page.goto(live_server.url + "/login/")
        assert page.locator('link[href="/branding/style.css"]').count() == 0
        assert page.get_by_role("button", name="Log in").is_visible()
        assert not attempted


@pytest.mark.django_db(transaction=True)
def test_magic_only_png_falls_back_and_decodes(
    page: Page, live_server, tmp_path: Path, output_path
) -> None:
    (tmp_path / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (tmp_path / "favicon.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    with override_settings(BRANDING_DIR=str(tmp_path)):
        page.goto(live_server.url + "/login/")
        assert page.locator('link[rel="icon"]').get_attribute("href") == STATIC_LOGO
        assert page.locator("img.brand-logo").get_attribute("src") == STATIC_LOGO
        _screenshot(page, output_path, "branding-malformed-png-fallback")
