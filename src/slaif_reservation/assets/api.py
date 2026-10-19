from __future__ import annotations

from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response

from slaif_reservation.api.permissions import IsActiveStaffHuman
from slaif_reservation.assets.models import Asset
from slaif_reservation.assets.selectors import (
    AssetFilterError,
    asset_inventory_queryset,
    parse_asset_filters,
)
from slaif_reservation.assets.serializers import AssetSerializer


class AssetLimitOffsetPagination(LimitOffsetPagination):  # type: ignore[misc]
    default_limit = 50
    max_limit = 100


asset_filter_parameters = [
    OpenApiParameter("kind", str, OpenApiParameter.QUERY, description="Asset kind."),
    OpenApiParameter(
        "parent",
        OpenApiTypes.UUID,
        OpenApiParameter.QUERY,
        description="Parent asset UUID.",
    ),
    OpenApiParameter("tag", str, OpenApiParameter.QUERY, description="Asset tag slug."),
    OpenApiParameter("active", bool, OpenApiParameter.QUERY, description="Filter active assets."),
    OpenApiParameter(
        "reservable",
        bool,
        OpenApiParameter.QUERY,
        description="Filter reservable assets.",
    ),
    OpenApiParameter("q", str, OpenApiParameter.QUERY, description="Safe text search."),
]


class AssetListAPIView(ListAPIView):  # type: ignore[misc]
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsActiveStaffHuman]
    serializer_class = AssetSerializer
    pagination_class = AssetLimitOffsetPagination

    @extend_schema(
        parameters=asset_filter_parameters,
        description=(
            "Staff-session-authenticated asset inventory list. Bearer/API-token "
            "authentication is intentionally deferred."
        ),
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Asset]:
        try:
            filters = parse_asset_filters(self.request.query_params)
        except AssetFilterError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return asset_inventory_queryset(filters)


class AssetDetailAPIView(RetrieveAPIView):  # type: ignore[misc]
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsActiveStaffHuman]
    serializer_class = AssetSerializer
    lookup_url_kwarg = "asset_id"
    lookup_field = "id"

    @extend_schema(
        description=(
            "Staff-session-authenticated asset inventory detail. Internal provenance "
            "and physical locator fields are intentionally omitted."
        )
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Asset]:
        return asset_inventory_queryset()
