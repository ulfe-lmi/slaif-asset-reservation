from __future__ import annotations

import uuid
from datetime import date
from typing import Any
from zoneinfo import ZoneInfo

from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
)
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _

from slaif_reservation.assets.models import Asset
from slaif_reservation.assets.selectors import AssetFilterError
from slaif_reservation.reservations.exceptions import (
    ASSET_INACTIVE,
    ASSET_NOT_RESERVABLE,
    BOOKING_HORIZON_VIOLATION,
    CANCELLATION_CUTOFF,
    DURATION_TOO_LONG,
    DURATION_TOO_SHORT,
    INVALID_TIME_RANGE,
    LEAD_TIME_VIOLATION,
    MAX_CONCURRENT_EXCEEDED,
    MAX_UPCOMING_EXCEEDED,
    POLICY_AMBIGUOUS,
    POLICY_NOT_CONFIGURED,
    PRINCIPAL_INACTIVE,
    PURPOSE_REQUIRED,
    RESERVATION_CONFLICT,
    RESERVATION_IN_PAST,
    RESERVATION_NOT_CANCELLABLE,
    RESERVATION_NOT_OWNED,
    RESERVATION_NOT_RELEASABLE,
    UNSUPPORTED_BOOKING_MODE,
    ReservationDomainError,
)
from slaif_reservation.reservations.models import (
    Reservation,
    ReservationLifecycle,
    derive_lifecycle,
)
from slaif_reservation.reservations.services import (
    cancel_reservation,
    create_reservation,
    release_reservation,
)
from slaif_reservation.web.auth import active_human_required
from slaif_reservation.web.availability import MAX_AVAILABILITY_DAYS, availability_for_asset
from slaif_reservation.web.forms import (
    CancellationForm,
    HumanAuthenticationForm,
    ProfileForm,
    ReservationForm,
)
from slaif_reservation.web.selectors import (
    dashboard_reservations,
    get_member_asset,
    get_owned_reservation,
    member_asset_context,
    owned_reservations_queryset,
    parse_member_asset_filters,
)

DOMAIN_ERROR_MESSAGES = {
    POLICY_NOT_CONFIGURED: _("This asset is not currently bookable."),
    POLICY_AMBIGUOUS: _("This asset is not currently bookable."),
    PRINCIPAL_INACTIVE: _("Your account cannot make reservations."),
    ASSET_INACTIVE: _("This asset is inactive."),
    ASSET_NOT_RESERVABLE: _("This asset is not reservable."),
    UNSUPPORTED_BOOKING_MODE: _("This asset cannot be reserved through this page."),
    INVALID_TIME_RANGE: _("Check the requested start and end time."),
    RESERVATION_IN_PAST: _("Reservations cannot start in the past."),
    LEAD_TIME_VIOLATION: _("The reservation starts before the required lead time."),
    BOOKING_HORIZON_VIOLATION: _("The reservation starts beyond the booking horizon."),
    DURATION_TOO_SHORT: _("The reservation is shorter than the policy minimum."),
    DURATION_TOO_LONG: _("The reservation is longer than the policy maximum."),
    PURPOSE_REQUIRED: _("A purpose is required for this reservation."),
    MAX_UPCOMING_EXCEEDED: _("You have reached the upcoming reservation limit."),
    MAX_CONCURRENT_EXCEEDED: _("You have reached the concurrent reservation limit."),
    RESERVATION_CONFLICT: _("That time is no longer available."),
    RESERVATION_NOT_OWNED: _("That reservation was not found."),
    RESERVATION_NOT_CANCELLABLE: _("This reservation cannot be cancelled."),
    CANCELLATION_CUTOFF: _("This reservation is past the cancellation cutoff."),
    RESERVATION_NOT_RELEASABLE: _("This reservation cannot be released."),
}


class HumanLoginView(LoginView):
    template_name = "web/login.html"
    authentication_form = HumanAuthenticationForm
    redirect_authenticated_user = True


@method_decorator(active_human_required, name="dispatch")
class HumanLogoutView(LogoutView):
    http_method_names = ["post", "options"]


@active_human_required
def dashboard(request: HttpRequest) -> HttpResponse:
    return render(request, "web/dashboard.html", dashboard_reservations(request.user))


@active_human_required
def profile(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Profile updated."))
            return redirect("web:profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "web/profile.html", {"form": form})


@active_human_required
def asset_list(request: HttpRequest) -> HttpResponse:
    try:
        filters = parse_member_asset_filters(request.GET)
    except AssetFilterError as exc:
        return HttpResponseBadRequest(str(exc))
    return render(
        request,
        "web/asset_list.html",
        {
            "context": member_asset_context(filters),
            "kinds": Asset.KIND_CHOICES,
        },
    )


@active_human_required
def asset_detail(request: HttpRequest, asset_id: uuid.UUID) -> HttpResponse:
    try:
        asset = get_member_asset(asset_id)
    except ObjectDoesNotExist as exc:
        raise Http404 from exc
    availability = _availability_from_request(request, asset)
    if isinstance(availability, HttpResponse):
        return availability
    return render(request, "web/asset_detail.html", {"asset": asset, "availability": availability})


@active_human_required
def reserve_asset(request: HttpRequest, asset_id: uuid.UUID) -> HttpResponse:
    try:
        asset = get_member_asset(asset_id)
    except ObjectDoesNotExist as exc:
        raise Http404 from exc

    availability = _availability_from_request(request, asset)
    if isinstance(availability, HttpResponse):
        return availability
    timezone_name = _display_timezone(request.user)
    if request.method == "POST":
        form = ReservationForm(request.POST, timezone_name=timezone_name)
        if form.is_valid():
            try:
                result = create_reservation(
                    asset=asset,
                    requested_by_user=request.user,
                    start_at=form.cleaned_data["start_instant"],
                    end_at=form.cleaned_data["end_instant"],
                    purpose=form.cleaned_data["purpose"],
                    source=Reservation.SOURCE_WEB,
                )
            except ReservationDomainError as exc:
                form.add_error(None, _domain_message(exc))
                availability = _availability_from_request(request, asset)
                if isinstance(availability, HttpResponse):
                    return availability
            else:
                messages.success(request, _("Reservation created."))
                return redirect("web:reservation-detail", reservation_id=result.reservation.id)
    else:
        form = ReservationForm(timezone_name=timezone_name)
    return render(
        request,
        "web/reserve.html",
        {
            "asset": asset,
            "form": form,
            "timezone_name": timezone_name,
            "availability": availability,
        },
    )


@active_human_required
def reservation_list(request: HttpRequest) -> HttpResponse:
    now = timezone.now()
    reservations = list(owned_reservations_queryset(request.user))
    grouped: dict[ReservationLifecycle, list[Reservation]] = {
        ReservationLifecycle.ACTIVE: [],
        ReservationLifecycle.UPCOMING: [],
        ReservationLifecycle.COMPLETED: [],
        ReservationLifecycle.CANCELLED: [],
        ReservationLifecycle.RELEASED: [],
    }
    for reservation in reservations:
        grouped[derive_lifecycle(reservation, at=now)].append(reservation)
    history = grouped[ReservationLifecycle.COMPLETED]
    paginator = Paginator(history, 25)
    history_page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "web/reservation_list.html",
        {
            "active": grouped[ReservationLifecycle.ACTIVE],
            "upcoming": grouped[ReservationLifecycle.UPCOMING],
            "cancelled": grouped[ReservationLifecycle.CANCELLED],
            "released": grouped[ReservationLifecycle.RELEASED],
            "history_page": history_page,
        },
    )


@active_human_required
def reservation_detail(request: HttpRequest, reservation_id: uuid.UUID) -> HttpResponse:
    reservation = _owned_or_404(reservation_id, request.user)
    return render(
        request,
        "web/reservation_detail.html",
        {
            "reservation": reservation,
            "lifecycle": derive_lifecycle(reservation, at=timezone.now()),
            "cancel_form": CancellationForm(),
        },
    )


@active_human_required
def cancel_own_reservation(request: HttpRequest, reservation_id: uuid.UUID) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    reservation = _owned_or_404(reservation_id, request.user)
    form = CancellationForm(request.POST)
    if form.is_valid():
        try:
            cancel_reservation(
                reservation=reservation,
                requested_by_user=request.user,
                reason=form.cleaned_data["reason"],
                source=Reservation.SOURCE_WEB,
            )
        except ReservationDomainError as exc:
            messages.error(request, _domain_message(exc))
        else:
            messages.success(request, _("Reservation cancelled."))
    else:
        messages.error(request, _("Check the cancellation reason."))
    return redirect("web:reservation-detail", reservation_id=reservation.id)


@active_human_required
def release_own_reservation(request: HttpRequest, reservation_id: uuid.UUID) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    reservation = _owned_or_404(reservation_id, request.user)
    try:
        release_reservation(
            reservation=reservation,
            requested_by_user=request.user,
            source=Reservation.SOURCE_WEB,
        )
    except ReservationDomainError as exc:
        messages.error(request, _domain_message(exc))
    else:
        messages.success(request, _("Reservation released."))
    return redirect("web:reservation-detail", reservation_id=reservation.id)


def _owned_or_404(reservation_id: uuid.UUID, user: Any) -> Reservation:
    try:
        return get_owned_reservation(reservation_id, user)
    except ObjectDoesNotExist as exc:
        raise Http404 from exc


def _display_timezone(user: Any) -> str:
    return str(getattr(user, "timezone", "") or "Europe/Ljubljana")


def _availability_from_request(request: HttpRequest, asset: Asset) -> Any:
    timezone_name = _display_timezone(request.user)
    raw_date = request.GET.get("date")
    raw_days = request.GET.get("days")
    try:
        start_date = (
            date.fromisoformat(raw_date)
            if raw_date
            else timezone.now().astimezone(ZoneInfo(timezone_name)).date()
        )
    except ValueError:
        return HttpResponseBadRequest("Invalid availability date.")
    try:
        days = int(raw_days) if raw_days else 7
    except ValueError:
        return HttpResponseBadRequest("Invalid availability window.")
    if days < 1 or days > MAX_AVAILABILITY_DAYS:
        return HttpResponseBadRequest("Availability window must be between 1 and 7 days.")
    return availability_for_asset(
        asset=asset,
        principal=request.user,
        start_date=start_date,
        days=days,
        display_timezone=timezone_name,
    )


def _domain_message(error: ReservationDomainError) -> str:
    return str(DOMAIN_ERROR_MESSAGES.get(error.code, _("The reservation could not be changed.")))
