from __future__ import annotations

from typing import Any

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import CharField, DictField, Serializer
from rest_framework.views import APIView


class ApiRootSerializer(Serializer):  # type: ignore[misc]
    name = CharField(read_only=True)
    version = CharField(read_only=True)
    endpoints = DictField(read_only=True)


class ApiRootView(APIView):  # type: ignore[misc]
    permission_classes = [AllowAny]
    authentication_classes: list[type[Any]] = []

    @extend_schema(responses=ApiRootSerializer)
    def get(self, _request: Request) -> Response:
        return Response(
            {
                "name": "SLAIF Asset Reservation API",
                "version": "v1",
                "endpoints": {
                    "assets": "/api/v1/assets/",
                    "availability": "/api/v1/assets/{asset_id}/availability/",
                    "me": "/api/v1/me/",
                    "reservations": "/api/v1/reservations/",
                    "all_reservations": "/api/v1/all-reservations/",
                },
            }
        )
