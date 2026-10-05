"""Rendered form guidance tests (order 037-a, SAR-044).

These tests verify actually rendered GET and invalid-POST pages across the
member, management and administration surfaces: meaningful nearby help for
every non-obvious control, matching help IDs and ``aria-describedby`` wiring,
human-readable token-scope labels with unchanged machine values, humanized
policy units, the safe admin password status and read-only protection
guidance. The unchanged validation negatives re-assert that the guidance is
presentation only.
"""

from __future__ import annotations

import re
from datetime import timedelta
from html import unescape

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from slaif_reservation.accounts.models import ApiToken, User
from slaif_reservation.accounts.services import issue_api_token
from slaif_reservation.assets.models import Asset, AssetTag
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.reservations.models import (
    MaintenanceBlackout,
    Reservation,
    ReservationPolicy,
)


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
    return Asset.objects.create(
        slug="guidance-gpu",
        name="Guidance GPU",
        kind=Asset.KIND_GPU,
        parent=machine,
        active=True,
        reservable=True,
    )


@pytest.fixture
def default_policy(asset: Asset) -> ReservationPolicy:
    return ReservationPolicy.objects.create(
        name="guidance-default",
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


@pytest.fixture
def asset_tag() -> AssetTag:
    return AssetTag.objects.create(slug="guidance-tag", name="Guidance Tag")


def _assert_no_dangling_aria(html: str) -> None:
    for match in re.finditer(r'aria-describedby="([^"]+)"', html):
        for target in match.group(1).split():
            assert f'id="{target}"' in html, f"aria-describedby target missing: {target}"


def _assert_guided(
    html: str,
    help_id: str,
    fragment: str,
    *,
    aria: str | None = None,
) -> None:
    """Help paragraph with the given ID renders the fragment, optionally
    wired via aria-describedby on the control."""
    assert f'id="{help_id}"' in html, f"missing help element id={help_id}"
    text = unescape(html)
    assert fragment in text, f"missing guidance fragment: {fragment!r}"
    if aria is not None:
        assert f'aria-describedby="{help_id}"' in html
        assert f'aria-describedby="{aria}"' in html if aria != help_id else True


# --- Member surfaces -----------------------------------------------------


@pytest.mark.django_db
def test_member_login_guidance_and_invalid_post(client: Client) -> None:
    response = client.get("/login/")
    html = response.content.decode()
    assert response.status_code == 200
    _assert_no_dangling_aria(html)
    _assert_guided(
        html,
        "id_username-help",
        "Accounts are created by an administrator; self-registration is not available.",
        aria="id_username-help",
    )

    # Invalid credentials keep the guidance and the generic denial.
    response = client.post("/login/", {"username": "nobody@example.com", "password": "nope"})
    html = response.content.decode()
    assert response.status_code == 200
    assert "Enter a valid email address and password" in html
    assert "id_username-help" in html
    _assert_no_dangling_aria(html)


@pytest.mark.django_db
def test_profile_guidance_and_invalid_timezone_post(client: Client, member_user: User) -> None:
    client.force_login(member_user)
    html = client.get("/profile/").content.decode()
    _assert_no_dangling_aria(html)
    _assert_guided(
        html,
        "id_display_name-help",
        "Shown to staff in management views and on reservation records.",
        aria="id_display_name-help",
    )
    _assert_guided(
        html,
        "id_timezone-help",
        "Required. IANA time zone name",
        aria="id_timezone-help",
    )

    # Unchanged negative: an invalid IANA name is still rejected.
    response = client.post(
        "/profile/",
        {"display_name": "Still here", "timezone": "Not/AZone"},
    )
    html = response.content.decode()
    assert response.status_code == 200
    assert "timezone" in html
    assert "id_timezone-help" in html
    assert member_user.display_name == "Guidance Member"

    response = client.post(
        "/profile/",
        {"display_name": "Still here", "timezone": "UTC"},
    )
    assert response.status_code == 302
    member_user.refresh_from_db()
    assert member_user.display_name == "Still here"
    assert member_user.timezone == "UTC"


@pytest.mark.django_db
def test_reservation_form_guidance_and_invalid_post(
    client: Client,
    member_user: User,
    asset: Asset,
    default_policy: ReservationPolicy,
) -> None:
    client.force_login(member_user)
    html = client.get(f"/assets/{asset.id}/reserve/").content.decode()
    _assert_no_dangling_aria(html)
    _assert_guided(
        html,
        "id_start-help",
        "Local date and time the asset is needed, in Europe/Ljubljana",
        aria="id_start-help",
    )
    _assert_guided(
        html,
        "id_end-help",
        "Local end date and time, in Europe/Ljubljana, after the start",
        aria="id_end-help",
    )
    _assert_guided(
        html,
        "id_start_fold-help",
        "Only needed when this local time falls on a daylight-saving transition",
        aria="id_start_fold-help",
    )
    _assert_guided(
        html,
        "id_purpose-help",
        "Optional unless the policy for this asset requires it",
        aria="id_purpose-help",
    )
    # Fold choice values stay machine strings.
    for value in ('value=""', 'value="0"', 'value="1"'):
        assert value in html

    # Unchanged negative: a start in the past is still rejected with guidance kept.
    now = timezone.now()
    past = (now - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M")
    future = (now + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M")
    response = client.post(
        f"/assets/{asset.id}/reserve/",
        {"start": past, "end": future, "purpose": "late"},
    )
    html = response.content.decode()
    assert response.status_code == 200
    assert "start" in html
    assert "id_start-help" in html
    assert Reservation.objects.count() == 0


@pytest.mark.django_db
def test_reservation_detail_cancel_and_release_guidance(
    client: Client,
    member_user: User,
    asset: Asset,
    default_policy: ReservationPolicy,
) -> None:
    now = timezone.now()
    upcoming = Reservation.objects.create(
        asset=asset,
        requested_by_user=member_user,
        source=Reservation.SOURCE_WEB,
        status=Reservation.STATUS_CONFIRMED,
        start_at=now + timedelta(hours=6),
        end_at=now + timedelta(hours=8),
        effective_end_at=now + timedelta(hours=8),
    )
    active = Reservation.objects.create(
        asset=asset,
        requested_by_user=member_user,
        source=Reservation.SOURCE_WEB,
        status=Reservation.STATUS_CONFIRMED,
        start_at=now - timedelta(hours=1),
        end_at=now + timedelta(hours=5),
        effective_end_at=now + timedelta(hours=5),
    )
    client.force_login(member_user)

    html = client.get(f"/reservations/{upcoming.id}/").content.decode()
    _assert_no_dangling_aria(html)
    _assert_guided(
        html,
        "id_reason-help",
        "Optional. Recorded with the cancellation and visible to staff.",
        aria="id_reason-help",
    )
    assert "Cancelling frees the reserved time for other bookings and cannot be undone." in html

    html = client.get(f"/reservations/{active.id}/").content.decode()
    assert "Releasing ends the reservation now." in html
    assert "cannot be undone" in html


@pytest.mark.django_db
def test_token_create_guidance_wire_values_and_invalid_post(
    client: Client,
    member_user: User,
    default_policy: ReservationPolicy,
) -> None:
    client.force_login(member_user)
    response = client.get("/tokens/new/")
    html = response.content.decode()
    assert response.status_code == 200
    _assert_no_dangling_aria(html)
    _assert_guided(
        html,
        "id_name-help",
        "It never changes what the token can do.",
        aria="id_name-help",
    )
    assert "<legend>Scopes (what the token may do)</legend>" in html
    for scope, label in [
        ("assets:read", "Asset inventory (reserved)"),
        ("availability:read", "Read availability"),
        ("reservations:read", "Read your reservations"),
        ("reservations:create", "Create reservations"),
        ("reservations:cancel", "Cancel reservations"),
        ("reservations:release", "Release reservations"),
    ]:
        assert f'value="{scope}"' in html, f"machine value missing for {scope}"
        assert label in html, f"human label missing for {scope}"
    assert "id_scopes-help" in html
    assert "Reserved for future use. It grants nothing today" in html
    assert "advisory availability" in html
    _assert_guided(
        html,
        "id_lifetime_days-help",
        "Days until the token expires on its own, between 1 and",
        aria="id_lifetime_days-help",
    )

    # Unchanged negative: an unknown scope is still rejected.
    response = client.post(
        "/tokens/new/",
        {"name": "Bad", "scopes": ["admin:*"], "lifetime_days": "7"},
    )
    html = response.content.decode()
    assert response.status_code == 200
    assert "scopes" in html
    assert "id_scopes-help" in html
    assert ApiToken.objects.count() == 0

    # A valid selection posts the machine values and renders human labels.
    response = client.post(
        "/tokens/new/",
        {
            "name": "Guidance token",
            "scopes": ["availability:read", "reservations:create"],
            "lifetime_days": "7",
        },
    )
    assert response.status_code == 200
    created = response.content.decode()
    assert "Read availability" in created
    assert "Create reservations" in created
    assert "availability:read" not in created
    assert "reservations:create" not in created
    token = ApiToken.objects.get()
    assert token.scopes == ["availability:read", "reservations:create"]

    list_html = client.get("/tokens/").content.decode()
    assert "Read availability" in list_html
    assert "Create reservations" in list_html
    assert "availability:read" not in list_html
    assert "reservations:create" not in list_html


@pytest.mark.django_db
def test_asset_list_filter_guidance(
    client: Client, member_user: User, asset: Asset, asset_tag: AssetTag
) -> None:
    asset.tags.add(asset_tag)
    client.force_login(member_user)
    html = client.get("/assets/").content.decode()
    _assert_no_dangling_aria(html)
    _assert_guided(html, "filter-q-help", "Matches the asset name, slug or description.")
    _assert_guided(
        html, "filter-kind-help", "One asset kind: Machine, GPU, CPU pool, Service or Other."
    )
    _assert_guided(html, "filter-parent-help", "Only child assets of that machine.")
    _assert_guided(html, "filter-tag-help", "Only assets carrying that tag.")
    _assert_guided(
        html, "filter-reservable-help", "Only assets you can book, or only assets you cannot book."
    )

    # The filters still work (behavior unchanged).
    html = client.get(f"/assets/?q={asset.slug}&tag={asset_tag.slug}").content.decode()
    assert "Guidance GPU" in html


@pytest.mark.django_db
def test_availability_latest_valid_start_help(
    client: Client,
    member_user: User,
    asset: Asset,
    default_policy: ReservationPolicy,
) -> None:
    client.force_login(member_user)
    html = client.get(f"/assets/{asset.id}/").content.decode()
    assert "latest valid start" in html
    assert (
        "The latest valid start is the last time a new booking could begin "
        "within that interval under the current policy limits." in html
    )


# --- Staff surfaces ------------------------------------------------------


@pytest.mark.django_db
def test_policy_form_guidance_and_invalid_post(
    client: Client, staff_user: User, asset: Asset
) -> None:
    client.force_login(staff_user)
    html = client.get("/manage/policies/new/").content.decode()
    _assert_no_dangling_aria(html)
    _assert_guided(html, "id_name-help", "Short unique name for this policy")
    _assert_guided(
        html,
        "id_asset-help",
        "Bookings check the exact asset first, then its parent machine, then the global policy",
    )
    _assert_guided(html, "id_min_duration_minutes-help", "1440 minutes = 24 hours = 1 day")
    _assert_guided(html, "id_max_duration_minutes-help", "2880 minutes = 48 hours = 2 days")
    _assert_guided(
        html, "id_booking_horizon_days-help", "How far into the future a booking may START"
    )
    _assert_guided(html, "id_min_lead_minutes-help", "0 allows bookings that start right now")
    _assert_guided(
        html,
        "id_cancellation_cutoff_minutes-help",
        "0 means cancellation stays possible up to the start time.",
    )
    _assert_guided(
        html, "id_max_upcoming_per_principal-help", "not-yet-started reservations one principal"
    )
    _assert_guided(
        html,
        "id_max_concurrent_per_principal-help",
        "8 rejects a new booking when 8 or more existing records already intersect it",
    )
    _assert_guided(html, "id_purpose_required-help", "Require members to enter a purpose")

    # Unchanged negative: min > max is still rejected with guidance kept.
    response = client.post(
        "/manage/policies/new/",
        {
            "name": "Broken",
            "asset": str(asset.id),
            "min_duration_minutes": "240",
            "max_duration_minutes": "120",
            "booking_horizon_days": "7",
            "min_lead_minutes": "0",
            "cancellation_cutoff_minutes": "0",
            "max_upcoming_per_principal": "10",
            "max_concurrent_per_principal": "2",
        },
    )
    html = response.content.decode()
    assert response.status_code == 200
    assert "id_max_duration_minutes-help" in html
    assert ReservationPolicy.objects.count() == 0


@pytest.mark.django_db
def test_policy_detail_human_units(
    client: Client,
    staff_user: User,
    asset: Asset,
    default_policy: ReservationPolicy,
) -> None:
    client.force_login(staff_user)
    html = client.get(f"/manage/policies/{default_policy.id}/").content.decode()
    assert "2880 minutes" in html
    assert "2 days" in html
    assert "7 days" in html
    assert "bookings may start up to 7 days from now" in html
    assert "No lead required (a booking may start right now)." in html
    assert "Members may cancel up to the start time." in html
    assert "50 upcoming / 8 overlapping per principal" in html
    assert "Deactivating stops this policy applying to new bookings immediately." in html


@pytest.mark.django_db
def test_blackout_form_guidance_and_invalid_post(
    client: Client,
    staff_user: User,
    asset: Asset,
) -> None:
    client.force_login(staff_user)
    html = client.get("/manage/blackouts/new/").content.decode()
    _assert_no_dangling_aria(html)
    _assert_guided(
        html,
        "id_asset-help",
        "The single asset that stops accepting new bookings during the blackout",
    )
    _assert_guided(html, "id_timezone-help", "IANA time zone name")
    _assert_guided(html, "id_start-help", "Local start date and time in the selected timezone.")
    _assert_guided(
        html, "id_end-help", "New overlapping bookings are blocked from the start until the end"
    )
    _assert_guided(html, "id_reason-help", "Required. Explains the maintenance")
    _assert_guided(
        html,
        "id_confirm_overlaps-help",
        "Creating the blackout never cancels or releases them",
    )

    # Unchanged negative: end before start is still rejected.
    now = timezone.now()
    start = (now + timedelta(hours=2)).replace(second=0, microsecond=0).isoformat()
    end = (now + timedelta(hours=1)).replace(second=0, microsecond=0).isoformat()
    response = client.post(
        "/manage/blackouts/new/",
        {
            "asset": str(asset.id),
            "timezone": "UTC",
            "start": start,
            "end": end,
            "reason": "maintenance",
            "confirm_overlaps": "on",
        },
    )
    html = response.content.decode()
    assert response.status_code == 200
    assert "id_end-help" in html
    assert MaintenanceBlackout.objects.count() == 0


@pytest.mark.django_db
def test_blackout_detail_guidance(
    client: Client,
    staff_user: User,
    member_user: User,
    asset: Asset,
    default_policy: ReservationPolicy,
) -> None:
    now = timezone.now()
    reservation = Reservation.objects.create(
        asset=asset,
        requested_by_user=member_user,
        source=Reservation.SOURCE_WEB,
        status=Reservation.STATUS_CONFIRMED,
        start_at=now + timedelta(hours=4),
        end_at=now + timedelta(hours=6),
        effective_end_at=now + timedelta(hours=6),
    )
    blackout = MaintenanceBlackout.objects.create(
        asset=asset,
        start_at=now + timedelta(hours=3),
        end_at=now + timedelta(hours=9),
        reason="guidance maintenance",
        active=True,
        created_by=staff_user,
    )
    client.force_login(staff_user)
    html = client.get(f"/manage/blackouts/{blackout.id}/").content.decode()
    assert str(reservation.id) in html
    assert "These reservations are not changed by the blackout." in html
    assert "Deactivating lets new overlapping bookings on this asset through immediately." in html


@pytest.mark.django_db
def test_reservation_filter_guidance(client: Client, staff_user: User) -> None:
    client.force_login(staff_user)
    html = client.get("/manage/reservations/").content.decode()
    _assert_no_dangling_aria(html)
    _assert_guided(html, "id_asset-help", "Narrow the list to one asset")
    _assert_guided(html, "id_q-help", "Matches the owner's email or display name")
    _assert_guided(html, "id_status-help", "Confirmed, cancelled or released.")
    _assert_guided(html, "id_lifecycle-help", "Active = started and still running")
    _assert_guided(html, "id_from-help", "Aware ISO-8601 timestamp")
    _assert_guided(html, "id_to-help", "Keep reservations whose start is before this.")
    assert "From (start at or after)" in html
    assert "To (start before)" in html


@pytest.mark.django_db
def test_audit_filter_guidance(client: Client, staff_user: User) -> None:
    client.force_login(staff_user)
    html = client.get("/manage/audit/").content.decode()
    _assert_no_dangling_aria(html)
    _assert_guided(html, "id_action-help", "Which operation was recorded.")
    _assert_guided(html, "id_target_type-help", "The record type the action applied to")
    _assert_guided(html, "id_actor-help", "part of a display name or email, or an exact user UUID")
    _assert_guided(html, "id_source-help", "Where the action came from")
    _assert_guided(html, "id_correlation_id-help", "UUID that links the events of one operation")
    _assert_guided(html, "id_occurred_from-help", "Keep events that happened at or after this.")
    _assert_guided(html, "id_occurred_to-help", "Keep events that happened at or before this.")
    assert "Downloads the current filtered view as CSV." in html


@pytest.mark.django_db
def test_staff_reservation_detail_guidance(
    client: Client,
    staff_user: User,
    member_user: User,
    asset: Asset,
    default_policy: ReservationPolicy,
) -> None:
    now = timezone.now()
    reservation = Reservation.objects.create(
        asset=asset,
        requested_by_user=member_user,
        source=Reservation.SOURCE_WEB,
        status=Reservation.STATUS_CONFIRMED,
        start_at=now + timedelta(hours=6),
        end_at=now + timedelta(hours=8),
        effective_end_at=now + timedelta(hours=8),
    )
    client.force_login(staff_user)
    html = client.get(f"/manage/reservations/{reservation.id}/").content.decode()
    assert (
        "Staff actions here affect other users' reservations and are recorded in the audit log."
        in unescape(html)
    )
    assert 'id="id_reason-help"' in html
    assert "Cancelling frees the reserved time and cannot be undone." in html
    assert "Releasing ends the reservation now; the original end stays in the history." in html


# --- Administration ------------------------------------------------------


@pytest.mark.django_db
def test_admin_login_guidance(client: Client) -> None:
    response = client.get("/admin/login/")
    html = response.content.decode()
    assert response.status_code == 200
    _assert_no_dangling_aria(html)
    _assert_guided(html, "id_username-help", "The email address of your administration account.")
    _assert_guided(
        html,
        "id_password-help",
        "The same generic error appears for a wrong password",
    )
    # Admission wording law: no credential-class disclosure on the page.
    lowered = html.lower()
    assert "staff" not in lowered
    assert "service" not in lowered


@pytest.mark.django_db
def test_admin_user_add_guidance(client: Client, admin_user: User) -> None:
    client.force_login(admin_user)
    html = client.get("/admin/accounts/user/add/").content.decode()
    _assert_no_dangling_aria(html)
    _assert_guided(html, "id_email_helptext", "Accounts are created by an administrator")
    _assert_guided(html, "id_password1_helptext", "Choose the initial password for this account")
    _assert_guided(html, "id_password2_helptext", "Re-enter the same password to confirm it.")
    _assert_guided(
        html,
        "id_is_staff_helptext",
        "Grants access to the management area and this administration.",
    )
    _assert_guided(
        html, "id_is_superuser_helptext", "Full administrative rights, including managing users."
    )


@pytest.mark.django_db
def test_admin_user_change_safe_password_status_and_help(
    client: Client,
    admin_user: User,
    member_user: User,
) -> None:
    client.force_login(admin_user)
    html = client.get(f"/admin/accounts/user/{member_user.pk}/change/").content.decode()
    _assert_no_dangling_aria(html)

    # Safe status instead of the inherited hash summary.
    assert "Password set." in html
    assert "The stored password is never displayed." in html
    assert "pbkdf2_sha256" not in html
    assert member_user.password[20:60] not in html
    password_change_url = reverse("admin:auth_user_password_change", args=[member_user.pk])
    assert f'href="{password_change_url}"' in html
    assert "Change password" in html

    for name, fragment in [
        ("email", "Sign-in identifier for the account"),
        ("display_name", "Shown to staff in management views"),
        ("timezone", "IANA time zone name"),
        ("is_service_account", "Machine account for API automation"),
        ("is_active", "Inactive accounts cannot sign in anywhere"),
        ("is_staff", "Grants access to the management area"),
        ("is_superuser", "Full administrative rights"),
        ("groups", "Groups are NOT project or membership authorization"),
        ("user_permissions", "administration and management access only"),
    ]:
        _assert_guided(html, f"id_{name}_helptext", fragment)

    # A valid change POST preserves the stored hash. The admin renders the
    # datetime fields with split date/time inputs.
    stored_hash = member_user.password
    joined = member_user.date_joined
    response = client.post(
        f"/admin/accounts/user/{member_user.pk}/change/",
        {
            "email": member_user.email,
            "display_name": "Renamed by admin",
            "timezone": "UTC",
            "is_service_account": "on",
            "is_active": "on",
            "last_login_0": "",
            "last_login_1": "",
            "date_joined_0": joined.strftime("%Y-%m-%d"),
            "date_joined_1": joined.strftime("%H:%M:%S"),
        },
    )
    assert response.status_code == 302
    member_user.refresh_from_db()
    assert member_user.password == stored_hash
    assert member_user.display_name == "Renamed by admin"


@pytest.mark.django_db
def test_admin_user_change_password_disabled_status(
    client: Client,
    admin_user: User,
    staff_user: User,
) -> None:
    staff_user.set_unusable_password()
    staff_user.save(update_fields=["password"])
    client.force_login(admin_user)
    html = client.get(f"/admin/accounts/user/{staff_user.pk}/change/").content.decode()
    assert "Password disabled" in html
    assert "pbkdf2_sha256" not in html


@pytest.mark.django_db
def test_admin_password_change_guidance(
    client: Client, admin_user: User, member_user: User
) -> None:
    client.force_login(admin_user)
    html = client.get(f"/admin/accounts/user/{member_user.pk}/password/").content.decode()
    _assert_no_dangling_aria(html)
    _assert_guided(
        html,
        "id_password1_helptext",
        "Your password must contain at least 8 characters.",
    )
    _assert_guided(
        html,
        "id_password2_helptext",
        "Enter the same password as before, for verification.",
    )

    # Unchanged negative: mismatched passwords are still rejected.
    response = client.post(
        f"/admin/accounts/user/{member_user.pk}/password/",
        {"password1": "a-new-passw0rd", "password2": "different-passw0rd"},
    )
    assert response.status_code == 200
    member_user.refresh_from_db()
    assert member_user.has_usable_password()


@pytest.mark.django_db
def test_admin_group_permissions_help(client: Client, admin_user: User) -> None:
    client.force_login(admin_user)
    html = client.get("/admin/auth/group/add/").content.decode()
    assert "Site permissions granted through this group" in html
    assert "NOT project or membership authorization" in html


@pytest.mark.django_db
def test_admin_asset_forms_guidance(client: Client, admin_user: User) -> None:
    client.force_login(admin_user)
    html = client.get("/admin/assets/asset/add/").content.decode()
    _assert_no_dangling_aria(html)
    _assert_guided(html, "id_parent_helptext", "The machine this asset belongs to")
    _assert_guided(html, "id_slug_helptext", "Stable public identifier used in URLs and the API")
    _assert_guided(html, "id_kind_helptext", "What kind of resource this is")
    _assert_guided(html, "id_booking_mode_helptext", "Only 'Exclusive' is supported")
    _assert_guided(html, "id_location_helptext", "Internal room or location label for staff")
    _assert_guided(html, "id_physical_locator_helptext", "Internal physical location for operators")

    html = client.get("/admin/assets/assettag/add/").content.decode()
    _assert_guided(html, "id_name_helptext", "Display name of the tag")
    _assert_guided(html, "id_slug_helptext", "Stable identifier, generated from the name")


@pytest.mark.django_db
def test_admin_readonly_banners(
    client: Client,
    admin_user: User,
    staff_user: User,
    member_user: User,
    asset: Asset,
    default_policy: ReservationPolicy,
) -> None:
    now = timezone.now()
    policy = ReservationPolicy.objects.create(
        name="guidance-readonly",
        asset=asset,
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
    reservation = Reservation.objects.create(
        asset=asset,
        requested_by_user=member_user,
        source=Reservation.SOURCE_WEB,
        status=Reservation.STATUS_CONFIRMED,
        start_at=now + timedelta(hours=6),
        end_at=now + timedelta(hours=8),
        effective_end_at=now + timedelta(hours=8),
    )
    blackout = MaintenanceBlackout.objects.create(
        asset=asset,
        start_at=now + timedelta(hours=3),
        end_at=now + timedelta(hours=9),
        reason="guidance maintenance",
        active=True,
        created_by=staff_user,
    )
    audit = AuditEvent.objects.create(
        occurred_at=now,
        actor_user=admin_user,
        action=AuditEvent.ACTION_RESERVATION_CREATED,
        target_type="reservation",
        target_id=reservation.id,
        correlation_id=reservation.id,
        source=AuditEvent.SOURCE_WEB,
    )
    token = issue_api_token(
        owner=member_user,
        name="guidance-token",
        scopes=["reservations:read"],
        lifetime_days=1,
    ).token

    client.force_login(admin_user)
    expected = {
        f"/admin/reservations/reservationpolicy/{policy.id}/change/": (
            "This policy is read-only here.",
            "/manage/policies/",
        ),
        f"/admin/reservations/reservation/{reservation.id}/change/": (
            "This reservation is read-only here.",
            "/manage/reservations/",
        ),
        f"/admin/reservations/maintenanceblackout/{blackout.id}/change/": (
            "This blackout is read-only here.",
            "/manage/blackouts/",
        ),
        f"/admin/audit/auditevent/{audit.id}/change/": (
            "Audit records are append-only",
            "/manage/audit/",
        ),
        f"/admin/accounts/apitoken/{token.id}/change/": (
            "Tokens are read-only here.",
            "/tokens/",
        ),
    }
    for path, (banner, link) in expected.items():
        response = client.get(path)
        assert response.status_code == 200, path
        html = response.content.decode()
        assert banner in html, path
        assert f'href="{link}"' in html, path
