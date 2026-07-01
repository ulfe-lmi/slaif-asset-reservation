from __future__ import annotations

import csv
import json
import uuid
from datetime import timedelta
from typing import Any

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseNotAllowed,
    StreamingHttpResponse,
)
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _

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
    audit_queryset,
    blackout_queryset,
    effective_policy_context,
    policy_queryset,
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
    overlapping_blocking_reservations,
    release_reservation,
    update_policy,
)

EXPORT_LIMIT = 500


@management_required
def dashboard(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "management_ui/dashboard.html",
        {
            "policy_count": ReservationPolicy.objects.count(),
            "active_blackout_count": MaintenanceBlackout.objects.filter(active=True).count(),
            "reservation_count": Reservation.objects.count(),
        },
    )


@management_required
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
        },
    )


@management_required
def policy_detail(request: HttpRequest, policy_id: uuid.UUID) -> HttpResponse:
    policy = _policy_or_404(policy_id)
    return render(request, "management_ui/policy_detail.html", {"policy": policy})


@management_required
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


@management_required
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


@management_required
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


@management_required
def blackout_list(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "management_ui/blackout_list.html",
        {"page": _page(request, blackout_queryset(), per_page=50)},
    )


@management_required
def blackout_detail(request: HttpRequest, blackout_id: uuid.UUID) -> HttpResponse:
    blackout = _blackout_or_404(blackout_id)
    affected = overlapping_blocking_reservations(
        asset=blackout.asset,
        start_at=blackout.start_at,
        end_at=blackout.end_at,
    )
    return render(
        request,
        "management_ui/blackout_detail.html",
        {"blackout": blackout, "affected_reservations": affected},
    )


@management_required
def blackout_create(request: HttpRequest) -> HttpResponse:
    affected: list[Reservation] = []
    if request.method == "POST":
        form = MaintenanceBlackoutForm(request.POST)
        if form.is_valid():
            affected = overlapping_blocking_reservations(
                asset=form.cleaned_data["asset"],
                start_at=form.cleaned_data["start_instant"],
                end_at=form.cleaned_data["end_instant"],
            )
            if affected and not form.cleaned_data["confirm_overlaps"]:
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
        {"form": form, "affected_reservations": affected},
    )


@management_required
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


@management_required
def reservation_list(request: HttpRequest) -> HttpResponse:
    form = ReservationFilterForm(request.GET)
    queryset = (
        reservation_queryset(form.cleaned_data) if form.is_valid() else Reservation.objects.none()
    )
    return render(
        request,
        "management_ui/reservation_list.html",
        {"filter_form": form, "page": _page(request, queryset, per_page=50)},
    )


@management_required
def reservation_detail(request: HttpRequest, reservation_id: uuid.UUID) -> HttpResponse:
    reservation = _reservation_or_404(reservation_id)
    return render(
        request,
        "management_ui/reservation_detail.html",
        {
            "reservation": reservation,
            "lifecycle": derive_lifecycle(reservation, at=timezone.now()),
            "cancel_form": ManagementCancellationForm(),
        },
    )


@management_required
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
    return redirect("management-ui:reservation-detail", reservation_id=reservation.id)


@management_required
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
    return redirect("management-ui:reservation-detail", reservation_id=reservation.id)


@management_required
def audit_list(request: HttpRequest) -> HttpResponse:
    form = AuditFilterForm(request.GET)
    queryset = audit_queryset(form.cleaned_data) if form.is_valid() else AuditEvent.objects.none()
    return render(
        request,
        "management_ui/audit_list.html",
        {"filter_form": form, "page": _page(request, queryset, per_page=50)},
    )


@management_required
def audit_detail(request: HttpRequest, event_id: uuid.UUID) -> HttpResponse:
    event = _audit_or_404(event_id)
    return render(request, "management_ui/audit_detail.html", {"event": event})


@management_required
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
