"""Integrated pilot path (scope item 2): one asset's reservation state shared
consistently across the three real entry points.

Member books in the browser (real form login/CSRF via Playwright live_server),
an agent books against the same asset over the bearer API (real one-time token
display path, no force_authenticate, no DB token reads), staff applies
maintenance through the management UI (real client.login, CSRF on mutations),
and cancellation/release flow back into every surface's view.

The journey is one sequential transaction (``transaction=True``) so that all
surfaces observe the same committed state.
"""

from __future__ import annotations

import os
import re
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from django.utils import timezone

from slaif_reservation.accounts.models import ApiToken, User
from slaif_reservation.assets.models import Asset, AssetTag
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.reservations.exceptions import (
    RESERVATION_CONFLICT,
    ReservationDomainError,
)
from slaif_reservation.reservations.models import (
    MaintenanceBlackout,
    Reservation,
    ReservationPolicy,
)
from slaif_reservation.reservations.services import create_reservation

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

BEARER_RE = re.compile(r"sar_[0-9a-f]{32}_[A-Za-z0-9_-]+")


def _grant_booking(created: User) -> None:
    # A16: positive booking fixtures explicitly carry the baseline
    # reservations.book_assets capability (real Permission row).
    created.user_permissions.add(
        Permission.objects.get(codename="book_assets", content_type__app_label="reservations")
    )
    return created


@pytest.fixture
def pilot_member() -> User:
    return _grant_booking(
        User.objects.create_user(
            email="pilot-member@example.com",
            password="not-a-secret",
            display_name="Pilot Member",
            timezone="Europe/Ljubljana",
        )
    )


@pytest.fixture
def pilot_agent() -> User:
    return _grant_booking(
        User.objects.create_user(
            email="pilot-agent@example.com",
            password="not-a-secret",
            display_name="Pilot Agent",
        )
    )


@pytest.fixture
def pilot_other() -> User:
    return _grant_booking(
        User.objects.create_user(
            email="pilot-other@example.com",
            password="not-a-secret",
            display_name="Pilot Other",
        )
    )


@pytest.fixture
def pilot_staff() -> User:
    return User.objects.create_user(
        email="pilot-staff@example.com",
        password="not-a-secret",
        display_name="Pilot Staff",
        is_staff=True,
    )


@pytest.fixture
def pilot_service() -> User:
    return User.objects.create_user(
        email="pilot-service@example.com",
        password="not-a-secret",
        display_name="Pilot Service",
        is_service_account=True,
    )


@pytest.fixture
def pilot_machine() -> Asset:
    return Asset.objects.create(
        slug="pilot-machine",
        name="Pilot Machine",
        kind=Asset.KIND_MACHINE,
        active=True,
        reservable=False,
        verification_required=False,
    )


@pytest.fixture
def pilot_asset(pilot_machine: Asset) -> Asset:
    asset = Asset.objects.create(
        slug="pilot-gpu",
        name="Pilot GPU",
        kind=Asset.KIND_GPU,
        parent=pilot_machine,
        active=True,
        reservable=True,
        verification_required=True,
    )
    tag = AssetTag.objects.create(slug="pilot-tag", name="Pilot Tag")
    asset.tags.add(tag)
    return asset


@pytest.fixture
def pilot_policy(pilot_asset: Asset) -> ReservationPolicy:
    return ReservationPolicy.objects.create(
        name="Pilot policy",
        asset=pilot_asset,
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


def _login(page, live_server, user: User) -> None:
    page.goto(f"{live_server.url}/login/")
    page.get_by_label("Email").fill(user.email)
    page.get_by_label("Password").fill("not-a-secret")
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server.url}/")


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _local(value: datetime, user: User) -> str:
    return value.astimezone(ZoneInfo(user.timezone)).strftime("%Y-%m-%dT%H:%M")


def _local_display(value: datetime, user: User) -> str:
    return value.astimezone(ZoneInfo(user.timezone)).strftime("%Y-%m-%d %H:%M")


def _window(days: int, hour: int, minute: int = 0) -> datetime:
    return (timezone.now() + timedelta(days=days)).replace(
        hour=hour, minute=minute, second=0, microsecond=0
    )


def _api_body(asset: Asset, start: datetime, end: datetime, purpose: str) -> dict[str, str]:
    return {
        "asset_id": str(asset.id),
        "start_at": _iso(start),
        "end_at": _iso(end),
        "purpose": purpose,
    }


def _blackout_payload(asset: Asset, start: datetime, end: datetime) -> dict[str, str]:
    fmt = "%Y-%m-%dT%H:%M"
    return {
        "asset": str(asset.id),
        "timezone": "UTC",
        "start": start.astimezone(UTC).strftime(fmt),
        "end": end.astimezone(UTC).strftime(fmt),
        "reason": "private pilot blackout reason",
    }


def _issue_token_via_web_flow(
    django_client: Client, user: User, name: str, scopes: list[str]
) -> tuple[str, ApiToken]:
    """Drive the real one-time-display token flow; capture the one-time value
    from the rendered page (never from the DB row)."""
    assert django_client.login(email=user.email, password="not-a-secret") is True
    django_client.get("/tokens/new/")
    csrf = django_client.cookies["csrftoken"].value
    response = django_client.post(
        "/tokens/new/",
        {"name": name, "scopes": list(scopes), "lifetime_days": "7"},
        HTTP_X_CSRFTOKEN=csrf,
    )
    assert response.status_code == 200
    body = response.content.decode()
    match = BEARER_RE.search(body)
    assert match is not None
    token = ApiToken.objects.get(owner=user)
    return match.group(0), token


def _availability_section_text(page, index: int) -> str:
    return (
        page.locator("section[aria-labelledby='availability-heading'] ul").nth(index).inner_text()
    )


def _book_via_form(
    page,
    live_server,
    user: User,
    asset: Asset,
    start: datetime,
    end: datetime,
    purpose: str,
    **query: str,
) -> None:
    url = f"{live_server.url}/assets/{asset.id}/reserve/"
    if query:
        url += "?" + "&".join(f"{key}={value}" for key, value in query.items())
    page.goto(url)
    page.locator("#id_start").fill(_local(start, user))
    page.locator("#id_end").fill(_local(end, user))
    page.get_by_label("Purpose").fill(purpose)
    page.get_by_role("button", name="Create reservation").click()


@pytest.mark.django_db(transaction=True)
def test_integrated_pilot_path_shared_state_across_surfaces(
    page,
    live_server,
    client,
    pilot_member: User,
    pilot_agent: User,
    pilot_other: User,
    pilot_staff: User,
    pilot_service: User,
    pilot_machine: Asset,
    pilot_asset: Asset,
    pilot_policy: ReservationPolicy,
) -> None:
    base = live_server.url
    member, agent, other, staff = pilot_member, pilot_agent, pilot_other, pilot_staff
    service, asset = pilot_service, pilot_asset
    journey_start = timezone.now()

    # ------------------------------------------------------------------ 2a
    # Agent token issued via the REAL one-time-display path; real Bearer on
    # /api/v1/me/ (safe context: no verifier/pepper/admin fields).
    agent_client = Client(enforce_csrf_checks=True)
    agent_token, token_row = _issue_token_via_web_flow(
        agent_client,
        agent,
        "Pilot agent token",
        [
            "availability:read",
            "reservations:read",
            "reservations:create",
            "reservations:cancel",
            "reservations:release",
        ],
    )
    assert token_row.scopes == [
        "availability:read",
        "reservations:cancel",
        "reservations:create",
        "reservations:read",
        "reservations:release",
    ]

    agent_auth = {"HTTP_AUTHORIZATION": f"Bearer {agent_token}"}
    me = client.get("/api/v1/me/", **agent_auth)
    assert me.status_code == 200
    payload = me.json()
    assert payload["principal"]["id"] == str(agent.id)
    assert "email" not in payload["principal"]
    assert "verifier" not in me.content.decode().lower()
    assert "pepper" not in me.content.decode().lower()
    assert "is_staff" not in me.content.decode()

    # The member establishes the shared browser reservation (scope item 1
    # pattern through the real form), so items 2b/2d share that state.
    _login(page, live_server, member)
    m_start = _window(2, 8)
    m_end = m_start + timedelta(hours=1)
    _book_via_form(page, live_server, member, asset, m_start, m_end, "Pilot member window")
    page.wait_for_url("**/reservations/**/")
    assert "Reservation created" in page.content()
    r_member = Reservation.objects.get(requested_by_user=member)
    assert r_member.source == Reservation.SOURCE_WEB

    # ------------------------------------------------------------------ 2b
    # Availability for the same asset: the member's window is busy; no owner
    # identity, purpose, or reservation UUID leaks (SAR-019).
    availability = client.get(
        f"/api/v1/assets/{asset.id}/availability/",
        {"date": m_start.date().isoformat(), "days": "2", "timezone": "UTC"},
        **agent_auth,
    )
    assert availability.status_code == 200
    availability_payload = availability.json()
    assert availability_payload["busy"] == [
        {
            "start": _iso(m_start),
            "end": _iso(m_end),
            "label": "Unavailable",
            "reservation_id": None,
        }
    ]
    availability_body = availability.content.decode()
    assert member.email not in availability_body
    assert "Pilot Member" not in availability_body
    assert "Pilot member window" not in availability_body
    assert str(r_member.id) not in availability_body

    # ------------------------------------------------------------------ 2c
    # Agent creates a second non-overlapping future window with
    # Idempotency-Key -> 201 + Location; exact replay is stable; a changed
    # body under the same key conflicts.
    a_start = _window(3, 8)
    a_end = a_start + timedelta(hours=1)
    create_headers = {**agent_auth, "HTTP_IDEMPOTENCY_KEY": "pilot-create-1"}
    first = client.post(
        "/api/v1/reservations/",
        _api_body(asset, a_start, a_end, "Pilot agent window"),
        content_type="application/json",
        **create_headers,
    )
    assert first.status_code == 201
    r_agent = Reservation.objects.get(requested_by_user=agent)
    assert first["Location"].endswith(f"/api/v1/reservations/{r_agent.id}/")
    replay = client.post(
        "/api/v1/reservations/",
        _api_body(asset, a_start, a_end, "Pilot agent window"),
        content_type="application/json",
        **create_headers,
    )
    assert replay.status_code == 201
    assert replay["X-Idempotent-Replay"] == "true"
    assert replay.json() == first.json()
    assert replay["Location"] == first["Location"]
    conflict = client.post(
        "/api/v1/reservations/",
        _api_body(asset, a_start, a_end, "changed purpose"),
        content_type="application/json",
        **create_headers,
    )
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "idempotency_conflict"
    assert Reservation.objects.filter(asset=asset).count() == 2
    assert (
        AuditEvent.objects.filter(
            action=AuditEvent.ACTION_RESERVATION_CREATED,
            source=AuditEvent.SOURCE_API,
        ).count()
        == 1
    )

    # ------------------------------------------------------------------ 2d
    # Cross-surface exclusivity (SAR-001): the member's browser availability
    # now shows the agent's window busy; a browser create on that exact
    # window gets conflict feedback with input preserved; no second
    # reservation exists.
    page.goto(f"{base}/assets/{asset.id}/?date={a_start.date().isoformat()}&days=2")
    busy_text = _availability_section_text(page, 0)
    assert _local_display(a_start, member) in busy_text
    page_body = page.content()
    assert agent.email not in page_body
    assert "Pilot Agent" not in page_body
    assert "Pilot agent window" not in page_body

    _book_via_form(
        page,
        live_server,
        member,
        asset,
        a_start,
        a_end,
        "Conflict probe",
        date=a_start.date().isoformat(),
        days="2",
    )
    content = page.content()
    assert "That time is no longer available" in content
    assert "Conflict probe" in content
    assert Reservation.objects.filter(asset=asset).count() == 2

    # ------------------------------------------------------------------ 2e
    # Staff journey: blackout over the next free window of the same asset.
    # It overlaps the agent's confirmed reservation, so the affected
    # reservation confirmation path must be exercised (list shown, explicit
    # confirm, no auto-cancel).
    staff_client = Client(enforce_csrf_checks=True)
    assert staff_client.login(email=staff.email, password="not-a-secret") is True

    def staff_csrf() -> str:
        return staff_client.cookies["csrftoken"].value

    staff_client.get("/manage/blackouts/new/")
    b_start = a_start + timedelta(minutes=30)
    b_end = a_start + timedelta(hours=2, minutes=30)
    unconfirmed = staff_client.post(
        "/manage/blackouts/new/",
        _blackout_payload(asset, b_start, b_end),
        HTTP_X_CSRFTOKEN=staff_csrf(),
    )
    assert unconfirmed.status_code == 200
    unconfirmed_body = unconfirmed.content.decode()
    assert "Overlapping reservations" in unconfirmed_body
    assert str(r_agent.id) in unconfirmed_body
    assert "Pilot Agent" in unconfirmed_body
    assert "Confirm creation because reservations overlap this blackout." in unconfirmed_body
    assert MaintenanceBlackout.objects.count() == 0

    confirmed = staff_client.post(
        "/manage/blackouts/new/",
        _blackout_payload(asset, b_start, b_end) | {"confirm_overlaps": "on"},
        HTTP_X_CSRFTOKEN=staff_csrf(),
    )
    assert confirmed.status_code == 302
    blackout = MaintenanceBlackout.objects.get()
    assert blackout.active
    r_agent.refresh_from_db()
    assert r_agent.status == Reservation.STATUS_CONFIRMED
    blackout_created_event = AuditEvent.objects.filter(
        action=AuditEvent.ACTION_BLACKOUT_CREATED, target_id=blackout.id
    ).get()
    assert blackout_created_event.metadata["overlapping_reservations"] == 1

    # Member browser availability clips the blackout window without revealing
    # the reason.
    page.goto(f"{base}/assets/{asset.id}/?date={a_start.date().isoformat()}&days=2")
    busy_text = _availability_section_text(page, 0)
    assert _local_display(b_end, member) in busy_text
    page_body = page.content()
    assert "private pilot blackout reason" not in page_body
    assert agent.email not in page_body
    assert "Pilot Agent" not in page_body

    # Member browser create on the blackout window is rejected.
    bm_start = a_start + timedelta(hours=1)
    bm_end = a_start + timedelta(hours=2)
    _book_via_form(
        page,
        live_server,
        member,
        asset,
        bm_start,
        bm_end,
        "Blackout probe",
        date=a_start.date().isoformat(),
        days="2",
    )
    content = page.content()
    assert "That time is unavailable for maintenance." in content
    assert "Blackout probe" in content
    assert Reservation.objects.filter(asset=asset).count() == 2

    # Agent API create on the blackout window is rejected with a
    # blackout-related problem detail and no reason leakage.
    agent_reject = client.post(
        "/api/v1/reservations/",
        _api_body(asset, bm_start, bm_end, "Blackout probe api"),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {agent_token}",
        HTTP_IDEMPOTENCY_KEY="pilot-blackout-1",
    )
    assert agent_reject.status_code == 409
    assert agent_reject.json()["code"] == "blackout_conflict"
    assert "private pilot blackout reason" not in agent_reject.content.decode()
    assert "Traceback" not in agent_reject.content.decode()
    assert Reservation.objects.filter(asset=asset).count() == 2

    # Staff deactivates; BOTH surfaces can then book the window again.
    deactivated = staff_client.post(
        f"/manage/blackouts/{blackout.id}/deactivate/", HTTP_X_CSRFTOKEN=staff_csrf()
    )
    assert deactivated.status_code == 302
    blackout.refresh_from_db()
    assert not blackout.active
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_BLACKOUT_DEACTIVATED).count() == 1

    _book_via_form(
        page,
        live_server,
        member,
        asset,
        bm_start,
        bm_end,
        "Pilot member post-maintenance",
        date=a_start.date().isoformat(),
        days="2",
    )
    page.wait_for_url("**/reservations/**/")
    assert "Reservation created" in page.content()
    r_member_two = Reservation.objects.get(purpose="Pilot member post-maintenance")

    late_start = a_start + timedelta(hours=2)
    late_end = a_start + timedelta(hours=3)
    late_create = client.post(
        "/api/v1/reservations/",
        _api_body(asset, late_start, late_end, "Pilot agent post-maintenance"),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {agent_token}",
        HTTP_IDEMPOTENCY_KEY="pilot-create-2",
    )
    assert late_create.status_code == 201
    r_agent_two = Reservation.objects.get(purpose="Pilot agent post-maintenance")
    assert Reservation.objects.filter(asset=asset).count() == 4

    # ------------------------------------------------------------------ 2f
    # Cross-surface lifecycle (SAR-006).
    # (i) The agent cancels via the API; the idempotent replay returns the
    # original accepted response; the cancelled window is free again on the
    # member's availability.
    cancel_headers = {
        **agent_auth,
        "HTTP_IDEMPOTENCY_KEY": "pilot-cancel-1",
    }
    cancelled = client.post(
        f"/api/v1/reservations/{r_agent.id}/cancel/",
        {"reason": "Pilot agent cancel"},
        content_type="application/json",
        **cancel_headers,
    )
    assert cancelled.status_code == 200
    replayed_cancel = client.post(
        f"/api/v1/reservations/{r_agent.id}/cancel/",
        {"reason": "Pilot agent cancel"},
        content_type="application/json",
        **cancel_headers,
    )
    assert replayed_cancel.status_code == 200
    assert replayed_cancel["X-Idempotent-Replay"] == "true"
    assert replayed_cancel.json() == cancelled.json()
    r_agent.refresh_from_db()
    assert r_agent.status == Reservation.STATUS_CANCELLED
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_RESERVATION_CANCELLED).count() == 1

    page.goto(f"{base}/assets/{asset.id}/?date={a_start.date().isoformat()}&days=2")
    busy_text = _availability_section_text(page, 0)
    free_text = _availability_section_text(page, 1)
    # The cancelled window [a_start, a_end) is inside the free interval again:
    # its end is now a free-interval boundary, and its start no longer appears
    # as a busy boundary.
    assert _local_display(a_start, member) not in busy_text
    assert _local_display(a_end, member) in free_text

    # (ii) A reservation in ACTIVE state (start in the past) is released via
    # the member browser (chosen over the agent API for this leg); after
    # release the consumed prefix [start_at, effective_end_at) still blocks
    # while the remainder is bookable.
    now = timezone.now()
    active_start = now - timedelta(minutes=30)
    active_end = now + timedelta(minutes=90)
    active = Reservation.objects.create(
        asset=asset,
        requested_by_user=member,
        source=Reservation.SOURCE_WEB,
        status=Reservation.STATUS_CONFIRMED,
        start_at=active_start,
        end_at=active_end,
        effective_end_at=active_end,
        purpose="Pilot active window",
    )
    page.goto(f"{base}/reservations/")
    assert f"/reservations/{active.id}/" in page.content()
    page.goto(f"{base}/reservations/{active.id}/")
    assert "Active" in page.content()
    assert page.get_by_role("button", name="Release reservation").count() == 1
    assert page.get_by_role("button", name="Cancel reservation").count() == 0
    with page.expect_navigation():
        page.get_by_role("button", name="Release reservation").click()
    assert "Reservation released" in page.content()
    active.refresh_from_db()
    assert active.status == Reservation.STATUS_RELEASED
    assert active.released_at is not None
    assert active.effective_end_at == active.released_at
    assert active.end_at == active_end

    # Consumed prefix still blocks: a service-level create overlapping the
    # prefix (under a consistent clock before the release point) must fail
    # with the domain conflict, and the availability still shows the prefix.
    # The probe starts after the probe clock (so it is a valid future start
    # under that clock) but still overlaps the consumed prefix
    # [active_start, release_at): the overlap check must reject it.
    with pytest.raises(ReservationDomainError, check=lambda exc: exc.code == RESERVATION_CONFLICT):
        create_reservation(
            asset=asset,
            requested_by_user=member,
            start_at=now - timedelta(minutes=2),
            end_at=now + timedelta(minutes=58),
            purpose="prefix probe",
            now=now - timedelta(minutes=5),
        )
    assert Reservation.objects.filter(asset=asset).count() == 5
    # The availability window is explicit: start it at active_start's date
    # in the MEMBER PROFILE timezone and span two local days, so the
    # default current-day window cannot clip a consumed prefix that began
    # late the previous local day.  Domain timing is untouched.
    active_local = active_start.astimezone(ZoneInfo(member.timezone))
    page.goto(f"{base}/assets/{asset.id}/?date={active_local.date().isoformat()}&days=2")
    busy_text = _availability_section_text(page, 0)
    assert _local_display(active_start, member) in busy_text
    assert _local_display(active.effective_end_at, member) in busy_text

    # Remainder is bookable through the real browser form.
    rem_start = (now + timedelta(minutes=5)).replace(second=0, microsecond=0)
    rem_end = (now + timedelta(minutes=85)).replace(second=0, microsecond=0)
    _book_via_form(page, live_server, member, asset, rem_start, rem_end, "Pilot remainder")
    page.wait_for_url("**/reservations/**/")
    assert "Reservation created" in page.content()
    r_remainder = Reservation.objects.get(purpose="Pilot remainder")
    assert Reservation.objects.filter(asset=asset).count() == 6

    # ------------------------------------------------------------------ 2g
    # Audit trail (staff session, bounded window): every journey event is
    # present with its source/actor; the CSV export is credential-free and
    # honors the bounded filter.
    audit_list = staff_client.get("/manage/audit/", {"occurred_from": journey_start.isoformat()})
    assert audit_list.status_code == 200
    events = list(
        AuditEvent.objects.filter(occurred_at__gte=journey_start).order_by("occurred_at", "id")
    )
    assert len(events) == 10
    observed = [(event.action, event.source, str(event.actor_user_id)) for event in events]
    assert (AuditEvent.ACTION_API_TOKEN_CREATED, AuditEvent.SOURCE_WEB, str(agent.id)) in observed
    assert (
        observed.count(
            (AuditEvent.ACTION_RESERVATION_CREATED, AuditEvent.SOURCE_WEB, str(member.id))
        )
        == 3
    )
    assert (
        observed.count(
            (AuditEvent.ACTION_RESERVATION_CREATED, AuditEvent.SOURCE_API, str(agent.id))
        )
        == 2
    )
    assert (
        AuditEvent.ACTION_RESERVATION_CANCELLED,
        AuditEvent.SOURCE_API,
        str(agent.id),
    ) in observed
    assert (
        AuditEvent.ACTION_RESERVATION_RELEASED,
        AuditEvent.SOURCE_WEB,
        str(member.id),
    ) in observed
    assert (
        AuditEvent.ACTION_BLACKOUT_CREATED,
        AuditEvent.SOURCE_ADMIN,
        str(staff.id),
    ) in observed
    assert (
        AuditEvent.ACTION_BLACKOUT_DEACTIVATED,
        AuditEvent.SOURCE_ADMIN,
        str(staff.id),
    ) in observed

    list_body = audit_list.content.decode()
    targets = (r_member.id, r_agent.id, r_agent_two.id, r_member_two.id, r_remainder.id, active.id)
    for target in targets:
        assert str(target) in list_body
    assert str(blackout.id) in list_body
    assert str(token_row.id) in list_body

    # Correlation: the API-created reservation's audit event carries the
    # request correlation; the browser-created one is browsable with its
    # correlation shown.
    api_created_event = AuditEvent.objects.filter(
        action=AuditEvent.ACTION_RESERVATION_CREATED, target_id=r_agent.id
    ).get()
    assert str(api_created_event.correlation_id) == first.json()["correlation_id"]
    web_created_event = AuditEvent.objects.filter(
        action=AuditEvent.ACTION_RESERVATION_CREATED, target_id=r_member.id
    ).get()
    detail = staff_client.get(f"/manage/audit/{web_created_event.id}/")
    assert detail.status_code == 200
    assert str(web_created_event.correlation_id) in detail.content.decode()

    export = staff_client.get(
        "/manage/audit/export.csv", {"occurred_from": journey_start.isoformat()}
    )
    assert export.status_code == 200
    export_body = b"".join(export.streaming_content).decode()
    assert "reservation.created" in export_body
    assert "reservation.cancelled" in export_body
    assert "reservation.released" in export_body
    assert "maintenance_blackout.created" in export_body
    assert "maintenance_blackout.deactivated" in export_body
    assert "api_token.created" in export_body
    assert agent_token not in export_body
    assert token_row.verifier not in export_body
    assert "not-a-secret" not in export_body
    assert "Authorization" not in export_body
    assert "pepper" not in export_body.lower()

    # Bounded filter: up to (and including) the blackout creation instant.
    bounded_export = staff_client.get(
        "/manage/audit/export.csv",
        {"occurred_to": blackout_created_event.occurred_at.isoformat()},
    )
    bounded_body = b"".join(bounded_export.streaming_content).decode()
    assert "maintenance_blackout.created" in bounded_body
    assert "maintenance_blackout.deactivated" not in bounded_body

    # ------------------------------------------------------------------ 2h
    # Integrated negatives.
    # (i) Revoked agent token -> 401 generic problem detail, no disclosure.
    csrf = agent_client.cookies["csrftoken"].value
    revoke = agent_client.post(f"/tokens/{token_row.id}/revoke/", {}, HTTP_X_CSRFTOKEN=csrf)
    assert revoke.status_code == 302
    token_row.refresh_from_db()
    assert token_row.revoked_at is not None

    revoked_call = client.get("/api/v1/me/", **agent_auth)
    assert revoked_call.status_code == 401
    assert revoked_call["Content-Type"].startswith("application/problem+json")
    revoked_payload = revoked_call.json()
    assert revoked_payload["code"] == "invalid_token"
    assert revoked_payload["correlation_id"]
    revoked_body = revoked_call.content.decode()
    assert agent_token not in revoked_body
    assert str(token_row.id) not in revoked_body
    assert agent.email not in revoked_body
    assert "verifier" not in revoked_body.lower()

    # (ii) Another member's browser/API view of the agent's reservation
    # detail -> non-disclosing 404 with the endpoint code.
    other_client = Client(enforce_csrf_checks=True)
    other_token, _other_row = _issue_token_via_web_flow(
        other_client, other, "Pilot other token", ["reservations:read"]
    )
    other_api = client.get(
        f"/api/v1/reservations/{r_agent.id}/",
        HTTP_AUTHORIZATION=f"Bearer {other_token}",
    )
    assert other_api.status_code == 404
    assert other_api.json()["code"] == "reservation_not_found"
    other_api_body = other_api.content.decode()
    assert "Pilot agent window" not in other_api_body
    assert agent.email not in other_api_body
    assert "Traceback" not in other_api_body
    assert "Reservation object" not in other_api_body

    other_context = page.context.browser.new_context()
    other_page = other_context.new_page()
    try:
        _login(other_page, live_server, other)
        detail_response = other_page.goto(f"{base}/reservations/{r_agent.id}/")
        assert detail_response is not None
        assert detail_response.status == 404
        other_detail_body = other_page.content()
        assert "Pilot agent window" not in other_detail_body
        assert agent.email not in other_detail_body
    finally:
        other_context.close()

    # (iii) Service-account login to the member UI is rejected.
    service_context = page.context.browser.new_context()
    service_page = service_context.new_page()
    try:
        service_page.goto(f"{base}/login/")
        service_page.get_by_label("Email").fill(service.email)
        service_page.get_by_label("Password").fill("not-a-secret")
        service_page.get_by_role("button", name="Log in").click()
        assert "Enter a valid email address and password" in service_page.content()
        assert service_page.url.endswith("/login/")
    finally:
        service_context.close()

    # Final state of the shared asset.
    assert Reservation.objects.filter(asset=asset).count() == 6
    assert MaintenanceBlackout.objects.count() == 1
