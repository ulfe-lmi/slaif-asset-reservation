"""Read-only asset reservation calendar (order 054-a, issue #111).

Focused PostgreSQL-backed coverage of the new /manage/reservations/calendar/
surface: the permission matrix (anonymous, member, staff-without-grant,
Administration-View-only, service account, inactive, group grant, superuser),
bounded GET input, exact-asset isolation, Monday-Sunday one/four-week windows
with previous/next navigation, viewer profile timezone and DST boundaries,
half-open [start, effective_end) semantics, released consumed-time clipping,
cancelled absence, the output cap, and zero writes.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, timedelta
from html import unescape
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client
from django.urls import reverse

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.management_ui.selectors import CALENDAR_MAX_INTERVALS
from slaif_reservation.reservations.models import Reservation, ReservationPolicy

VIEWER_EMAIL = "cal-viewer@example.com"
VIEWER_NAME = "Calendar Viewer"
OWNER_EMAIL = "cal-owner@example.com"
OWNER_NAME = "Calendar Owner"

#: Fixed stable CET week (no transition inside).
WEEK_MONDAY = date(2026, 11, 2)
WEEK_END = WEEK_MONDAY + timedelta(days=7)
#: Fall-back week: 2026-10-25 01:00 UTC, local 02:00-03:00 repeated.
FALL_MONDAY = date(2026, 10, 19)
#: Spring-forward week: 2027-03-28 01:00 UTC, local 02:00-03:00 skipped.
SPRING_MONDAY = date(2027, 3, 22)

assert WEEK_MONDAY.weekday() == 0
assert FALL_MONDAY.weekday() == 0
assert SPRING_MONDAY.weekday() == 0


def utc(y: int, mo: int, d: int, h: int = 0, mi: int = 0) -> datetime:
    return datetime(y, mo, d, h, mi, tzinfo=UTC)


def local_cet(y: int, mo: int, d: int, h: int = 0, mi: int = 0) -> datetime:
    """Europe/Ljubljana November wall time (CET, UTC+1)."""
    return utc(y, mo, d, h, mi) - timedelta(hours=1)


def local_cest(y: int, mo: int, d: int, h: int = 0, mi: int = 0) -> datetime:
    """Europe/Ljubljana summer wall time (CEST, UTC+2)."""
    return utc(y, mo, d, h, mi) - timedelta(hours=2)


def permission(codename: str) -> Permission:
    return Permission.objects.get(codename=codename, content_type__app_label="reservations")


def grant(user: User, *codenames: str) -> User:
    user.user_permissions.add(*[permission(c) for c in codenames])
    return user


def make_user(
    email: str,
    display_name: str,
    *,
    timezone_name: str = "Europe/Ljubljana",
    is_staff: bool = False,
    is_active: bool = True,
    is_service_account: bool = False,
    **extra: object,
) -> User:
    return User.objects.create_user(
        email=email,
        password="not-a-secret",
        display_name=display_name,
        timezone=timezone_name,
        is_staff=is_staff,
        is_active=is_active,
        is_service_account=is_service_account,
        **extra,
    )


@pytest.fixture
def viewer() -> User:
    return grant(make_user(VIEWER_EMAIL, VIEWER_NAME), "view_all_reservations")


@pytest.fixture
def viewer_utc() -> User:
    return grant(
        make_user("cal-viewer-utc@example.com", "UTC Viewer", timezone_name="UTC"),
        "view_all_reservations",
    )


@pytest.fixture
def member_booker() -> User:
    return grant(make_user("cal-member@example.com", "Calendar Member"), "book_assets")


@pytest.fixture
def staff_only() -> User:
    return make_user("cal-staffonly@example.com", "Staff Only", is_staff=True)


@pytest.fixture
def admin_view_only() -> User:
    user = make_user("cal-adminview@example.com", "Admin View", is_staff=True)
    ct = ContentType.objects.get_for_model(Reservation)
    user.user_permissions.add(Permission.objects.get(codename="view_reservation", content_type=ct))
    return user


@pytest.fixture
def service_account() -> User:
    return grant(
        make_user(
            "cal-svc@example.com",
            "Calendar Service",
            is_staff=True,
            is_service_account=True,
        ),
        "view_all_reservations",
    )


@pytest.fixture
def inactive_viewer() -> User:
    return grant(
        make_user("cal-inactive@example.com", "Inactive Viewer", is_active=False),
        "view_all_reservations",
    )


@pytest.fixture
def group_viewer() -> User:
    user = make_user("cal-group@example.com", "Group Viewer")
    group = Group.objects.create(name="cal-readers")
    group.permissions.add(permission("view_all_reservations"))
    user.groups.add(group)
    return user


@pytest.fixture
def superuser() -> User:
    return User.objects.create_superuser(
        email="cal-super@example.com",
        password="not-a-secret",
        display_name="Calendar Super",
        timezone="Europe/Ljubljana",
    )


@pytest.fixture
def owner() -> User:
    return make_user(OWNER_EMAIL, OWNER_NAME)


@pytest.fixture
def machine() -> Asset:
    return Asset.objects.create(
        slug="cal-machine",
        name="Cal Machine",
        kind=Asset.KIND_MACHINE,
        active=True,
        reservable=False,
        verification_required=False,
    )


@pytest.fixture
def asset(machine: Asset) -> Asset:
    return Asset.objects.create(
        slug="cal-gpu",
        name="Cal GPU",
        kind=Asset.KIND_GPU,
        parent=machine,
        active=True,
        reservable=True,
        verification_required=False,
    )


@pytest.fixture
def other_machine() -> Asset:
    return Asset.objects.create(
        slug="cal-machine-2",
        name="Cal Machine 2",
        kind=Asset.KIND_MACHINE,
        active=True,
        reservable=False,
        verification_required=False,
    )


@pytest.fixture
def other_asset(other_machine: Asset) -> Asset:
    return Asset.objects.create(
        slug="cal-gpu-2",
        name="Cal GPU 2",
        kind=Asset.KIND_GPU,
        parent=other_machine,
        active=True,
        reservable=True,
        verification_required=False,
    )


@pytest.fixture
def policy(asset: Asset, other_asset: Asset) -> ReservationPolicy:
    ReservationPolicy.objects.create(
        name="Cal policy",
        asset=asset,
        min_duration_minutes=10,
        max_duration_minutes=1440,
        booking_horizon_days=60,
        min_lead_minutes=0,
        cancellation_cutoff_minutes=0,
        max_upcoming_per_principal=50,
        max_concurrent_per_principal=10,
        purpose_required=False,
    )
    return ReservationPolicy.objects.create(
        name="Cal policy 2",
        asset=other_asset,
        min_duration_minutes=10,
        max_duration_minutes=1440,
        booking_horizon_days=60,
        min_lead_minutes=0,
        cancellation_cutoff_minutes=0,
        max_upcoming_per_principal=50,
        max_concurrent_per_principal=10,
        purpose_required=False,
    )


def make_reservation(
    user: User,
    target: Asset,
    start: datetime,
    end: datetime,
    *,
    status: str = Reservation.STATUS_CONFIRMED,
    effective_end: datetime | None = None,
) -> Reservation:
    effective = effective_end or end
    return Reservation.objects.create(
        asset=target,
        requested_by_user=user,
        source=Reservation.SOURCE_WEB,
        status=status,
        start_at=start,
        end_at=end,
        effective_end_at=effective,
        # The released-fields check requires effective_end_at == released_at
        # strictly inside (start_at, end_at); released callers must therefore
        # pass an effective_end earlier than the original end.
        released_at=(effective if status == Reservation.STATUS_RELEASED else None),
        cancelled_at=(
            start + timedelta(minutes=5) if status == Reservation.STATUS_CANCELLED else None
        ),
        cancelled_by=user if status == Reservation.STATUS_CANCELLED else None,
        cancellation_reason="" if status != Reservation.STATUS_CANCELLED else "gone",
    )


def calendar_url(asset: Asset, **query: object) -> str:
    path = reverse("management-ui:reservation-calendar", args=[asset.id])
    if not query:
        return path
    params = "&".join(f"{key}={value}" for key, value in query.items())
    return f"{path}?{params}"


def week_query(monday: date, weeks: int) -> dict[str, object]:
    return {"week": monday.isoformat(), "weeks": weeks}


def window_label(html: str) -> str:
    """The displayed Monday-Sunday window label paragraph text."""
    match = re.search(r'<p class="calendar-window">(.*?)</p>', html, re.S)
    assert match, "window label paragraph not found"
    return match.group(1).strip()


def chip_labels(html: str, day_heading: str) -> list[str]:
    """Time labels of the interval chips inside one day cell."""
    cell = re.search(
        rf'<h2 class="calendar-day-heading">{re.escape(day_heading)}'
        r"</h2>(.*?)(?=\s*</div>)",
        html,
        re.S,
    )
    assert cell, f"day cell not found for {day_heading!r}"
    return [
        unescape(label)
        for label in re.findall(r'calendar-interval-time">([^<]+)</span>', cell.group(1))
    ]


# --------------------------------------------------------------------------
# Permission matrix
# --------------------------------------------------------------------------


@pytest.mark.django_db
def test_anonymous_redirected_to_login(client: Client, asset: Asset) -> None:
    response = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1)))
    assert response.status_code == 302
    assert response["Location"].startswith("/login/?next=")


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("user_fixture", "expected"),
    [
        ("member_booker", 403),
        ("staff_only", 403),
        ("admin_view_only", 403),
        ("service_account", 403),
        # An inactive session is demoted to anonymous by Django, so the
        # route redirects to login instead of answering 403.
        ("inactive_viewer", 302),
    ],
)
def test_unauthorized_principals_denied_before_rows(
    client: Client,
    asset: Asset,
    owner: User,
    user_fixture: str,
    expected: int,
    request: pytest.FixtureRequest,
) -> None:
    user = request.getfixturevalue(user_fixture)
    reservation = make_reservation(
        owner, asset, local_cet(2026, 11, 3, 14), local_cet(2026, 11, 3, 16)
    )
    client.force_login(user)
    response = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1)))
    assert response.status_code == expected
    content = response.content.decode()
    assert OWNER_EMAIL not in content
    assert OWNER_NAME not in content
    assert str(reservation.id) not in content


@pytest.mark.django_db
@pytest.mark.parametrize("user_fixture", ["viewer", "group_viewer", "superuser"])
def test_authorized_principals_admitted(
    client: Client, asset: Asset, user_fixture: str, request: pytest.FixtureRequest
) -> None:
    user = request.getfixturevalue(user_fixture)
    client.force_login(user)
    response = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1)))
    assert response.status_code == 200
    assert b"Cal GPU" in response.content


@pytest.mark.django_db
def test_denied_principal_fetches_no_rows(
    client: Client, asset: Asset, staff_only: User, owner: User
) -> None:
    """The 403 must be produced before any protected row is read."""
    make_reservation(owner, asset, local_cet(2026, 11, 3, 14), local_cet(2026, 11, 3, 16))
    client.force_login(staff_only)
    response = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1)))
    assert response.status_code == 403
    assert b"Cal GPU" not in response.content


@pytest.mark.django_db
def test_post_is_not_allowed(client: Client, asset: Asset, viewer: User) -> None:
    client.force_login(viewer)
    response = client.post(calendar_url(asset, **week_query(WEEK_MONDAY, 1)), data={"reason": "x"})
    assert response.status_code == 405
    assert response["Allow"] == "GET"


# --------------------------------------------------------------------------
# Bounded input
# --------------------------------------------------------------------------


@pytest.mark.django_db
def test_unknown_asset_is_404(client: Client, asset: Asset, viewer: User) -> None:
    import uuid

    client.force_login(viewer)
    path = reverse("management-ui:reservation-calendar", args=[uuid.uuid4()])
    response = client.get(f"{path}?week={WEEK_MONDAY.isoformat()}&weeks=1")
    assert response.status_code == 404
    # A non-UUID path segment never resolves to the calendar route either.
    assert client.get("/manage/reservations/calendar/not-a-uuid/").status_code == 404


@pytest.mark.django_db
def test_malformed_week_is_400(client: Client, asset: Asset, viewer: User) -> None:
    client.force_login(viewer)
    for bad in ("not-a-date", "2026-13-40", "2026/11/02", "2026-11-02T00:00"):
        response = client.get(calendar_url(asset, week=bad, weeks=1))
        assert response.status_code == 400, bad
        assert b"Traceback" not in response.content
    # ISO-8601 basic form (no dashes) is a valid date and is accepted.
    assert client.get(calendar_url(asset, week="20261102", weeks=1)).status_code == 200


@pytest.mark.django_db
def test_out_of_range_week_is_400(client: Client, asset: Asset, viewer: User) -> None:
    client.force_login(viewer)
    response = client.get(calendar_url(asset, week="2037-01-05", weeks=1))
    assert response.status_code == 400
    response = client.get(calendar_url(asset, week="2016-01-04", weeks=1))
    assert response.status_code == 400


@pytest.mark.django_db
def test_invalid_week_length_is_400(client: Client, asset: Asset, viewer: User) -> None:
    client.force_login(viewer)
    for bad in ("0", "2", "5", "abc", "-4", "1.5"):
        response = client.get(calendar_url(asset, week=WEEK_MONDAY.isoformat(), weeks=bad))
        assert response.status_code == 400, bad
        assert b"Traceback" not in response.content


@pytest.mark.django_db
def test_default_window_is_current_local_week(client: Client, asset: Asset, viewer: User) -> None:
    from django.utils import timezone

    client.force_login(viewer)
    response = client.get(calendar_url(asset))
    assert response.status_code == 200
    today_local = timezone.now().astimezone(ZoneInfo("Europe/Ljubljana")).date()
    monday = today_local - timedelta(days=today_local.weekday())
    assert monday.strftime("%A %d %b %Y").encode() in response.content


@pytest.mark.django_db
def test_non_monday_anchor_is_normalized(
    client: Client, asset: Asset, owner: User, viewer: User
) -> None:
    # A reservation on Wednesday of the fixed week is visible whether the
    # anchor is the Monday or the Wednesday.
    make_reservation(owner, asset, local_cet(2026, 11, 4, 9), local_cet(2026, 11, 4, 10))
    client.force_login(viewer)
    via_monday = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1)))
    via_wednesday = client.get(calendar_url(asset, week="2026-11-04", weeks=1))
    assert via_monday.status_code == 200
    assert via_wednesday.status_code == 200
    assert (
        chip_labels(via_monday.content.decode(), "Wednesday 04 Nov 2026")
        == chip_labels(via_wednesday.content.decode(), "Wednesday 04 Nov 2026")
        == ["09:00 - 10:00"]
    )


@pytest.mark.django_db
def test_exact_asset_isolation(
    client: Client, asset: Asset, other_asset: Asset, owner: User, viewer: User
) -> None:
    make_reservation(owner, asset, local_cet(2026, 11, 3, 14), local_cet(2026, 11, 3, 15))
    make_reservation(owner, other_asset, local_cet(2026, 11, 3, 15), local_cet(2026, 11, 3, 16))
    client.force_login(viewer)
    html = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1))).content.decode()
    labels = chip_labels(html, "Tuesday 03 Nov 2026")
    assert labels == ["14:00 - 15:00"]
    # The other asset's 15:00-16:00 interval must not appear.
    assert "15:00 - 16:00" not in html


# --------------------------------------------------------------------------
# Truthful interval rendering
# --------------------------------------------------------------------------


@pytest.mark.django_db
def test_confirmed_interval_shows_owner_times_and_detail_link(
    client: Client, asset: Asset, owner: User, viewer: User
) -> None:
    reservation = make_reservation(
        owner, asset, local_cet(2026, 11, 3, 14), local_cet(2026, 11, 3, 16)
    )
    client.force_login(viewer)
    html = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1))).content.decode()
    labels = chip_labels(html, "Tuesday 03 Nov 2026")
    assert labels == ["14:00 - 16:00"]
    assert OWNER_NAME in html
    assert f'href="{reverse("management-ui:reservation-detail", args=[reservation.id])}"' in html
    tuesday_cell = re.search(
        r'<h2 class="calendar-day-heading">Tuesday 03 Nov 2026</h2>(.*?)(?=\s*</div>)',
        html,
        re.S,
    ).group(1)
    assert "calendar-interval-released" not in tuesday_cell


@pytest.mark.django_db
def test_overnight_interval_splits_across_days(
    client: Client, asset: Asset, owner: User, viewer: User
) -> None:
    make_reservation(owner, asset, local_cet(2026, 11, 4, 18, 30), local_cet(2026, 11, 5, 2))
    client.force_login(viewer)
    html = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1))).content.decode()
    assert chip_labels(html, "Wednesday 04 Nov 2026") == ["18:30 ->"]
    assert chip_labels(html, "Thursday 05 Nov 2026") == ["-> 02:00"]
    assert chip_labels(html, "Friday 06 Nov 2026") == []


@pytest.mark.django_db
def test_multiday_interval_uses_all_day_label(
    client: Client, asset: Asset, owner: User, viewer: User
) -> None:
    make_reservation(owner, asset, local_cet(2026, 11, 3, 18, 30), local_cet(2026, 11, 6, 9))
    client.force_login(viewer)
    html = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1))).content.decode()
    assert chip_labels(html, "Tuesday 03 Nov 2026") == ["18:30 ->"]
    assert chip_labels(html, "Wednesday 04 Nov 2026") == ["All day"]
    assert chip_labels(html, "Thursday 05 Nov 2026") == ["All day"]
    assert chip_labels(html, "Friday 06 Nov 2026") == ["-> 09:00"]
    assert chip_labels(html, "Saturday 07 Nov 2026") == []


@pytest.mark.django_db
def test_interval_starting_before_window_is_clipped(
    client: Client, asset: Asset, owner: User, viewer: User
) -> None:
    make_reservation(
        owner,
        asset,
        local_cet(2026, 11, 1, 22),
        local_cet(2026, 11, 4, 9),
    )
    client.force_login(viewer)
    html = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1))).content.decode()
    assert chip_labels(html, "Monday 02 Nov 2026") == ["All day"]
    assert chip_labels(html, "Tuesday 03 Nov 2026") == ["All day"]
    assert chip_labels(html, "Wednesday 04 Nov 2026") == ["-> 09:00"]


@pytest.mark.django_db
def test_interval_continuing_past_window_shows_continuation(
    client: Client, asset: Asset, owner: User, viewer: User
) -> None:
    # Starts before the displayed week and keeps occupying the asset well
    # past the last visible Sunday (the true end is Friday 13 Nov 06:00).
    make_reservation(owner, asset, local_cet(2026, 11, 1, 22), local_cet(2026, 11, 13, 6))
    client.force_login(viewer)
    html = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1))).content.decode()
    for day in (
        "Monday 02 Nov 2026",
        "Tuesday 03 Nov 2026",
        "Wednesday 04 Nov 2026",
        "Thursday 05 Nov 2026",
        "Friday 06 Nov 2026",
        "Saturday 07 Nov 2026",
    ):
        assert chip_labels(html, day) == ["All day"], day
    # The last visible day must show continuation, not the later end time.
    assert chip_labels(html, "Sunday 08 Nov 2026") == ["All day ->"]
    # The four-week view contains the true end and labels it there, not as
    # a continuation: the clipping is to the display window only.
    html4 = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 4))).content.decode()
    assert chip_labels(html4, "Friday 13 Nov 2026") == ["-> 06:00"]
    assert chip_labels(html4, "Sunday 08 Nov 2026") == ["All day"]


@pytest.mark.django_db
def test_interval_starting_in_window_and_continuing_past_it(
    client: Client, asset: Asset, owner: User, viewer: User
) -> None:
    make_reservation(owner, asset, local_cet(2026, 11, 6, 10), local_cet(2026, 11, 15, 18))
    client.force_login(viewer)
    html = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1))).content.decode()
    assert chip_labels(html, "Friday 06 Nov 2026") == ["10:00 ->"]
    assert chip_labels(html, "Saturday 07 Nov 2026") == ["All day"]
    assert chip_labels(html, "Sunday 08 Nov 2026") == ["All day ->"]
    html4 = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 4))).content.decode()
    assert chip_labels(html4, "Friday 06 Nov 2026") == ["10:00 ->"]
    assert chip_labels(html4, "Sunday 15 Nov 2026") == ["-> 18:00"]


@pytest.mark.django_db
def test_released_consumed_midnight_end_past_window_continues(
    client: Client, asset: Asset, owner: User, viewer: User
) -> None:
    # Consumed until local Tuesday 10 Nov 00:00, one day past the instant
    # the one-week window half-open ends. The last visible day shows
    # continuation; the true half-open midnight end belongs to the previous
    # day, so the four-week view ends it at Monday 00:00 and never
    # occupies Tuesday.
    make_reservation(
        owner,
        asset,
        local_cet(2026, 11, 5, 10),
        local_cet(2026, 11, 10, 12),
        status=Reservation.STATUS_RELEASED,
        effective_end=local_cet(2026, 11, 10, 0),
    )
    client.force_login(viewer)
    html = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1))).content.decode()
    assert chip_labels(html, "Thursday 05 Nov 2026") == ["10:00 ->"]
    assert chip_labels(html, "Friday 06 Nov 2026") == ["All day"]
    assert chip_labels(html, "Saturday 07 Nov 2026") == ["All day"]
    assert chip_labels(html, "Sunday 08 Nov 2026") == ["All day ->"]
    html4 = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 4))).content.decode()
    assert chip_labels(html4, "Sunday 08 Nov 2026") == ["All day"]
    assert chip_labels(html4, "Monday 09 Nov 2026") == ["-> 00:00"]
    assert chip_labels(html4, "Tuesday 10 Nov 2026") == []


@pytest.mark.django_db
def test_half_open_window_boundaries(
    client: Client, asset: Asset, owner: User, viewer: User
) -> None:
    window_start = utc(2026, 11, 1, 23)  # Mon 02 Nov 00:00 CET
    window_end = utc(2026, 11, 8, 23)  # Mon 09 Nov 00:00 CET
    # Starts exactly at window start: included.
    starts_at_start = make_reservation(
        owner, asset, window_start, window_start + timedelta(hours=2)
    )
    # Ends exactly at window end: occupies only up to Sun 08 Nov (local
    # midnight), never the following day.
    ends_at_end = make_reservation(
        owner,
        asset,
        window_end - timedelta(hours=2),
        window_end,
    )
    client.force_login(viewer)
    html = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1))).content.decode()
    assert chip_labels(html, "Monday 02 Nov 2026") == ["00:00 - 02:00"]
    assert chip_labels(html, "Sunday 08 Nov 2026") == ["22:00 - 00:00"]
    # Monday 09 Nov is outside the one-week window; render the 4-week view
    # to prove the interval does not leak onto the next week's Monday.
    html4 = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 4))).content.decode()
    assert chip_labels(html4, "Monday 09 Nov 2026") == []
    assert chip_labels(html4, "Sunday 08 Nov 2026") == ["22:00 - 00:00"]
    assert starts_at_start.id is not None and ends_at_end.id is not None


@pytest.mark.django_db
def test_released_interval_clips_to_effective_end(
    client: Client, asset: Asset, owner: User, viewer: User
) -> None:
    make_reservation(
        owner,
        asset,
        local_cet(2026, 11, 5, 10),
        local_cet(2026, 11, 5, 18),
        status=Reservation.STATUS_RELEASED,
        effective_end=local_cet(2026, 11, 5, 12),
    )
    client.force_login(viewer)
    html = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1))).content.decode()
    assert chip_labels(html, "Thursday 05 Nov 2026") == ["10:00 - 12:00"]
    cell = re.search(
        r'<h2 class="calendar-day-heading">Thursday 05 Nov 2026</h2>(.*?)(?=\s*</div>)',
        html,
        re.S,
    ).group(1)
    assert "calendar-interval-released" in cell
    assert "Released" in cell
    assert "18:00" not in cell


@pytest.mark.django_db
def test_cancelled_interval_absent_but_kept_in_history(
    client: Client, asset: Asset, owner: User, viewer: User
) -> None:
    make_reservation(
        owner,
        asset,
        local_cet(2026, 11, 6, 9),
        local_cet(2026, 11, 6, 10),
        status=Reservation.STATUS_CANCELLED,
    )
    client.force_login(viewer)
    html = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1))).content.decode()
    assert chip_labels(html, "Friday 06 Nov 2026") == []
    listing = client.get(
        reverse("management-ui:reservation-list"),
        {"asset": asset.id, "status": Reservation.STATUS_CANCELLED},
    )
    assert listing.status_code == 200
    assert OWNER_NAME.encode() in listing.content


# --------------------------------------------------------------------------
# Timezones and DST
# --------------------------------------------------------------------------


@pytest.mark.django_db
def test_viewer_timezone_drives_day_assignment(
    client: Client, asset: Asset, owner: User, viewer: User, viewer_utc: User
) -> None:
    # UTC 2026-11-03 22:00 - 2026-11-04 01:00.
    make_reservation(owner, asset, utc(2026, 11, 3, 22), utc(2026, 11, 4, 1))
    client.force_login(viewer_utc)
    html_utc = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1))).content.decode()
    assert chip_labels(html_utc, "Tuesday 03 Nov 2026") == ["22:00 ->"]
    assert chip_labels(html_utc, "Wednesday 04 Nov 2026") == ["-> 01:00"]
    client.force_login(viewer)
    html_lj = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1))).content.decode()
    assert chip_labels(html_lj, "Tuesday 03 Nov 2026") == ["23:00 ->"]
    assert chip_labels(html_lj, "Wednesday 04 Nov 2026") == ["-> 02:00"]


@pytest.mark.django_db
def test_timezone_banner_shown(client: Client, asset: Asset, viewer: User) -> None:
    client.force_login(viewer)
    response = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1)))
    assert b"Times shown in Europe/Ljubljana." in response.content


@pytest.mark.django_db
def test_fall_back_week_crossing_transition(
    client: Client, asset: Asset, owner: User, viewer: User
) -> None:
    # Crosses the 2026-10-25 01:00 UTC transition: 23:30 CEST Sat -> 04:00 CET Sun.
    make_reservation(
        owner,
        asset,
        local_cest(2026, 10, 24, 23, 30),
        local_cet(2026, 10, 25, 4),
    )
    client.force_login(viewer)
    html = client.get(calendar_url(asset, **week_query(FALL_MONDAY, 1))).content.decode()
    assert chip_labels(html, "Saturday 24 Oct 2026") == ["23:30 ->"]
    assert chip_labels(html, "Sunday 25 Oct 2026") == ["-> 04:00"]
    # All seven days of the 25-hour Sunday week still render.
    for heading in (
        "Monday 19 Oct 2026",
        "Tuesday 20 Oct 2026",
        "Wednesday 21 Oct 2026",
        "Thursday 22 Oct 2026",
        "Friday 23 Oct 2026",
        "Saturday 24 Oct 2026",
        "Sunday 25 Oct 2026",
    ):
        assert f'<h2 class="calendar-day-heading">{heading}</h2>' in html


@pytest.mark.django_db
def test_fall_back_week_repeated_wall_time(
    client: Client, asset: Asset, owner: User, viewer: User
) -> None:
    # Two distinct UTC instants inside the first and second pass of the
    # repeated 02:00-03:00 local window render the same wall-clock label.
    make_reservation(owner, asset, utc(2026, 10, 25, 0, 15), utc(2026, 10, 25, 0, 30))
    make_reservation(owner, asset, utc(2026, 10, 25, 1, 15), utc(2026, 10, 25, 1, 30))
    client.force_login(viewer)
    html = client.get(calendar_url(asset, **week_query(FALL_MONDAY, 1))).content.decode()
    assert chip_labels(html, "Sunday 25 Oct 2026") == ["02:15 - 02:30", "02:15 - 02:30"]


@pytest.mark.django_db
def test_spring_forward_week_crossing_transition(
    client: Client, asset: Asset, owner: User, viewer: User
) -> None:
    # Crosses the 2027-03-28 01:00 UTC transition: 23:00 CET Sat -> 04:00 CEST Sun.
    make_reservation(
        owner,
        asset,
        local_cet(2027, 3, 27, 23),
        local_cest(2027, 3, 28, 4),
    )
    client.force_login(viewer)
    html = client.get(calendar_url(asset, **week_query(SPRING_MONDAY, 1))).content.decode()
    assert chip_labels(html, "Saturday 27 Mar 2027") == ["23:00 ->"]
    assert chip_labels(html, "Sunday 28 Mar 2027") == ["-> 04:00"]


@pytest.mark.django_db
def test_spring_forward_week_skipped_wall_time(
    client: Client, asset: Asset, owner: User, viewer: User
) -> None:
    # Spans the skipped 02:00-03:00 wall time (01:30 CET -> 03:30 CEST).
    make_reservation(owner, asset, utc(2027, 3, 28, 0, 30), utc(2027, 3, 28, 1, 30))
    client.force_login(viewer)
    html = client.get(calendar_url(asset, **week_query(SPRING_MONDAY, 1))).content.decode()
    assert chip_labels(html, "Sunday 28 Mar 2027") == ["01:30 - 03:30"]


@pytest.mark.django_db
def test_window_label_uses_local_date_arithmetic_across_spring_forward(
    client: Client, asset: Asset, viewer: User
) -> None:
    # The 2027-03-28 01:00 UTC transition makes the local week starting
    # Monday 2027-03-22 only 167 hours long. A fixed 24-hour UTC
    # subtraction from the half-open end instant would label the last
    # displayed day Saturday 27 Mar; local date arithmetic gives Sunday.
    client.force_login(viewer)
    html = client.get(calendar_url(asset, **week_query(SPRING_MONDAY, 1))).content.decode()
    assert window_label(html) == "Mon 22 Mar 2027 - Sun 28 Mar 2027"
    # Four weeks spanning the same transition end Sunday 2027-04-04, not
    # Friday 2027-04-03.
    html4 = client.get(calendar_url(asset, week="2027-03-08", weeks=4)).content.decode()
    assert window_label(html4) == "Mon 08 Mar 2027 - Sun 04 Apr 2027"


@pytest.mark.django_db
def test_window_label_fall_back_week_local_dates(
    client: Client, asset: Asset, viewer: User
) -> None:
    # The 23-hour fall-back week and a four-week window crossing it keep
    # the same local Monday-Sunday labels.
    client.force_login(viewer)
    html = client.get(calendar_url(asset, **week_query(FALL_MONDAY, 1))).content.decode()
    assert window_label(html) == "Mon 19 Oct 2026 - Sun 25 Oct 2026"
    html4 = client.get(calendar_url(asset, week="2026-10-05", weeks=4)).content.decode()
    assert window_label(html4) == "Mon 05 Oct 2026 - Sun 01 Nov 2026"


# --------------------------------------------------------------------------
# Navigation, cap, writes, entry points
# --------------------------------------------------------------------------


@pytest.mark.django_db
def test_navigation_links_preserve_asset_and_week(
    client: Client, asset: Asset, viewer: User
) -> None:
    client.force_login(viewer)
    html = unescape(client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1))).content.decode())
    base = f"/manage/reservations/calendar/{asset.id}/"
    assert f"{base}?week=2026-10-26&weeks=1" in html
    assert f"{base}?week=2026-11-09&weeks=1" in html
    assert f"{base}?week=2026-11-02&weeks=4" in html
    html4 = unescape(client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 4))).content.decode())
    assert f"{base}?week=2026-10-05&weeks=4" in html4
    assert f"{base}?week=2026-11-30&weeks=4" in html4
    assert f"{base}?week=2026-11-02&weeks=1" in html4


@pytest.mark.django_db
def test_switching_length_preserves_selected_week(
    client: Client, asset: Asset, owner: User, viewer: User
) -> None:
    make_reservation(owner, asset, local_cet(2026, 11, 3, 14), local_cet(2026, 11, 3, 15))
    client.force_login(viewer)
    html1 = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1))).content.decode()
    assert html1.count("calendar-day-heading") == 7
    html4 = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 4))).content.decode()
    assert html4.count("calendar-day-heading") == 28
    assert chip_labels(html4, "Tuesday 03 Nov 2026") == ["14:00 - 15:00"]
    # The fourth week's Monday heading proves four full weeks are rendered
    # (window Nov 2 - Nov 29), and the fifth Monday is outside it.
    assert "Monday 09 Nov 2026" in html4
    assert "Monday 23 Nov 2026" in html4
    assert "Monday 30 Nov 2026" not in html4


@pytest.mark.django_db
def test_output_cap_falls_back_to_complete_asset_history(
    client: Client, asset: Asset, owner: User, viewer: User
) -> None:
    start = local_cet(2026, 11, 3, 8)
    for offset in range(CALENDAR_MAX_INTERVALS + 1):
        # Each ten-minute row is released one minute early so the released
        # field constraints hold.
        make_reservation(
            owner,
            asset,
            start + timedelta(minutes=10 * offset),
            start + timedelta(minutes=10 * (offset + 1)),
            status=Reservation.STATUS_RELEASED,
            effective_end=start + timedelta(minutes=10 * (offset + 1) - 1),
        )
    # A booking that started before the displayed window (Sunday 23:30)
    # and still occupies it (Monday 00:30): the All reservations from/to
    # filters select by reservation START, so no start-based window
    # filter can find it. It renders exactly one chip (Monday).
    pre_window = make_reservation(
        owner, asset, local_cet(2026, 11, 1, 23, 30), local_cet(2026, 11, 2, 0, 30)
    )
    client.force_login(viewer)
    html = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1))).content.decode()
    assert html.count('<a class="calendar-interval') == CALENDAR_MAX_INTERVALS
    assert f"at most {CALENDAR_MAX_INTERVALS} intervals" in html
    # The warning no longer promises a filtered complete window.
    assert "complete window" not in html
    assert "complete asset history" in html
    link = re.search(r'href="(/manage/reservations/\?asset=[^"]+)"', html)
    assert link, "capped window must link to the asset's All reservations history"
    assert f"asset={asset.id}" in link.group(1)
    # No start-based from/to window filters on the fallback link.
    assert "from=" not in link.group(1) and "to=" not in link.group(1)
    first_page = client.get(link.group(1))
    assert first_page.status_code == 200
    # 102 rows at 50 per page: the pre-window booking (oldest start) sits
    # on the final page, reachable through the fallback link.
    assert "Page 1 of 3" in first_page.content.decode()
    last_page = client.get(f"{link.group(1)}&page=3")
    assert last_page.status_code == 200
    assert str(pre_window.id) in last_page.content.decode()


@pytest.mark.django_db
def test_calendar_performs_zero_writes(
    client: Client, asset: Asset, owner: User, viewer: User
) -> None:
    reservation = make_reservation(
        owner, asset, local_cet(2026, 11, 3, 14), local_cet(2026, 11, 3, 16)
    )
    client.force_login(viewer)
    before = list(
        Reservation.objects.values_list(
            "id", "status", "start_at", "end_at", "effective_end_at", "updated_at"
        )
    )
    audit_before = AuditEvent.objects.count()
    for query in (week_query(WEEK_MONDAY, 1), week_query(WEEK_MONDAY, 4)):
        response = client.get(calendar_url(asset, **query))
        assert response.status_code == 200
    after = list(
        Reservation.objects.values_list(
            "id", "status", "start_at", "end_at", "effective_end_at", "updated_at"
        )
    )
    assert before == after
    assert AuditEvent.objects.count() == audit_before
    assert Reservation.objects.get(pk=reservation.id).updated_at == before[0][5]


@pytest.mark.django_db
def test_invalid_profile_timezone_redirects_to_profile(
    client: Client, asset: Asset, viewer: User
) -> None:
    User.objects.filter(pk=viewer.pk).update(timezone="Not/AZone")
    viewer.refresh_from_db()
    client.force_login(viewer)
    response = client.get(calendar_url(asset, **week_query(WEEK_MONDAY, 1)))
    assert response.status_code == 302
    assert response["Location"] == reverse("web:profile")


@pytest.mark.django_db
def test_asset_detail_shows_calendar_link_only_for_granted(
    client: Client, asset: Asset, viewer: User, staff_only: User
) -> None:
    detail = reverse("web:asset-detail", args=[asset.id])
    client.force_login(staff_only)
    html = client.get(detail).content.decode()
    assert f"/manage/reservations/calendar/{asset.id}/" not in html
    client.force_login(viewer)
    html = client.get(detail).content.decode()
    assert f'/manage/reservations/calendar/{asset.id}/">' in html


@pytest.mark.django_db
def test_reservation_list_shows_calendar_link_only_with_asset_filter(
    client: Client, asset: Asset, viewer: User
) -> None:
    client.force_login(viewer)
    html = client.get(reverse("management-ui:reservation-list")).content.decode()
    assert f"/manage/reservations/calendar/{asset.id}/" not in html
    html = client.get(
        reverse("management-ui:reservation-list"), {"asset": asset.id}
    ).content.decode()
    assert f"{f'/manage/reservations/calendar/{asset.id}/'}?weeks=1" in html
