from __future__ import annotations

import uuid
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from slaif_reservation.audit.validators import validate_audit_metadata


class AuditEventQuerySet(models.QuerySet["AuditEvent"]):
    def bulk_create(self, objs: Any, *args: Any, **kwargs: Any) -> Any:
        raise ValidationError("Audit events are append-only.")

    async def abulk_create(self, objs: Any, *args: Any, **kwargs: Any) -> Any:
        raise ValidationError("Audit events are append-only.")

    def update(self, **kwargs: Any) -> int:
        raise ValidationError("Audit events are append-only.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ValidationError("Audit events are append-only.")


AuditEventManagerBase = models.Manager.from_queryset(AuditEventQuerySet)


class AuditEventManager(AuditEventManagerBase["AuditEvent"]):
    def bulk_create(self, objs: Any, *args: Any, **kwargs: Any) -> Any:
        raise ValidationError("Audit events are append-only.")

    async def abulk_create(self, objs: Any, *args: Any, **kwargs: Any) -> Any:
        raise ValidationError("Audit events are append-only.")

    def bulk_update(
        self,
        objs: Any,
        fields: Any,
        batch_size: int | None = None,
    ) -> int:
        raise ValidationError("Audit events are append-only.")


class AuditEvent(models.Model):
    ACTION_RESERVATION_CREATED = "reservation.created"
    ACTION_RESERVATION_CANCELLED = "reservation.cancelled"
    ACTION_RESERVATION_RELEASED = "reservation.released"
    ACTION_POLICY_CREATED = "reservation_policy.created"
    ACTION_POLICY_UPDATED = "reservation_policy.updated"
    ACTION_POLICY_DEACTIVATED = "reservation_policy.deactivated"
    ACTION_API_TOKEN_CREATED = "api_token.created"
    ACTION_API_TOKEN_REVOKED = "api_token.revoked"
    ACTION_CHOICES = [
        (ACTION_RESERVATION_CREATED, "Reservation created"),
        (ACTION_RESERVATION_CANCELLED, "Reservation cancelled"),
        (ACTION_RESERVATION_RELEASED, "Reservation released"),
        (ACTION_POLICY_CREATED, "Reservation policy created"),
        (ACTION_POLICY_UPDATED, "Reservation policy updated"),
        (ACTION_POLICY_DEACTIVATED, "Reservation policy deactivated"),
        (ACTION_API_TOKEN_CREATED, "API token created"),
        (ACTION_API_TOKEN_REVOKED, "API token revoked"),
    ]

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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    occurred_at = models.DateTimeField()
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="audit_events",
    )
    action = models.CharField(max_length=80, choices=ACTION_CHOICES)
    target_type = models.CharField(max_length=80)
    target_id = models.UUIDField()
    correlation_id = models.UUIDField()
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    metadata = models.JSONField(default=dict, blank=True, validators=[validate_audit_metadata])

    objects = AuditEventManager()

    class Meta:
        ordering = ["-occurred_at", "-id"]
        indexes = [
            models.Index(fields=["target_type", "target_id"], name="audit_target_idx"),
            models.Index(fields=["correlation_id"], name="audit_correlation_idx"),
            models.Index(fields=["action", "occurred_at"], name="audit_action_time_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    action__in=[
                        "reservation.created",
                        "reservation.cancelled",
                        "reservation.released",
                        "reservation_policy.created",
                        "reservation_policy.updated",
                        "reservation_policy.deactivated",
                        "api_token.created",
                        "api_token.revoked",
                    ]
                ),
                name="audit_event_action_allowed",
            ),
            models.CheckConstraint(
                condition=models.Q(source__in=["web", "api", "admin", "migration"]),
                name="audit_event_source_allowed",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.action} {self.target_type}:{self.target_id}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self._state.adding and self.pk and type(self)._base_manager.filter(pk=self.pk).exists():
            raise ValidationError("Audit events are append-only.")
        if not self._state.adding and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Audit events are append-only.")
        if self._state.adding:
            self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: object, **kwargs: object) -> tuple[int, dict[str, int]]:
        raise ValidationError("Audit events are append-only.")

    def clean(self) -> None:
        super().clean()
        validate_audit_metadata(self.metadata)
