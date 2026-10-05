from __future__ import annotations

import pytest
from playwright.sync_api import Page

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.models import Asset, AssetTag
from slaif_reservation.reservations.models import Reservation, ReservationPolicy

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


@pytest.fixture
def member_user() -> User:
    return User.objects.create_user(
        email="entry-member@example.com",
        password="not-a-secret",
        timezone="Europe/Ljubljana",
    )


@pytest.fixture
def staff_user() -> User:
    return User.objects.create_user(
        email="entry-staff@example.com",
        password="not-a-secret",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def service_account() -> User:
    return User.objects.create_user(
        email="entry-agent@example.com",
        password="not-a-secret",
        is_service_account=True,
    )


@pytest.fixture
def machine() -> Asset:
    return Asset.objects.create(
        slug="entry-machine",
        name="Entry Machine",
        kind=Asset.KIND_MACHINE,
        active=True,
        reservable=False,
        verification_required=False,
    )


@pytest.fixture
def asset(machine: Asset) -> Asset:
    asset = Asset.objects.create(
        slug="entry-gpu",
        name="Entry GPU",
        kind=Asset.KIND_GPU,
        parent=machine,
        active=True,
        reservable=True,
        verification_required=True,
    )
    asset.tags.add(AssetTag.objects.create(slug="entry-tag", name="Entry Tag"))
    return asset


@pytest.fixture
def policy(asset: Asset) -> ReservationPolicy:
    return ReservationPolicy.objects.create(
        name="Entry policy",
        asset=asset,
        active=True,
        min_duration_minutes=30,
        max_duration_minutes=240,
        booking_horizon_days=30,
        min_lead_minutes=0,
        cancellation_cutoff_minutes=0,
        max_upcoming_per_principal=10,
        max_concurrent_per_principal=3,
        purpose_required=False,
    )


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


def _screenshot(page: Page, output_path, name: str) -> str:
    path = f"{output_path}/{name}.png"
    page.screenshot(path=path)
    return path


@pytest.mark.django_db(transaction=True)
def test_browser_anonymous_landing_identity_and_ctas(page: Page, live_server, output_path) -> None:
    page.set_viewport_size(DESKTOP)
    page.goto(live_server.url + "/")

    assert page.title() == BRANDING
    assert page.get_by_role("heading", name=BRANDING, exact=True).is_visible()
    assert page.locator("img.landing-logo").is_visible()
    assert "shared laboratory" in page.get_by_text("Reserve shared laboratory").inner_text()

    # Obvious, exact public actions in both the nav and the hero CTA row.
    nav = page.get_by_label("Primary navigation")
    hero = page.locator("#content")
    for scope in (nav, hero):
        login_link = scope.get_by_role("link", name="Log in")
        admin_link = scope.get_by_role("link", name="Administration")
        assert login_link.is_visible()
        assert admin_link.is_visible()
        assert login_link.get_attribute("href") == "/login/"
        assert admin_link.get_attribute("href") == "/admin/"
    assert page.get_by_role("link", name="My reservations").count() == 0
    assert page.get_by_role("link", name="API tokens").count() == 0

    _assert_no_framework_branding(page)
    _assert_no_horizontal_overflow(page)

    # Keyboard reachability of the public actions.
    page.keyboard.press("Tab")
    focused = page.evaluate("document.activeElement && document.activeElement.tagName")
    assert focused in ("A", "BUTTON", "SKIP", "SKIP-LINK")
    for _ in range(8):
        page.keyboard.press("Tab")
        label = page.evaluate(
            "document.activeElement ? (document.activeElement.textContent || '').trim() : ''"
        )
        if label in ("Log in", "Administration"):
            break
    else:
        raise AssertionError("public actions not keyboard-reachable")

    _screenshot(page, output_path, "landing-1440")
    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "landing-390")


@pytest.mark.django_db(transaction=True)
def test_browser_landing_login_action_reaches_dashboard(
    page: Page, live_server, output_path, member_user: User, asset: Asset, policy: ReservationPolicy
) -> None:
    from datetime import timedelta

    from django.utils import timezone

    from slaif_reservation.reservations.services import create_reservation

    # Representative populated state: an in-progress own reservation is
    # seeded synthetically (the domain service rejects new bookings with
    # past starts), while the upcoming reservations are created through
    # the existing domain service, enforcing the effective policy,
    # exclusivity and audit.
    now = timezone.now()
    active_end = now + timedelta(minutes=30)
    Reservation.objects.create(
        asset=asset,
        requested_by_user=member_user,
        source=Reservation.SOURCE_WEB,
        status=Reservation.STATUS_CONFIRMED,
        start_at=now - timedelta(minutes=30),
        end_at=active_end,
        effective_end_at=active_end,
        purpose="entry-active-purpose-036b",
    )
    create_reservation(
        asset=asset,
        requested_by_user=member_user,
        start_at=now + timedelta(hours=1),
        end_at=now + timedelta(hours=2),
        purpose="entry-upcoming-purpose-036b",
        now=now,
    )

    page.set_viewport_size(DESKTOP)
    page.goto(live_server.url + "/")
    page.locator("#content").get_by_role("link", name="Log in").click()
    page.wait_for_url(f"{live_server.url}/login/")
    _screenshot(page, output_path, "member-login-1440")

    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "member-login-390")

    page.set_viewport_size(DESKTOP)
    page.get_by_label("Email").fill(member_user.email)
    page.get_by_label("Password").fill("not-a-secret")
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server.url}/")

    assert page.title() == "Dashboard — SLAIF Asset Reservation"
    for label in ("Dashboard", "Assets", "My reservations", "API tokens", "Profile"):
        assert page.get_by_role("link", name=label, exact=True).is_visible()
    assert page.get_by_role("link", name="Management", exact=True).count() == 0
    assert page.get_by_role("link", name="Administration", exact=True).count() == 0

    # Populated dashboard: own reservation, displayed in the member
    # timezone, without private free-text disclosure.
    assert "Active reservation" in page.inner_text("#content")
    assert "Next upcoming reservations" in page.inner_text("#content")
    assert asset.name in page.inner_text("#content")
    assert "Times shown in Europe/Ljubljana." in page.inner_text("header")
    assert "entry-active-purpose-036b" not in page.content()
    assert "entry-upcoming-purpose-036b" not in page.content()
    _assert_no_framework_branding(page)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "member-dashboard-1440")

    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "member-dashboard-390")


@pytest.mark.django_db(transaction=True)
def test_browser_administration_action_enters_admin_login(
    page: Page, live_server, output_path
) -> None:
    page.set_viewport_size(DESKTOP)
    page.goto(live_server.url + "/")
    page.locator("#content").get_by_role("link", name="Administration").click()
    page.wait_for_url(lambda u: u == f"{live_server.url}/admin/login/?next=/admin/")

    assert BRANDING + " administration" in page.title()
    assert page.get_by_text(BRANDING + " administration").first.is_visible()
    assert page.locator("img.admin-brand-logo").is_visible()
    _assert_no_framework_branding(page)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "admin-login-1440")

    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "admin-login-390")


@pytest.mark.django_db(transaction=True)
def test_browser_staff_navigation_management_and_admin_index(
    page: Page, live_server, output_path, staff_user: User
) -> None:
    page.set_viewport_size(DESKTOP)
    _login(page, live_server, staff_user)

    assert page.get_by_role("link", name="Management").is_visible()
    assert page.get_by_role("link", name="Administration").is_visible()
    page.get_by_role("link", name="Management").click()
    page.wait_for_url(f"{live_server.url}/manage/")
    assert "Management" in page.title()
    _assert_no_framework_branding(page)

    page.get_by_role("link", name="Administration").click()
    page.wait_for_url(f"{live_server.url}/admin/")
    assert BRANDING + " administration" in page.title()
    assert page.get_by_role("heading", name="Administration", exact=True).is_visible()
    assert page.get_by_role("link", name="Users").count() >= 1
    _assert_no_framework_branding(page)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "admin-index-1440")

    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "admin-index-390")


@pytest.mark.django_db(transaction=True)
def test_browser_member_is_denied_administration_content(
    page: Page, live_server, member_user: User
) -> None:
    _login(page, live_server, member_user)
    response = page.goto(f"{live_server.url}/admin/")
    assert response is not None
    assert page.url == f"{live_server.url}/admin/login/?next=/admin/"
    assert "Users" not in page.inner_text("main") or page.url.endswith("login/")
    _assert_no_framework_branding(page)


@pytest.mark.django_db(transaction=True)
def test_browser_admin_login_rejects_service_accounts(
    page: Page, live_server, service_account: User
) -> None:
    page.goto(f"{live_server.url}/admin/login/")
    page.get_by_label("Email").fill(service_account.email)
    page.get_by_label("Password").fill("not-a-secret")
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server.url}/admin/login/")

    assert "Enter a valid email address and password" in page.content()
    lowered = page.inner_text("body").lower()
    assert "service" not in lowered
    _assert_no_framework_branding(page)


@pytest.mark.django_db(transaction=True)
def test_browser_admin_login_rejects_non_staff_members(
    page: Page, live_server, member_user: User
) -> None:
    # A valid active member credential is denied at the administration
    # login with the same generic message, and the member's own session
    # access is preserved.
    page.goto(f"{live_server.url}/login/")
    page.get_by_label("Email").fill(member_user.email)
    page.get_by_label("Password").fill("not-a-secret")
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server.url}/")

    page.goto(f"{live_server.url}/admin/login/")
    page.get_by_label("Email").fill(member_user.email)
    page.get_by_label("Password").fill("not-a-secret")
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server.url}/admin/login/")

    assert "Enter a valid email address and password" in page.content()
    lowered = page.inner_text("body").lower()
    assert "staff" not in lowered
    assert "service" not in lowered
    _assert_no_framework_branding(page)

    # Normal member access survives the denied administration attempt.
    page.goto(f"{live_server.url}/")
    assert page.title() == "Dashboard — SLAIF Asset Reservation"


@pytest.mark.django_db(transaction=True)
def test_browser_admin_flag_transition_denies_and_terminates(
    page: Page, live_server, staff_user: User
) -> None:
    # Real HTTP flag transition: a valid human staff session loses every
    # admin route as soon as the operator marks the account a service
    # account, and the session is terminated.
    _login(page, live_server, staff_user)
    page.goto(f"{live_server.url}/admin/")
    page.wait_for_url(f"{live_server.url}/admin/")
    assert page.get_by_role("heading", name="Administration", exact=True).is_visible()

    staff_user.is_service_account = True
    staff_user.save(update_fields=["is_service_account"])

    page.goto(f"{live_server.url}/admin/")
    page.wait_for_url(lambda u: u == f"{live_server.url}/admin/login/?next=/admin/")
    assert "Api tokens" not in page.content()
    _assert_no_framework_branding(page)

    # The terminated session no longer reaches the member dashboard either.
    page.goto(f"{live_server.url}/")
    assert page.title() == BRANDING
    assert "Dashboard" not in page.inner_text("#content")


@pytest.mark.django_db(transaction=True)
def test_browser_browsable_api_html_and_json_controls(
    page: Page, live_server, staff_user: User, asset: Asset, policy: ReservationPolicy
) -> None:
    _login(page, live_server, staff_user)
    page.goto(f"{live_server.url}/api/v1/assets/")

    assert "SLAIF Asset Reservation API" in page.title()
    assert "Django REST framework" not in page.content()
    assert page.get_by_role("link", name="SLAIF Asset Reservation API").is_visible()
    # Existing HTML controls retained.
    assert (
        page.get_by_role("button", name="GET").count()
        + page.get_by_role("link", name="GET").count()
        >= 1
    )
    assert "Entry GPU" in page.content()

    # The existing format controls are present (json + html).
    assert page.locator("a.format-option[href*='format=json']").count() >= 1
    assert page.locator("a.format-option[href*='format=api']").count() >= 1

    # The JSON representation remains fully available alongside HTML.
    json_response = page.request.get(f"{live_server.url}/api/v1/assets/?format=json")
    assert json_response.status == 200
    assert json_response.json()["results"][0]["slug"] == "entry-gpu"

    # Anonymous permission boundary stays a branded denial (fresh context,
    # so no staff session cookies are shared).
    anon_context = page.context.browser.new_context()
    anon_page = anon_context.new_page()
    response = anon_page.goto(f"{live_server.url}/api/v1/assets/")
    assert response is not None
    assert response.status == 403
    assert "Django REST framework" not in anon_page.content()
    assert "SLAIF Asset Reservation API" in anon_page.title()
    anon_context.close()


@pytest.mark.django_db(transaction=True)
def test_browser_csrf_failure_is_branded(page: Page, live_server, member_user: User) -> None:
    _login(page, live_server, member_user)
    response = page.request.post(f"{live_server.url}/logout/")
    assert response.status == 403
    body = response.text()
    assert BRANDING in body
    assert "CSRF" not in body
    assert "Traceback" not in body


@pytest.mark.django_db(transaction=True)
def test_browser_public_surfaces_disclose_no_private_canaries(
    page: Page,
    live_server,
    member_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    from datetime import timedelta

    from django.utils import timezone

    from slaif_reservation.accounts.services import issue_api_token

    purpose = "entry-canary-purpose-036a"
    start = timezone.now() - timedelta(days=1)
    end = start + timedelta(hours=1)
    Reservation.objects.create(
        asset=asset,
        requested_by_user=member_user,
        source=Reservation.SOURCE_WEB,
        status=Reservation.STATUS_CONFIRMED,
        start_at=start,
        end_at=end,
        effective_end_at=end,
        purpose=purpose,
    )
    issue_api_token(
        owner=member_user,
        name="entry-canary-token-036a",
        scopes=["reservations:read"],
        lifetime_days=1,
    )

    for path in ("/", "/login/", "/admin/login/"):
        page.goto(live_server.url + path)
        content = page.content()
        assert purpose not in content
        assert "entry-canary-token-036a" not in content
        assert asset.name not in content
        assert member_user.email not in content


@pytest.mark.django_db(transaction=True)
def test_browser_admin_index_lists_protected_token_model_readonly(
    page: Page, live_server, staff_user: User
) -> None:
    _login(page, live_server, staff_user)
    response = page.goto(f"{live_server.url}/admin/accounts/apitoken/")
    assert response is not None
    assert response.status == 200
    # No creation action for the protected token model.
    assert page.get_by_role("link", name="Add API token").count() == 0
    _assert_no_framework_branding(page)
