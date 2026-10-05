"""Browser checks for rendered form guidance (order 037-a, SAR-044).

Representative seeded forms at 1440/390: nearby help is visible, controls
remain keyboard-reachable, long labels do not overflow the page, and the
admin password display stays a safe status. Screenshots are privacy-safe:
no one-time token page, no entered credentials, no CSRF/cookie material.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.models import Asset, AssetTag
from slaif_reservation.reservations.models import (
    Reservation,
    ReservationPolicy,
)

DESKTOP = {"width": 1440, "height": 900}
MOBILE = {"width": 390, "height": 844}


@pytest.fixture
def member_user() -> User:
    return User.objects.create_user(
        email="guidance-member@example.com",
        password="not-a-secret",
        display_name="Guidance Member",
        timezone="Europe/Ljubljana",
    )


@pytest.fixture
def staff_user() -> User:
    return User.objects.create_user(
        email="guidance-staff@example.com",
        password="not-a-secret",
        display_name="Guidance Staff",
        is_staff=True,
    )


@pytest.fixture
def admin_user() -> User:
    return User.objects.create_superuser(
        email="guidance-admin@example.com",
        password="not-a-secret",
        display_name="Guidance Admin",
    )


@pytest.fixture
def machine() -> Asset:
    return Asset.objects.create(
        slug="guidance-machine",
        name="Guidance Machine",
        kind=Asset.KIND_MACHINE,
        active=True,
        reservable=False,
    )


@pytest.fixture
def asset(machine: Asset) -> Asset:
    asset = Asset.objects.create(
        slug="guidance-gpu",
        name="Guidance GPU",
        kind=Asset.KIND_GPU,
        parent=machine,
        active=True,
        reservable=True,
    )
    asset.tags.add(AssetTag.objects.create(slug="guidance-tag", name="Guidance Tag"))
    return asset


@pytest.fixture
def default_policy(asset: Asset) -> ReservationPolicy:
    return ReservationPolicy.objects.create(
        name="guidance-custom",
        asset=None,
        active=True,
        min_duration_minutes=30,
        max_duration_minutes=2880,
        booking_horizon_days=7,
        min_lead_minutes=0,
        cancellation_cutoff_minutes=0,
        max_upcoming_per_principal=50,
        max_concurrent_per_principal=8,
        purpose_required=False,
    )


def _login(page: Page, live_server, user: User) -> None:
    page.goto(f"{live_server.url}/login/")
    page.get_by_label("Email").fill(user.email)
    page.get_by_label("Password").fill("not-a-secret")
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server.url}/")


def _admin_login(page: Page, live_server, user: User) -> None:
    page.goto(f"{live_server.url}/admin/login/")
    page.get_by_label("Email").fill(user.email)
    page.get_by_label("Password").fill("not-a-secret")
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server.url}/admin/")


def _assert_no_horizontal_overflow(page: Page) -> None:
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), (
        "horizontal page overflow"
    )


def _assert_help_near_control(page: Page, control_selector: str, help_id: str) -> None:
    """Substantive nearby-help check.

    The control exists and is visible; the help element exists and is
    visible; the control's own aria-describedby binds this exact help
    element; and both live in the same real field container (nearby, not
    floating at the bottom of the page).
    """
    control = page.locator(control_selector)
    assert control.count() == 1, f"ambiguous or missing control {control_selector}"
    assert control.first.is_visible(), f"control {control_selector} is not visible"
    help_el = page.locator(f"#{help_id}")
    assert help_el.count() == 1, f"missing help #{help_id}"
    assert help_el.first.is_visible(), f"help #{help_id} is not visible"
    bound_and_near = page.evaluate(
        r"""([control, help]) => {
            const c = document.querySelector(control);
            const h = document.getElementById(help);
            if (!c || !h) return false;
            const described = (c.getAttribute("aria-describedby") || "").split(/\s+/);
            if (!described.includes(h.id)) return false;
            const box = c.closest(".field, .filter, .form-row, fieldset");
            return box !== null && box.contains(h);
        }""",
        [control_selector, help_id],
    )
    assert bound_and_near, f"help #{help_id} is not bound to and near {control_selector}"


def _assert_select_filter_bound(page: Page, base_id: str, help_id: str) -> None:
    """Substantive association for admin select-filter controls.

    After the admin SelectFilter2 JavaScript replaces the delivered
    select, BOTH generated list boxes (id_<name>_from / id_<name>_to)
    must exist, be visible, and each carry an aria-describedby binding
    to the field's rendered, visible help element inside the same real
    field container.
    """
    for suffix in ("_from", "_to"):
        page.wait_for_function(
            r"""([sel, help]) => {
                const el = document.querySelector(sel);
                const h = document.getElementById(help);
                return !!(el && h && (el.getAttribute("aria-describedby") || "")
                    .split(/\s+/).includes(h.id));
            }""",
            arg=[f"#{base_id}{suffix}", help_id],
            timeout=10000,
        )
    for suffix in ("_from", "_to"):
        control = page.locator(f"#{base_id}{suffix}")
        assert control.count() == 1, f"missing control #{base_id}{suffix}"
        assert control.first.is_visible(), f"control #{base_id}{suffix} is not visible"
        assert help_id in (control.first.get_attribute("aria-describedby") or "").split(), (
            f"control #{base_id}{suffix} does not bind help #{help_id}"
        )
    help_el = page.locator(f"#{help_id}")
    assert help_el.count() == 1, f"missing help #{help_id}"
    assert help_el.first.is_visible(), f"help #{help_id} is not visible"
    near = page.evaluate(
        r"""([c, h]) => {
            const box = document.querySelector(c).closest(".field, .filter, .form-row, fieldset");
            return box !== null && box.contains(document.getElementById(h));
        }""",
        [f"#{base_id}_from", help_id],
    )
    assert near, f"help #{help_id} is not near #{base_id}_from"


def _assert_radio_help_bound(page: Page, first_id: str, help_id: str) -> None:
    """Both rendered radio choices bind the field's rendered help element.

    The help element exists and is visible; both choices exist, are
    visible and carry the matching aria-describedby; the field label
    binds the first choice; and the second choice is keyboard-focusable.
    """
    help_el = page.locator(f"#{help_id}")
    assert help_el.count() == 1, f"missing help #{help_id}"
    assert help_el.first.is_visible(), f"help #{help_id} is not visible"
    second_id = first_id[:-1] + "1"
    for control_id in (first_id, second_id):
        control = page.locator(f"#{control_id}")
        assert control.count() == 1, f"missing control #{control_id}"
        assert control.first.is_visible(), f"control #{control_id} is not visible"
        assert help_id in (control.first.get_attribute("aria-describedby") or "").split(), (
            f"control #{control_id} does not bind help #{help_id}"
        )
    assert page.evaluate(
        """(id) => Array.from(document.querySelectorAll("label[for]"))
            .some((l) => l.getAttribute("for") === id && !l.querySelector("input"))""",
        first_id,
    ), "no field label binds the first radio choice"
    page.focus(f"#{second_id}")
    assert page.evaluate("(id) => document.activeElement.id === id", second_id)


def _keyboard_walk(page: Page, start_selector: str, hops: int) -> list[str]:
    page.locator(start_selector).first.focus()
    tags: list[str] = []
    for _ in range(hops):
        page.keyboard.press("Tab")
        tag = page.evaluate("document.activeElement ? document.activeElement.tagName : ''")
        assert tag, "focus lost during keyboard walk"
        tags.append(tag)
    return tags


def _capture(page: Page, output_path, name: str, *, full_page: bool = False) -> None:
    page.screenshot(path=f"{output_path}/{name}.png", full_page=full_page)


@pytest.mark.django_db(transaction=True)
def test_browser_reservation_and_profile_guidance(
    page: Page,
    live_server,
    output_path,
    member_user: User,
    asset: Asset,
    default_policy: ReservationPolicy,
) -> None:
    page.set_viewport_size(DESKTOP)
    _login(page, live_server, member_user)

    # Reservation form: nearby help for start/end/occurrences/purpose.
    page.goto(f"{live_server.url}/assets/{asset.id}/reserve/")
    for selector, help_id, fragment in [
        ("#id_start", "id_start-help", "Local date and time the asset is needed"),
        ("#id_end", "id_end-help", "Local end date and time"),
        (
            "#id_start_fold",
            "id_start_fold-help",
            "On fall-back the clock time repeats and Automatic is then rejected",
        ),
        ("#id_purpose", "id_purpose-help", "Optional unless the policy"),
    ]:
        assert page.locator(f"#{help_id}").inner_text()
        _assert_help_near_control(page, selector, help_id)
        assert fragment in page.locator(f"#{help_id}").inner_text()
    _assert_no_horizontal_overflow(page)
    assert set(_keyboard_walk(page, "#id_start", 6)) <= {
        "INPUT",
        "SELECT",
        "TEXTAREA",
        "BUTTON",
        "A",
    }
    _capture(page, output_path, "reserve-1440")
    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "reserve-390")

    # Profile: display name and required timezone guidance.
    page.set_viewport_size(DESKTOP)
    page.goto(f"{live_server.url}/profile/")
    assert "Required. IANA time zone name" in page.locator("#id_timezone-help").inner_text()
    _assert_help_near_control(page, "#id_timezone", "id_timezone-help")
    _assert_help_near_control(page, "#id_display_name", "id_display_name-help")
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "profile-1440")
    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "profile-390")


@pytest.mark.django_db(transaction=True)
def test_browser_token_create_guidance(
    page: Page,
    live_server,
    output_path,
    member_user: User,
    default_policy: ReservationPolicy,
) -> None:
    page.set_viewport_size(DESKTOP)
    _login(page, live_server, member_user)
    page.goto(f"{live_server.url}/tokens/new/")

    # The legend is the fieldset group's accessible name in the a11y tree.
    assert page.get_by_role("group", name="Scopes (what the token may do)").is_visible()
    assert (
        page.locator("fieldset.scope-group legend").inner_text() == "Scopes (what the token may do)"
    )
    for label in (
        "Asset inventory (reserved)",
        "Read availability",
        "Read your reservations",
        "Create reservations",
        "Cancel reservations",
        "Release reservations",
    ):
        assert page.get_by_label(label).is_visible(), label
    assert "grants nothing today" in page.content()
    _assert_help_near_control(page, "#id_name", "id_name-help")
    _assert_help_near_control(page, "#id_lifetime_days", "id_lifetime_days-help")
    _assert_no_horizontal_overflow(page)
    assert "INPUT" in _keyboard_walk(page, "#id_name", 10)
    _capture(page, output_path, "token-create-1440")
    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "token-create-390")


@pytest.mark.django_db(transaction=True)
def test_browser_asset_filters_and_availability_guidance(
    page: Page,
    live_server,
    output_path,
    member_user: User,
    asset: Asset,
    default_policy: ReservationPolicy,
) -> None:
    page.set_viewport_size(DESKTOP)
    _login(page, live_server, member_user)
    page.goto(f"{live_server.url}/assets/")
    for selector, help_id in [
        ("#filter-q", "filter-q-help"),
        ("#filter-kind", "filter-kind-help"),
        ("#filter-parent", "filter-parent-help"),
        ("#filter-tag", "filter-tag-help"),
        ("#filter-reservable", "filter-reservable-help"),
    ]:
        _assert_help_near_control(page, selector, help_id)
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "asset-filters-1440")
    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "asset-filters-390")

    page.set_viewport_size(DESKTOP)
    page.goto(f"{live_server.url}/assets/{asset.id}/")
    assert "latest valid start" in page.content()
    assert "The latest valid start is the last time a new booking could begin" in page.content()
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "asset-availability-1440")
    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "asset-availability-390")


@pytest.mark.django_db(transaction=True)
def test_browser_policy_and_blackout_guidance(
    page: Page,
    live_server,
    output_path,
    staff_user: User,
    asset: Asset,
    default_policy: ReservationPolicy,
) -> None:
    page.set_viewport_size(DESKTOP)
    _login(page, live_server, staff_user)

    page.goto(f"{live_server.url}/manage/policies/new/")
    for selector, help_id in [
        ("#id_name", "id_name-help"),
        ("#id_asset", "id_asset-help"),
        ("#id_min_duration_minutes", "id_min_duration_minutes-help"),
        ("#id_max_duration_minutes", "id_max_duration_minutes-help"),
        ("#id_booking_horizon_days", "id_booking_horizon_days-help"),
        ("#id_min_lead_minutes", "id_min_lead_minutes-help"),
        ("#id_cancellation_cutoff_minutes", "id_cancellation_cutoff_minutes-help"),
        ("#id_max_upcoming_per_principal", "id_max_upcoming_per_principal-help"),
        ("#id_max_concurrent_per_principal", "id_max_concurrent_per_principal-help"),
        ("#id_purpose_required", "id_purpose_required-help"),
    ]:
        _assert_help_near_control(page, selector, help_id)
    assert "2880 minutes = 48 hours = 2 days" in page.content()
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "policy-form-1440")
    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "policy-form-390")

    page.set_viewport_size(DESKTOP)
    page.goto(f"{live_server.url}/manage/policies/{default_policy.id}/")
    assert "2 days" in page.content()
    assert "bookings may start up to 7 days from now" in page.content()
    _capture(page, output_path, "policy-detail-1440")

    page.goto(f"{live_server.url}/manage/blackouts/new/")
    for selector, help_id in [
        ("#id_asset", "id_asset-help"),
        ("#id_timezone", "id_timezone-help"),
        ("#id_start", "id_start-help"),
        ("#id_end", "id_end-help"),
        ("#id_reason", "id_reason-help"),
        ("#id_confirm_overlaps", "id_confirm_overlaps-help"),
    ]:
        _assert_help_near_control(page, selector, help_id)
    assert "never cancels or releases them" in page.content()
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "blackout-form-1440")
    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "blackout-form-390")


@pytest.mark.django_db(transaction=True)
def test_browser_reservations_and_audit_filters_guidance(
    page: Page,
    live_server,
    output_path,
    staff_user: User,
    member_user: User,
    asset: Asset,
    default_policy: ReservationPolicy,
) -> None:
    from datetime import timedelta

    from django.utils import timezone

    now = timezone.now()
    Reservation.objects.create(
        asset=asset,
        requested_by_user=member_user,
        source=Reservation.SOURCE_WEB,
        status=Reservation.STATUS_CONFIRMED,
        start_at=now + timedelta(hours=6),
        end_at=now + timedelta(hours=8),
        effective_end_at=now + timedelta(hours=8),
    )

    page.set_viewport_size(DESKTOP)
    _login(page, live_server, staff_user)

    page.goto(f"{live_server.url}/manage/reservations/")
    for selector, help_id in [
        ("#id_asset", "id_asset-help"),
        ("#id_q", "id_q-help"),
        ("#id_status", "id_status-help"),
        ("#id_lifecycle", "id_lifecycle-help"),
        ("#id_from", "id_from-help"),
        ("#id_to", "id_to-help"),
    ]:
        _assert_help_near_control(page, selector, help_id)
    assert "From (start at or after)" in page.content()
    assert "To (start before)" in page.content()
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "reservation-filters-1440")
    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "reservation-filters-390")

    page.set_viewport_size(DESKTOP)
    page.goto(f"{live_server.url}/manage/audit/")
    for selector, help_id in [
        ("#id_action", "id_action-help"),
        ("#id_target_type", "id_target_type-help"),
        ("#id_actor", "id_actor-help"),
        ("#id_source", "id_source-help"),
        ("#id_correlation_id", "id_correlation_id-help"),
        ("#id_occurred_from", "id_occurred_from-help"),
        ("#id_occurred_to", "id_occurred_to-help"),
    ]:
        _assert_help_near_control(page, selector, help_id)
    assert "Downloads the current filtered view as CSV." in page.content()
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "audit-filters-1440")
    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "audit-filters-390")


@pytest.mark.django_db(transaction=True)
def test_browser_admin_user_forms_guidance(
    page: Page,
    live_server,
    output_path,
    admin_user: User,
    member_user: User,
) -> None:
    # Admin login at 1440 and 390.
    for viewport, name in ((DESKTOP, "admin-login-1440"), (MOBILE, "admin-login-390")):
        page.set_viewport_size(viewport)
        page.goto(f"{live_server.url}/admin/login/")
        _assert_help_near_control(page, "#id_username", "id_username-help")
        _assert_help_near_control(page, "#id_password", "id_password-help")
        assert "The email address of your administration account." in page.content()
        _assert_no_horizontal_overflow(page)
        _capture(page, output_path, name)

    _admin_login(page, live_server, admin_user)

    # User add: guided initial fields at 1440 (full page) and 390.
    page.goto(f"{live_server.url}/admin/accounts/user/add/")
    page.set_viewport_size(DESKTOP)
    _assert_help_near_control(page, "#id_email", "id_email_helptext")
    _assert_help_near_control(page, "#id_password1", "id_password1_helptext")
    _assert_help_near_control(page, "#id_password2", "id_password2_helptext")
    _assert_help_near_control(page, "#id_is_staff", "id_is_staff_helptext")
    assert (
        "Members cannot change their own password"
        in page.locator("#id_password1_helptext").inner_text()
    )
    assert (
        "not granted by individual permission selections"
        in page.locator("#id_is_staff_helptext").inner_text()
    )
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "admin-user-add-1440", full_page=True)
    page.set_viewport_size(MOBILE)
    _assert_help_near_control(page, "#id_email", "id_email_helptext")
    _assert_help_near_control(page, "#id_password1", "id_password1_helptext")
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "admin-user-add-390", full_page=True)

    # User change: safe password status, no hash material, guided flags and
    # editable important dates, at 1440 (full page) and 390.
    page.goto(f"{live_server.url}/admin/accounts/user/{member_user.pk}/change/")
    page.set_viewport_size(DESKTOP)
    assert "Password set." in page.content()
    assert "pbkdf2_sha256" not in page.content()
    _assert_help_near_control(page, "#id_email", "id_email_helptext")
    _assert_help_near_control(page, "#id_is_service_account", "id_is_service_account_helptext")
    _assert_help_near_control(page, "#id_is_staff", "id_is_staff_helptext")
    _assert_help_near_control(page, "#id_is_superuser", "id_is_superuser_helptext")
    # After the selectfilter JS initializes, BOTH generated list boxes of
    # each permission/group selector bind the rendered field help.
    _assert_select_filter_bound(page, "id_groups", "id_groups_helptext")
    _assert_select_filter_bound(page, "id_user_permissions", "id_user_permissions_helptext")
    _assert_help_near_control(page, "#id_last_login_0", "id_last_login_0_helptext")
    _assert_help_near_control(page, "#id_date_joined_0", "id_date_joined_0_helptext")
    assert (
        "does not bypass the active-human/staff admission gate"
        in page.locator("#id_is_superuser_helptext").inner_text()
    )
    assert (
        "per-model administration operations in this administration only"
        in page.locator("#id_is_staff_helptext").inner_text()
    )
    assert (
        "do not grant management access, which follows the active staff flag"
        in page.locator("#id_user_permissions_helptext").inner_text()
    )
    assert (
        "Booking and availability logic never reads it"
        in page.locator("#id_last_login_0_helptext").inner_text()
    )
    _assert_no_horizontal_overflow(page)
    assert "INPUT" in _keyboard_walk(page, "#id_email", 8)
    _capture(page, output_path, "admin-user-change-1440", full_page=True)
    page.set_viewport_size(MOBILE)
    _assert_help_near_control(page, "#id_email", "id_email_helptext")
    _assert_help_near_control(page, "#id_last_login_0", "id_last_login_0_helptext")
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "admin-user-change-390", full_page=True)

    # Per-user password change: guided high-impact choice, no secrets
    # displayed, at 1440 and 390.
    page.goto(f"{live_server.url}/admin/accounts/user/{member_user.pk}/password/")
    page.set_viewport_size(DESKTOP)
    assert (
        "Your password must contain at least 8 characters"
        in page.locator("#id_password1_helptext").inner_text()
    )
    _assert_help_near_control(page, "#id_password2", "id_password2_helptext")
    # The rendered RadioSelect keeps a bindable help id and BOTH choices
    # carry the aria-describedby association; the field label binds the
    # first choice and the second choice is keyboard-reachable.
    _assert_radio_help_bound(page, "id_usable_password_0", "id_usable_password_0_helptext")
    assert (
        "a disabled user cannot sign in until an administrator sets"
        in page.locator("#id_usable_password_0_helptext").inner_text()
    )
    assert "If disabled, the current password for this user will be lost." in page.content()
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "admin-password-change-1440")
    page.set_viewport_size(MOBILE)
    _assert_radio_help_bound(page, "id_usable_password_0", "id_usable_password_0_helptext")
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "admin-password-change-390")

    # Invalid (mismatched) POST keeps the rendered, bound help.
    page.set_viewport_size(DESKTOP)
    page.goto(f"{live_server.url}/admin/accounts/user/{member_user.pk}/password/")
    page.locator("#id_password1").fill("mismatched-passw0rd")
    page.locator("#id_password2").fill("different-passw0rd")
    page.get_by_role("button", name="Change password").click()
    assert page.locator(".errornote").count() >= 1
    _assert_radio_help_bound(page, "id_usable_password_0", "id_usable_password_0_helptext")
    assert (
        "a disabled user cannot sign in until an administrator sets"
        in page.locator("#id_usable_password_0_helptext").inner_text()
    )


@pytest.mark.django_db(transaction=True)
def test_browser_admin_group_and_asset_forms_guidance(
    page: Page,
    live_server,
    output_path,
    admin_user: User,
    machine: Asset,
    asset: Asset,
) -> None:
    _admin_login(page, live_server, admin_user)

    # Group add: permissions guidance at 1440 (full page) and 390.
    page.goto(f"{live_server.url}/admin/auth/group/add/")
    page.set_viewport_size(DESKTOP)
    _assert_select_filter_bound(page, "id_permissions", "id_permissions_helptext")
    assert "Site permissions granted through this group" in page.content()
    assert (
        "not management access, which follows the active human staff status"
        in page.locator("#id_permissions_helptext").inner_text()
    )
    assert "NOT project or membership authorization" in page.content()
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "admin-group-add-1440", full_page=True)
    page.set_viewport_size(MOBILE)
    _assert_select_filter_bound(page, "id_permissions", "id_permissions_helptext")
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "admin-group-add-390", full_page=True)

    # Asset add: corrected parent/slug/kind guidance at 1440 (full page) and
    # 390.
    page.goto(f"{live_server.url}/admin/assets/asset/add/")
    page.set_viewport_size(DESKTOP)
    _assert_help_near_control(page, "#id_parent", "id_parent_helptext")
    _assert_help_near_control(page, "#id_slug", "id_slug_helptext")
    _assert_help_near_control(page, "#id_kind", "id_kind_helptext")
    _assert_help_near_control(page, "#id_booking_mode", "id_booking_mode_helptext")
    _assert_help_near_control(page, "#id_timezone", "id_timezone_helptext")
    _assert_help_near_control(page, "#id_physical_locator", "id_physical_locator_helptext")
    assert "a machine itself never has a parent" in page.locator("#id_parent_helptext").inner_text()
    assert (
        "changing the slug does not change those URLs"
        in page.locator("#id_slug_helptext").inner_text()
    )
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "admin-asset-add-1440", full_page=True)
    page.set_viewport_size(MOBILE)
    _assert_help_near_control(page, "#id_parent", "id_parent_helptext")
    _assert_help_near_control(page, "#id_slug", "id_slug_helptext")
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "admin-asset-add-390", full_page=True)

    # Asset change at 1440 and 390.
    page.goto(f"{live_server.url}/admin/assets/asset/{asset.pk}/change/")
    page.set_viewport_size(DESKTOP)
    _assert_help_near_control(page, "#id_slug", "id_slug_helptext")
    assert "Stable label used for display and search" in page.content()
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "admin-asset-change-1440", full_page=True)
    page.set_viewport_size(MOBILE)
    _assert_help_near_control(page, "#id_slug", "id_slug_helptext")
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "admin-asset-change-390", full_page=True)

    # Tag add at 1440 and 390.
    page.goto(f"{live_server.url}/admin/assets/assettag/add/")
    page.set_viewport_size(DESKTOP)
    _assert_help_near_control(page, "#id_name", "id_name_helptext")
    assert "Display name of the tag" in page.content()
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "admin-tag-add-1440")
    page.set_viewport_size(MOBILE)
    _assert_help_near_control(page, "#id_name", "id_name_helptext")
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "admin-tag-add-390")
