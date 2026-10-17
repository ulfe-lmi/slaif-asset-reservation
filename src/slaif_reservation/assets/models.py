from __future__ import annotations

import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from slaif_reservation.assets.validators import validate_capabilities, validate_legacy_metadata


class AssetTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(unique=True, max_length=80)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["slug"]

    def __str__(self) -> str:
        return self.name


class Asset(models.Model):
    KIND_MACHINE = "machine"
    KIND_GPU = "gpu"
    KIND_CPU_POOL = "cpu_pool"
    KIND_SERVICE = "service"
    KIND_OTHER = "other"
    KIND_CHOICES = [
        (KIND_MACHINE, "Machine"),
        (KIND_GPU, "GPU"),
        (KIND_CPU_POOL, "CPU pool"),
        (KIND_SERVICE, "Service"),
        (KIND_OTHER, "Other"),
    ]

    BOOKING_EXCLUSIVE = "exclusive"
    BOOKING_MODE_CHOICES = [(BOOKING_EXCLUSIVE, "Exclusive")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="children",
    )
    slug = models.SlugField(unique=True, max_length=120)
    name = models.CharField(max_length=180)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    booking_mode = models.CharField(
        max_length=20,
        choices=BOOKING_MODE_CHOICES,
        default=BOOKING_EXCLUSIVE,
    )
    description = models.TextField(blank=True)
    location = models.CharField(max_length=180, blank=True)
    timezone = models.CharField(max_length=64, default="Europe/Ljubljana")
    active = models.BooleanField(default=True)
    reservable = models.BooleanField(default=False)
    booking_restricted = models.BooleanField(
        default=False,
        help_text=(
            "Restrict booking of this asset to members of the "
            "selected allowed groups. Unrestricted assets remain "
            "bookable by any user holding the booking permission."
        ),
    )
    allowed_booking_groups = models.ManyToManyField(
        "auth.Group",
        blank=True,
        related_name="allowed_booking_assets",
        help_text=(
            "Existing permission groups whose members may book "
            "this asset while it is restricted. Membership in any "
            "one selected group is sufficient. Ignored while the "
            "asset is unrestricted."
        ),
    )
    capabilities = models.JSONField(default=dict, blank=True, validators=[validate_capabilities])
    verification_required = models.BooleanField(default=True)
    physical_locator = models.CharField(max_length=180, blank=True)
    legacy_source = models.CharField(max_length=80, null=True, blank=True)  # noqa: DJ001
    legacy_id = models.CharField(max_length=160, null=True, blank=True)  # noqa: DJ001
    legacy_metadata = models.JSONField(
        default=dict,
        blank=True,
        validators=[validate_legacy_metadata],
    )
    tags = models.ManyToManyField(AssetTag, blank=True, related_name="assets")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["slug"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(parent=F("id")),
                name="asset_parent_not_self",
            ),
            models.CheckConstraint(
                condition=~Q(kind="machine") | Q(parent__isnull=True),
                name="asset_machine_has_no_parent",
            ),
            models.CheckConstraint(
                condition=Q(active=True) | Q(reservable=False),
                name="asset_inactive_not_reservable",
            ),
            models.CheckConstraint(
                condition=(
                    Q(legacy_source__isnull=True, legacy_id__isnull=True)
                    | Q(legacy_source__isnull=False, legacy_id__isnull=False)
                ),
                name="asset_legacy_source_id_paired",
            ),
            models.CheckConstraint(
                condition=(
                    Q(legacy_source__isnull=True, legacy_id__isnull=True)
                    | (
                        Q(legacy_source__isnull=False, legacy_id__isnull=False)
                        & Q(legacy_source__regex=r"\S")
                        & Q(legacy_id__regex=r"\S")
                    )
                ),
                name="asset_legacy_source_id_meaningful",
            ),
            models.CheckConstraint(
                condition=Q(booking_mode="exclusive"),
                name="asset_booking_mode_exclusive_only",
            ),
            models.CheckConstraint(
                condition=Q(
                    kind__in=[
                        "machine",
                        "gpu",
                        "cpu_pool",
                        "service",
                        "other",
                    ]
                ),
                name="asset_kind_allowed",
            ),
            models.UniqueConstraint(
                fields=["legacy_source", "legacy_id"],
                condition=Q(legacy_source__isnull=False, legacy_id__isnull=False),
                name="asset_unique_legacy_source_id",
            ),
        ]

    def __str__(self) -> str:
        if self.parent_id:
            return f"{self.parent} / {self.name}"
        return self.name

    def clean(self) -> None:
        super().clean()
        errors: dict[str, list[str]] = {}

        if self.parent_id and self.id and self.parent_id == self.id:
            errors.setdefault("parent", []).append("An asset cannot parent itself.")

        if self.kind == self.KIND_MACHINE and self.parent_id:
            errors.setdefault("parent", []).append("Machine assets cannot have a parent.")

        if self.parent is not None:
            if self.parent.kind != self.KIND_MACHINE:
                errors.setdefault("parent", []).append("A child asset parent must be a machine.")
            if self.parent.parent_id is not None:
                errors.setdefault("parent", []).append(
                    "Asset hierarchy is limited to machine -> child."
                )

        if not self.active and self.reservable:
            errors.setdefault("reservable", []).append("Inactive assets cannot be reservable.")

        source_present = self.legacy_source is not None
        legacy_id_present = self.legacy_id is not None
        if source_present != legacy_id_present:
            errors.setdefault("legacy_id", []).append("Legacy source and legacy ID must be paired.")
        elif source_present and legacy_id_present:
            assert self.legacy_source is not None
            assert self.legacy_id is not None
            if not self.legacy_source.strip() or not self.legacy_id.strip():
                errors.setdefault("legacy_id", []).append(
                    "Legacy source and legacy ID must be non-empty strings."
                )

        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError:
            errors.setdefault("timezone", []).append("Timezone must resolve through zoneinfo.")

        if self.booking_mode != self.BOOKING_EXCLUSIVE:
            errors.setdefault("booking_mode", []).append("Unsupported booking mode.")

        try:
            validate_capabilities(self.capabilities)
        except ValidationError as exc:
            errors.setdefault("capabilities", []).extend(exc.messages)

        try:
            validate_legacy_metadata(self.legacy_metadata)
        except ValidationError as exc:
            errors.setdefault("legacy_metadata", []).extend(exc.messages)

        if errors:
            raise ValidationError(errors)
