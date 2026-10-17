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
from datetime import UTC, datetime, timedelta
from html import unescape

import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import resolve, reverse
from django.utils import timezone

from slaif_reservation.accounts.exceptions import TOKEN_OWNER_INVALID, ApiTokenDomainError
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
    created = User.objects.create_user(
        email="guidance-member@example.com",
        password="not-a-secret",
        display_name="Guidance Member",
        timezone="Europe/Ljubljana",
    )
    # A16: explicit baseline booking capability (real Permission row).
    created.user_permissions.add(
        Permission.objects.get(codename="book_assets", content_type__app_label="reservations")
    )
    return created


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


@pytest.fixture
def asset_tag() -> AssetTag:
    return AssetTag.objects.create(slug="guidance-tag", name="Guidance Tag")


def _assert_no_dangling_aria(html: str) -> None:
    for match in re.finditer(r'aria-describedby="([^"]+)"', html):
        for target in match.group(1).split():
            assert f'id="{target}"' in html, f"aria-describedby target missing: {target}"


def _control_binds_help(html: str, control_id: str, help_id: str) -> None:
    """The control's own element carries aria-describedby naming the help."""
    tag = re.search(r'<[a-zA-Z][^>]*\bid="' + re.escape(control_id) + r'"[^>]*>', html)
    described = re.search(r'aria-describedby="([^"]*)"', tag.group(0))
    assert described, f"control #{control_id} has no aria-describedby"
    assert help_id in described.group(1).split(), (
        f"control #{control_id} does not bind help #{help_id}"
    )


def _assert_guided(
    html: str,
    help_id: str,
    fragment: str,
    *,
    control_id: str,
) -> None:
    """Help element with the given ID renders the fragment and is bound to
    the control's own element via its aria-describedby."""
    assert f'id="{help_id}"' in html, f"missing help element id={help_id}"
    text = unescape(html)
    assert fragment in text, f"missing guidance fragment: {fragment!r}"
    _control_binds_help(html, control_id, help_id)


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
        control_id="id_username",
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
        control_id="id_display_name",
    )
    _assert_guided(
        html,
        "id_timezone-help",
        "Required. IANA time zone name",
        control_id="id_timezone",
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
        control_id="id_start",
    )
    _assert_guided(
        html,
        "id_end-help",
        "Local end date and time, in Europe/Ljubljana, after the start",
        control_id="id_end",
    )
    _assert_guided(
        html,
        "id_start_fold-help",
        "On fall-back the clock time repeats and Automatic is then rejected",
        control_id="id_start_fold",
    )
    _assert_guided(
        html,
        "id_end_fold-help",
        "A time inside the spring-forward gap does not exist and is always rejected",
        control_id="id_end_fold",
    )
    _assert_guided(
        html,
        "id_purpose-help",
        "Optional unless the policy for this asset requires it",
        control_id="id_purpose",
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


def test_human_duration_preserves_remainder_minutes() -> None:
    from slaif_reservation.web.templatetags.form_guidance import human_duration

    cases = {
        0: "0 minutes",
        1: "1 minute",
        59: "59 minutes",
        60: "1 hour",
        90: "1 hour, 30 minutes",
        1440: "1 day",
        1441: "1 day, 1 minute",
        1501: "1 day, 1 hour, 1 minute",
        2880: "2 days",
        2881: "2 days, 1 minute",
        2890: "2 days, 10 minutes",
    }
    for minutes, expected in cases.items():
        assert human_duration(minutes) == expected, minutes
    # Non-numeric and negative input renders nothing (unchanged).
    assert human_duration(None) == ""
    assert human_duration("nope") == ""
    assert human_duration(-5) == ""


@pytest.mark.django_db
def test_policy_detail_nonround_minutes_humanized(
    client: Client,
    staff_user: User,
) -> None:
    policy = ReservationPolicy.objects.create(
        name="nonround",
        asset=None,
        active=True,
        min_duration_minutes=1441,
        max_duration_minutes=2890,
        booking_horizon_days=7,
        min_lead_minutes=90,
        cancellation_cutoff_minutes=30,
        max_upcoming_per_principal=50,
        max_concurrent_per_principal=8,
        purpose_required=False,
    )
    client.force_login(staff_user)
    html = client.get(f"/manage/policies/{policy.id}/").content.decode()
    assert "1441 to 2890 minutes" in html
    assert "1 day, 1 minute - 2 days, 10 minutes" in html
    assert "90 minutes (1 hour, 30 minutes)" in html
    assert "30 minutes before start (30 minutes)" in html


@pytest.mark.django_db
def test_reservation_ambiguous_automatic_post_keeps_help(
    client: Client,
    member_user: User,
    asset: Asset,
    default_policy: ReservationPolicy,
) -> None:
    """An ambiguous fall-back wall time with Automatic is rejected at the
    form boundary and the corrected occurrence help stays on the page."""
    client.force_login(member_user)
    response = client.post(
        f"/assets/{asset.id}/reserve/",
        {
            "start": "2025-10-26T02:30",
            "end": "2025-10-26T04:30",
            "purpose": "dst check",
        },
    )
    html = response.content.decode()
    assert response.status_code == 200
    assert "Local wall time is ambiguous; specify fold." in html
    assert "id_start_fold-help" in html
    assert "On fall-back the clock time repeats and Automatic is then rejected" in html
    assert Reservation.objects.count() == 0


@pytest.mark.django_db
def test_reservation_form_fold_semantics(
    asset: Asset,
    default_policy: ReservationPolicy,
    member_user: User,
) -> None:
    from slaif_reservation.web.forms import ReservationForm

    base = {"start": "2025-10-26T02:30", "end": "2025-10-26T04:30", "purpose": ""}

    # The repeated fall-back time is resolvable with an explicit occurrence;
    # the two choices pick the two real instants.
    form = ReservationForm({**base, "start_fold": "0"}, timezone_name="Europe/Ljubljana")
    assert form.is_valid(), form.errors
    assert form.cleaned_data["start_instant"] == datetime(2025, 10, 26, 0, 30, tzinfo=UTC)
    assert form.cleaned_data["end_instant"] == datetime(2025, 10, 26, 3, 30, tzinfo=UTC)
    form = ReservationForm({**base, "start_fold": "1"}, timezone_name="Europe/Ljubljana")
    assert form.is_valid(), form.errors
    assert form.cleaned_data["start_instant"] == datetime(2025, 10, 26, 1, 30, tzinfo=UTC)

    # A nonexistent spring-forward wall time is rejected however it is chosen.
    for fold in ("", "0", "1"):
        form = ReservationForm(
            {**base, "start": "2025-03-30T02:30", "start_fold": fold},
            timezone_name="Europe/Ljubljana",
        )
        assert not form.is_valid()
        assert "Local wall time does not exist in this timezone." in str(form.errors)


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
        control_id="id_reason",
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
        control_id="id_name",
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
        control_id="id_lifetime_days",
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
    _assert_guided(
        html, "filter-q-help", "Matches the asset name, slug or description.", control_id="filter-q"
    )
    _assert_guided(
        html,
        "filter-kind-help",
        "One asset kind: Machine, GPU, CPU pool, Service or Other.",
        control_id="filter-kind",
    )
    _assert_guided(
        html, "filter-parent-help", "Only child assets of that machine.", control_id="filter-parent"
    )
    _assert_guided(
        html, "filter-tag-help", "Only assets carrying that tag.", control_id="filter-tag"
    )
    _assert_guided(
        html,
        "filter-reservable-help",
        "Filter by the asset reservable flag (a property of the asset, not of "
        "your personal booking access).",
        control_id="filter-reservable",
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
    _assert_guided(
        html,
        "id_name-help",
        "Names are not unique; only the active target is constrained",
        control_id="id_name",
    )
    _assert_guided(
        html,
        "id_asset-help",
        "Bookings check the exact asset first, then its parent machine, then the global policy",
        control_id="id_asset",
    )
    _assert_guided(
        html,
        "id_min_duration_minutes-help",
        "1440 minutes = 24 hours = 1 day",
        control_id="id_min_duration_minutes",
    )
    _assert_guided(
        html,
        "id_max_duration_minutes-help",
        "2880 minutes = 48 hours = 2 days",
        control_id="id_max_duration_minutes",
    )
    _assert_guided(
        html,
        "id_booking_horizon_days-help",
        "How far into the future a booking may START",
        control_id="id_booking_horizon_days",
    )
    _assert_guided(
        html,
        "id_min_lead_minutes-help",
        "0 allows bookings that start right now",
        control_id="id_min_lead_minutes",
    )
    _assert_guided(
        html,
        "id_cancellation_cutoff_minutes-help",
        "0 means cancellation stays possible up to the start time.",
        control_id="id_cancellation_cutoff_minutes",
    )
    _assert_guided(
        html,
        "id_max_upcoming_per_principal-help",
        "not-yet-started reservations one principal",
        control_id="id_max_upcoming_per_principal",
    )
    _assert_guided(
        html,
        "id_max_concurrent_per_principal-help",
        "8 rejects a new booking when 8 or more existing records already intersect it",
        control_id="id_max_concurrent_per_principal",
    )
    _assert_guided(
        html,
        "id_purpose_required-help",
        "Require members to enter a purpose",
        control_id="id_purpose_required",
    )

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
def test_fresh_default_policy_presentation_real_initializer(
    client: Client,
    staff_user: User,
) -> None:
    """Fresh-install default policy presentation uses the real initializer.

    The fresh default minimum is 1 minute (not 30): the 30-minute value in
    the browser fixtures is a CUSTOM fixture, never the fresh default.
    """
    from slaif_reservation.reservations.initialization import initialize_default_policy

    result = initialize_default_policy()
    assert result.created, result.reason
    policy = result.policy
    assert policy is not None
    assert policy.name == "default"
    assert policy.min_duration_minutes == 1
    assert policy.max_duration_minutes == 2880
    client.force_login(staff_user)
    html = client.get(f"/manage/policies/{policy.id}/").content.decode()
    assert "1 to 2880 minutes" in html
    assert "1 minute - 2 days" in html
    assert "No lead required (a booking may start right now)." in html
    assert "Members may cancel up to the start time." in html
    assert "50 upcoming / 8 overlapping per principal" in html


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
        control_id="id_asset",
    )
    _assert_guided(html, "id_timezone-help", "IANA time zone name", control_id="id_timezone")
    _assert_guided(
        html,
        "id_start-help",
        "Local start date and time in the selected timezone.",
        control_id="id_start",
    )
    _assert_guided(
        html,
        "id_end-help",
        "New overlapping bookings are blocked from the start until the end",
        control_id="id_end",
    )
    _assert_guided(
        html, "id_reason-help", "Required. Explains the maintenance", control_id="id_reason"
    )
    _assert_guided(
        html,
        "id_confirm_overlaps-help",
        "Creating the blackout never cancels or releases them",
        control_id="id_confirm_overlaps",
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
def test_blackout_ambiguous_automatic_post_keeps_help(
    client: Client,
    staff_user: User,
    asset: Asset,
) -> None:
    """The staff blackout form rejects the ambiguous Automatic wall time
    and keeps the corrected occurrence help."""
    client.force_login(staff_user)
    response = client.post(
        "/manage/blackouts/new/",
        {
            "asset": str(asset.id),
            "timezone": "Europe/Ljubljana",
            "start": "2025-10-26T02:30",
            "end": "2025-10-26T04:30",
            "reason": "maintenance",
            "confirm_overlaps": "on",
        },
    )
    html = response.content.decode()
    assert response.status_code == 200
    assert "Local wall time is ambiguous; specify fold." in html
    assert "id_start_fold-help" in html
    assert "On fall-back the clock time repeats and Automatic is then rejected" in html
    assert MaintenanceBlackout.objects.count() == 0


@pytest.mark.django_db
def test_blackout_form_fold_semantics(asset: Asset) -> None:
    from slaif_reservation.management_ui.forms import MaintenanceBlackoutForm

    base = {
        "asset": str(asset.id),
        "timezone": "Europe/Ljubljana",
        "start": "2025-10-26T02:30",
        "end": "2025-10-26T04:30",
        "reason": "maintenance",
    }
    # Explicit occurrences resolve the repeated fall-back time.
    for fold in ("0", "1"):
        form = MaintenanceBlackoutForm({**base, "start_fold": fold})
        assert form.is_valid(), form.errors
    # Nonexistent spring-forward time is rejected however it is chosen.
    for fold in ("", "0", "1"):
        form = MaintenanceBlackoutForm({**base, "start": "2025-03-30T02:30", "start_fold": fold})
        assert not form.is_valid()
        assert "Local wall time does not exist in this timezone." in str(form.errors)


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
    _assert_guided(html, "id_asset-help", "Narrow the list to one asset", control_id="id_asset")
    _assert_guided(
        html, "id_q-help", "Matches the owner's email or display name", control_id="id_q"
    )
    _assert_guided(
        html, "id_status-help", "Confirmed, cancelled or released.", control_id="id_status"
    )
    _assert_guided(
        html, "id_lifecycle-help", "Active = started and still running", control_id="id_lifecycle"
    )
    _assert_guided(html, "id_from-help", "Aware ISO-8601 timestamp", control_id="id_from")
    _assert_guided(
        html,
        "id_to-help",
        "Keep reservations whose start is before this.",
        control_id="id_to",
    )
    assert "From (start at or after)" in html
    assert "To (start before)" in html


@pytest.mark.django_db
def test_audit_filter_guidance(client: Client, staff_user: User) -> None:
    client.force_login(staff_user)
    html = client.get("/manage/audit/").content.decode()
    _assert_no_dangling_aria(html)
    _assert_guided(html, "id_action-help", "Which operation was recorded.", control_id="id_action")
    _assert_guided(
        html,
        "id_target_type-help",
        "The record type the action applied to",
        control_id="id_target_type",
    )
    _assert_guided(
        html,
        "id_actor-help",
        "part of a display name or email, or an exact user UUID",
        control_id="id_actor",
    )
    _assert_guided(html, "id_source-help", "Where the action came from", control_id="id_source")
    _assert_guided(
        html,
        "id_correlation_id-help",
        "UUID that links the events of one operation",
        control_id="id_correlation_id",
    )
    _assert_guided(
        html,
        "id_occurred_from-help",
        "Keep events that happened at or after this.",
        control_id="id_occurred_from",
    )
    _assert_guided(
        html,
        "id_occurred_to-help",
        "Keep events that happened at or before this.",
        control_id="id_occurred_to",
    )
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
    _assert_guided(
        html,
        "id_username-help",
        "The email address of your administration account.",
        control_id="id_username",
    )
    _assert_guided(
        html,
        "id_password-help",
        "The same generic error appears for a wrong password",
        control_id="id_password",
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
    _assert_guided(
        html, "id_email_helptext", "Accounts are created by an administrator", control_id="id_email"
    )
    _assert_guided(
        html,
        "id_password1_helptext",
        "Members cannot change their own password",
        control_id="id_password1",
    )
    _assert_guided(
        html,
        "id_password2_helptext",
        "Re-enter the same password to confirm it.",
        control_id="id_password2",
    )
    _assert_guided(
        html,
        "id_is_staff_helptext",
        "not granted by individual permission selections",
        control_id="id_is_staff",
    )
    _assert_guided(
        html,
        "id_is_superuser_helptext",
        "does not bypass the active-human/staff admission gate",
        control_id="id_is_superuser",
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
        ("is_service_account", "Service-account API access is not supported"),
        ("is_active", "Inactive accounts cannot sign in anywhere"),
        ("is_staff", "per-model administration operations in this administration only"),
        ("is_superuser", "does not bypass the active-human/staff admission gate"),
        (
            "groups",
            "a group carrying reservations.book_assets lets its members create new reservations",
        ),
        (
            "user_permissions",
            "selecting reservations.book_assets lets this account create new reservations",
        ),
    ]:
        _assert_guided(html, f"id_{name}_helptext", fragment, control_id=f"id_{name}")
    _assert_guided(
        html,
        "id_is_service_account_helptext",
        "blocks member and administration sign-in and API token issuance/use",
        control_id="id_is_service_account",
    )
    assert "active human owner's scoped API token" in unescape(html)
    assert "Machine account for API automation" not in html
    # The select-filter association helper ships on the pages whose
    # JS-generated list boxes it binds (presentation only).
    assert "web/admin-form-guidance.js" in html
    # Editable important dates: real help, bound to the first split
    # sub-input via the bound-help widget (Django's template only ids
    # help divs that have a single control id).
    _assert_guided(
        html,
        "id_last_login_0_helptext",
        "Booking and availability logic never reads it",
        control_id="id_last_login_0",
    )
    _assert_guided(
        html,
        "id_date_joined_0_helptext",
        "the separate created_at timestamp is the immutable product record",
        control_id="id_date_joined_0",
    )

    # A valid change POST preserves the stored hash. The admin renders the
    # datetime fields with split date/time inputs.
    issued = issue_api_token(
        owner=member_user, name="Guidance regression", scopes=["reservations:read"], lifetime_days=1
    )
    authorization = f"Bearer {issued.bearer_token}"
    assert client.get("/api/v1/me/", HTTP_AUTHORIZATION=authorization).status_code == 200
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
    assert member_user.is_service_account
    denied = client.get("/api/v1/me/", HTTP_AUTHORIZATION=authorization)
    assert denied.status_code == 401 and denied.json()["code"] == "invalid_token"
    with pytest.raises(ApiTokenDomainError) as error:
        issue_api_token(
            owner=member_user, name="Denied", scopes=["reservations:read"], lifetime_days=1
        )
    assert error.value.code == TOKEN_OWNER_INVALID


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
        control_id="id_password1",
    )
    _assert_guided(
        html,
        "id_password2_helptext",
        "Enter the same password as before, for verification.",
        control_id="id_password2",
    )

    # The dynamically added high-impact choice is explained with the
    # product truth: no alternate human login backend exists here. The
    # help div keeps the first choice's id and BOTH rendered choices
    # bind it via aria-describedby.
    assert "This deployment provides no other human login backend" in unescape(html)
    assert "a disabled user cannot sign in until an administrator sets" in unescape(html)
    assert "If disabled, the current password for this user will be lost." in html
    assert 'id="id_unusable_warning"' in html
    assert "they may still be able to authenticate using other backends" not in html
    _assert_guided(
        html,
        "id_usable_password_0_helptext",
        "This deployment provides no other human login backend",
        control_id="id_usable_password_0",
    )
    _control_binds_help(html, "id_usable_password_1", "id_usable_password_0_helptext")

    # Unchanged negative: mismatched passwords are still rejected, and the
    # re-rendered page keeps the bound help.
    response = client.post(
        f"/admin/accounts/user/{member_user.pk}/password/",
        {"password1": "a-new-passw0rd", "password2": "different-passw0rd"},
    )
    assert response.status_code == 200
    member_user.refresh_from_db()
    assert member_user.has_usable_password()
    rehtml = response.content.decode()
    _assert_no_dangling_aria(rehtml)
    assert 'id="id_usable_password_0_helptext"' in rehtml
    _control_binds_help(rehtml, "id_usable_password_0", "id_usable_password_0_helptext")
    _control_binds_help(rehtml, "id_usable_password_1", "id_usable_password_0_helptext")
    assert "This deployment provides no other human login backend" in unescape(rehtml)


@pytest.mark.django_db
def test_admin_password_change_enable_disable_behavior(
    client: Client, admin_user: User, staff_user: User
) -> None:
    url = f"/admin/accounts/user/{staff_user.pk}/password/"

    # A user without a usable password gets the enable page: no
    # usable_password choice, only the enable action.
    staff_user.set_unusable_password()
    staff_user.save(update_fields=["password"])
    client.force_login(admin_user)
    html = client.get(url).content.decode()
    # The template wraps "enable" in <strong>, so match the contiguous part.
    assert "password-based authentication for this user" in unescape(html)
    assert 'id="id_usable_password"' not in html
    assert "Enable password-based authentication" in html

    # Enabling sets a real password through the unchanged validators.
    response = client.post(
        url,
        {
            "usable_password": "true",
            "password1": "fresh-staff-passw0rd",
            "password2": "fresh-staff-passw0rd",
        },
    )
    assert response.status_code == 302
    staff_user.refresh_from_db()
    assert staff_user.has_usable_password()
    assert staff_user.check_password("fresh-staff-passw0rd")

    # Disabling removes the current password; no alternate backend exists.
    # The disable submission must carry the unset-password action.
    response = client.post(url, {"usable_password": "false", "unset-password": "1"})
    assert response.status_code == 302
    staff_user.refresh_from_db()
    assert not staff_user.has_usable_password()
    assert not staff_user.check_password("fresh-staff-passw0rd")

    # The change page now shows the safe disabled status again.
    html = client.get(f"/admin/accounts/user/{staff_user.pk}/change/").content.decode()
    assert "Password disabled" in html


@pytest.mark.django_db
def test_admin_group_permissions_help(client: Client, admin_user: User) -> None:
    client.force_login(admin_user)
    html = client.get("/admin/auth/group/add/").content.decode()
    _assert_guided(
        html,
        "id_permissions_helptext",
        "Permissions granted through this group",
        control_id="id_permissions",
    )
    assert (
        "a group with reservations.book_assets lets its members create new reservations"
        in unescape(html)
    )
    assert "do not grant management access (which follows the active staff flag)" in unescape(html)
    assert "not project or membership authorization" in html
    # The select-filter association helper ships on the group pages too.
    assert "web/admin-form-guidance.js" in html


@pytest.mark.django_db
def test_admin_permission_help_matches_authorization(client: Client, admin_user: User) -> None:
    """The rendered permission help states the real authorization rules.

    Management access follows the active human staff status alone
    (management_ui/auth.py); no model permission is consulted there.
    Model permissions govern per-model administration operations in the
    administration only, and protected models stay protected.
    """
    bare_staff = User.objects.create_user(
        email="bare-staff@example.com",
        password="not-a-secret",
        display_name="Bare Staff",
        is_staff=True,
    )
    # Real staff WITHOUT individual/group permissions can access management.
    client.force_login(bare_staff)
    assert client.get("/manage/").status_code == 200
    assert client.get("/manage/reservations/").status_code == 200
    # The same user cannot perform administration model operations:
    # model permission enforcement is retained.
    assert client.get("/admin/reservations/reservationpolicy/").status_code == 403
    # Protected model: even a superuser has no add permission for tokens.
    client.force_login(admin_user)
    assert client.get("/admin/accounts/apitoken/add/").status_code == 403
    # Rendered wording pins the same rules on the user change page.
    html = client.get(f"/admin/accounts/user/{bare_staff.pk}/change/").content.decode()
    for name, fragment in [
        ("is_staff", "management itself needs none of them"),
        ("user_permissions", "do not grant management access, which follows the active staff flag"),
    ]:
        _assert_guided(html, f"id_{name}_helptext", fragment, control_id=f"id_{name}")


def _routed_callback_modules() -> set[str]:
    """Modules of every view callback actually present in the URL conf."""
    from django.urls import get_resolver

    modules: set[str] = set()
    stack = list(get_resolver().url_patterns)
    while stack:
        pattern = stack.pop()
        handler = getattr(pattern, "_handler", None)
        if handler is not None and hasattr(handler, "url_patterns"):
            stack.extend(handler.url_patterns)
        else:
            module = getattr(handler, "__module__", None)
            if module:
                modules.add(module)
    return modules


@pytest.mark.django_db
def test_staff_asset_api_routes_are_live(
    client: Client,
    staff_user: User,
    member_user: User,
    asset: Asset,
) -> None:
    """The staff REST endpoints of assets/api.py ARE routed (superseding
    the 037-b blanket unreachable-REST claim). config.urls includes
    api.urls, which expands assets.api_urls: /api/v1/assets/ and the
    UUID detail are live staff-session endpoints. No routes are added or
    removed here; the legacy assets/views.py HTML views are the only
    unrouted assets-app surface.
    """
    from slaif_reservation.assets.api import AssetDetailAPIView, AssetListAPIView

    # Real resolver correspondence.
    assert reverse("api-v1:asset-list") == "/api/v1/assets/"
    assert reverse("api-v1:asset-detail", args=[asset.id]) == f"/api/v1/assets/{asset.id}/"
    assert resolve("/api/v1/assets/").func.cls is AssetListAPIView
    assert resolve(f"/api/v1/assets/{asset.id}/").func.cls is AssetDetailAPIView

    # The legacy HTML inventory views of assets/views.py are NOT routed.
    modules = _routed_callback_modules()
    assert "slaif_reservation.assets.views" not in modules

    # The live endpoints stay staff-session-only (the bearer assets:read
    # scope remains reserved: no token authentication is offered there).
    assert client.get("/api/v1/assets/").status_code == 403
    client.force_login(member_user)
    assert client.get("/api/v1/assets/").status_code == 403
    client.force_login(staff_user)
    response = client.get("/api/v1/assets/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2  # machine + child asset fixtures
    assert {item["slug"] for item in payload["results"]} == {
        "guidance-machine",
        "guidance-gpu",
    }
    detail = client.get(f"/api/v1/assets/{asset.id}/")
    assert detail.status_code == 200
    assert detail.json()["slug"] == "guidance-gpu"


@pytest.mark.django_db
def test_admin_asset_forms_guidance(client: Client, admin_user: User) -> None:
    client.force_login(admin_user)
    html = client.get("/admin/assets/asset/add/").content.decode()
    _assert_no_dangling_aria(html)
    _assert_guided(
        html,
        "id_parent_helptext",
        "a machine itself never has a parent",
        control_id="id_parent",
    )
    _assert_guided(
        html,
        "id_slug_helptext",
        "changing the slug does not change those URLs",
        control_id="id_slug",
    )
    _assert_guided(
        html,
        "id_kind_helptext",
        "Only a machine can take children",
        control_id="id_kind",
    )
    _assert_guided(
        html,
        "id_booking_mode_helptext",
        "Only 'Exclusive' is supported",
        control_id="id_booking_mode",
    )
    _assert_guided(
        html,
        "id_location_helptext",
        "Internal room or location label for staff",
        control_id="id_location",
    )
    _assert_guided(
        html,
        "id_timezone_helptext",
        "availability is shown in each member's own profile timezone",
        control_id="id_timezone",
    )
    _assert_guided(
        html,
        "id_physical_locator_helptext",
        "Internal physical location for operators",
        control_id="id_physical_locator",
    )

    html = client.get("/admin/assets/assettag/add/").content.decode()
    _assert_guided(html, "id_name_helptext", "Display name of the tag", control_id="id_name")
    _assert_guided(
        html, "id_slug_helptext", "Stable identifier, generated from the name", control_id="id_slug"
    )


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
