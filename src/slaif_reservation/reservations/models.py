from __future__ import annotations

import uuid
from typing import Any

from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeBoundary, RangeOperators
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q, Value
from django.db.models.expressions import Func

from slaif_reservation.assets.models import Asset


class TsTzRange(Func):
    function = "TSTZRANGE"
    output_field = DateTimeRangeField()


class ReservationPolicy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=180)
    asset = models.ForeignKey(
        Asset,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reservation_policies",
    )
    active = models.BooleanField(default=True)
    min_duration_minutes = models.PositiveIntegerField()
    max_duration_minutes = models.PositiveIntegerField()
    booking_horizon_days = models.PositiveIntegerField()
    min_lead_minutes = models.PositiveIntegerField(default=0)
    cancellation_cutoff_minutes = models.PositiveIntegerField(default=0)
    max_upcoming_per_principal = models.PositiveIntegerField()
    max_concurrent_per_principal = models.PositiveIntegerField()
    purpose_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(min_duration_minutes__gte=1),
                name="reservation_policy_min_duration_gte_1",
            ),
            models.CheckConstraint(
                condition=Q(max_duration_minutes__gte=F("min_duration_minutes")),
                name="reservation_policy_max_duration_gte_min",
            ),
            models.CheckConstraint(
                condition=Q(booking_horizon_days__gte=0),
                name="reservation_policy_horizon_gte_0",
            ),
            models.CheckConstraint(
                condition=Q(min_lead_minutes__gte=0),
                name="reservation_policy_lead_gte_0",
            ),
            models.CheckConstraint(
                condition=Q(cancellation_cutoff_minutes__gte=0),
                name="reservation_policy_cutoff_gte_0",
            ),
            models.CheckConstraint(
                condition=Q(max_upcoming_per_principal__gte=1),
                name="reservation_policy_upcoming_gte_1",
            ),
            models.CheckConstraint(
                condition=Q(max_concurrent_per_principal__gte=1),
                name="reservation_policy_concurrent_gte_1",
            ),
            models.UniqueConstraint(
                fields=["asset"],
                condition=Q(active=True, asset__isnull=False),
                name="reservation_policy_one_active_per_asset",
            ),
            models.UniqueConstraint(
                Value(1),
                condition=Q(active=True, asset__isnull=True),
                name="reservation_policy_one_active_global",
            ),
        ]

    def __str__(self) -> str:
        if self.asset_id:
            return f"{self.name} ({self.asset})"
        return f"{self.name} (global)"

    def clean(self) -> None:
        super().clean()
        errors: dict[str, list[str]] = {}
        if self.asset is not None and self.asset.kind not in {Asset.KIND_MACHINE, Asset.KIND_GPU}:
            errors.setdefault("asset", []).append(
                "Policy asset target must be a machine or child asset."
            )
        if self.min_duration_minutes < 1:
            errors.setdefault("min_duration_minutes", []).append("Minimum duration must be >= 1.")
        if self.max_duration_minutes < self.min_duration_minutes:
            errors.setdefault("max_duration_minutes", []).append(
                "Maximum duration must be >= minimum duration."
            )
        if self.max_upcoming_per_principal < 1:
            errors.setdefault("max_upcoming_per_principal", []).append(
                "Upcoming limit must be >= 1."
            )
        if self.max_concurrent_per_principal < 1:
            errors.setdefault("max_concurrent_per_principal", []).append(
                "Concurrent limit must be >= 1."
            )
        if errors:
            raise ValidationError(errors)


class Reservation(models.Model):
    SOURCE_WEB = "web"
    SOURCE_API = "api"
    SOURCE_ADMIN = "admin"
    SOURCE_MIGRATION = "migration"
    SOURCE_CHOICES = [
        (SOURCE_WEB, "Web"),
        (SOURCE_API, "API"),
        (SOURCE_ADMIN, "Admin"),
        (SOURCE_MIGRATION, "Migration"),
    ]

    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"
    STATUS_RELEASED = "released"
    STATUS_CHOICES = [
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_RELEASED, "Released"),
    ]

    EXCLUSION_CONSTRAINT_NAME = "reservation_no_overlap_per_asset"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="reservations")
    requested_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reservations",
    )
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CONFIRMED)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    effective_end_at = models.DateTimeField()
    purpose = models.TextField(blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="cancelled_reservations",
    )
    cancellation_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_at", "id"]
        indexes = [
            models.Index(
                fields=["asset", "start_at", "effective_end_at"], name="reservation_asset_time_idx"
            ),
            models.Index(
                fields=["requested_by_user", "start_at"], name="reservation_user_time_idx"
            ),
            models.Index(
                fields=["status", "start_at", "effective_end_at"],
                name="reservation_status_time_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(source__in=["web", "api", "admin", "migration"]),
                name="reservation_source_allowed",
            ),
            models.CheckConstraint(
                condition=Q(status__in=["confirmed", "cancelled", "released"]),
                name="reservation_status_allowed",
            ),
            models.CheckConstraint(
                condition=Q(end_at__gt=F("start_at")), name="reservation_end_gt_start"
            ),
            models.CheckConstraint(
                condition=Q(effective_end_at__gt=F("start_at")),
                name="reservation_effective_end_gt_start",
            ),
            models.CheckConstraint(
                condition=Q(effective_end_at__lte=F("end_at")),
                name="reservation_effective_end_lte_end",
            ),
            models.CheckConstraint(
                condition=(
                    ~Q(status="confirmed")
                    | (
                        Q(effective_end_at=F("end_at"))
                        & Q(cancelled_at__isnull=True)
                        & Q(cancelled_by__isnull=True)
                        & Q(released_at__isnull=True)
                        & Q(cancellation_reason="")
                    )
                ),
                name="reservation_confirmed_fields_valid",
            ),
            models.CheckConstraint(
                condition=(
                    ~Q(status="cancelled")
                    | (
                        Q(cancelled_at__isnull=False)
                        & Q(cancelled_by__isnull=False)
                        & Q(released_at__isnull=True)
                        & Q(effective_end_at=F("end_at"))
                    )
                ),
                name="reservation_cancelled_fields_valid",
            ),
            models.CheckConstraint(
                condition=(
                    ~Q(status="released")
                    | (
                        Q(released_at__isnull=False)
                        & Q(cancelled_at__isnull=True)
                        & Q(cancelled_by__isnull=True)
                        & Q(cancellation_reason="")
                        & Q(effective_end_at=F("released_at"))
                        & Q(released_at__gt=F("start_at"))
                        & Q(released_at__lt=F("end_at"))
                    )
                ),
                name="reservation_released_fields_valid",
            ),
            ExclusionConstraint(
                name="reservation_no_overlap_per_asset",
                expressions=[
                    ("asset", RangeOperators.EQUAL),
                    (
                        TsTzRange("start_at", "effective_end_at", RangeBoundary()),
                        RangeOperators.OVERLAPS,
                    ),
                ],
                condition=Q(status__in=["confirmed", "released"]),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.asset} {self.start_at.isoformat()}-{self.effective_end_at.isoformat()}"

    def clean(self) -> None:
        super().clean()
        errors: dict[str, list[str]] = {}
        for field in ("start_at", "end_at", "effective_end_at", "released_at", "cancelled_at"):
            value = getattr(self, field)
            if value is not None and value.tzinfo is None:
                errors.setdefault(field, []).append("Timestamp must be timezone-aware.")

        if self.end_at <= self.start_at:
            errors.setdefault("end_at", []).append("End must be after start.")
        if self.effective_end_at <= self.start_at:
            errors.setdefault("effective_end_at", []).append("Effective end must be after start.")
        if self.effective_end_at > self.end_at:
            errors.setdefault("effective_end_at", []).append("Effective end cannot exceed end.")
        if self.source not in {
            self.SOURCE_WEB,
            self.SOURCE_API,
            self.SOURCE_ADMIN,
            self.SOURCE_MIGRATION,
        }:
            errors.setdefault("source", []).append("Unsupported reservation source.")
        if self.status not in {self.STATUS_CONFIRMED, self.STATUS_CANCELLED, self.STATUS_RELEASED}:
            errors.setdefault("status", []).append("Unsupported reservation status.")

        if self.status == self.STATUS_CONFIRMED:
            if self.effective_end_at != self.end_at:
                errors.setdefault("effective_end_at", []).append(
                    "Confirmed reservations end at end_at."
                )
            if (
                self.cancelled_at
                or self.cancelled_by_id
                or self.released_at
                or self.cancellation_reason
            ):
                errors.setdefault("status", []).append(
                    "Confirmed reservations cannot have terminal fields."
                )
        elif self.status == self.STATUS_CANCELLED:
            if not self.cancelled_at or not self.cancelled_by_id:
                errors.setdefault("cancelled_at", []).append(
                    "Cancelled reservations require cancelled_at and cancelled_by."
                )
            if self.released_at:
                errors.setdefault("released_at", []).append(
                    "Cancelled reservations cannot be released."
                )
            if self.effective_end_at != self.end_at:
                errors.setdefault("effective_end_at", []).append(
                    "Cancelled reservations keep original end."
                )
        elif self.status == self.STATUS_RELEASED:
            if not self.released_at:
                errors.setdefault("released_at", []).append(
                    "Released reservations require released_at."
                )
            elif not (self.start_at < self.released_at < self.end_at):
                errors.setdefault("released_at", []).append(
                    "Release must be within the reservation."
                )
            if self.cancelled_at or self.cancelled_by_id or self.cancellation_reason:
                errors.setdefault("status", []).append(
                    "Released reservations cannot have cancellation fields."
                )
            if self.released_at and self.effective_end_at != self.released_at:
                errors.setdefault("effective_end_at", []).append(
                    "Released reservations end at released_at."
                )

        if errors:
            raise ValidationError(errors)


class ReservationLifecycle(models.TextChoices):
    UPCOMING = "upcoming", "Upcoming"
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    RELEASED = "released", "Released"


def derive_lifecycle(reservation: Reservation, *, at: Any) -> ReservationLifecycle:
    if reservation.status == Reservation.STATUS_CANCELLED:
        return ReservationLifecycle.CANCELLED
    if reservation.status == Reservation.STATUS_RELEASED:
        return ReservationLifecycle.RELEASED
    if reservation.start_at > at:
        return ReservationLifecycle.UPCOMING
    if reservation.effective_end_at <= at:
        return ReservationLifecycle.COMPLETED
    return ReservationLifecycle.ACTIVE
