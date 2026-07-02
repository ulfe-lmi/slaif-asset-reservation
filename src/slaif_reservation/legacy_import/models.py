from __future__ import annotations

import uuid
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from slaif_reservation.assets.validators import validate_legacy_metadata
from slaif_reservation.reservations.models import Reservation


class LegacyImportBatch(models.Model):
    MODE_DRY_RUN = "dry_run"
    MODE_APPLY = "apply"
    MODE_CHOICES = [(MODE_DRY_RUN, "Dry-run"), (MODE_APPLY, "Apply")]

    STATUS_PLANNED = "planned"
    STATUS_APPLIED = "applied"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PLANNED, "Planned"),
        (STATUS_APPLIED, "Applied"),
        (STATUS_FAILED, "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_name = models.CharField(max_length=80)
    source_checksum = models.CharField(max_length=64)
    synthetic = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="legacy_import_batches",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    summary = models.JSONField(default=dict, blank=True, validators=[validate_legacy_metadata])
    error_count = models.PositiveIntegerField(default=0)
    warning_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["source_name", "created_at"], name="legacy_batch_source_time_idx"),
            models.Index(fields=["status", "created_at"], name="legacy_batch_status_time_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(mode__in=["dry_run", "apply"]),
                name="legacy_batch_mode_allowed",
            ),
            models.CheckConstraint(
                condition=Q(status__in=["planned", "applied", "failed"]),
                name="legacy_batch_status_allowed",
            ),
            models.CheckConstraint(
                condition=Q(source_checksum__regex=r"^[0-9a-f]{64}$"),
                name="legacy_batch_checksum_sha256",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        validate_legacy_metadata(self.summary)
        if not self.source_name.strip():
            raise ValidationError({"source_name": ["Source name is required."]})


class LegacyImportRecord(models.Model):
    RESULT_IMPORTED = "imported"
    RESULT_ALREADY_IMPORTED = "already_imported"
    RESULT_LEGACY_CHANGED = "legacy_changed"
    RESULT_SKIPPED = "skipped"
    RESULT_CONFLICT = "conflict"
    RESULT_ERROR = "error"
    RESULT_CHOICES = [
        (RESULT_IMPORTED, "Imported"),
        (RESULT_ALREADY_IMPORTED, "Already imported"),
        (RESULT_LEGACY_CHANGED, "Legacy changed"),
        (RESULT_SKIPPED, "Skipped"),
        (RESULT_CONFLICT, "Conflict"),
        (RESULT_ERROR, "Error"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(
        LegacyImportBatch,
        on_delete=models.PROTECT,
        related_name="records",
    )
    legacy_source = models.CharField(max_length=80)
    legacy_id = models.CharField(max_length=160)
    normalized_hash = models.CharField(max_length=64)
    result = models.CharField(max_length=40, choices=RESULT_CHOICES)
    reservation = models.ForeignKey(
        Reservation,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="legacy_import_records",
    )
    safe_metadata = models.JSONField(
        default=dict, blank=True, validators=[validate_legacy_metadata]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["legacy_source", "legacy_id"]
        indexes = [
            models.Index(fields=["legacy_source", "legacy_id"], name="legacy_record_source_id_idx"),
            models.Index(fields=["result", "created_at"], name="legacy_record_result_time_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["legacy_source", "legacy_id"],
                name="legacy_import_unique_source_id",
            ),
            models.CheckConstraint(
                condition=Q(normalized_hash__regex=r"^[0-9a-f]{64}$"),
                name="legacy_record_hash_sha256",
            ),
            models.CheckConstraint(
                condition=Q(
                    result__in=[
                        "imported",
                        "already_imported",
                        "legacy_changed",
                        "skipped",
                        "conflict",
                        "error",
                    ]
                ),
                name="legacy_record_result_allowed",
            ),
        ]

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            raise ValidationError("Legacy import records are append-only.")
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        errors: dict[str, list[str]] = {}
        if not self.legacy_source.strip():
            errors.setdefault("legacy_source", []).append("Legacy source is required.")
        if not self.legacy_id.strip():
            errors.setdefault("legacy_id", []).append("Legacy ID is required.")
        try:
            validate_legacy_metadata(self.safe_metadata)
        except ValidationError as exc:
            errors.setdefault("safe_metadata", []).extend(exc.messages)
        if errors:
            raise ValidationError(errors)
