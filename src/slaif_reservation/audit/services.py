from __future__ import annotations

import uuid
from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from slaif_reservation.audit.models import AuditEvent

UserModel = get_user_model()


def append_audit_event(
    *,
    action: str,
    target_type: str,
    target_id: uuid.UUID,
    correlation_id: uuid.UUID,
    source: str,
    actor_user: Any | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    with transaction.atomic(savepoint=False):
        event = AuditEvent(
            occurred_at=timezone.now(),
            actor_user=actor_user,
            action=action,
            target_type=target_type,
            target_id=target_id,
            correlation_id=correlation_id,
            source=source,
            metadata=metadata or {},
        )
        event.full_clean()
        event.save()
        return event
