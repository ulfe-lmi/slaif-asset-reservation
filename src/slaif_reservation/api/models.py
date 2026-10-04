from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class IdempotencyRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="api_idempotency_records",
    )
    api_token = models.ForeignKey(
        "accounts.ApiToken",
        on_delete=models.PROTECT,
        related_name="idempotency_records",
    )
    action = models.CharField(max_length=80)
    idempotency_key = models.CharField(max_length=128)
    canonical_request_hash = models.CharField(max_length=64)
    request_method = models.CharField(max_length=12)
    request_path = models.CharField(max_length=512)
    response_status = models.PositiveSmallIntegerField(null=True, blank=True)
    response_body = models.JSONField(default=dict, blank=True)
    response_headers = models.JSONField(default=dict, blank=True)
    target_type = models.CharField(max_length=80, blank=True)
    target_id = models.UUIDField(null=True, blank=True)
    correlation_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "api_token", "action", "idempotency_key"],
                name="api_idempotency_owner_token_action_key_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["expires_at"], name="api_idempotency_expires_idx"),
            models.Index(
                fields=["owner", "action", "idempotency_key"],
                name="api_idem_owner_action_key_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.action}:{self.idempotency_key}"


class AbuseBucket(models.Model):
    """Expiring shared security counter; keys are scoped HMAC digests."""

    key = models.CharField(primary_key=True, max_length=64)
    count = models.PositiveIntegerField()
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        db_table = "api_abuse_bucket"
