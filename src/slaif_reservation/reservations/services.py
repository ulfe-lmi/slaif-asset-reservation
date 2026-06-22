from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.audit.services import append_audit_event
from slaif_reservation.reservations.exceptions import (
    ASSET_INACTIVE,
    ASSET_NOT_RESERVABLE,
    BOOKING_HORIZON_VIOLATION,
    CANCELLATION_CUTOFF,
    DURATION_TOO_LONG,
    DURATION_TOO_SHORT,
    INVALID_TIME_RANGE,
    LEAD_TIME_VIOLATION,
    MAX_CONCURRENT_EXCEEDED,
    MAX_UPCOMING_EXCEEDED,
    POLICY_AMBIGUOUS,
    POLICY_NOT_CONFIGURED,
    PRINCIPAL_INACTIVE,
    PURPOSE_REQUIRED,
    RESERVATION_CONFLICT,
    RESERVATION_IN_PAST,
    RESERVATION_NOT_CANCELLABLE,
    RESERVATION_NOT_OWNED,
    RESERVATION_NOT_RELEASABLE,
    UNSUPPORTED_BOOKING_MODE,
    ReservationDomainError,
)
from slaif_reservation.reservations.models import Reservation, ReservationPolicy

UserModel = get_user_model()


@dataclass(frozen=True)
class ReservationMutationResult:
    reservation: Reservation
    correlation_id: uuid.UUID


@dataclass(frozen=True)
class PolicyMutationResult:
    policy: ReservationPolicy
    correlation_id: uuid.UUID


def _correlation(value: uuid.UUID | None) -> uuid.UUID:
    return value or uuid.uuid4()


def _raise(code: str, message: str) -> None:
    raise ReservationDomainError(code, message)


def _lock_principal(principal: Any) -> Any:
    locked = UserModel.objects.select_for_update().get(pk=principal.pk)
    if not locked.is_active:
        _raise(PRINCIPAL_INACTIVE, "Principal is inactive.")
    return locked


def _lock_asset(asset: Asset) -> Asset:
    locked = Asset.objects.select_for_update().get(pk=asset.pk)
    if locked.parent_id:
        locked.parent = Asset.objects.get(pk=locked.parent_id)
    return locked


def _validate_asset(asset: Asset) -> None:
    if not asset.active:
        _raise(ASSET_INACTIVE, "Asset is inactive.")
    if not asset.reservable:
        _raise(ASSET_NOT_RESERVABLE, "Asset is not reservable.")
    if asset.booking_mode != Asset.BOOKING_EXCLUSIVE:
        _raise(UNSUPPORTED_BOOKING_MODE, "Only exclusive assets are supported.")


def _asset_for_reservation(reservation: Reservation) -> Asset:
    asset = Asset.objects.get(pk=reservation.asset_id)
    if asset.parent_id:
        asset.parent = Asset.objects.get(pk=asset.parent_id)
    return asset


def _active_policies_for(query: Q) -> list[ReservationPolicy]:
    return list(ReservationPolicy.objects.filter(active=True).filter(query)[:2])


def resolve_effective_policy(asset: Asset) -> ReservationPolicy:
    candidates: list[tuple[str, Q]] = [("asset", Q(asset=asset))]
    if asset.parent_id:
        candidates.append(("parent", Q(asset=asset.parent)))
    candidates.append(("global", Q(asset__isnull=True)))

    for _level, query in candidates:
        policies = _active_policies_for(query)
        if len(policies) > 1:
            _raise(POLICY_AMBIGUOUS, "Multiple active policies match at the same priority.")
        if len(policies) == 1:
            return policies[0]

    _raise(POLICY_NOT_CONFIGURED, "No active reservation policy applies to this asset.")
    raise AssertionError("unreachable")


def _validate_time_range(start_at: datetime, end_at: datetime, now: datetime) -> timedelta:
    if start_at.tzinfo is None or end_at.tzinfo is None:
        _raise(INVALID_TIME_RANGE, "Reservation timestamps must be timezone-aware.")
    if end_at <= start_at:
        _raise(INVALID_TIME_RANGE, "Reservation end must be after start.")
    if start_at < now:
        _raise(RESERVATION_IN_PAST, "Reservations cannot start in the past.")
    return end_at - start_at


def _enforce_policy(
    *,
    policy: ReservationPolicy,
    principal: Any,
    start_at: Any,
    end_at: Any,
    purpose: str,
    now: Any,
) -> None:
    duration = _validate_time_range(start_at, end_at, now)
    duration_minutes = duration.total_seconds() / 60
    if duration_minutes < policy.min_duration_minutes:
        _raise(DURATION_TOO_SHORT, "Reservation duration is shorter than the policy minimum.")
    if duration_minutes > policy.max_duration_minutes:
        _raise(DURATION_TOO_LONG, "Reservation duration exceeds the policy maximum.")
    if start_at < now + timedelta(minutes=policy.min_lead_minutes):
        _raise(LEAD_TIME_VIOLATION, "Reservation starts before the policy lead time.")
    if start_at > now + timedelta(days=policy.booking_horizon_days):
        _raise(BOOKING_HORIZON_VIOLATION, "Reservation starts beyond the policy horizon.")
    if policy.purpose_required and not purpose.strip():
        _raise(PURPOSE_REQUIRED, "Reservation purpose is required by policy.")

    upcoming_count = Reservation.objects.filter(
        requested_by_user=principal,
        status=Reservation.STATUS_CONFIRMED,
        start_at__gte=now,
    ).count()
    if upcoming_count >= policy.max_upcoming_per_principal:
        _raise(MAX_UPCOMING_EXCEEDED, "Principal has too many upcoming reservations.")

    concurrent_count = Reservation.objects.filter(
        requested_by_user=principal,
        status__in=[Reservation.STATUS_CONFIRMED, Reservation.STATUS_RELEASED],
        start_at__lt=end_at,
        effective_end_at__gt=start_at,
    ).count()
    if concurrent_count >= policy.max_concurrent_per_principal:
        _raise(MAX_CONCURRENT_EXCEEDED, "Principal has too many concurrent reservations.")


def _raise_if_asset_overlap(asset: Asset, start_at: Any, end_at: Any) -> None:
    if Reservation.objects.filter(
        asset=asset,
        status__in=[Reservation.STATUS_CONFIRMED, Reservation.STATUS_RELEASED],
        start_at__lt=end_at,
        effective_end_at__gt=start_at,
    ).exists():
        _raise(RESERVATION_CONFLICT, "Reservation conflicts with an existing reservation.")


def _is_named_reservation_constraint(exc: IntegrityError) -> bool:
    cause = getattr(exc, "__cause__", None)
    constraint_name = getattr(getattr(cause, "diag", None), "constraint_name", None)
    if constraint_name == Reservation.EXCLUSION_CONSTRAINT_NAME:
        return True
    return Reservation.EXCLUSION_CONSTRAINT_NAME in str(exc)


def create_reservation(
    *,
    asset: Asset,
    requested_by_user: Any,
    start_at: Any,
    end_at: Any,
    purpose: str,
    source: str = Reservation.SOURCE_WEB,
    now: Any | None = None,
    correlation_id: uuid.UUID | None = None,
) -> ReservationMutationResult:
    now = now or timezone.now()
    correlation = _correlation(correlation_id)

    with transaction.atomic():
        principal = _lock_principal(requested_by_user)
        locked_asset = _lock_asset(asset)
        _validate_asset(locked_asset)
        policy = resolve_effective_policy(locked_asset)
        _enforce_policy(
            policy=policy,
            principal=principal,
            start_at=start_at,
            end_at=end_at,
            purpose=purpose,
            now=now,
        )
        _raise_if_asset_overlap(locked_asset, start_at, end_at)

        reservation = Reservation(
            asset=locked_asset,
            requested_by_user=principal,
            source=source,
            status=Reservation.STATUS_CONFIRMED,
            start_at=start_at,
            end_at=end_at,
            effective_end_at=end_at,
            purpose=purpose,
        )
        reservation.full_clean()

        try:
            with transaction.atomic():
                reservation.save()
        except IntegrityError as exc:
            if _is_named_reservation_constraint(exc):
                _raise(
                    RESERVATION_CONFLICT,
                    "Reservation conflicts with an existing reservation.",
                )
            raise

        append_audit_event(
            action=AuditEvent.ACTION_RESERVATION_CREATED,
            target_type="reservation",
            target_id=reservation.id,
            correlation_id=correlation,
            source=source,
            actor_user=principal,
            metadata={
                "asset_id": str(locked_asset.id),
                "start_at": start_at.isoformat(),
                "end_at": end_at.isoformat(),
            },
        )
        return ReservationMutationResult(reservation=reservation, correlation_id=correlation)


def _authorized_for_existing_reservation(requester: Any, reservation: Reservation) -> bool:
    return bool(requester.is_staff or requester.pk == reservation.requested_by_user_id)


def cancel_reservation(
    *,
    reservation: Reservation,
    requested_by_user: Any,
    reason: str = "",
    source: str = Reservation.SOURCE_WEB,
    now: Any | None = None,
    correlation_id: uuid.UUID | None = None,
) -> ReservationMutationResult:
    now = now or timezone.now()
    correlation = _correlation(correlation_id)

    with transaction.atomic():
        requester = _lock_principal(requested_by_user)
        locked = (
            Reservation.objects.select_for_update()
            .select_related("requested_by_user")
            .get(pk=reservation.pk)
        )
        if not _authorized_for_existing_reservation(requester, locked):
            _raise(RESERVATION_NOT_OWNED, "Requester cannot cancel this reservation.")
        if locked.status != Reservation.STATUS_CONFIRMED or locked.start_at <= now:
            _raise(RESERVATION_NOT_CANCELLABLE, "Reservation is not cancellable.")
        policy = resolve_effective_policy(_asset_for_reservation(locked))
        cutoff_at = locked.start_at - timedelta(minutes=policy.cancellation_cutoff_minutes)
        if now > cutoff_at:
            _raise(CANCELLATION_CUTOFF, "Reservation is past the cancellation cutoff.")

        locked.status = Reservation.STATUS_CANCELLED
        locked.cancelled_at = now
        locked.cancelled_by = requester
        locked.cancellation_reason = reason
        locked.effective_end_at = locked.end_at
        locked.full_clean()
        locked.save()
        append_audit_event(
            action=AuditEvent.ACTION_RESERVATION_CANCELLED,
            target_type="reservation",
            target_id=locked.id,
            correlation_id=correlation,
            source=source,
            actor_user=requester,
            metadata={"asset_id": str(locked.asset_id)},
        )
        return ReservationMutationResult(reservation=locked, correlation_id=correlation)


def release_reservation(
    *,
    reservation: Reservation,
    requested_by_user: Any,
    source: str = Reservation.SOURCE_WEB,
    now: Any | None = None,
    correlation_id: uuid.UUID | None = None,
) -> ReservationMutationResult:
    now = now or timezone.now()
    correlation = _correlation(correlation_id)

    with transaction.atomic():
        requester = _lock_principal(requested_by_user)
        locked = (
            Reservation.objects.select_for_update()
            .select_related("requested_by_user")
            .get(pk=reservation.pk)
        )
        if not _authorized_for_existing_reservation(requester, locked):
            _raise(RESERVATION_NOT_OWNED, "Requester cannot release this reservation.")
        if locked.status != Reservation.STATUS_CONFIRMED or not (
            locked.start_at < now < locked.effective_end_at
        ):
            _raise(RESERVATION_NOT_RELEASABLE, "Reservation is not releasable.")
        resolve_effective_policy(_asset_for_reservation(locked))

        locked.status = Reservation.STATUS_RELEASED
        locked.released_at = now
        locked.effective_end_at = now
        locked.full_clean()
        locked.save()
        append_audit_event(
            action=AuditEvent.ACTION_RESERVATION_RELEASED,
            target_type="reservation",
            target_id=locked.id,
            correlation_id=correlation,
            source=source,
            actor_user=requester,
            metadata={"asset_id": str(locked.asset_id), "released_at": now.isoformat()},
        )
        return ReservationMutationResult(reservation=locked, correlation_id=correlation)


def create_policy(
    *,
    actor_user: Any,
    source: str = AuditEvent.SOURCE_ADMIN,
    correlation_id: uuid.UUID | None = None,
    **values: Any,
) -> PolicyMutationResult:
    correlation = _correlation(correlation_id)
    with transaction.atomic():
        actor = _lock_principal(actor_user)
        policy = ReservationPolicy(**values)
        policy.full_clean()
        policy.save()
        append_audit_event(
            action=AuditEvent.ACTION_POLICY_CREATED,
            target_type="reservation_policy",
            target_id=policy.id,
            correlation_id=correlation,
            source=source,
            actor_user=actor,
            metadata={"asset_id": str(policy.asset_id) if policy.asset_id else None},
        )
        return PolicyMutationResult(policy=policy, correlation_id=correlation)


def update_policy(
    *,
    policy: ReservationPolicy,
    actor_user: Any,
    source: str = AuditEvent.SOURCE_ADMIN,
    correlation_id: uuid.UUID | None = None,
    **values: Any,
) -> PolicyMutationResult:
    correlation = _correlation(correlation_id)
    with transaction.atomic():
        actor = _lock_principal(actor_user)
        locked = ReservationPolicy.objects.select_for_update().get(pk=policy.pk)
        for field, value in values.items():
            setattr(locked, field, value)
        locked.full_clean()
        locked.save()
        append_audit_event(
            action=AuditEvent.ACTION_POLICY_UPDATED,
            target_type="reservation_policy",
            target_id=locked.id,
            correlation_id=correlation,
            source=source,
            actor_user=actor,
            metadata={"asset_id": str(locked.asset_id) if locked.asset_id else None},
        )
        return PolicyMutationResult(policy=locked, correlation_id=correlation)


def deactivate_policy(
    *,
    policy: ReservationPolicy,
    actor_user: Any,
    source: str = AuditEvent.SOURCE_ADMIN,
    correlation_id: uuid.UUID | None = None,
) -> PolicyMutationResult:
    correlation = _correlation(correlation_id)
    with transaction.atomic():
        actor = _lock_principal(actor_user)
        locked = ReservationPolicy.objects.select_for_update().get(pk=policy.pk)
        locked.active = False
        locked.full_clean()
        locked.save()
        append_audit_event(
            action=AuditEvent.ACTION_POLICY_DEACTIVATED,
            target_type="reservation_policy",
            target_id=locked.id,
            correlation_id=correlation,
            source=source,
            actor_user=actor,
            metadata={"asset_id": str(locked.asset_id) if locked.asset_id else None},
        )
        return PolicyMutationResult(policy=locked, correlation_id=correlation)
