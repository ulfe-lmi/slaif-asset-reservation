from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import serializers

from slaif_reservation.accounts.validators import validate_timezone_name
from slaif_reservation.assets.models import Asset
from slaif_reservation.reservations.models import Reservation, derive_lifecycle


class AssetSummarySerializer(serializers.ModelSerializer):  # type: ignore[misc]
    parent = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = ["id", "slug", "name", "kind", "parent", "timezone", "verification_required"]

    def get_parent(self, obj: Asset) -> dict[str, Any] | None:
        if obj.parent_id is None:
            return None
        parent = obj.parent
        assert parent is not None
        return {"id": str(parent.id), "slug": parent.slug, "name": parent.name}


class MeSerializer(serializers.Serializer):  # type: ignore[misc]
    principal = serializers.DictField(read_only=True)
    token = serializers.DictField(read_only=True)


class AvailabilityQuerySerializer(serializers.Serializer):  # type: ignore[misc]
    date = serializers.DateField(required=False)
    days = serializers.IntegerField(required=False, min_value=1, max_value=7, default=7)
    timezone = serializers.CharField(required=False, allow_blank=False, max_length=64)

    def validate_timezone(self, value: str) -> str:
        try:
            validate_timezone_name(value)
        except Exception as exc:
            raise serializers.ValidationError("Enter a valid IANA timezone name.") from exc
        return value


class AwareIsoDateTimeField(serializers.DateTimeField):  # type: ignore[misc]
    def to_internal_value(self, value: Any) -> datetime:
        if not isinstance(value, str):
            raise serializers.ValidationError("Timestamp must be an ISO-8601 string.")
        parsed = parse_datetime(value)
        if parsed is None:
            raise serializers.ValidationError("Timestamp must be a valid ISO-8601 datetime.")
        return _require_aware(parsed)


class ReservationCreateSerializer(serializers.Serializer):  # type: ignore[misc]
    asset_id = serializers.UUIDField()
    start_at = AwareIsoDateTimeField()
    end_at = AwareIsoDateTimeField()
    purpose = serializers.CharField(allow_blank=True, required=False, max_length=1000)

    def validate_start_at(self, value: datetime) -> datetime:
        return _require_aware(value)

    def validate_end_at(self, value: datetime) -> datetime:
        return _require_aware(value)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        attrs["purpose"] = attrs.get("purpose", "")
        unknown = set(getattr(self, "initial_data", {})) - {
            "asset_id",
            "start_at",
            "end_at",
            "purpose",
        }
        if unknown:
            raise serializers.ValidationError("Unknown request field.")
        return attrs


class ReservationCancelSerializer(serializers.Serializer):  # type: ignore[misc]
    reason = serializers.CharField(allow_blank=True, required=False, max_length=1000)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        attrs["reason"] = attrs.get("reason", "")
        unknown = set(getattr(self, "initial_data", {})) - {"reason"}
        if unknown:
            raise serializers.ValidationError("Unknown request field.")
        return attrs


class EmptyMutationSerializer(serializers.Serializer):  # type: ignore[misc]
    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if getattr(self, "initial_data", {}):
            raise serializers.ValidationError("Unknown request field.")
        return attrs


class ReservationListQuerySerializer(serializers.Serializer):  # type: ignore[misc]
    asset = serializers.UUIDField(required=False)
    status = serializers.ChoiceField(
        choices=[choice for choice, _label in Reservation.STATUS_CHOICES],
        required=False,
    )
    lifecycle = serializers.ChoiceField(
        choices=["active", "upcoming", "completed", "cancelled", "released"],
        required=False,
    )
    from_at = AwareIsoDateTimeField(required=False)
    to = AwareIsoDateTimeField(required=False)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        data = kwargs.get("data")
        if data is not None and "from" in data:
            copied = data.copy()
            copied["from_at"] = copied.pop("from")
            kwargs["data"] = copied
        super().__init__(*args, **kwargs)

    def validate_from_at(self, value: datetime) -> datetime:
        return _require_aware(value)

    def validate_to(self, value: datetime) -> datetime:
        return _require_aware(value)


def reservation_representation(
    reservation: Reservation,
    *,
    correlation_id: uuid.UUID | None,
) -> dict[str, Any]:
    return {
        "id": str(reservation.id),
        "asset": AssetSummarySerializer(reservation.asset).data,
        "status": reservation.status,
        "lifecycle": derive_lifecycle(reservation, at=timezone.now()).value,
        "start_at": _iso_utc(reservation.start_at),
        "end_at": _iso_utc(reservation.end_at),
        "effective_end_at": _iso_utc(reservation.effective_end_at),
        "released_at": _iso_utc(reservation.released_at),
        "cancelled_at": _iso_utc(reservation.cancelled_at),
        "cancellation_reason": reservation.cancellation_reason,
        "purpose": reservation.purpose,
        "source": reservation.source,
        "created_at": _iso_utc(reservation.created_at),
        "correlation_id": str(correlation_id) if correlation_id else None,
    }


def availability_representation(result: Any) -> dict[str, Any]:
    return {
        "asset": AssetSummarySerializer(result.asset).data,
        "display_timezone": result.timezone,
        "window": {
            "start": _iso_utc(result.start),
            "end": _iso_utc(result.end),
        },
        "bookable": result.bookable,
        "reason": result.reason,
        "advisory_notice": result.advisory_notice,
        "policy": {
            "min_duration_minutes": result.min_duration_minutes,
        },
        "busy": [
            {
                "start": _iso_utc(interval.start),
                "end": _iso_utc(interval.end),
                "label": interval.label,
                "reservation_id": str(interval.reservation_id) if interval.reservation_id else None,
            }
            for interval in result.busy
        ],
        "free": [
            {
                "start": _iso_utc(interval.start),
                "end": _iso_utc(interval.end),
                "latest_valid_start": _iso_utc(interval.latest_start),
            }
            for interval in result.free
        ],
    }


def _require_aware(value: datetime) -> datetime:
    if not timezone.is_aware(value):
        raise serializers.ValidationError("Timestamp must include an explicit UTC offset.")
    return value.astimezone(UTC)


def _iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if not timezone.is_aware(value):
        return value.replace(tzinfo=ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
