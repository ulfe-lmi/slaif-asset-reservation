from __future__ import annotations

import csv
import json
import uuid
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    StreamingHttpResponse,
)
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from slaif_reservation.accounts.authorization import (
    MANAGEMENT_PERMISSIONS,
    has_any_reservation_permission,
    has_reservation_permission,
)
from slaif_reservation.accounts.validators import validate_timezone_name
from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.management_ui.auth import management_required
from slaif_reservation.management_ui.forms import (
    AuditFilterForm,
    MaintenanceBlackoutForm,
    ManagementCancellationForm,
    ReservationFilterForm,
    ReservationPolicyForm,
)
from slaif_reservation.management_ui.selectors import (
    CALENDAR_MAX_INTERVALS,
    audit_queryset,
    blackout_queryset,
    effective_policy_context,
    policy_queryset,
    reservation_calendar_query,
    reservation_queryset,
)
from slaif_reservation.reservations.exceptions import (
    BLACKOUT_CONFLICT,
    ReservationDomainError,
)
from slaif_reservation.reservations.models import (
    MaintenanceBlackout,
    Reservation,
    ReservationPolicy,
    derive_lifecycle,
)
from slaif_reservation.reservations.services import (
    cancel_reservation,
    create_blackout,
    create_policy,
    deactivate_blackout,
    deactivate_policy,
    overlapping_blocking_reservations_queryset,
    release_reservation,
    update_policy,
)
from slaif_reservation.reservations.time_utils import (
    LocalTimeError,
    interpret_local_wall_time,
)

EXPORT_LIMIT = 500

#: Read capabilities whose modules include a manage counterpart (SAR-048:
#: manage includes that module's read interface, never the reverse).
POLICY_READ_CAPABILITIES = ("view_booking_policies", "manage_booking_policies")
BLACKOUT_READ_CAPABILITIES = ("view_maintenance_blackouts", "manage_maintenance_blackouts")


@management_required(*MANAGEMENT_PERMISSIONS)
def dashboard(request: HttpRequest) -> HttpResponse:
    user = request.user
    can_view_policies = has_any_reservation_permission(user, POLICY_READ_CAPABILITIES)
    can_manage_policies = has_reservation_permission(user, "manage_booking_policies")
    can_view_blackouts = has_any_reservation_permission(user, BLACKOUT_READ_CAPABILITIES)
    can_manage_blackouts = has_reservation_permission(user, "manage_maintenance_blackouts")
    can_view_all_reservations = has_reservation_permission(user, "view_all_reservations")
    can_view_audit = has_reservation_permission(user, "view_audit_history")
    can_export_audit = has_reservation_permission(user, "export_audit_history")
    context: dict[str, Any] = {
        "can_view_policies": can_view_policies,
        "can_manage_policies": can_manage_policies,
        "can_view_blackouts": can_view_blackouts,
        "can_manage_blackouts": can_manage_blackouts,
        "can_view_all_reservations": can_view_all_reservations,
        "can_view_audit": can_view_audit,
        "can_export_audit": can_export_audit,
        "has_any_read_module": (
            can_view_policies or can_view_blackouts or can_view_all_reservations or can_view_audit
        ),
    }
    # Only authorized modules are counted or passed: an unauthorized count,
    # link or action must never reach the page.
    if can_view_policies:
        context["policy_count"] = ReservationPolicy.objects.count()
    if can_view_blackouts:
        context["active_blackout_count"] = MaintenanceBlackout.objects.filter(active=True).count()
    if can_view_all_reservations:
        context["reservation_count"] = Reservation.objects.count()
    if can_export_audit and not can_view_audit:
        context["export_filter_form"] = AuditFilterForm(request.GET)
    return render(request, "management_ui/dashboard.html", context)


@management_required(*POLICY_READ_CAPABILITIES)
def policy_list(request: HttpRequest) -> HttpResponse:
    asset_context = None
    asset_id = request.GET.get("asset")
    if asset_id:
        try:
            asset_context = effective_policy_context(Asset.objects.get(pk=asset_id))
        except (ValueError, ObjectDoesNotExist):
            asset_context = {"asset": None, "policy": None, "state": "asset_not_found"}
    return render(
        request,
        "management_ui/policy_list.html",
        {
            "page": _page(request, policy_queryset(), per_page=50),
            "assets": Asset.objects.order_by("slug"),
            "asset_context": asset_context,
            "can_manage_policies": has_reservation_permission(
                request.user, "manage_booking_policies"
            ),
        },
    )


@management_required(*POLICY_READ_CAPABILITIES)
def policy_detail(request: HttpRequest, policy_id: uuid.UUID) -> HttpResponse:
    policy = _policy_or_404(policy_id)
    return render(
        request,
        "management_ui/policy_detail.html",
        {
            "policy": policy,
            "can_manage_policies": has_reservation_permission(
                request.user, "manage_booking_policies"
            ),
        },
    )


@management_required("manage_booking_policies")
def policy_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ReservationPolicyForm(request.POST)
        if form.is_valid():
            try:
                result = create_policy(
                    actor_user=request.user,
                    source=AuditEvent.SOURCE_ADMIN,
                    **form.service_values(),
                )
            except (ReservationDomainError, ValidationError, IntegrityError):
                form.add_error(None, _("The policy could not be created. Check for conflicts."))
            else:
                messages.success(request, _("Policy created."))
                return redirect("management-ui:policy-detail", policy_id=result.policy.id)
    else:
        form = ReservationPolicyForm()
    return render(request, "management_ui/policy_form.html", {"form": form, "verb": "Create"})


@management_required("manage_booking_policies")
def policy_update(request: HttpRequest, policy_id: uuid.UUID) -> HttpResponse:
    policy = _policy_or_404(policy_id)
    if request.method == "POST":
        form = ReservationPolicyForm(request.POST, instance=policy)
        if form.is_valid():
            try:
                result = update_policy(
                    policy=policy,
                    actor_user=request.user,
                    source=AuditEvent.SOURCE_ADMIN,
                    **form.service_values(),
                )
            except (ReservationDomainError, ValidationError, IntegrityError):
                form.add_error(None, _("The policy could not be updated. Check for conflicts."))
            else:
                messages.success(request, _("Policy updated."))
                return redirect("management-ui:policy-detail", policy_id=result.policy.id)
    else:
        form = ReservationPolicyForm(instance=policy)
    return render(
        request,
        "management_ui/policy_form.html",
        {"form": form, "policy": policy, "verb": "Update"},
    )


@management_required("manage_booking_policies")
def policy_deactivate(request: HttpRequest, policy_id: uuid.UUID) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    policy = _policy_or_404(policy_id)
    try:
        deactivate_policy(policy=policy, actor_user=request.user, source=AuditEvent.SOURCE_ADMIN)
    except ReservationDomainError:
        messages.error(request, _("The policy could not be deactivated."))
    else:
        messages.success(request, _("Policy deactivated."))
    return redirect("management-ui:policy-detail", policy_id=policy.id)


@management_required(*BLACKOUT_READ_CAPABILITIES)
def blackout_list(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "management_ui/blackout_list.html",
        {
            "page": _page(request, blackout_queryset(), per_page=50),
            "can_manage_blackouts": has_reservation_permission(
                request.user, "manage_maintenance_blackouts"
            ),
        },
    )


@management_required(*BLACKOUT_READ_CAPABILITIES)
def blackout_detail(request: HttpRequest, blackout_id: uuid.UUID) -> HttpResponse:
    blackout = _blackout_or_404(blackout_id)
    return render(
        request,
        "management_ui/blackout_detail.html",
        _blackout_detail_context(request.user, blackout),
    )


def _blackout_detail_context(user: Any, blackout: MaintenanceBlackout) -> dict[str, Any]:
    """Affected-booking preview respecting the cross-user read boundary.

    A viewer/manager holding view_all_reservations sees the existing full
    affected list with links. Everyone else receives only the safe overlap
    COUNT and confirmation-relevant wording: no row objects, UUIDs, names,
    emails, purposes or free text leave the server.
    """
    queryset = overlapping_blocking_reservations_queryset(
        asset=blackout.asset,
        start_at=blackout.start_at,
        end_at=blackout.end_at,
    )
    if has_reservation_permission(user, "view_all_reservations"):
        affected = list(queryset)
        context: dict[str, Any] = {
            "blackout": blackout,
            "affected_reservations": affected,
            "affected_count": len(affected),
            "affected_hidden": False,
            "can_manage_blackouts": has_reservation_permission(
                user, "manage_maintenance_blackouts"
            ),
        }
    else:
        context = {
            "blackout": blackout,
            "affected_reservations": [],
            "affected_count": queryset.count(),
            "affected_hidden": True,
            "can_manage_blackouts": has_reservation_permission(
                user, "manage_maintenance_blackouts"
            ),
        }
    return context


@management_required("manage_maintenance_blackouts")
def blackout_create(request: HttpRequest) -> HttpResponse:
    can_view_all_reservations = has_reservation_permission(request.user, "view_all_reservations")
    affected: list[Reservation] = []
    affected_count = 0
    if request.method == "POST":
        form = MaintenanceBlackoutForm(request.POST)
        if form.is_valid():
            queryset = overlapping_blocking_reservations_queryset(
                asset=form.cleaned_data["asset"],
                start_at=form.cleaned_data["start_instant"],
                end_at=form.cleaned_data["end_instant"],
            )
            affected_count = queryset.count()
            if can_view_all_reservations:
                affected = list(queryset)
            if affected_count and not form.cleaned_data["confirm_overlaps"]:
                form.add_error(
                    "confirm_overlaps",
                    _("Confirm creation because reservations overlap this blackout."),
                )
            else:
                try:
                    result = create_blackout(
                        asset=form.cleaned_data["asset"],
                        actor_user=request.user,
                        reason=form.cleaned_data["reason"],
                        start_at=form.cleaned_data["start_instant"],
                        end_at=form.cleaned_data["end_instant"],
                        confirmed_overlap=form.cleaned_data["confirm_overlaps"],
                    )
                except ReservationDomainError as exc:
                    form.add_error(None, _management_domain_message(exc))
                except ValidationError:
                    form.add_error(None, _("The blackout could not be created."))
                else:
                    messages.success(request, _("Maintenance blackout created."))
                    return redirect(
                        "management-ui:blackout-detail",
                        blackout_id=result.blackout.id,
                    )
    else:
        form = MaintenanceBlackoutForm()
    return render(
        request,
        "management_ui/blackout_form.html",
        {
            "form": form,
            "affected_reservations": affected,
            "affected_count": affected_count,
            "affected_hidden": not can_view_all_reservations,
        },
    )


@management_required("manage_maintenance_blackouts")
def blackout_deactivate(request: HttpRequest, blackout_id: uuid.UUID) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    blackout = _blackout_or_404(blackout_id)
    try:
        deactivate_blackout(blackout=blackout, actor_user=request.user)
    except ReservationDomainError:
        messages.error(request, _("The blackout could not be deactivated."))
    else:
        messages.success(request, _("Maintenance blackout deactivated."))
    return redirect("management-ui:blackout-detail", blackout_id=blackout.id)


@management_required("view_all_reservations")
def reservation_list(request: HttpRequest) -> HttpResponse:
    form = ReservationFilterForm(request.GET)
    queryset = (
        reservation_queryset(form.cleaned_data) if form.is_valid() else Reservation.objects.none()
    )
    page = _page(request, queryset, per_page=50)
    # The read-only asset calendar covers one exact asset, so it is offered
    # only while a valid exact-asset filter is selected.
    calendar_asset = form.cleaned_data.get("asset") if form.is_valid() else None
    return render(
        request,
        "management_ui/reservation_list.html",
        {
            "filter_form": form,
            "page": page,
            "pagination": _pagination(request, page),
            "calendar_asset": calendar_asset,
        },
    )


class _CalendarInputError(ValueError):
    """Bounded GET input problem: answer with a plain 400, no traceback."""


#: Calendar week anchors are only meaningful close to the present; anything
#: farther away is rejected as out of range rather than queried.
CALENDAR_ANCHOR_MAX_DAYS = 366 * 10


def _parse_calendar_week_anchor(raw: str | None, today: date) -> date:
    """Parse the ``week`` GET input and normalize it to the Monday of that week.

    Missing input defaults to the current local week. Any valid ISO date is
    accepted and snapped to its Monday; malformed or out-of-range values
    raise :class:`_CalendarInputError`.
    """
    if raw is None or not str(raw).strip():
        anchor = today
    else:
        try:
            anchor = date.fromisoformat(str(raw).strip())
        except ValueError as exc:
            raise _CalendarInputError("Invalid calendar week; use a date like 2026-10-19.") from exc
    monday = anchor - timedelta(days=anchor.weekday())
    if abs((monday - today).days) > CALENDAR_ANCHOR_MAX_DAYS:
        raise _CalendarInputError("Calendar week is outside the supported range.")
    return monday


def _parse_calendar_weeks(raw: str | None) -> int:
    """Parse the ``weeks`` GET input: exactly 1 or 4, defaulting to 1."""
    if raw is None or not str(raw).strip():
        return 1
    try:
        weeks = int(str(raw).strip())
    except ValueError as exc:
        raise _CalendarInputError("Calendar length must be 1 or 4 weeks.") from exc
    if weeks not in (1, 4):
        raise _CalendarInputError("Calendar length must be 1 or 4 weeks.")
    return weeks


def _calendar_url(asset: Asset, week: date, weeks: int) -> str:
    return f"/manage/reservations/calendar/{asset.id}/?week={week.isoformat()}&weeks={weeks}"


def _local_day_label(value: datetime) -> str:
    return value.strftime("%a %d %b %H:%M")


def _calendar_interval_days(
    reservation: Reservation, zone: Any, window_start: date, window_end: date
) -> list[dict[str, Any]]:
    """Per-day presentation of one interval in the viewer's profile timezone.

    The interval is rendered once per local day it covers, clipped to the
    window. Half-open semantics are preserved: an interval ending exactly at
    a local midnight does not cover the following day. A day is labelled as
    the ending day only when the interval's true effective end falls on it;
    an interval still running past the last visible day shows an explicit
    continuation instead of an apparent end.
    """
    start_local = reservation.start_at.astimezone(zone)
    end_local = reservation.effective_end_at.astimezone(zone)
    first_day = start_local.date()
    # The interval's true last covered local day (a local-midnight end
    # belongs to the previous day, never the following one).
    true_last_day = end_local.date()
    if end_local.time() == time.min:
        true_last_day = true_last_day - timedelta(days=1)
    continues_past_window = true_last_day > window_end
    first_day = max(first_day, window_start)
    last_day = min(true_last_day, window_end)
    if first_day > last_day:
        return []

    owner = reservation.requested_by_user
    chips: list[dict[str, Any]] = []
    for offset in range((last_day - first_day).days + 1):
        day = first_day + timedelta(days=offset)
        starts_on_day = day == start_local.date()
        ends_on_day = day == true_last_day
        if starts_on_day and ends_on_day:
            label = f"{start_local.strftime('%H:%M')} - {end_local.strftime('%H:%M')}"
        elif starts_on_day:
            label = f"{start_local.strftime('%H:%M')} ->"
        elif ends_on_day:
            label = f"-> {end_local.strftime('%H:%M')}"
        elif continues_past_window and day == last_day:
            label = "All day ->"
        else:
            label = "All day"
        chips.append(
            {
                "date": day,
                "label": label,
                "full_label": (f"{_local_day_label(start_local)} - {_local_day_label(end_local)}"),
                "owner": owner.display_name or owner.email,
                "status": reservation.status,
                "detail_url": reverse("management-ui:reservation-detail", args=[reservation.id]),
            }
        )
    return chips


def _calendar_days(
    monday: date,
    weeks: int,
    zone: Any,
    window_start_date: date,
    window_end_date: date,
    reservations: list[Reservation],
    today: date,
) -> list[list[dict[str, Any]]]:
    """Week rows of day cells covering the fixed window, with intervals."""
    total_days = weeks * 7
    days_by_date: dict[date, list[dict[str, Any]]] = {
        monday + timedelta(days=offset): [] for offset in range(total_days)
    }
    for reservation in reservations:
        for chip in _calendar_interval_days(reservation, zone, window_start_date, window_end_date):
            if chip["date"] in days_by_date:
                days_by_date[chip["date"]].append(chip)

    week_rows: list[list[dict[str, Any]]] = []
    for week_offset in range(weeks):
        row: list[dict[str, Any]] = []
        for day_offset in range(7):
            day = monday + timedelta(days=week_offset * 7 + day_offset)
            row.append(
                {
                    "date": day,
                    "heading": day.strftime("%A %d %b %Y"),
                    "is_today": day == today,
                    "is_weekend": day.weekday() >= 5,
                    "intervals": days_by_date[day],
                }
            )
        week_rows.append(row)
    return week_rows


@management_required("view_all_reservations")
def reservation_calendar(request: HttpRequest, asset_id: uuid.UUID) -> HttpResponse:
    """Read-only one/four-week Monday-Sunday calendar for one exact asset.

    Authorized by the same ``view_all_reservations`` capability as the All
    reservations browser (staff alone is insufficient; inactive and
    service-account sessions are denied before any row is fetched). Dates
    and times use the viewer's profile timezone, including DST boundaries.
    Only confirmed intervals and released consumed intervals are rendered;
    cancelled rows remain in the All reservations history only.
    """
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    user = request.user
    tz_name = str(getattr(user, "timezone", "") or "").strip()
    try:
        validate_timezone_name(tz_name)
    except ValidationError:
        messages.error(request, _("Update your timezone before using reservation pages."))
        return redirect("web:profile")
    zone = ZoneInfo(tz_name)
    now_local = timezone.now().astimezone(zone)
    today = now_local.date()

    try:
        monday = _parse_calendar_week_anchor(request.GET.get("week"), today)
        weeks = _parse_calendar_weeks(request.GET.get("weeks"))
    except _CalendarInputError as exc:
        return HttpResponseBadRequest(str(exc))

    try:
        window_start = interpret_local_wall_time(
            datetime.combine(monday, time.min), timezone_name=tz_name, fold=0
        ).instant
        window_end = interpret_local_wall_time(
            datetime.combine(monday + timedelta(days=7 * weeks), time.min),
            timezone_name=tz_name,
            fold=0,
        ).instant
    except (LocalTimeError, ValidationError, ZoneInfoNotFoundError, ValueError, OSError):
        return HttpResponseBadRequest("Invalid calendar week for your timezone.")

    try:
        asset = Asset.objects.get(pk=asset_id)
    except ObjectDoesNotExist as exc:
        raise Http404 from exc

    reservations = list(
        reservation_calendar_query(asset, window_start, window_end)[: CALENDAR_MAX_INTERVALS + 1]
    )
    truncated = len(reservations) > CALENDAR_MAX_INTERVALS
    if truncated:
        reservations = reservations[:CALENDAR_MAX_INTERVALS]

    window_end_date = monday + timedelta(days=7 * weeks - 1)
    week_rows = _calendar_days(monday, weeks, zone, monday, window_end_date, reservations, today)

    # Plain fallback link so a capped window never omits silently: the
    # existing All reservations list for this exact asset. It carries no
    # start-based from/to window filters, so it is the complete asset
    # history: an interval that started before this window and still
    # occupies it remains visible there.
    all_reservations_link = f"/manage/reservations/?asset={asset.id}"
    window_start_local = window_start.astimezone(zone)
    return render(
        request,
        "management_ui/reservation_calendar.html",
        {
            "asset": asset,
            "weeks": weeks,
            "week": monday,
            "week_rows": week_rows,
            # The displayed last day is Monday plus 7*weeks-1 local calendar
            # days: a fixed 24-hour UTC subtraction from the half-open end
            # instant mislabels the day across a spring-forward transition,
            # where the week is 167 hours long, not 168.
            "window_label": (
                f"{window_start_local.strftime('%a %d %b %Y')} - "
                f"{window_end_date.strftime('%a %d %b %Y')}"
            ),
            "display_timezone": tz_name,
            "prev_url": _calendar_url(asset, monday - timedelta(days=7 * weeks), weeks),
            "next_url": _calendar_url(asset, monday + timedelta(days=7 * weeks), weeks),
            "this_week_url": _calendar_url(asset, today - timedelta(days=today.weekday()), weeks),
            "one_week_url": _calendar_url(asset, monday, 1),
            "four_week_url": _calendar_url(asset, monday, 4),
            "is_current_window": monday == today - timedelta(days=today.weekday()),
            "truncated": truncated,
            "calendar_limit": CALENDAR_MAX_INTERVALS,
            "all_reservations_link": all_reservations_link,
        },
    )


@management_required("view_all_reservations")
def reservation_detail(request: HttpRequest, reservation_id: uuid.UUID) -> HttpResponse:
    reservation = _reservation_or_404(reservation_id)
    return render(
        request,
        "management_ui/reservation_detail.html",
        {
            "reservation": reservation,
            "lifecycle": derive_lifecycle(reservation, at=timezone.now()),
            "cancel_form": ManagementCancellationForm(),
            "can_cancel_others": has_reservation_permission(
                request.user, "cancel_others_reservations"
            ),
            "can_release_others": has_reservation_permission(
                request.user, "release_others_reservations"
            ),
        },
    )


def _reservation_safe_redirect(request: HttpRequest, reservation_id: uuid.UUID) -> HttpResponse:
    """Post-mutation redirect that never hands a mutation-only principal a
    private detail page they could not open on a direct GET."""
    if has_reservation_permission(request.user, "view_all_reservations"):
        return redirect("management-ui:reservation-detail", reservation_id=reservation_id)
    return redirect("management-ui:dashboard")


@management_required("cancel_others_reservations")
def reservation_cancel(request: HttpRequest, reservation_id: uuid.UUID) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    reservation = _reservation_or_404(reservation_id)
    form = ManagementCancellationForm(request.POST)
    if form.is_valid():
        try:
            cancel_reservation(
                reservation=reservation,
                requested_by_user=request.user,
                reason=form.cleaned_data["reason"],
                source=Reservation.SOURCE_ADMIN,
            )
        except ReservationDomainError as exc:
            messages.error(request, _management_domain_message(exc))
        else:
            messages.success(request, _("Reservation cancelled."))
    else:
        messages.error(request, _("Check the cancellation reason."))
    return _reservation_safe_redirect(request, reservation.id)


@management_required("release_others_reservations")
def reservation_release(request: HttpRequest, reservation_id: uuid.UUID) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    reservation = _reservation_or_404(reservation_id)
    try:
        release_reservation(
            reservation=reservation,
            requested_by_user=request.user,
            source=Reservation.SOURCE_ADMIN,
        )
    except ReservationDomainError as exc:
        messages.error(request, _management_domain_message(exc))
    else:
        messages.success(request, _("Reservation released."))
    return _reservation_safe_redirect(request, reservation.id)


@management_required("view_audit_history")
def audit_list(request: HttpRequest) -> HttpResponse:
    form = AuditFilterForm(request.GET)
    queryset = audit_queryset(form.cleaned_data) if form.is_valid() else AuditEvent.objects.none()
    return render(
        request,
        "management_ui/audit_list.html",
        {
            "filter_form": form,
            "page": _page(request, queryset, per_page=50),
            "can_export_audit": has_reservation_permission(request.user, "export_audit_history"),
        },
    )


@management_required("view_audit_history")
def audit_detail(request: HttpRequest, event_id: uuid.UUID) -> HttpResponse:
    event = _audit_or_404(event_id)
    return render(request, "management_ui/audit_detail.html", {"event": event})


@management_required("export_audit_history")
def audit_export(request: HttpRequest) -> StreamingHttpResponse:
    form = AuditFilterForm(request.GET)
    queryset = audit_queryset(form.cleaned_data) if form.is_valid() else AuditEvent.objects.none()
    if not form.has_real_filters():
        queryset = queryset.filter(occurred_at__gte=timezone.now() - timedelta(days=7))
    rows = list(queryset[:EXPORT_LIMIT])
    response = StreamingHttpResponse(
        _audit_csv_rows(rows),
        content_type="text/csv; charset=utf-8",
    )
    response["Content-Disposition"] = 'attachment; filename="slaif-audit-export.csv"'
    return response


def _policy_or_404(policy_id: uuid.UUID) -> ReservationPolicy:
    try:
        return policy_queryset().get(pk=policy_id)
    except ObjectDoesNotExist as exc:
        raise Http404 from exc


def _blackout_or_404(blackout_id: uuid.UUID) -> MaintenanceBlackout:
    try:
        return blackout_queryset().get(pk=blackout_id)
    except ObjectDoesNotExist as exc:
        raise Http404 from exc


def _reservation_or_404(reservation_id: uuid.UUID) -> Reservation:
    try:
        return reservation_queryset().get(pk=reservation_id)
    except ObjectDoesNotExist as exc:
        raise Http404 from exc


def _audit_or_404(event_id: uuid.UUID) -> AuditEvent:
    try:
        return audit_queryset().get(pk=event_id)
    except ObjectDoesNotExist as exc:
        raise Http404 from exc


def _page(request: HttpRequest, queryset: Any, *, per_page: int) -> Any:
    return Paginator(queryset, per_page).get_page(request.GET.get("page"))


def _pagination(request: HttpRequest, page_obj: Any) -> dict[str, Any]:
    """Previous/next links that preserve every submitted filter parameter."""
    params = request.GET.copy()

    def _href(number: int | None) -> str:
        if number is None or number < 1:
            return ""
        params["page"] = str(number)
        return f"?{params.urlencode()}"

    return {
        "has_previous": page_obj.has_previous(),
        "has_next": page_obj.has_next(),
        "prev_url": _href(page_obj.previous_page_number()) if page_obj.has_previous() else "",
        "next_url": _href(page_obj.next_page_number()) if page_obj.has_next() else "",
        "number": page_obj.number,
        "num_pages": page_obj.paginator.num_pages,
    }


def _audit_csv_rows(events: list[AuditEvent]) -> Any:
    class Echo:
        def write(self, value: str) -> str:
            return value

    writer = csv.writer(Echo())
    yield writer.writerow(
        [
            "occurred_at",
            "action",
            "target_type",
            "target_id",
            "actor",
            "source",
            "correlation_id",
            "metadata",
        ]
    )
    for event in events:
        yield writer.writerow(
            [
                event.occurred_at.isoformat(),
                event.action,
                event.target_type,
                str(event.target_id),
                str(event.actor_user_id or ""),
                event.source,
                str(event.correlation_id),
                json.dumps(event.metadata, sort_keys=True, separators=(",", ":")),
            ]
        )


def _management_domain_message(error: ReservationDomainError) -> str:
    if error.code == BLACKOUT_CONFLICT:
        return str(_("The requested interval conflicts with existing reservations or maintenance."))
    return str(_("The management operation could not be completed."))
