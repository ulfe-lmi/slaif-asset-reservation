from __future__ import annotations

import uuid
from datetime import date
from typing import Any, cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib import messages
from django.contrib.auth import SESSION_KEY
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.paginator import Page, Paginator
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
from django.views.decorators.debug import sensitive_variables

from slaif_reservation.accounts.exceptions import ApiTokenDomainError
from slaif_reservation.accounts.services import issue_api_token, revoke_api_token
from slaif_reservation.accounts.tokens import OneTimeBearerToken
from slaif_reservation.accounts.validators import validate_timezone_name
from slaif_reservation.assets.authorization import (
    STATE_ELIGIBLE,
    STATE_NO_BOOKING_PERMISSION,
    batch_asset_booking_states,
)
from slaif_reservation.assets.models import Asset
from slaif_reservation.assets.selectors import AssetFilterError
from slaif_reservation.reservations.exceptions import (
    ASSET_INACTIVE,
    ASSET_NOT_RESERVABLE,
    BLACKOUT_CONFLICT,
    BOOKING_HORIZON_VIOLATION,
    BOOKING_NOT_AUTHORIZED,
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
    derive_lifecycle,
)
from slaif_reservation.reservations.services import (
    cancel_reservation,
    create_reservation,
    release_reservation,
    resolve_effective_policy,
)
from slaif_reservation.web.auth import active_human_required, is_active_human
from slaif_reservation.web.availability import (
    MAX_AVAILABILITY_DAYS,
    AvailabilityInputError,
    availability_for_asset,
)
from slaif_reservation.web.forms import (
    ApiTokenCreationForm,
    CancellationForm,
    HumanAuthenticationForm,
    ProfileForm,
    ReservationForm,
)
from slaif_reservation.web.selectors import (
    dashboard_reservations,
    get_member_asset,
    get_owned_api_token,
    get_owned_reservation,
    member_asset_context,
    owned_api_tokens_queryset,
    owned_reservations_queryset,
    parse_member_asset_filters,
)

DOMAIN_ERROR_MESSAGES = {
    POLICY_NOT_CONFIGURED: _("This asset is not currently bookable."),
    BOOKING_NOT_AUTHORIZED: _(
        "Your account cannot book this asset right now. If you believe this "
        "is an error, contact an administrator."
    ),
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
    BLACKOUT_CONFLICT: _("That time is unavailable for maintenance."),
    RESERVATION_NOT_OWNED: _("That reservation was not found."),
    RESERVATION_NOT_CANCELLABLE: _("This reservation cannot be cancelled."),
    CANCELLATION_CUTOFF: _("This reservation is past the cancellation cutoff."),
    RESERVATION_NOT_RELEASABLE: _("This reservation cannot be released."),
}


class HumanLoginView(LoginView):
    template_name = "web/login.html"
    authentication_form = HumanAuthenticationForm
    redirect_authenticated_user = True

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if (
            request.user.is_authenticated or SESSION_KEY in request.session
        ) and not is_active_human(request.user):
            auth_logout(request)
        return cast(HttpResponse, super().dispatch(request, *args, **kwargs))


@method_decorator(active_human_required, name="dispatch")
class HumanLogoutView(LogoutView):
    http_method_names = ["post", "options"]


def root(request: HttpRequest) -> HttpResponse:
    """Public entry point.

    Anonymous visitors receive the public landing; anyone with an
    authenticated (or session-bearing) request is dispatched to the
    dashboard, which enforces the active-human boundary and terminates
    disallowed sessions exactly as before.
    """
    if request.user.is_authenticated or SESSION_KEY in request.session:
        return dashboard(request)
    return render(request, "web/landing.html")


@active_human_required
def dashboard(request: HttpRequest) -> HttpResponse:
    timezone_name = _member_timezone_or_profile(request)
    if isinstance(timezone_name, HttpResponse):
        return timezone_name
    return render(
        request,
        "web/dashboard.html",
        {
            **dashboard_reservations(request.user),
            "display_timezone": timezone_name,
        },
    )


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
    try:
        display_timezone = _display_timezone(request.user)
    except InvalidMemberTimezone:
        display_timezone = ""
    return render(
        request,
        "web/profile.html",
        {
            "form": form,
            "display_timezone": display_timezone,
        },
    )


@active_human_required
def token_list(request: HttpRequest) -> HttpResponse:
    timezone_name = _member_timezone_or_profile(request)
    if isinstance(timezone_name, HttpResponse):
        return timezone_name
    return render(
        request,
        "web/token_list.html",
        {
            "page": _page_queryset(
                request,
                owned_api_tokens_queryset(request.user),
                "page",
                per_page=25,
            ),
            "display_timezone": timezone_name,
        },
    )


@active_human_required
@sensitive_variables("result")
def token_create(request: HttpRequest) -> HttpResponse:
    timezone_name = _member_timezone_or_profile(request)
    if isinstance(timezone_name, HttpResponse):
        return timezone_name
    if request.method == "POST":
        form = ApiTokenCreationForm(request.POST)
        if form.is_valid():
            try:
                result = issue_api_token(
                    owner=request.user,
                    name=form.cleaned_data["name"],
                    scopes=form.cleaned_data["scopes"],
                    lifetime_days=form.cleaned_data["lifetime_days"],
                )
            except (ApiTokenDomainError, ValidationError):
                form.add_error(None, _("The API token could not be created."))
            else:
                response = render(
                    request,
                    "web/token_created.html",
                    {
                        "token": result.token,
                        "bearer_token": OneTimeBearerToken(result.bearer_token),
                        "display_timezone": timezone_name,
                    },
                )
                response["Cache-Control"] = "no-store, private"
                response["Pragma"] = "no-cache"
                response["Referrer-Policy"] = "no-referrer"
                return response
    else:
        form = ApiTokenCreationForm()
    return render(
        request,
        "web/token_create.html",
        {
            "form": form,
            "display_timezone": timezone_name,
        },
    )


@active_human_required
def revoke_own_token(request: HttpRequest, token_id: uuid.UUID) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    token = _owned_token_or_404(token_id, request.user)
    try:
        revoke_api_token(token=token, owner=request.user)
    except ApiTokenDomainError:
        messages.error(request, _("The API token could not be revoked."))
    else:
        messages.success(request, _("API token revoked."))
    return redirect("web:token-list")


def _booking_note(state: str) -> str:
    if state == STATE_NO_BOOKING_PERMISSION:
        return _(
            "Your account does not have the booking permission, so this asset cannot be reserved."
        )
    return _(
        "This asset can only be booked by members of specific approved "
        "groups; your account is not currently one of them."
    )


def _booking_access(state: str) -> str:
    if state == STATE_ELIGIBLE:
        return _("You can book this asset.")
    if state == STATE_NO_BOOKING_PERMISSION:
        return _("Your account does not have the booking permission.")
    return _("Restricted to specific approved groups (your account is not currently one of them).")


def _is_bookable(asset: Asset, state: str) -> bool:
    return (
        state == STATE_ELIGIBLE
        and asset.reservable
        and asset.booking_mode == Asset.BOOKING_EXCLUSIVE
    )


@active_human_required
def asset_list(request: HttpRequest) -> HttpResponse:
    timezone_name = _member_timezone_or_profile(request)
    if isinstance(timezone_name, HttpResponse):
        return timezone_name
    try:
        filters = parse_member_asset_filters(request.GET)
    except AssetFilterError as exc:
        return HttpResponseBadRequest(str(exc))
    context = member_asset_context(filters)
    assets = list(context.assets)
    states = batch_asset_booking_states(request.user, assets)
    rows = [(asset, _is_bookable(asset, states[asset.id])) for asset in assets]
    return render(
        request,
        "web/asset_list.html",
        {
            "context": context,
            "rows": rows,
            "kinds": Asset.KIND_CHOICES,
            "display_timezone": timezone_name,
        },
    )


@active_human_required
def asset_detail(request: HttpRequest, asset_id: uuid.UUID) -> HttpResponse:
    timezone_name = _member_timezone_or_profile(request)
    if isinstance(timezone_name, HttpResponse):
        return timezone_name
    try:
        asset = get_member_asset(asset_id)
    except ObjectDoesNotExist as exc:
        raise Http404 from exc
    availability = _availability_from_request(request, asset, timezone_name=timezone_name)
    if isinstance(availability, HttpResponse):
        return availability
    state = batch_asset_booking_states(request.user, [asset])[asset.id]
    bookable = _is_bookable(asset, state)
    shows_access_line = asset.reservable and asset.booking_mode == Asset.BOOKING_EXCLUSIVE
    return render(
        request,
        "web/asset_detail.html",
        {
            "asset": asset,
            "availability": availability,
            "display_timezone": timezone_name,
            "bookable": bookable,
            "shows_access_line": shows_access_line,
            "booking_access": _booking_access(state) if shows_access_line else "",
            "booking_note": _booking_note(state) if shows_access_line and not bookable else "",
        },
    )


@active_human_required
def reserve_asset(request: HttpRequest, asset_id: uuid.UUID) -> HttpResponse:
    timezone_name = _member_timezone_or_profile(request)
    if isinstance(timezone_name, HttpResponse):
        return timezone_name
    try:
        asset = get_member_asset(asset_id)
    except ObjectDoesNotExist as exc:
        raise Http404 from exc

    # The booking gate applies to DIRECT requests, not only to the hidden
    # button: an active human without current capability/asset eligibility
    # is denied here, and the authoritative row-locked service rechecks the
    # same predicate for any write that still reaches it.
    state = batch_asset_booking_states(request.user, [asset])[asset.id]
    bookable = _is_bookable(asset, state)

    availability = _availability_from_request(request, asset, timezone_name=timezone_name)
    if isinstance(availability, HttpResponse):
        return availability
    try:
        policy = resolve_effective_policy(asset)
    except ReservationDomainError:
        policy = None
    if not bookable:
        if request.method != "POST":
            messages.error(request, _booking_note(state))
            return redirect("web:asset-detail", asset_id=asset.id)
        form = ReservationForm(request.POST, timezone_name=timezone_name, policy=policy)
        form.add_error(None, _booking_note(state))
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
    if request.method == "POST":
        form = ReservationForm(request.POST, timezone_name=timezone_name, policy=policy)
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
                availability = _availability_from_request(
                    request, asset, timezone_name=timezone_name
                )
                if isinstance(availability, HttpResponse):
                    return availability
            else:
                messages.success(request, _("Reservation created."))
                return redirect("web:reservation-detail", reservation_id=result.reservation.id)
    else:
        form = ReservationForm(timezone_name=timezone_name, policy=policy)
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
    timezone_name = _member_timezone_or_profile(request)
    if isinstance(timezone_name, HttpResponse):
        return timezone_name
    now = timezone.now()
    owned = owned_reservations_queryset(request.user)
    return render(
        request,
        "web/reservation_list.html",
        {
            "active_page": _page_queryset(
                request,
                owned.filter(
                    status=Reservation.STATUS_CONFIRMED,
                    start_at__lte=now,
                    effective_end_at__gt=now,
                ),
                "active_page",
                per_page=10,
            ),
            "upcoming_page": _page_queryset(
                request,
                owned.filter(status=Reservation.STATUS_CONFIRMED, start_at__gt=now).order_by(
                    "start_at", "created_at"
                ),
                "upcoming_page",
                per_page=10,
            ),
            "completed_page": _page_queryset(
                request,
                owned.filter(
                    status=Reservation.STATUS_CONFIRMED,
                    effective_end_at__lte=now,
                ),
                "completed_page",
                per_page=25,
            ),
            "cancelled_page": _page_queryset(
                request,
                owned.filter(status=Reservation.STATUS_CANCELLED),
                "cancelled_page",
                per_page=25,
            ),
            "released_page": _page_queryset(
                request,
                owned.filter(status=Reservation.STATUS_RELEASED),
                "released_page",
                per_page=25,
            ),
            "display_timezone": timezone_name,
        },
    )


@active_human_required
def reservation_detail(request: HttpRequest, reservation_id: uuid.UUID) -> HttpResponse:
    timezone_name = _member_timezone_or_profile(request)
    if isinstance(timezone_name, HttpResponse):
        return timezone_name
    reservation = _owned_or_404(reservation_id, request.user)
    return render(
        request,
        "web/reservation_detail.html",
        {
            "reservation": reservation,
            "lifecycle": derive_lifecycle(reservation, at=timezone.now()),
            "cancel_form": CancellationForm(),
            "display_timezone": timezone_name,
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


def _owned_token_or_404(token_id: uuid.UUID, user: Any) -> Any:
    try:
        return get_owned_api_token(token_id, user)
    except ObjectDoesNotExist as exc:
        raise Http404 from exc


class InvalidMemberTimezone(ValueError):
    pass


def _display_timezone(user: Any) -> str:
    timezone_name = str(getattr(user, "timezone", "") or "").strip()
    try:
        validate_timezone_name(timezone_name)
    except ValidationError as exc:
        raise InvalidMemberTimezone("Member timezone is invalid.") from exc
    return timezone_name


def _member_timezone_or_profile(request: HttpRequest) -> str | HttpResponse:
    try:
        return _display_timezone(request.user)
    except InvalidMemberTimezone:
        messages.error(request, _("Update your timezone before using reservation pages."))
        return redirect("web:profile")


def _availability_from_request(request: HttpRequest, asset: Asset, *, timezone_name: str) -> Any:
    raw_date = request.GET.get("date")
    raw_days = request.GET.get("days")
    try:
        start_date = (
            date.fromisoformat(raw_date)
            if raw_date
            else timezone.now().astimezone(ZoneInfo(timezone_name)).date()
        )
    except (ValueError, ZoneInfoNotFoundError):
        return HttpResponseBadRequest("Invalid availability date.")
    try:
        days = int(raw_days) if raw_days else 7
    except ValueError:
        return HttpResponseBadRequest("Invalid availability window.")
    if days < 1 or days > MAX_AVAILABILITY_DAYS:
        return HttpResponseBadRequest("Availability window must be between 1 and 7 days.")
    try:
        return availability_for_asset(
            asset=asset,
            principal=request.user,
            start_date=start_date,
            days=days,
            display_timezone=timezone_name,
        )
    except AvailabilityInputError:
        return HttpResponseBadRequest("Invalid availability date.")


def _domain_message(error: ReservationDomainError) -> str:
    return str(DOMAIN_ERROR_MESSAGES.get(error.code, _("The reservation could not be changed.")))


def _page_queryset(
    request: HttpRequest,
    queryset: Any,
    page_param: str,
    *,
    per_page: int,
) -> Page[Any]:
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get(page_param))
