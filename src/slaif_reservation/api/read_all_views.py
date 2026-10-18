"""Explicit read-all cross-user reservation read surface (order 051-a).

Exactly two bearer routes, both GET-only:

- ``GET /api/v1/all-reservations/``
- ``GET /api/v1/all-reservations/<uuid>/``

Both require the ``reservations:read_all`` token scope AND the token
owner's CURRENT ``reservations.view_all_reservations`` application
capability, rechecked per request through the shared active-human helper
BEFORE any reservation row is fetched. There is no process-global grant
cache: the request-time owner instance observes group/permission removal
immediately. No cross-user bearer mutation surface exists here — any
other HTTP verb is refused (405 for an authorized request), and the
owner-scoped endpoints keep their unconditional owner filter.
"""

from __future__ import annotations

import uuid
from typing import Any, cast

from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response

from slaif_reservation.accounts.authorization import has_reservation_permission
from slaif_reservation.api.problem import (
    correlation_id_from_request,
    problem_response,
)
from slaif_reservation.api.reservation_views import (
    ApiLimitOffsetPagination,
    BearerAPIView,
    _apply_reservation_filters,
)
from slaif_reservation.api.serializers import (
    ReadAllReservationDetailSerializer,
    ReadAllReservationListSerializer,
    ReservationListQuerySerializer,
    read_all_reservation_representation,
)
from slaif_reservation.reservations.models import Reservation

READ_ALL_SCOPE = "reservations:read_all"
READ_ALL_CAPABILITY = "view_all_reservations"

_READ_ALL_LIST_PARAMETERS = [
    OpenApiParameter("asset", str, OpenApiParameter.QUERY),
    OpenApiParameter("status", str, OpenApiParameter.QUERY),
    OpenApiParameter("lifecycle", str, OpenApiParameter.QUERY),
    OpenApiParameter("from", str, OpenApiParameter.QUERY),
    OpenApiParameter("to", str, OpenApiParameter.QUERY),
    OpenApiParameter("limit", int, OpenApiParameter.QUERY),
    OpenApiParameter("offset", int, OpenApiParameter.QUERY),
    OpenApiParameter("X-Request-ID", str, OpenApiParameter.HEADER),
]


class ReadAllBearerAPIView(BearerAPIView):
    """Shared base: read_all scope gate, then the owner's CURRENT capability.

    The scope gate is the existing ``HasApiTokenScope`` check (missing
    scope -> ``403 insufficient_scope``); the capability gate uses the
    existing ``PermissionDenied`` -> ``403 permission_denied`` handler.
    Both run before any private query. Every response of these views
    (success, error and 405) carries ``Cache-Control: private,
    no-store`` and a ``Vary`` header including ``Authorization``; old
    endpoint headers are untouched.
    """

    required_scopes: tuple[str, ...] = (READ_ALL_SCOPE,)

    def check_permissions(self, request: Request) -> None:
        super().check_permissions(request)
        if not has_reservation_permission(request.user, READ_ALL_CAPABILITY):
            raise PermissionDenied()

    def finalize_response(
        self, request: Request, response: Response, *args: Any, **kwargs: Any
    ) -> Response:
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        vary = response.get("Vary")
        if vary is None:
            response["Vary"] = "Authorization"
        elif "Authorization" not in vary.split(","):
            response["Vary"] = f"{vary}, Authorization"
        return response


def read_all_reservations_queryset(filters: dict[str, Any]) -> QuerySet[Reservation]:
    """Global (cross-user) list queryset, built only inside authorized views.

    Reuses the exact validated filter expressions through
    :func:`_apply_reservation_filters` on the unfiltered base queryset;
    it includes historical/inactive assets and reservation owners —
    booking-eligibility or account-status changes never delete or rewrite
    accepted records, and the active-human restriction applies to the
    token owner, not to reservation history owners.
    """
    queryset = Reservation.objects.select_related("asset", "requested_by_user").order_by(
        "-start_at", "-created_at"
    )
    return _apply_reservation_filters(queryset, filters)


def read_all_reservation_or_none(reservation_id: uuid.UUID) -> Reservation | None:
    return (
        Reservation.objects.select_related("asset", "requested_by_user")
        .filter(id=reservation_id)
        .first()
    )


def _reservation_not_found(request: Request, correlation_id: uuid.UUID) -> Response:
    return problem_response(
        request=request,
        status_code=404,
        code="reservation_not_found",
        title="Reservation not found",
        detail="The requested reservation was not found.",
        correlation_id=correlation_id,
    )


class AllReservationListAPIView(ReadAllBearerAPIView):
    pagination_class = ApiLimitOffsetPagination

    @extend_schema(
        responses={
            200: ReadAllReservationListSerializer,
            429: OpenApiTypes.OBJECT,
            503: OpenApiTypes.OBJECT,
        },
        operation_id="api_v1_all_reservation_list",
        parameters=_READ_ALL_LIST_PARAMETERS,
        description=(
            "Cross-user reservation list for token owners that currently hold "
            "the view_all_reservations capability. Requires BOTH the "
            "reservations:read_all scope and the current application "
            "capability; read-only with the minimal explicit cross-user "
            "representation. ``from``/``to`` are overlap bounds "
            "(effective_end_at > from, start_at < to)."
        ),
    )
    def get(self, request: Request) -> Response:
        correlation_id = correlation_id_from_request(request)
        serializer = ReservationListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        queryset = read_all_reservations_queryset(serializer.validated_data)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        assert page is not None
        data = [read_all_reservation_representation(reservation) for reservation in page]
        response = paginator.get_paginated_response(data)
        response.data["correlation_id"] = str(correlation_id)
        response["X-Request-ID"] = str(correlation_id)
        return response


class AllReservationDetailAPIView(ReadAllBearerAPIView):
    @extend_schema(
        responses={
            200: ReadAllReservationDetailSerializer,
            429: OpenApiTypes.OBJECT,
            503: OpenApiTypes.OBJECT,
        },
        operation_id="api_v1_all_reservation_retrieve",
        parameters=[OpenApiParameter("X-Request-ID", str, OpenApiParameter.HEADER)],
        description=(
            "One cross-user reservation by opaque UUID for token owners that "
            "currently hold the view_all_reservations capability. Requires "
            "BOTH the reservations:read_all scope and the current application "
            "capability; read-only with the minimal explicit cross-user "
            "representation. Missing UUIDs return 404 reservation_not_found."
        ),
    )
    def get(self, request: Request, reservation_id: uuid.UUID) -> Response:
        correlation_id = correlation_id_from_request(request)
        reservation = read_all_reservation_or_none(reservation_id)
        if reservation is None:
            return _reservation_not_found(request, correlation_id)
        row = read_all_reservation_representation(reservation)
        row["correlation_id"] = str(correlation_id)
        data = ReadAllReservationDetailSerializer(row).data
        response = Response(cast(Any, data))
        response["X-Request-ID"] = str(correlation_id)
        return response
