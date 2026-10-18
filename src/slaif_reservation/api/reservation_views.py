from __future__ import annotations

import uuid
from datetime import UTC
from typing import Any, cast
from zoneinfo import ZoneInfo

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet
from django.urls import reverse
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from slaif_reservation.accounts.models import ApiToken
from slaif_reservation.api.authentication import ApiTokenAuthentication
from slaif_reservation.api.idempotency import MutationResult, execute_idempotent_mutation
from slaif_reservation.api.permissions import HasApiTokenScope
from slaif_reservation.api.problem import (
    api_exception_handler,
    correlation_id_from_request,
    problem_response,
)
from slaif_reservation.api.serializers import (
    AvailabilityQuerySerializer,
    EmptyMutationSerializer,
    MeSerializer,
    ReservationCancelSerializer,
    ReservationCreateSerializer,
    ReservationListQuerySerializer,
    availability_representation,
    reservation_representation,
)
from slaif_reservation.assets.authorization import user_can_book_asset
from slaif_reservation.assets.models import Asset
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
from slaif_reservation.reservations.models import Reservation
from slaif_reservation.reservations.services import (
    cancel_reservation,
    create_reservation,
    release_reservation,
)
from slaif_reservation.web.availability import (
    MAX_AVAILABILITY_DAYS,
    AvailabilityInputError,
    availability_for_asset,
)


class ApiLimitOffsetPagination(LimitOffsetPagination):  # type: ignore[misc]
    default_limit = 50
    max_limit = 100


class BearerAPIView(APIView):  # type: ignore[misc]
    authentication_classes = [ApiTokenAuthentication]
    permission_classes = [IsAuthenticated, HasApiTokenScope]
    required_scopes: tuple[str, ...] = ()

    @property
    def api_token(self) -> ApiToken:
        token = self.request.auth
        assert isinstance(token, ApiToken)
        return token

    def handle_exception(self, exc: Exception) -> Response:
        response = api_exception_handler(exc, {"request": self.request, "view": self})
        if response is not None:
            return response
        return super().handle_exception(exc)


class MeAPIView(BearerAPIView):
    required_scopes: tuple[str, ...] = ()

    @extend_schema(
        responses={200: MeSerializer, 429: OpenApiTypes.OBJECT, 503: OpenApiTypes.OBJECT},
        operation_id="api_v1_me_retrieve",
        description="Bearer-token-authenticated principal and token context.",
    )
    def get(self, request: Request) -> Response:
        token = self.api_token
        correlation_id = correlation_id_from_request(request)
        response = Response(
            {
                "principal": {
                    "id": str(request.user.id),
                    "display_name": request.user.display_name,
                },
                "token": {
                    "id": str(token.id),
                    "display_prefix": token.display_prefix,
                    "scopes": token.scopes,
                    "expires_at": _iso(token.expires_at),
                    "last_used_at": _iso(token.last_used_at),
                },
                "correlation_id": str(correlation_id),
            }
        )
        response["X-Request-ID"] = str(correlation_id)
        return response


class AvailabilityAPIView(BearerAPIView):
    required_scopes = ("availability:read",)

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT, 429: OpenApiTypes.OBJECT, 503: OpenApiTypes.OBJECT},
        operation_id="api_v1_asset_availability_retrieve",
        parameters=[
            OpenApiParameter("date", str, OpenApiParameter.QUERY),
            OpenApiParameter("days", int, OpenApiParameter.QUERY),
            OpenApiParameter("timezone", str, OpenApiParameter.QUERY),
            OpenApiParameter("X-Request-ID", str, OpenApiParameter.HEADER),
        ],
        description="Privacy-safe advisory availability for one asset.",
    )
    def get(self, request: Request, asset_id: uuid.UUID) -> Response:
        correlation_id = correlation_id_from_request(request)
        serializer = AvailabilityQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        asset = _asset_or_none(asset_id)
        if asset is None:
            return _asset_not_found_response(request, correlation_id)
        display_timezone = serializer.validated_data.get("timezone") or request.user.timezone
        requested_date = serializer.validated_data.get("date") or timezone.localdate(
            timezone=ZoneInfo(display_timezone)
        )
        days = serializer.validated_data.get("days", MAX_AVAILABILITY_DAYS)
        try:
            result = availability_for_asset(
                asset=asset,
                principal=request.user,
                start_date=requested_date,
                days=days,
                display_timezone=display_timezone,
            )
        except (AvailabilityInputError, ValueError):
            return problem_response(
                request=request,
                status_code=status.HTTP_400_BAD_REQUEST,
                code="validation_error",
                title="Validation error",
                detail="Availability parameters are invalid.",
                correlation_id=correlation_id,
            )
        response = Response(
            {
                **availability_representation(result),
                "correlation_id": str(correlation_id),
            }
        )
        response["X-Request-ID"] = str(correlation_id)
        return response


class ReservationListCreateAPIView(BearerAPIView):
    pagination_class = ApiLimitOffsetPagination

    def get_required_scopes(self, method: str) -> tuple[str, ...]:
        if method == "POST":
            return ("reservations:create",)
        return ("reservations:read",)

    def check_permissions(self, request: Request) -> None:
        self.required_scopes = self.get_required_scopes(request.method)
        super().check_permissions(request)

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT, 429: OpenApiTypes.OBJECT, 503: OpenApiTypes.OBJECT},
        operation_id="api_v1_reservation_list",
        parameters=[
            OpenApiParameter("asset", str, OpenApiParameter.QUERY),
            OpenApiParameter("status", str, OpenApiParameter.QUERY),
            OpenApiParameter("lifecycle", str, OpenApiParameter.QUERY),
            OpenApiParameter("from", str, OpenApiParameter.QUERY),
            OpenApiParameter("to", str, OpenApiParameter.QUERY),
            OpenApiParameter("limit", int, OpenApiParameter.QUERY),
            OpenApiParameter("offset", int, OpenApiParameter.QUERY),
            OpenApiParameter("X-Request-ID", str, OpenApiParameter.HEADER),
        ],
        description="List the authenticated token owner's reservations.",
    )
    def get(self, request: Request) -> Response:
        correlation_id = correlation_id_from_request(request)
        serializer = ReservationListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        queryset = _filtered_reservations(request.user, serializer.validated_data)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        assert page is not None
        data = [
            reservation_representation(reservation, correlation_id=None) for reservation in page
        ]
        response = paginator.get_paginated_response(data)
        response.data["correlation_id"] = str(correlation_id)
        response["X-Request-ID"] = str(correlation_id)
        return response

    @extend_schema(
        request=ReservationCreateSerializer,
        responses={201: OpenApiTypes.OBJECT, 429: OpenApiTypes.OBJECT, 503: OpenApiTypes.OBJECT},
        operation_id="api_v1_reservation_create",
        parameters=[
            OpenApiParameter("Idempotency-Key", str, OpenApiParameter.HEADER, required=True),
            OpenApiParameter("X-Request-ID", str, OpenApiParameter.HEADER),
        ],
        description=(
            "Create a reservation through the authoritative domain service. "
            "Active maintenance overlap is reported as blackout_conflict."
        ),
    )
    def post(self, request: Request) -> Response:
        correlation_id = correlation_id_from_request(request)
        if key_problem := _idempotency_header_problem(request, correlation_id):
            return key_problem
        serializer = ReservationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Authorization is part of the request contract, not of the
        # idempotent result: recheck the owner's CURRENT booking
        # capability and exact-asset eligibility on every creation
        # request, BEFORE any cached idempotent response is returned.
        # The asset predicate is prefetched only when the asset exists so
        # the existing missing-asset 404 callback (and its idempotent
        # recording) is preserved; the global capability check applies
        # regardless.  The authoritative row-locked service rechecks the
        # same predicate for actual new writes.
        preflight_asset = _asset_or_none(serializer.validated_data["asset_id"])
        if not user_can_book_asset(request.user, preflight_asset):
            return problem_response(
                request=request,
                status_code=status.HTTP_403_FORBIDDEN,
                code=BOOKING_NOT_AUTHORIZED,
                title="Booking not authorized",
                detail="You do not currently have permission to create this reservation.",
                correlation_id=correlation_id,
            )

        def mutate() -> MutationResult:
            try:
                asset = Asset.objects.get(pk=serializer.validated_data["asset_id"])
            except ObjectDoesNotExist:
                body = _problem_body(
                    status_code=status.HTTP_404_NOT_FOUND,
                    code="asset_not_found",
                    title="Asset not found",
                    detail="The requested asset was not found.",
                    correlation_id=correlation_id,
                )
                return MutationResult(
                    status_code=status.HTTP_404_NOT_FOUND,
                    body=body,
                    target_type="asset",
                    target_id=None,
                )
            try:
                result = create_reservation(
                    asset=asset,
                    requested_by_user=request.user,
                    start_at=serializer.validated_data["start_at"],
                    end_at=serializer.validated_data["end_at"],
                    purpose=serializer.validated_data["purpose"],
                    source=Reservation.SOURCE_API,
                    correlation_id=correlation_id,
                )
            except ReservationDomainError as exc:
                return _domain_mutation_result(exc, correlation_id=correlation_id)
            body = reservation_representation(
                result.reservation,
                correlation_id=result.correlation_id,
            )
            return MutationResult(
                status_code=status.HTTP_201_CREATED,
                body=body,
                target_type="reservation",
                target_id=result.reservation.id,
                headers={
                    "Location": request.build_absolute_uri(
                        reverse("api-v1:reservation-detail", args=[result.reservation.id])
                    )
                },
            )

        return execute_idempotent_mutation(
            request=request,
            owner=request.user,
            api_token=self.api_token,
            action="reservation.create",
            body=serializer.validated_data,
            correlation_id=correlation_id,
            callback=mutate,
        )


class ReservationDetailAPIView(BearerAPIView):
    required_scopes = ("reservations:read",)

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT, 429: OpenApiTypes.OBJECT, 503: OpenApiTypes.OBJECT},
        operation_id="api_v1_reservation_retrieve",
        description="Retrieve one owned reservation by opaque UUID.",
    )
    def get(self, request: Request, reservation_id: uuid.UUID) -> Response:
        correlation_id = correlation_id_from_request(request)
        reservation = _owned_reservation_or_none(reservation_id, request.user)
        if reservation is None:
            return _reservation_not_found_response(request, correlation_id)
        response = Response(reservation_representation(reservation, correlation_id=correlation_id))
        response["X-Request-ID"] = str(correlation_id)
        return response


class ReservationCancelAPIView(BearerAPIView):
    required_scopes = ("reservations:cancel",)

    @extend_schema(
        request=ReservationCancelSerializer,
        responses={200: OpenApiTypes.OBJECT, 429: OpenApiTypes.OBJECT, 503: OpenApiTypes.OBJECT},
        operation_id="api_v1_reservation_cancel",
        parameters=[
            OpenApiParameter("Idempotency-Key", str, OpenApiParameter.HEADER, required=True),
            OpenApiParameter("X-Request-ID", str, OpenApiParameter.HEADER),
        ],
        description="Cancel one owned future reservation through the domain service.",
    )
    def post(self, request: Request, reservation_id: uuid.UUID) -> Response:
        correlation_id = correlation_id_from_request(request)
        if key_problem := _idempotency_header_problem(request, correlation_id):
            return key_problem
        serializer = ReservationCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reservation = _owned_reservation_or_none(reservation_id, request.user)
        if reservation is None:
            return _reservation_not_found_response(request, correlation_id)

        def mutate() -> MutationResult:
            try:
                result = cancel_reservation(
                    reservation=reservation,
                    requested_by_user=request.user,
                    reason=serializer.validated_data["reason"],
                    source=Reservation.SOURCE_API,
                    correlation_id=correlation_id,
                )
            except ReservationDomainError as exc:
                return _domain_mutation_result(exc, correlation_id=correlation_id)
            return MutationResult(
                status_code=status.HTTP_200_OK,
                body=reservation_representation(
                    result.reservation,
                    correlation_id=result.correlation_id,
                ),
                target_type="reservation",
                target_id=result.reservation.id,
            )

        return execute_idempotent_mutation(
            request=request,
            owner=request.user,
            api_token=self.api_token,
            action="reservation.cancel",
            body=serializer.validated_data | {"reservation_id": str(reservation_id)},
            correlation_id=correlation_id,
            callback=mutate,
        )


class ReservationReleaseAPIView(BearerAPIView):
    required_scopes = ("reservations:release",)

    @extend_schema(
        request=EmptyMutationSerializer,
        responses={200: OpenApiTypes.OBJECT, 429: OpenApiTypes.OBJECT, 503: OpenApiTypes.OBJECT},
        operation_id="api_v1_reservation_release",
        parameters=[
            OpenApiParameter("Idempotency-Key", str, OpenApiParameter.HEADER, required=True),
            OpenApiParameter("X-Request-ID", str, OpenApiParameter.HEADER),
        ],
        description="Release one owned active reservation through the domain service.",
    )
    def post(self, request: Request, reservation_id: uuid.UUID) -> Response:
        correlation_id = correlation_id_from_request(request)
        if key_problem := _idempotency_header_problem(request, correlation_id):
            return key_problem
        serializer = EmptyMutationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reservation = _owned_reservation_or_none(reservation_id, request.user)
        if reservation is None:
            return _reservation_not_found_response(request, correlation_id)

        def mutate() -> MutationResult:
            try:
                result = release_reservation(
                    reservation=reservation,
                    requested_by_user=request.user,
                    source=Reservation.SOURCE_API,
                    correlation_id=correlation_id,
                )
            except ReservationDomainError as exc:
                return _domain_mutation_result(exc, correlation_id=correlation_id)
            return MutationResult(
                status_code=status.HTTP_200_OK,
                body=reservation_representation(
                    result.reservation,
                    correlation_id=result.correlation_id,
                ),
                target_type="reservation",
                target_id=result.reservation.id,
            )

        return execute_idempotent_mutation(
            request=request,
            owner=request.user,
            api_token=self.api_token,
            action="reservation.release",
            body={"reservation_id": str(reservation_id)},
            correlation_id=correlation_id,
            callback=mutate,
        )


DOMAIN_STATUS = {
    ASSET_INACTIVE: status.HTTP_409_CONFLICT,
    BOOKING_NOT_AUTHORIZED: status.HTTP_403_FORBIDDEN,
    ASSET_NOT_RESERVABLE: status.HTTP_409_CONFLICT,
    UNSUPPORTED_BOOKING_MODE: status.HTTP_409_CONFLICT,
    POLICY_NOT_CONFIGURED: status.HTTP_409_CONFLICT,
    POLICY_AMBIGUOUS: status.HTTP_409_CONFLICT,
    PRINCIPAL_INACTIVE: status.HTTP_403_FORBIDDEN,
    INVALID_TIME_RANGE: status.HTTP_400_BAD_REQUEST,
    RESERVATION_IN_PAST: status.HTTP_400_BAD_REQUEST,
    LEAD_TIME_VIOLATION: status.HTTP_400_BAD_REQUEST,
    BOOKING_HORIZON_VIOLATION: status.HTTP_400_BAD_REQUEST,
    DURATION_TOO_SHORT: status.HTTP_400_BAD_REQUEST,
    DURATION_TOO_LONG: status.HTTP_400_BAD_REQUEST,
    PURPOSE_REQUIRED: status.HTTP_400_BAD_REQUEST,
    MAX_UPCOMING_EXCEEDED: status.HTTP_409_CONFLICT,
    MAX_CONCURRENT_EXCEEDED: status.HTTP_409_CONFLICT,
    RESERVATION_CONFLICT: status.HTTP_409_CONFLICT,
    BLACKOUT_CONFLICT: status.HTTP_409_CONFLICT,
    RESERVATION_NOT_OWNED: status.HTTP_404_NOT_FOUND,
    RESERVATION_NOT_CANCELLABLE: status.HTTP_409_CONFLICT,
    CANCELLATION_CUTOFF: status.HTTP_409_CONFLICT,
    RESERVATION_NOT_RELEASABLE: status.HTTP_409_CONFLICT,
}


def _apply_reservation_filters(
    queryset: QuerySet[Reservation],
    filters: dict[str, Any],
) -> QuerySet[Reservation]:
    """Apply the validated list filters to an already-chosen queryset.

    The exact filter expressions are shared by the owner-scoped list and
    the authorized cross-user read-all list (``from`` is the lower overlap
    bound ``effective_end_at > from``, ``to`` the upper bound
    ``start_at < to``, strict half-open). Ownership is deliberately NOT
    applied here: each caller selects its own queryset, and the old owner
    builder keeps its unconditional owner filter.
    """
    now = timezone.now()
    if asset_id := filters.get("asset"):
        queryset = queryset.filter(asset_id=asset_id)
    if status_value := filters.get("status"):
        queryset = queryset.filter(status=status_value)
    if start := filters.get("from_at"):
        queryset = queryset.filter(effective_end_at__gt=start)
    if end := filters.get("to"):
        queryset = queryset.filter(start_at__lt=end)
    if lifecycle := filters.get("lifecycle"):
        if lifecycle == "active":
            queryset = queryset.filter(
                status=Reservation.STATUS_CONFIRMED,
                start_at__lte=now,
                effective_end_at__gt=now,
            )
        elif lifecycle == "upcoming":
            queryset = queryset.filter(status=Reservation.STATUS_CONFIRMED, start_at__gt=now)
        elif lifecycle == "completed":
            queryset = queryset.filter(
                status=Reservation.STATUS_CONFIRMED,
                effective_end_at__lte=now,
            )
        elif lifecycle == "cancelled":
            queryset = queryset.filter(status=Reservation.STATUS_CANCELLED)
        elif lifecycle == "released":
            queryset = queryset.filter(status=Reservation.STATUS_RELEASED)
    return queryset


def _filtered_reservations(user: Any, filters: dict[str, Any]) -> QuerySet[Reservation]:
    queryset = (
        Reservation.objects.filter(requested_by_user=user)
        .select_related("asset", "asset__parent", "cancelled_by")
        .order_by("-start_at", "-created_at")
    )
    return _apply_reservation_filters(queryset, filters)


def _idempotency_header_problem(request: Request, correlation_id: uuid.UUID) -> Response | None:
    raw_key = request.headers.get("Idempotency-Key")
    if raw_key is None:
        return problem_response(
            request=request,
            status_code=status.HTTP_400_BAD_REQUEST,
            code="idempotency_required",
            title="Idempotency key required",
            detail="Mutation endpoints require a valid Idempotency-Key header.",
            correlation_id=correlation_id,
        )
    return None


def _asset_or_none(asset_id: uuid.UUID) -> Asset | None:
    return Asset.objects.select_related("parent").filter(pk=asset_id).first()


def _owned_reservation_or_none(reservation_id: uuid.UUID, user: Any) -> Reservation | None:
    return (
        Reservation.objects.select_related("asset", "asset__parent", "cancelled_by")
        .filter(id=reservation_id, requested_by_user=user)
        .first()
    )


def _asset_not_found_response(request: Request, correlation_id: uuid.UUID) -> Response:
    return problem_response(
        request=request,
        status_code=status.HTTP_404_NOT_FOUND,
        code="asset_not_found",
        title="Asset not found",
        detail="The requested asset was not found.",
        correlation_id=correlation_id,
    )


def _reservation_not_found_response(request: Request, correlation_id: uuid.UUID) -> Response:
    return problem_response(
        request=request,
        status_code=status.HTTP_404_NOT_FOUND,
        code="reservation_not_found",
        title="Reservation not found",
        detail="The requested reservation was not found.",
        correlation_id=correlation_id,
    )


def _domain_mutation_result(
    exc: ReservationDomainError,
    *,
    correlation_id: uuid.UUID,
) -> MutationResult:
    status_code = DOMAIN_STATUS.get(exc.code, status.HTTP_400_BAD_REQUEST)
    body = _problem_body(
        status_code=status_code,
        code=exc.code,
        title=_title_for_code(exc.code),
        detail=_detail_for_code(exc.code),
        correlation_id=correlation_id,
    )
    return MutationResult(
        status_code=status_code,
        body=body,
        target_type="reservation_error",
        target_id=None,
    )


def _problem_body(
    *,
    status_code: int,
    code: str,
    title: str,
    detail: str,
    correlation_id: uuid.UUID,
) -> dict[str, Any]:
    return {
        "type": f"https://slaif.local/problems/{code}",
        "title": title,
        "status": status_code,
        "code": code,
        "detail": detail,
        "correlation_id": str(correlation_id),
    }


def _title_for_code(code: str) -> str:
    return code.replace("_", " ").title()


def _detail_for_code(code: str) -> str:
    if code == RESERVATION_CONFLICT:
        return "The requested time is no longer available."
    if code == BOOKING_NOT_AUTHORIZED:
        return "You do not currently have permission to create this reservation."
    if code == BLACKOUT_CONFLICT:
        return "The requested time is unavailable."
    if code == RESERVATION_NOT_OWNED:
        return "The requested reservation was not found."
    return "The reservation request could not be completed."


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    return cast(str, value.astimezone(UTC).isoformat().replace("+00:00", "Z"))
