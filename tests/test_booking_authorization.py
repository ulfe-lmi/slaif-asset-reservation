"""Order 049-a: one authoritative booking capability + exact-asset eligibility.

Real PostgreSQL (pytest-django against the owned PostgreSQL 17 test
database) positive/negative coverage for the selected A16 booking
slice:

- the global ``reservations.book_assets`` capability via direct grants,
  group grants and additive multi-group unions;
- exact-asset group eligibility: unrestricted, restricted, restricted
  with an empty allow-list, last allowed group deleted, all five asset
  kinds, and no parent-to-child inheritance in either direction;
- staff / unrelated Administration permissions / superuser boundaries;
- browser GET/POST denial on direct requests plus eligibility display;
- bearer authorization BEFORE cached idempotent replay (and restored
  grant replay returning the original record), with the missing-asset
  404 callback preserved;
- retained owner list/inspect/cancel/release after losing the booking
  capability or membership;
- legacy import: FUTURE confirmed appointments reuse the same current
  predicate (plan and stale-plan apply), completed-past appointments
  keep the documented historical exception;
- unchanged conflict/policy/audit authority for eligible principals.

No global test grants: every positive fixture grants the capability
explicitly through real Permission records.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
import yaml
from django.contrib.auth.models import Group, Permission
from django.urls import reverse
from django.utils import timezone

from slaif_reservation.accounts.models import User
from slaif_reservation.accounts.services import issue_api_token
from slaif_reservation.assets.authorization import (
    STATE_ELIGIBLE,
    STATE_NO_ALLOWED_GROUP,
    STATE_NO_BOOKING_PERMISSION,
    batch_asset_booking_states,
    user_can_book_asset,
)
from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.legacy_import.importer import apply_import
from slaif_reservation.legacy_import.mapping import load_mapping
from slaif_reservation.legacy_import.parser import parse_synthetic_export
from slaif_reservation.legacy_import.planner import plan_import
from slaif_reservation.reservations.exceptions import (
    BOOKING_NOT_AUTHORIZED,
    DURATION_TOO_LONG,
    PRINCIPAL_INACTIVE,
    RESERVATION_CONFLICT,
    ReservationDomainError,
)
from slaif_reservation.reservations.models import Reservation, ReservationPolicy
from slaif_reservation.reservations.services import (
    create_reservation,
)

pytestmark = pytest.mark.django_db

LEGACY_SOURCE = "049a-synthetic"


# --- capability / group fixtures -------------------------------------------


def book_permission() -> Permission:
    return Permission.objects.get(codename="book_assets", content_type__app_label="reservations")


def grant_book(target: User) -> None:
    """Explicit baseline capability through a real Permission record."""
    target.user_permissions.add(book_permission())


@pytest.fixture
def group_book() -> Group:
    group = Group.objects.create(name="049a-book")
    group.permissions.add(book_permission())
    return group


@pytest.fixture
def group_a() -> Group:
    return Group.objects.create(name="049a-group-a")


@pytest.fixture
def group_b() -> Group:
    return Group.objects.create(name="049a-group-b")


@pytest.fixture
def no_grant() -> User:
    return User.objects.create_user(
        email="049a-none@example.com", password="not-a-secret", display_name="No Grant"
    )


@pytest.fixture
def direct_booker() -> User:
    user = User.objects.create_user(
        email="049a-direct@example.com", password="not-a-secret", display_name="Direct Booker"
    )
    grant_book(user)
    return user


@pytest.fixture
def group_booker(group_book: Group) -> User:
    user = User.objects.create_user(
        email="049a-group@example.com", password="not-a-secret", display_name="Group Booker"
    )
    user.groups.add(group_book)
    return user


@pytest.fixture
def union_booker(group_book: Group, group_a: Group) -> User:
    """Book capability from one group, asset membership from another."""
    user = User.objects.create_user(
        email="049a-union@example.com", password="not-a-secret", display_name="Union Booker"
    )
    user.groups.add(group_book, group_a)
    return user


@pytest.fixture
def staff_no_grant() -> User:
    return User.objects.create_user(
        email="049a-staff@example.com",
        password="not-a-secret",
        display_name="Staff No Grant",
        is_staff=True,
    )


@pytest.fixture
def unrelated_admin() -> User:
    """Staff holding an unrelated Administration model permission."""
    user = User.objects.create_user(
        email="049a-adminperm@example.com",
        password="not-a-secret",
        display_name="Unrelated Admin Perm",
        is_staff=True,
    )
    user.user_permissions.add(
        Permission.objects.get(codename="view_asset", content_type__app_label="assets")
    )
    return user


@pytest.fixture
def superuser() -> User:
    return User.objects.create_superuser(email="049a-super@example.com", password="not-a-secret")


@pytest.fixture
def superuser_member(group_a: Group) -> User:
    user = User.objects.create_superuser(
        email="049a-supermember@example.com", password="not-a-secret"
    )
    user.groups.add(group_a)
    return user


@pytest.fixture
def service_account() -> User:
    user = User.objects.create_user(
        email="049a-service@example.com",
        password="not-a-secret",
        is_service_account=True,
    )
    grant_book(user)
    return user


@pytest.fixture
def inactive_booker() -> User:
    user = User.objects.create_user(
        email="049a-inactive@example.com", password="not-a-secret", is_active=False
    )
    grant_book(user)
    return user


# --- asset fixtures ----------------------------------------------------------


def make_asset(slug: str, *, kind: str = Asset.KIND_GPU, **overrides: object) -> Asset:
    values = {
        "slug": slug,
        "name": slug.replace("-", " ").title(),
        "kind": kind,
        "active": True,
        "reservable": True,
    }
    values.update(overrides)
    return Asset.objects.create(**values)


@pytest.fixture(autouse=True)
def global_policy() -> ReservationPolicy:
    return ReservationPolicy.objects.create(
        name="049a-global",
        asset=None,
        min_duration_minutes=15,
        max_duration_minutes=240,
        booking_horizon_days=30,
        min_lead_minutes=0,
        cancellation_cutoff_minutes=0,
        max_upcoming_per_principal=20,
        max_concurrent_per_principal=10,
        purpose_required=False,
    )


@pytest.fixture
def unrestricted(global_policy) -> Asset:
    return make_asset("049a-unrestricted")


@pytest.fixture
def restricted_a(global_policy, group_a: Group) -> Asset:
    asset = make_asset("049a-restricted-a", booking_restricted=True)
    asset.allowed_booking_groups.add(group_a)
    return asset


@pytest.fixture
def restricted_empty(global_policy) -> Asset:
    return make_asset("049a-restricted-empty", booking_restricted=True)


def future_window(hours: int = 2) -> tuple:
    start = (timezone.now() + timedelta(days=1, hours=hours)).replace(second=0, microsecond=0)
    return start, start + timedelta(hours=1)


# --- shared predicate --------------------------------------------------------


@pytest.mark.parametrize(
    ("principal", "asset", "expected"),
    [
        ("no_grant", "unrestricted", False),
        ("direct_booker", "unrestricted", True),
        ("group_booker", "unrestricted", True),
        ("union_booker", "unrestricted", True),
        ("staff_no_grant", "unrestricted", False),
        ("unrelated_admin", "unrestricted", False),
        ("superuser", "unrestricted", True),
        ("service_account", "unrestricted", False),
        ("direct_booker", "restricted_a", False),
        ("union_booker", "restricted_a", True),
        ("superuser", "restricted_a", False),
        ("superuser_member", "restricted_a", True),
        ("direct_booker", "restricted_empty", False),
        ("group_booker", "restricted_empty", False),
    ],
)
def test_predicate_semantics(principal: str, asset: str, expected: bool, request) -> None:
    user = request.getfixturevalue(principal)
    asset_obj = request.getfixturevalue(asset)
    assert user_can_book_asset(user, asset_obj) is expected


def test_asset_none_evaluates_global_capability_only(no_grant, direct_booker) -> None:
    assert user_can_book_asset(no_grant, None) is False
    assert user_can_book_asset(direct_booker, None) is True


def test_batch_states_use_prefetched_membership(
    no_grant, direct_booker, union_booker, unrestricted, restricted_a, restricted_empty
) -> None:
    assets = list(
        Asset.objects.filter(id__in=[unrestricted.id, restricted_a.id, restricted_empty.id])
    )
    assert batch_asset_booking_states(no_grant, assets) == {
        asset.id: STATE_NO_BOOKING_PERMISSION for asset in assets
    }
    assert batch_asset_booking_states(direct_booker, assets) == {
        unrestricted.id: STATE_ELIGIBLE,
        restricted_a.id: STATE_NO_ALLOWED_GROUP,
        restricted_empty.id: STATE_NO_ALLOWED_GROUP,
    }
    assert batch_asset_booking_states(union_booker, assets) == {
        unrestricted.id: STATE_ELIGIBLE,
        restricted_a.id: STATE_ELIGIBLE,
        restricted_empty.id: STATE_NO_ALLOWED_GROUP,
    }


# --- authoritative service ---------------------------------------------------


def test_service_denies_without_capability(no_grant, unrestricted) -> None:
    start, end = future_window()
    with pytest.raises(
        ReservationDomainError, check=lambda exc: exc.code == BOOKING_NOT_AUTHORIZED
    ):
        create_reservation(
            asset=unrestricted,
            requested_by_user=no_grant,
            start_at=start,
            end_at=end,
            purpose="",
        )
    assert Reservation.objects.count() == 0
    assert AuditEvent.objects.count() == 0


@pytest.mark.parametrize("booker_fixture", ["direct_booker", "group_booker", "union_booker"])
def test_service_allows_current_grants(booker_fixture: str, request, unrestricted) -> None:
    booker = request.getfixturevalue(booker_fixture)
    start, end = future_window()
    result = create_reservation(
        asset=unrestricted,
        requested_by_user=booker,
        start_at=start,
        end_at=end,
        purpose="allowed",
    )
    assert result.reservation.status == Reservation.STATUS_CONFIRMED
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_RESERVATION_CREATED).count() == 1


def test_service_denies_staff_and_unrelated_admin_permissions(
    staff_no_grant, unrelated_admin, unrestricted
) -> None:
    start, end = future_window()
    for principal in (staff_no_grant, unrelated_admin):
        with pytest.raises(
            ReservationDomainError, check=lambda exc: exc.code == BOOKING_NOT_AUTHORIZED
        ):
            create_reservation(
                asset=unrestricted,
                requested_by_user=principal,
                start_at=start,
                end_at=end,
                purpose="",
            )


def test_service_denies_inactive_and_service_accounts(
    inactive_booker, service_account, unrestricted
) -> None:
    start, end = future_window()
    with pytest.raises(ReservationDomainError):
        create_reservation(
            asset=unrestricted,
            requested_by_user=inactive_booker,
            start_at=start,
            end_at=end,
            purpose="",
        )
    with pytest.raises(
        ReservationDomainError, check=lambda exc: exc.code == BOOKING_NOT_AUTHORIZED
    ):
        create_reservation(
            asset=unrestricted,
            requested_by_user=service_account,
            start_at=start,
            end_at=end,
            purpose="",
        )
    # Superuser status does not bypass the active/service-account rules
    # either (not only ordinary service accounts): an inactive superuser
    # is inactive, and a service-account superuser is a service account.
    inactive_super = User.objects.create_superuser(
        email="049a-inactive-super@example.com", password="not-a-secret"
    )
    inactive_super.is_active = False
    inactive_super.save(update_fields=["is_active"])
    with pytest.raises(ReservationDomainError, check=lambda exc: exc.code == PRINCIPAL_INACTIVE):
        create_reservation(
            asset=unrestricted,
            requested_by_user=inactive_super,
            start_at=start,
            end_at=end,
            purpose="",
        )
    service_super = User.objects.create_superuser(
        email="049a-service-super@example.com", password="not-a-secret"
    )
    service_super.is_service_account = True
    service_super.save(update_fields=["is_service_account"])
    with pytest.raises(
        ReservationDomainError, check=lambda exc: exc.code == BOOKING_NOT_AUTHORIZED
    ):
        create_reservation(
            asset=unrestricted,
            requested_by_user=service_super,
            start_at=start,
            end_at=end,
            purpose="",
        )


def test_service_denies_restricted_without_membership(
    direct_booker, group_booker, restricted_a
) -> None:
    start, end = future_window()
    with pytest.raises(
        ReservationDomainError, check=lambda exc: exc.code == BOOKING_NOT_AUTHORIZED
    ):
        create_reservation(
            asset=restricted_a,
            requested_by_user=direct_booker,
            start_at=start,
            end_at=end,
            purpose="",
        )
    # group_booker belongs to the book-capability group only, not group_a.
    with pytest.raises(
        ReservationDomainError, check=lambda exc: exc.code == BOOKING_NOT_AUTHORIZED
    ):
        create_reservation(
            asset=restricted_a,
            requested_by_user=group_booker,
            start_at=start,
            end_at=end,
            purpose="",
        )


def test_service_allows_restricted_with_membership(union_booker, restricted_a) -> None:
    start, end = future_window()
    result = create_reservation(
        asset=restricted_a,
        requested_by_user=union_booker,
        start_at=start,
        end_at=end,
        purpose="member of allowed group",
    )
    assert result.reservation.asset_id == restricted_a.id


def test_restricted_empty_fail_closed_including_after_last_group_deletion(
    direct_booker, group_booker, restricted_empty, group_a
) -> None:
    restricted_empty.allowed_booking_groups.add(group_a)
    direct_booker.groups.add(group_a)
    start, end = future_window()
    result = create_reservation(
        asset=restricted_empty,
        requested_by_user=direct_booker,
        start_at=start,
        end_at=end,
        purpose="temporarily allowed",
    )
    assert result.reservation.asset_id == restricted_empty.id

    restricted_empty.allowed_booking_groups.clear()
    start2, end2 = future_window(hours=3)
    with pytest.raises(
        ReservationDomainError, check=lambda exc: exc.code == BOOKING_NOT_AUTHORIZED
    ):
        create_reservation(
            asset=restricted_empty,
            requested_by_user=direct_booker,
            start_at=start2,
            end_at=end2,
            purpose="",
        )
    with pytest.raises(
        ReservationDomainError, check=lambda exc: exc.code == BOOKING_NOT_AUTHORIZED
    ):
        create_reservation(
            asset=restricted_empty,
            requested_by_user=group_booker,
            start_at=start2,
            end_at=end2,
            purpose="",
        )


def test_last_allowed_group_deletion_denies_new_keeps_existing(
    direct_booker, restricted_empty, group_a
) -> None:
    """A real Group.delete() of the only allowed group (not just an M2M
    clear) leaves the asset restricted with an empty list: new creation is
    denied, the accepted booking is untouched."""
    restricted_empty.allowed_booking_groups.add(group_a)
    direct_booker.groups.add(group_a)
    start, end = future_window()
    existing = create_reservation(
        asset=restricted_empty,
        requested_by_user=direct_booker,
        start_at=start,
        end_at=end,
        purpose="accepted before deletion",
    ).reservation

    group_a.delete()  # real deletion of the last allowed group row

    restricted_empty.refresh_from_db()
    assert restricted_empty.booking_restricted is True
    assert restricted_empty.allowed_booking_groups.count() == 0
    start2, end2 = future_window(hours=3)
    with pytest.raises(
        ReservationDomainError, check=lambda exc: exc.code == BOOKING_NOT_AUTHORIZED
    ):
        create_reservation(
            asset=restricted_empty,
            requested_by_user=direct_booker,
            start_at=start2,
            end_at=end2,
            purpose="",
        )
    existing.refresh_from_db()
    assert existing.status == Reservation.STATUS_CONFIRMED
    assert existing.asset_id == restricted_empty.id


@pytest.mark.parametrize(
    ("parent_restricted", "child_restricted"),
    [
        (True, False),
        (False, True),
    ],
)
def test_no_parent_inheritance_either_direction(
    direct_booker, union_booker, group_a, parent_restricted: bool, child_restricted: bool
) -> None:
    parent = make_asset(
        f"049a-parent-{uuid.uuid4().hex[:8]}",
        kind=Asset.KIND_MACHINE,
        reservable=True,
        booking_restricted=parent_restricted,
    )
    if parent_restricted:
        parent.allowed_booking_groups.add(group_a)
    child = make_asset(
        f"049a-child-{uuid.uuid4().hex[:8]}",
        parent=parent,
        booking_restricted=child_restricted,
    )
    if child_restricted:
        child.allowed_booking_groups.add(group_a)
    start, end = future_window()

    # The parent's setting never applies to the child and vice versa.
    # direct_booker holds the global capability but is NOT a member of
    # group_a, so each asset is decided purely by its own flag/allow-list:
    # restricted parent denied / unrestricted child allowed, and
    # unrestricted parent allowed / restricted child denied.
    for asset in (parent, child):
        if asset.booking_restricted:
            with pytest.raises(
                ReservationDomainError, check=lambda exc: exc.code == BOOKING_NOT_AUTHORIZED
            ):
                create_reservation(
                    asset=asset,
                    requested_by_user=direct_booker,
                    start_at=start,
                    end_at=end,
                    purpose="",
                )
        else:
            result = create_reservation(
                asset=asset,
                requested_by_user=direct_booker,
                start_at=start,
                end_at=end,
                purpose="exact asset check",
            )
            assert result.reservation.asset_id == asset.id
    # Eligible-member positive control on the restricted asset, in a
    # non-conflicting window: membership decides it regardless of the
    # counterpart's different setting.
    restricted_asset = parent if parent_restricted else child
    start2, end2 = future_window(hours=3)
    result = create_reservation(
        asset=restricted_asset,
        requested_by_user=union_booker,
        start_at=start2,
        end_at=end2,
        purpose="member of allowed group",
    )
    assert result.reservation.asset_id == restricted_asset.id


@pytest.mark.parametrize(
    "kind",
    [Asset.KIND_MACHINE, Asset.KIND_GPU, Asset.KIND_CPU_POOL, Asset.KIND_SERVICE, Asset.KIND_OTHER],
)
def test_all_five_asset_kinds_follow_identical_eligibility(
    direct_booker, union_booker, group_a, kind: str
) -> None:
    asset = make_asset(f"049a-kind-{kind}-{uuid.uuid4().hex[:6]}", kind=kind)
    start, end = future_window()
    result = create_reservation(
        asset=asset,
        requested_by_user=direct_booker,
        start_at=start,
        end_at=end,
        purpose="",
    )
    assert result.reservation.asset_id == asset.id

    asset.booking_restricted = True
    asset.save(update_fields=["booking_restricted"])
    asset.allowed_booking_groups.add(group_a)
    start2, end2 = future_window(hours=3)
    with pytest.raises(
        ReservationDomainError, check=lambda exc: exc.code == BOOKING_NOT_AUTHORIZED
    ):
        create_reservation(
            asset=asset,
            requested_by_user=direct_booker,
            start_at=start2,
            end_at=end2,
            purpose="",
        )
    result = create_reservation(
        asset=asset,
        requested_by_user=union_booker,
        start_at=start2,
        end_at=end2,
        purpose="kind parity",
    )
    assert result.reservation.asset_id == asset.id


def test_conflict_and_policy_rules_remain_authoritative(
    direct_booker, group_booker, unrestricted
) -> None:
    start, end = future_window()
    create_reservation(
        asset=unrestricted,
        requested_by_user=direct_booker,
        start_at=start,
        end_at=end,
        purpose="first",
    )
    # An eligible second principal still hits the unchanged exclusivity
    # authority (not the new gate).
    with pytest.raises(ReservationDomainError, check=lambda exc: exc.code == RESERVATION_CONFLICT):
        create_reservation(
            asset=unrestricted,
            requested_by_user=group_booker,
            start_at=start + timedelta(minutes=30),
            end_at=end,
            purpose="overlap",
        )
    # An eligible principal still hits the unchanged policy math.
    start3, _ = future_window(hours=4)
    with pytest.raises(ReservationDomainError, check=lambda exc: exc.code == DURATION_TOO_LONG):
        create_reservation(
            asset=unrestricted,
            requested_by_user=group_booker,
            start_at=start3,
            end_at=start3 + timedelta(hours=6),
            purpose="too long",
        )
    # Authorization precedes policy: once the capability is gone the
    # principal is denied before any policy conclusion is reported.
    group_booker.user_permissions.clear()
    group_booker.groups.clear()
    with pytest.raises(
        ReservationDomainError, check=lambda exc: exc.code == BOOKING_NOT_AUTHORIZED
    ):
        create_reservation(
            asset=unrestricted,
            requested_by_user=group_booker,
            start_at=start3,
            end_at=start3 + timedelta(hours=6),
            purpose="too long and unauthorized",
        )


# --- browser surface ---------------------------------------------------------


def _local(value, user: User) -> str:
    # The reservation form interprets input in the member's profile
    # timezone; render the wall-clock string in that zone.
    return value.astimezone(ZoneInfo(user.timezone)).strftime("%Y-%m-%dT%H:%M")


def test_browser_denies_direct_get_and_post_for_unauthorized(
    no_grant, unrestricted, client
) -> None:
    client.force_login(no_grant)
    get_response = client.get(f"/assets/{unrestricted.id}/reserve/")
    assert get_response.status_code == 302
    assert get_response.url == reverse("web:asset-detail", args=[unrestricted.id])

    start, end = future_window()
    post_response = client.post(
        f"/assets/{unrestricted.id}/reserve/",
        {
            "start": _local(start, no_grant),
            "end": _local(end, no_grant),
            "duration": "custom",
            "purpose": "forged",
        },
    )
    assert post_response.status_code == 200
    content = post_response.content
    assert b"cannot book this asset" in content or b"booking permission" in content
    assert Reservation.objects.count() == 0
    assert AuditEvent.objects.count() == 0


def test_browser_denial_reason_is_truthful_for_nonreservable_asset(
    direct_booker, no_grant, client
) -> None:
    """A direct reserve URL must state the ACTUAL reason: an otherwise
    eligible member is told the asset is not reservable, never that they
    lack a group or the capability."""
    asset = make_asset("049a-nonres", reservable=False)
    start, end = future_window()

    client.force_login(direct_booker)
    get_response = client.get(f"/assets/{asset.id}/reserve/")
    assert get_response.status_code == 302
    assert get_response.url == reverse("web:asset-detail", args=[asset.id])
    detail = client.get(reverse("web:asset-detail", args=[asset.id])).content.decode()
    assert "This asset is not reservable." in detail
    assert "approved groups" not in detail

    post_response = client.post(
        f"/assets/{asset.id}/reserve/",
        {
            "start": _local(start, direct_booker),
            "end": _local(end, direct_booker),
            "duration": "custom",
            "purpose": "forged",
        },
    )
    assert post_response.status_code == 200
    content = post_response.content.decode()
    assert "This asset is not reservable." in content
    assert "approved groups" not in content
    assert Reservation.objects.count() == 0
    assert AuditEvent.objects.count() == 0

    # Missing the capability: the truthful user-state reason is stated.
    client.force_login(no_grant)
    post_response = client.post(
        f"/assets/{asset.id}/reserve/",
        {
            "start": _local(start, no_grant),
            "end": _local(end, no_grant),
            "duration": "custom",
            "purpose": "forged",
        },
    )
    assert post_response.status_code == 200
    content = post_response.content.decode()
    assert "booking permission" in content
    assert "approved groups" not in content
    assert Reservation.objects.count() == 0
    assert AuditEvent.objects.count() == 0


def test_browser_list_and_detail_show_eligibility_without_metadata(
    direct_booker, unrestricted, restricted_a, restricted_empty, group_a, client
) -> None:
    client.force_login(direct_booker)
    listing = client.get("/assets/").content.decode()
    for asset in (unrestricted, restricted_a, restricted_empty):
        assert asset.name in listing  # all remain browsable
    # The "You can book" column is per-row: yes for the unrestricted
    # asset, no for the restricted ones (while "Reservable" stays yes for
    # all three asset flags).
    assert listing.count("You can book") == 1  # header only
    rows = re.findall(r"<tr>.*?</tr>", listing, re.S)

    def row_for(asset_id: str) -> str:
        matches = [row for row in rows if f"/assets/{asset_id}/" in row]
        assert len(matches) == 1
        return matches[0]

    unrestricted_row = row_for(str(unrestricted.id))
    assert unrestricted_row.count("<td>yes</td>") == 2  # reservable + bookable
    assert "<td>no</td>" not in unrestricted_row
    for asset in (restricted_a, restricted_empty):
        restricted_row = row_for(str(asset.id))
        assert restricted_row.count("<td>yes</td>") == 1  # reservable only
        assert restricted_row.count("<td>no</td>") == 1  # not personally bookable
    # Group names are operator metadata and never leak to members.
    assert group_a.name not in listing

    detail = client.get(f"/assets/{restricted_a.id}/").content.decode()
    assert f'href="/assets/{restricted_a.id}/reserve/"' not in detail
    assert "specific approved groups" in detail
    assert group_a.name not in detail

    detail_ok = client.get(f"/assets/{unrestricted.id}/").content.decode()
    assert f'href="/assets/{unrestricted.id}/reserve/"' in detail_ok


def test_browser_reservable_filter_is_an_asset_flag_filter(
    direct_booker, unrestricted, restricted_a, restricted_empty, client
) -> None:
    client.force_login(direct_booker)
    html = client.get("/assets/?reservable=true").content.decode()
    # Restricted-but-reservable assets stay visible: the filter does not
    # silently hide assets the member is not personally eligible for.
    assert unrestricted.name in html
    assert restricted_a.name in html
    assert restricted_empty.name in html


def test_browser_eligible_booking_works_end_to_end(union_booker, restricted_a, client) -> None:
    client.force_login(union_booker)
    start, end = future_window()
    response = client.post(
        f"/assets/{restricted_a.id}/reserve/",
        {
            "start": _local(start, union_booker),
            "end": _local(end, union_booker),
            "duration": "custom",
            "purpose": "via web",
        },
    )
    assert response.status_code == 302
    reservation = Reservation.objects.get()
    assert reservation.requested_by_user_id == union_booker.id
    assert response.url == reverse("web:reservation-detail", args=[reservation.id])


def test_owner_retains_lifecycle_after_losing_capability_and_membership(
    direct_booker, group_booker, unrestricted, restricted_a, client
) -> None:
    start, end = future_window()
    future_reservation = create_reservation(
        asset=unrestricted,
        requested_by_user=direct_booker,
        start_at=start,
        end_at=end,
        purpose="mine",
    ).reservation
    # An accepted active reservation (created before the loss).
    now = timezone.now()
    active_reservation = Reservation.objects.create(
        asset=unrestricted,
        requested_by_user=group_booker,
        source=Reservation.SOURCE_WEB,
        status=Reservation.STATUS_CONFIRMED,
        start_at=now - timedelta(hours=1),
        end_at=now + timedelta(hours=1),
        effective_end_at=now + timedelta(hours=1),
        purpose="active mine",
    )
    # Loss: global capability AND membership both removed.
    direct_booker.user_permissions.clear()
    group_booker.user_permissions.clear()
    group_booker.groups.clear()
    # The asset also goes away from new bookings entirely.
    unrestricted.active = False
    unrestricted.reservable = False
    unrestricted.save()

    # New bookings are impossible...
    start2, end2 = future_window(hours=5)
    with pytest.raises(ReservationDomainError):
        create_reservation(
            asset=unrestricted,
            requested_by_user=direct_booker,
            start_at=start2,
            end_at=end2,
            purpose="too late",
        )
    # ...but the owners keep list/inspect/cancel/release of accepted
    # reservations (existing lifecycle/cutoff rules still apply).
    client.force_login(direct_booker)
    assert client.get("/reservations/").status_code == 200
    assert (
        client.get(reverse("web:reservation-detail", args=[future_reservation.id])).status_code
        == 200
    )
    cancel_response = client.post(
        reverse("web:reservation-cancel", args=[future_reservation.id]),
        {"reason": "planning changed"},
    )
    assert cancel_response.status_code == 302
    future_reservation.refresh_from_db()
    assert future_reservation.status == Reservation.STATUS_CANCELLED

    client.force_login(group_booker)
    release_response = client.post(
        reverse("web:reservation-release", args=[active_reservation.id]),
    )
    assert release_response.status_code == 302
    active_reservation.refresh_from_db()
    assert active_reservation.status == Reservation.STATUS_RELEASED

    # Bearer leg: the SAME retention holds on the API routes — list,
    # detail, cancel AND release (including bearer release, which the
    # browser-only leg never exercised) — after exact-asset eligibility
    # loss, under the current lifecycle/cutoff rules.
    start3, end3 = future_window(hours=7)
    upcoming_bearer = Reservation.objects.create(
        asset=unrestricted,
        requested_by_user=direct_booker,
        source=Reservation.SOURCE_API,
        status=Reservation.STATUS_CONFIRMED,
        start_at=start3,
        end_at=end3,
        effective_end_at=end3,
        purpose="upcoming bearer",
    )
    # A distinct asset: the browser leg already occupies an active window
    # on unrestricted (its consumed prefix would exclude this one).
    active_bearer = Reservation.objects.create(
        asset=restricted_a,
        requested_by_user=group_booker,
        source=Reservation.SOURCE_API,
        status=Reservation.STATUS_CONFIRMED,
        start_at=now - timedelta(hours=1),
        end_at=now + timedelta(hours=1),
        effective_end_at=now + timedelta(hours=1),
        purpose="active bearer",
    )

    bearer_direct = _token(
        direct_booker, ["reservations:read", "reservations:cancel", "reservations:release"]
    )
    listing = client.get(
        "/api/v1/reservations/",
        HTTP_AUTHORIZATION=f"Bearer {bearer_direct.bearer_token}",
    )
    assert listing.status_code == 200
    detail = client.get(
        f"/api/v1/reservations/{upcoming_bearer.id}/",
        HTTP_AUTHORIZATION=f"Bearer {bearer_direct.bearer_token}",
    )
    assert detail.status_code == 200
    cancel = client.post(
        f"/api/v1/reservations/{upcoming_bearer.id}/cancel/",
        {"reason": "bearer cancellation after loss"},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {bearer_direct.bearer_token}",
        HTTP_IDEMPOTENCY_KEY="049a-bearer-cancel-1",
    )
    assert cancel.status_code == 200
    upcoming_bearer.refresh_from_db()
    assert upcoming_bearer.status == Reservation.STATUS_CANCELLED

    bearer_group = _token(
        group_booker, ["reservations:read", "reservations:cancel", "reservations:release"]
    )
    active_detail = client.get(
        f"/api/v1/reservations/{active_bearer.id}/",
        HTTP_AUTHORIZATION=f"Bearer {bearer_group.bearer_token}",
    )
    assert active_detail.status_code == 200
    release = client.post(
        f"/api/v1/reservations/{active_bearer.id}/release/",
        {},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {bearer_group.bearer_token}",
        HTTP_IDEMPOTENCY_KEY="049a-bearer-release-1",
    )
    assert release.status_code == 200
    active_bearer.refresh_from_db()
    assert active_bearer.status == Reservation.STATUS_RELEASED
    assert active_bearer.released_at is not None
    assert active_bearer.effective_end_at == active_bearer.released_at


# --- bearer API --------------------------------------------------------------


def _token(owner: User, scopes: list[str]):
    return issue_api_token(owner=owner, name="049a token", scopes=scopes, lifetime_days=1)


def _create_payload(asset: Asset, start, end) -> dict:
    return {
        "asset_id": str(asset.id),
        "start_at": start.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "end_at": end.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "purpose": "api",
    }


def test_api_denies_before_any_record_when_unauthorized(no_grant, unrestricted, client) -> None:
    # 051-a: a create-scope token can only be minted while the owner
    # currently holds the booking capability, so represent a LEGITIMATE
    # historical token: grant, issue, then revoke before any request. The
    # final no-grant 403 and the no-write assertions are preserved.
    no_grant.user_permissions.add(book_permission())
    token = _token(no_grant, ["reservations:create"])
    no_grant.user_permissions.clear()
    before_audit_count = AuditEvent.objects.count()
    start, end = future_window()
    response = client.post(
        "/api/v1/reservations/",
        _create_payload(unrestricted, start, end),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token.bearer_token}",
        HTTP_IDEMPOTENCY_KEY="049a-deny-1",
    )
    assert response.status_code == 403
    body = response.json()
    assert body["code"] == BOOKING_NOT_AUTHORIZED
    assert body["detail"] == "You do not currently have permission to create this reservation."
    # No group/account/UID/SQL metadata may leak into the safe body; the
    # only non-static field is the random correlation UUID.
    assert no_grant.email not in str(body)
    assert "049a-" not in str(body)
    assert Reservation.objects.count() == 0
    # The denial writes nothing: no new audit event, no idempotency record.
    assert AuditEvent.objects.count() == before_audit_count
    from slaif_reservation.api.models import IdempotencyRecord

    assert IdempotencyRecord.objects.count() == 0


def test_api_allows_with_current_grant(direct_booker, unrestricted, client) -> None:
    token = _token(direct_booker, ["reservations:create"])
    start, end = future_window()
    response = client.post(
        "/api/v1/reservations/",
        _create_payload(unrestricted, start, end),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token.bearer_token}",
        HTTP_IDEMPOTENCY_KEY="049a-allow-1",
    )
    assert response.status_code == 201
    assert response.json()["id"] == str(Reservation.objects.get().id)


def test_api_authorization_rechecked_before_cached_replay(
    direct_booker, unrestricted, client
) -> None:
    token = _token(direct_booker, ["reservations:create"])
    start, end = future_window()
    original = client.post(
        "/api/v1/reservations/",
        _create_payload(unrestricted, start, end),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token.bearer_token}",
        HTTP_IDEMPOTENCY_KEY="049a-replay-1",
    )
    assert original.status_code == 201
    original_body = original.json()

    # Revoke the booking capability while the token stays valid.
    direct_booker.user_permissions.clear()
    denied = client.post(
        "/api/v1/reservations/",
        _create_payload(unrestricted, start, end),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token.bearer_token}",
        HTTP_IDEMPOTENCY_KEY="049a-replay-1",
    )
    assert denied.status_code == 403
    assert denied.json()["code"] == BOOKING_NOT_AUTHORIZED
    # The original accepted booking and its cached record stay unchanged.
    assert Reservation.objects.count() == 1
    assert denied.headers.get("X-Idempotent-Replay") is None

    # Restore the grant: the SAME key replays the original response.
    grant_book(direct_booker)
    replay = client.post(
        "/api/v1/reservations/",
        _create_payload(unrestricted, start, end),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token.bearer_token}",
        HTTP_IDEMPOTENCY_KEY="049a-replay-1",
    )
    assert replay.status_code == 201
    assert replay.headers.get("X-Idempotent-Replay") == "true"
    assert replay.json() == original_body
    assert Reservation.objects.count() == 1
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_RESERVATION_CREATED).count() == 1


def _post_create(client, token, payload: dict, key: str):
    return client.post(
        "/api/v1/reservations/",
        payload,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token.bearer_token}",
        HTTP_IDEMPOTENCY_KEY=key,
    )


def _assert_denied_403(denied) -> None:
    assert denied.status_code == 403
    assert denied.json()["code"] == BOOKING_NOT_AUTHORIZED
    assert denied.headers.get("X-Idempotent-Replay") is None


def _assert_original_replay(client, token, payload: dict, key: str, original) -> None:
    replay = _post_create(client, token, payload, key)
    assert replay.status_code == 201
    assert replay.headers.get("X-Idempotent-Replay") == "true"
    assert replay.json() == original.json()
    assert replay.headers.get("X-Request-ID") == original.headers.get("X-Request-ID")
    # Restored access replays the ORIGINAL record: no second reservation or
    # second creation audit.
    assert Reservation.objects.count() == 1
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_RESERVATION_CREATED).count() == 1


def test_api_capability_group_removal_denies_new_and_cached_then_replays(client) -> None:
    """Removing the group that carries book_assets, with a valid unchanged
    bearer token, blocks NEW and cached create POSTs; restoring the group
    replays the original response."""
    group = Group.objects.create(name="049a-cap-group")
    group.permissions.add(book_permission())
    owner = User.objects.create_user(
        email="049a-caploss@example.com", password="not-a-secret", display_name="Cap Loss"
    )
    owner.groups.add(group)
    asset = make_asset("049a-caploss")
    token = _token(owner, ["reservations:create"])
    start, end = future_window()
    payload = _create_payload(asset, start, end)

    original = _post_create(client, token, payload, "049a-caploss-1")
    assert original.status_code == 201

    owner.groups.remove(group)  # capability gone; the token stays valid
    _assert_denied_403(_post_create(client, token, payload, "049a-caploss-2"))
    _assert_denied_403(_post_create(client, token, payload, "049a-caploss-1"))
    assert Reservation.objects.count() == 1
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_RESERVATION_CREATED).count() == 1

    owner.groups.add(group)  # restore
    _assert_original_replay(client, token, payload, "049a-caploss-1", original)


def test_api_asset_membership_removal_denies_new_and_cached_then_replays(client) -> None:
    """Removing only the asset-allowed membership while retaining
    book_assets blocks NEW and cached create POSTs; restoring membership
    replays the original response."""
    group = Group.objects.create(name="049a-mem-group")
    owner = User.objects.create_user(
        email="049a-memloss@example.com", password="not-a-secret", display_name="Mem Loss"
    )
    owner.user_permissions.add(book_permission())  # keep the global capability
    owner.groups.add(group)
    asset = make_asset("049a-memloss", booking_restricted=True)
    asset.allowed_booking_groups.add(group)
    token = _token(owner, ["reservations:create"])
    start, end = future_window()
    payload = _create_payload(asset, start, end)

    original = _post_create(client, token, payload, "049a-memloss-1")
    assert original.status_code == 201

    owner.groups.remove(group)  # book_assets retained; asset membership lost
    _assert_denied_403(_post_create(client, token, payload, "049a-memloss-2"))
    _assert_denied_403(_post_create(client, token, payload, "049a-memloss-1"))
    assert Reservation.objects.count() == 1
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_RESERVATION_CREATED).count() == 1

    owner.groups.add(group)  # restore
    _assert_original_replay(client, token, payload, "049a-memloss-1", original)


def test_api_asset_allowlist_removal_denies_new_and_cached_then_replays(client) -> None:
    """Removing the group from the asset's allow-list (owner keeps both the
    capability and the membership) blocks NEW and cached create POSTs;
    re-adding the group replays the original response."""
    group = Group.objects.create(name="049a-acl-group")
    owner = User.objects.create_user(
        email="049a-aclloss@example.com", password="not-a-secret", display_name="ACL Loss"
    )
    owner.user_permissions.add(book_permission())
    owner.groups.add(group)
    asset = make_asset("049a-aclloss", booking_restricted=True)
    asset.allowed_booking_groups.add(group)
    token = _token(owner, ["reservations:create"])
    start, end = future_window()
    payload = _create_payload(asset, start, end)

    original = _post_create(client, token, payload, "049a-aclloss-1")
    assert original.status_code == 201

    asset.allowed_booking_groups.remove(group)  # capability + membership intact
    _assert_denied_403(_post_create(client, token, payload, "049a-aclloss-2"))
    _assert_denied_403(_post_create(client, token, payload, "049a-aclloss-1"))
    assert Reservation.objects.count() == 1
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_RESERVATION_CREATED).count() == 1

    asset.allowed_booking_groups.add(group)  # restore
    _assert_original_replay(client, token, payload, "049a-aclloss-1", original)


def test_api_missing_asset_404_callback_preserved_when_authorized(direct_booker, client) -> None:
    from slaif_reservation.api.models import IdempotencyRecord

    token = _token(direct_booker, ["reservations:create"])
    start, end = future_window()
    asset = make_asset("049a-missing-ref")
    payload = _create_payload(asset, start, end)
    payload["asset_id"] = str(uuid.uuid4())  # never-existing asset
    response = client.post(
        "/api/v1/reservations/",
        payload,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token.bearer_token}",
        HTTP_IDEMPOTENCY_KEY="049a-missing-1",
    )
    assert response.status_code == 404
    assert response.json()["code"] == "asset_not_found"
    # The existing missing-asset callback still records its 404 result.
    assert IdempotencyRecord.objects.count() == 1


def test_api_missing_asset_without_grant_is_403(no_grant, client) -> None:
    # 051-a: legitimate historical token (grant -> issue -> revoke).
    no_grant.user_permissions.add(book_permission())
    token = _token(no_grant, ["reservations:create"])
    no_grant.user_permissions.clear()
    start, end = future_window()
    payload = {
        "asset_id": str(uuid.uuid4()),
        "start_at": start.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "end_at": end.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "purpose": "api",
    }
    response = client.post(
        "/api/v1/reservations/",
        payload,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token.bearer_token}",
        HTTP_IDEMPOTENCY_KEY="049a-missing-2",
    )
    assert response.status_code == 403
    assert response.json()["code"] == BOOKING_NOT_AUTHORIZED


def test_api_owner_only_routes_need_no_booking_grant(no_grant, unrestricted, client) -> None:
    now = timezone.now()
    reservation = Reservation.objects.create(
        asset=unrestricted,
        requested_by_user=no_grant,
        source=Reservation.SOURCE_API,
        status=Reservation.STATUS_CONFIRMED,
        start_at=now - timedelta(hours=1),
        end_at=now + timedelta(hours=1),
        effective_end_at=now + timedelta(hours=1),
        purpose="mine",
    )
    token = _token(no_grant, ["reservations:read", "reservations:cancel", "reservations:release"])
    listing = client.get(
        "/api/v1/reservations/",
        HTTP_AUTHORIZATION=f"Bearer {token.bearer_token}",
    )
    assert listing.status_code == 200
    detail = client.get(
        f"/api/v1/reservations/{reservation.id}/",
        HTTP_AUTHORIZATION=f"Bearer {token.bearer_token}",
    )
    assert detail.status_code == 200
    start2, end2 = future_window()
    cancel_payload = {"reason": "no longer needed"}
    # Cancel requires a cancellable (upcoming) reservation; use a future one.
    upcoming = Reservation.objects.create(
        asset=unrestricted,
        requested_by_user=no_grant,
        source=Reservation.SOURCE_API,
        status=Reservation.STATUS_CONFIRMED,
        start_at=start2,
        end_at=end2,
        effective_end_at=end2,
        purpose="upcoming",
    )
    cancel = client.post(
        f"/api/v1/reservations/{upcoming.id}/cancel/",
        cancel_payload,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token.bearer_token}",
        HTTP_IDEMPOTENCY_KEY="049a-cancel-1",
    )
    assert cancel.status_code == 200
    upcoming.refresh_from_db()
    assert upcoming.status == Reservation.STATUS_CANCELLED


def test_api_scope_still_required_with_capability(direct_booker, unrestricted, client) -> None:
    token = _token(direct_booker, ["reservations:read"])  # no create scope
    start, end = future_window()
    response = client.post(
        "/api/v1/reservations/",
        _create_payload(unrestricted, start, end),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token.bearer_token}",
        HTTP_IDEMPOTENCY_KEY="049a-scope-1",
    )
    assert response.status_code == 403
    assert response.json()["code"] != BOOKING_NOT_AUTHORIZED
    assert Reservation.objects.count() == 0


# --- legacy import -----------------------------------------------------------


def _write_export(path: Path, *, start, end, status: str = "confirmed") -> Path:
    document = {
        "format": "slaif-smartscheduling-synthetic-v1",
        "source": LEGACY_SOURCE,
        "synthetic": True,
        "resources": [{"legacy_id": "049a-resource", "name": "Resource", "slug": "049a-res"}],
        "people": [{"legacy_id": "049a-person", "display_name": "Person"}],
        "appointments": [
            {
                "legacy_id": "049a-appointment",
                "resource_legacy_id": "049a-resource",
                "requester_legacy_id": "049a-person",
                "start": timezone.localtime(start)
                .replace(tzinfo=None)
                .isoformat(timespec="minutes"),
                "end": timezone.localtime(end).replace(tzinfo=None).isoformat(timespec="minutes"),
                "status": status,
            }
        ],
    }
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


def _mapping(path: Path, *, owner: User, asset_obj: Asset) -> Path:
    document = {
        "format": "slaif-smartscheduling-mapping-v1",
        "users": {"049a-person": str(owner.id)},
        "assets": {"049a-resource": str(asset_obj.id)},
    }
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


def _plan(tmp_path: Path, *, owner: User, asset_obj: Asset, start, end, status: str = "confirmed"):
    export = parse_synthetic_export(
        _write_export(tmp_path / "export.yaml", start=start, end=end, status=status),
        source_name=LEGACY_SOURCE,
        timezone_name="Europe/Ljubljana",
    )
    mapping = load_mapping(_mapping(tmp_path / "mapping.yaml", owner=owner, asset_obj=asset_obj))
    return plan_import(export, mapping)


def test_planner_future_unauthorized_reuses_current_predicate(
    tmp_path, no_grant, unrestricted
) -> None:
    start, end = future_window()
    plan = _plan(tmp_path, owner=no_grant, asset_obj=unrestricted, start=start, end=end)
    assert plan.counts["would_create"] == 0
    assert plan.counts["error"] == 1
    assert plan.records[0].messages[0].code == "booking_not_authorized"


def test_planner_future_authorized_remains_would_create(
    tmp_path, direct_booker, unrestricted
) -> None:
    start, end = future_window()
    plan = _plan(tmp_path, owner=direct_booker, asset_obj=unrestricted, start=start, end=end)
    assert plan.counts["would_create"] == 1


def test_planner_past_completed_exception_preserved(tmp_path, no_grant, unrestricted) -> None:
    start = timezone.now() - timedelta(days=2)
    plan = _plan(
        tmp_path,
        owner=no_grant,
        asset_obj=unrestricted,
        start=start,
        end=start + timedelta(hours=1),
        status="completed",
    )
    assert plan.counts["would_create"] == 1


def test_apply_stale_plan_rejects_removed_grant(tmp_path, direct_booker, unrestricted) -> None:
    start, end = future_window()
    plan = _plan(tmp_path, owner=direct_booker, asset_obj=unrestricted, start=start, end=end)
    assert plan.counts["would_create"] == 1

    # Access removal between planning and apply: the plan is advisory.
    direct_booker.user_permissions.clear()
    result = apply_import(plan)
    assert result.counts["imported"] == 0
    assert result.plan.records[0].classification == "error"
    assert result.plan.records[0].messages[0].code == "booking_not_authorized"
    assert Reservation.objects.count() == 0
    assert AuditEvent.objects.count() == 0
    from slaif_reservation.legacy_import.models import LegacyImportRecord

    assert LegacyImportRecord.objects.count() == 0


def test_apply_stale_plan_rejects_removed_group(tmp_path, union_booker, restricted_a) -> None:
    start, end = future_window()
    plan = _plan(tmp_path, owner=union_booker, asset_obj=restricted_a, start=start, end=end)
    assert plan.counts["would_create"] == 1

    union_booker.groups.clear()
    result = apply_import(plan)
    assert result.counts["imported"] == 0
    assert result.plan.records[0].messages[0].code == "booking_not_authorized"
    assert Reservation.objects.count() == 0


def test_apply_past_completed_still_imported_without_grant(
    tmp_path, no_grant, unrestricted
) -> None:
    start = timezone.now() - timedelta(days=2)
    plan = _plan(
        tmp_path,
        owner=no_grant,
        asset_obj=unrestricted,
        start=start,
        end=start + timedelta(hours=1),
        status="completed",
    )
    result = apply_import(plan)
    assert result.counts["imported"] == 1
    assert Reservation.objects.count() == 1


def test_planner_restricted_empty_denies_future(tmp_path, direct_booker, restricted_empty) -> None:
    start, end = future_window()
    plan = _plan(tmp_path, owner=direct_booker, asset_obj=restricted_empty, start=start, end=end)
    assert plan.counts["would_create"] == 0
    assert plan.records[0].messages[0].code == "booking_not_authorized"
