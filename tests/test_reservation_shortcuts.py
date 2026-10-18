from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth.models import Permission

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.models import Asset
from slaif_reservation.reservations.models import Reservation, ReservationPolicy
from slaif_reservation.reservations.services import update_policy
from slaif_reservation.web.forms import ReservationForm

NOW = datetime(2026, 10, 24, 8, 0, 30, tzinfo=UTC)


@pytest.fixture
def clock(monkeypatch):
    monkeypatch.setattr("django.utils.timezone.now", lambda: NOW)
    return NOW


@pytest.fixture
def member():
    created = User.objects.create_user(
        email="uat-member@example.test", password="not-a-secret", timezone="Asia/Kathmandu"
    )
    # A16: explicit baseline booking capability (real Permission row).
    created.user_permissions.add(
        Permission.objects.get(codename="book_assets", content_type__app_label="reservations")
    )
    return created


@pytest.fixture
def staff():
    # 050-a: explicit policy-management capability for this fixture.
    created = User.objects.create_user(
        email="uat-staff@example.test", password="not-a-secret", is_staff=True
    )
    created.user_permissions.add(
        Permission.objects.get(
            codename="manage_booking_policies",
            content_type__app_label="reservations",
        )
    )
    return created


@pytest.fixture
def asset():
    return Asset.objects.create(
        slug="uat-workstation",
        name="Atlas workstation",
        kind="machine",
        active=True,
        reservable=True,
    )


@pytest.fixture
def policy(asset):
    return ReservationPolicy.objects.create(
        name="UAT policy",
        asset=None,
        min_duration_minutes=15,
        max_duration_minutes=240,
        booking_horizon_days=7,
        min_lead_minutes=30,
        max_upcoming_per_principal=20,
        max_concurrent_per_principal=8,
    )


def local(instant, member):
    return instant.astimezone(ZoneInfo(member.timezone)).strftime("%Y-%m-%dT%H:%M:%S")


def post(client, member, asset, start, duration="60", **extra):
    client.force_login(member)
    return client.post(
        f"/assets/{asset.id}/reserve/",
        {"start": local(start, member), "duration": duration, "purpose": "", **extra},
    )


@pytest.mark.parametrize("minutes", [60, 120, 240])
def test_quick_duration_parses_without_end_and_ignores_browser_end(minutes):
    form = ReservationForm(
        {"start": "2026-10-24T14:45", "duration": str(minutes), "end": "not-a-date"},
        timezone_name="Asia/Kathmandu",
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["start_instant"] == datetime(2026, 10, 24, 9, tzinfo=UTC)
    assert form.cleaned_data["end_instant"] - form.cleaned_data["start_instant"] == timedelta(
        minutes=minutes
    )


@pytest.mark.parametrize("duration", ["custom", ""])
def test_custom_end_preserves_explicit_end_and_legacy_missing_choice(duration):
    form = ReservationForm(
        {"start": "2026-10-24T14:45", "end": "2026-10-24T17:15", "duration": duration},
        timezone_name="Asia/Kathmandu",
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["end_instant"] - form.cleaned_data["start_instant"] == timedelta(
        minutes=150
    )


@pytest.mark.parametrize(
    "data",
    [
        {"duration": "custom"},
        {"duration": "999"},
        {"duration": "custom", "end": "2026-10-24T08:00"},
    ],
)
def test_bad_choice_or_missing_or_reversed_custom_end(data):
    form = ReservationForm({"start": "2026-10-24T09:00", **data}, timezone_name="UTC")
    assert not form.is_valid()


@pytest.mark.parametrize(
    ("start", "fold", "expected"),
    [
        ("2026-03-29T01:30", "", datetime(2026, 3, 29, 1, 30, tzinfo=UTC)),
        ("2026-10-25T02:30", "0", datetime(2026, 10, 25, 1, 30, tzinfo=UTC)),
        ("2026-10-25T02:30", "1", datetime(2026, 10, 25, 2, 30, tzinfo=UTC)),
    ],
)
def test_quick_duration_is_elapsed_utc_time_across_dst(start, fold, expected):
    form = ReservationForm(
        {"start": start, "start_fold": fold, "duration": "60"}, timezone_name="Europe/Ljubljana"
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["end_instant"] == expected
    assert form.cleaned_data["end_instant"] - form.cleaned_data["start_instant"] == timedelta(
        hours=1
    )


@pytest.mark.parametrize(
    ("start", "fold"),
    [
        ("2026-10-25T02:30", ""),
        ("2026-03-29T02:30", ""),
        ("2026-03-29T02:30", "0"),
        ("2026-03-29T02:30", "1"),
    ],
)
def test_quick_duration_preserves_fold_and_gap_refusal(start, fold):
    form = ReservationForm(
        {"start": start, "start_fold": fold, "duration": "60"}, timezone_name="Europe/Ljubljana"
    )
    assert not form.is_valid()
    assert "start" in form.errors


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("minimum", "maximum", "expected"),
    [
        (15, 240, ["60", "120", "240", "custom"]),
        (90, 180, ["120", "custom"]),
        (300, 360, ["custom"]),
    ],
)
def test_duration_display_uses_effective_policy_only(minimum, maximum, expected, policy):
    policy.min_duration_minutes, policy.max_duration_minutes = minimum, maximum
    form = ReservationForm(timezone_name="UTC", policy=policy, now=NOW)
    assert [value for value, _ in form.fields["duration"].widget.choices] == expected


@pytest.mark.django_db
def test_native_range_is_in_profile_timezone_and_rounds_inward(
    clock, policy, client, member, asset
):
    client.force_login(member)
    response = client.get(f"/assets/{asset.id}/reserve/")
    form = response.context["form"]
    assert form.fields["start"].widget.attrs["min"] == "2026-10-24T14:16"
    assert form.fields["start"].widget.attrs["max"] == "2026-10-31T13:45"
    assert "Reservations may start between" in response.content.decode()
    assert "Asia/Kathmandu" in form.fields["start"].help_text


@pytest.mark.django_db
def test_horizon_is_elapsed_days_across_dst(clock, policy):
    policy.booking_horizon_days = 1
    form = ReservationForm(timezone_name="Europe/Ljubljana", policy=policy, now=NOW)
    assert form.fields["start"].widget.attrs["max"] == "2026-10-25T09:00"


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("start", "allowed", "error"),
    [
        (NOW + timedelta(minutes=30), True, ""),
        (NOW + timedelta(minutes=30, seconds=-1), False, "lead time"),
        (NOW + timedelta(days=7), True, ""),
        (NOW + timedelta(days=7, seconds=1), False, "booking horizon"),
    ],
)
def test_lead_and_start_horizon_remain_authoritative(
    clock, policy, client, member, asset, start, allowed, error
):
    response = post(client, member, asset, start)
    assert response.status_code == (302 if allowed else 200)
    assert Reservation.objects.count() == int(allowed)
    if not allowed:
        assert error in response.content.decode()
    else:
        assert Reservation.objects.get().end_at == start + timedelta(hours=1)


@pytest.mark.django_db
@pytest.mark.parametrize("change", ["horizon", "lead", "duration", "time"])
def test_changed_policy_or_clock_after_get_rejects_stale_post(
    clock, policy, client, member, asset, staff, monkeypatch, change
):
    client.force_login(member)
    assert client.get(f"/assets/{asset.id}/reserve/").status_code == 200
    start, duration = NOW + timedelta(days=2), "60"
    if change == "horizon":
        policy.booking_horizon_days = 1
    elif change == "lead":
        start = NOW + timedelta(minutes=60)
        policy.min_lead_minutes = 120
    elif change == "duration":
        duration = "120"
        policy.max_duration_minutes = 90
    else:
        monkeypatch.setattr("django.utils.timezone.now", lambda: NOW + timedelta(days=3))
    if change != "time":
        update_policy(
            policy=policy,
            actor_user=staff,
            booking_horizon_days=policy.booking_horizon_days,
            min_lead_minutes=policy.min_lead_minutes,
            max_duration_minutes=policy.max_duration_minutes,
        )
    response = post(client, member, asset, start, duration)
    assert response.status_code == 200
    assert Reservation.objects.count() == 0
    messages = {
        "horizon": "booking horizon",
        "lead": "lead time",
        "duration": "policy maximum",
        "time": "past",
    }
    assert messages[change] in response.content.decode()


@pytest.mark.django_db
def test_conflict_and_purpose_validation_still_use_service(
    clock, policy, client, member, asset, staff
):
    start = NOW + timedelta(hours=2)
    assert post(client, member, asset, start).status_code == 302
    response = post(client, member, asset, start)
    assert (
        response.status_code == 200
        and "That time is no longer available." in response.content.decode()
    )
    assert Reservation.objects.count() == 1
    update_policy(policy=policy, actor_user=staff, purpose_required=True)
    response = post(client, member, asset, NOW + timedelta(hours=4))
    assert response.status_code == 200 and "purpose" in response.content.decode().lower()
    assert Reservation.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize("minutes", [60, 120, 240])
def test_quick_post_creates_exact_duration(clock, policy, client, member, asset, minutes):
    start = NOW + timedelta(hours=2)
    response = post(client, member, asset, start, str(minutes))
    assert response.status_code == 302
    reservation = Reservation.objects.get()
    assert reservation.start_at == start
    assert reservation.end_at - reservation.start_at == timedelta(minutes=minutes)


def test_forged_extreme_start_is_a_form_error_not_a_server_exception():
    form = ReservationForm({"start": "9999-12-31T23:00", "duration": "240"}, timezone_name="UTC")
    assert not form.is_valid()
    assert "supported date range" in str(form.errors["start"])


@pytest.mark.parametrize(
    ("minimum", "maximum", "lead", "expected_start", "expected_end"),
    [
        (15, 240, 0, "2026-10-24T13:46", "2026-10-24T14:46"),
        (15, 240, 30, "2026-10-24T14:16", "2026-10-24T15:16"),
        (90, 180, 0, "2026-10-24T13:46", "2026-10-24T15:16"),
        (15, 30, 0, "2026-10-24T13:46", "2026-10-24T14:16"),
    ],
)
def test_new_form_defaults_use_current_time_profile_and_policy(
    minimum, maximum, lead, expected_start, expected_end
):
    policy = ReservationPolicy(
        min_duration_minutes=minimum,
        max_duration_minutes=maximum,
        min_lead_minutes=lead,
        booking_horizon_days=7,
    )
    form = ReservationForm(timezone_name="Asia/Kathmandu", policy=policy, now=NOW)
    assert form["start"].value() == expected_start
    assert form["end"].value() == expected_end
    assert form["duration"].value() == "custom"
    assert form["start_fold"].value() == form["end_fold"].value() == ""


@pytest.mark.parametrize(
    ("instant", "start", "end", "start_fold", "end_fold"),
    [
        (datetime(2026, 3, 29, 0, 30, tzinfo=UTC), "2026-03-29T01:30", "2026-03-29T03:30", "", ""),
        (
            datetime(2026, 10, 25, 0, 15, tzinfo=UTC),
            "2026-10-25T02:15",
            "2026-10-25T02:15",
            "0",
            "1",
        ),
        (
            datetime(2026, 10, 25, 1, 15, tzinfo=UTC),
            "2026-10-25T02:15",
            "2026-10-25T03:15",
            "1",
            "",
        ),
    ],
)
def test_generated_defaults_roundtrip_across_dst(instant, start, end, start_fold, end_fold):
    policy = ReservationPolicy(
        min_duration_minutes=15, max_duration_minutes=240, booking_horizon_days=7
    )
    form = ReservationForm(timezone_name="Europe/Ljubljana", policy=policy, now=instant)
    assert form["start"].value() == start
    assert form["end"].value() == end
    assert form["start_fold"].value() == start_fold
    assert form["end_fold"].value() == end_fold
    submitted = ReservationForm(form.initial, timezone_name="Europe/Ljubljana")
    assert submitted.is_valid(), submitted.errors
    assert submitted.cleaned_data["start_instant"] == instant
    assert submitted.cleaned_data["end_instant"] == instant + timedelta(hours=1)


def test_defaults_do_not_replace_bound_empty_or_invalid_values_or_explicit_initial():
    policy = ReservationPolicy(
        min_duration_minutes=15, max_duration_minutes=240, booking_horizon_days=7
    )
    for data in ({}, {"start": "invalid", "end": "", "start_fold": "1"}):
        form = ReservationForm(data, timezone_name="UTC", policy=policy, now=NOW)
        assert form["start"].value() == data.get("start")
        assert form["end"].value() == data.get("end")
        assert not form.is_valid()
        assert form.initial == {}
    initial = {"start": "2026-10-26T09:00", "end": "2026-10-26T11:00", "start_fold": "1"}
    form = ReservationForm(timezone_name="UTC", policy=policy, now=NOW, initial=initial)
    assert form.initial == initial


def test_no_defaults_when_no_policy_or_no_start_minute_is_available():
    form = ReservationForm(timezone_name="UTC", now=NOW)
    assert form.initial == {}
    policy = ReservationPolicy(
        min_duration_minutes=15, max_duration_minutes=240, booking_horizon_days=0
    )
    form = ReservationForm(timezone_name="UTC", policy=policy, now=NOW)
    assert form.initial == {}


@pytest.mark.django_db
def test_new_form_defaults_can_be_submitted_unchanged(clock, policy, client, member, asset):
    client.force_login(member)
    response = client.get(f"/assets/{asset.id}/reserve/")
    form = response.context["form"]
    response = client.post(
        f"/assets/{asset.id}/reserve/",
        {name: form[name].value() or "" for name in form.fields},
    )
    assert response.status_code == 302
    reservation = Reservation.objects.get()
    assert reservation.start_at == NOW.replace(minute=31, second=0)
    assert reservation.end_at == reservation.start_at + timedelta(hours=1)
