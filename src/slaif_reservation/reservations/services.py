from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q, QuerySet
from django.utils import timezone

from slaif_reservation.accounts.authorization import has_reservation_permission
from slaif_reservation.assets.authorization import user_can_book_asset
from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.audit.services import append_audit_event
from slaif_reservation.reservations.exceptions import (
    ASSET_INACTIVE,
    ASSET_NOT_RESERVABLE,
    BLACKOUT_CONFLICT,
    BOOKING_HORIZON_VIOLATION,
    BOOKING_NOT_AUTHORIZED,
    CANCELLATION_CUTOFF,
    DURATION_TOO_LONG,
    DURATION_TOO_SHORT,
    INVALID_POLICY_UPDATE,
    INVALID_TIME_RANGE,
    LEAD_TIME_VIOLATION,
    MAX_CONCURRENT_EXCEEDED,
    MAX_UPCOMING_EXCEEDED,
    POLICY_AMBIGUOUS,
    POLICY_MUTATION_NOT_AUTHORIZED,
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
from slaif_reservation.reservations.models import (
    SERVICE_UPDATE_ATTR,
    MaintenanceBlackout,
    Reservation,
    ReservationPolicy,
)
from slaif_reservation.reservations.time_utils import InstantError, require_aware_utc

UserModel = get_user_model()


@dataclass(frozen=True)
class ReservationMutationResult:
    reservation: Reservation
    correlation_id: uuid.UUID


@dataclass(frozen=True)
class PolicyMutationResult:
    policy: ReservationPolicy
    correlation_id: uuid.UUID


@dataclass(frozen=True)
class BlackoutMutationResult:
    blackout: MaintenanceBlackout
    correlation_id: uuid.UUID


def _correlation(value: uuid.UUID | None) -> uuid.UUID:
    return value or uuid.uuid4()


def _raise(code: str, message: str) -> None:
    raise ReservationDomainError(code, message)


def _instant(value: datetime, *, field_name: str) -> datetime:
    try:
        return require_aware_utc(value, field_name=field_name)
    except InstantError as exc:
        _raise(INVALID_TIME_RANGE, str(exc))
    raise AssertionError("unreachable")


def _service_save(instance: Any) -> None:
    setattr(instance, SERVICE_UPDATE_ATTR, True)
    try:
        instance.save()
    finally:
        if hasattr(instance, SERVICE_UPDATE_ATTR):
            delattr(instance, SERVICE_UPDATE_ATTR)


def _lock_principal(principal: Any) -> Any:
    # Serialize mutable principal state/counters without blocking harmless
    # foreign-key references from other audited transactions.
    locked = UserModel.objects.select_for_update(no_key=True).get(pk=principal.pk)
    if not locked.is_active:
        _raise(PRINCIPAL_INACTIVE, "Principal is inactive.")
    return locked


def _lock_capable_actor(actor_user: Any, codename: str) -> Any:
    """Row-locked actor rechecked against the explicit capability.

    The freshly row-locked principal is evaluated for the named
    reservations-namespace permission, so revocation between request start
    and this guard is observed. Inactivity is denied first by
    ``_lock_principal``; staff status alone confers nothing and service
    accounts never hold the capability even when a permission record is
    attached. The existing denial code is preserved.
    """
    actor = _lock_principal(actor_user)
    if not has_reservation_permission(actor, codename):
        _raise(
            POLICY_MUTATION_NOT_AUTHORIZED,
            "Mutation requires an active human holding the required capability.",
        )
    return actor


def _lock_asset(asset: Asset) -> Asset:
    locked = Asset.objects.select_for_update(no_key=True).get(pk=asset.pk)
    if locked.parent_id:
        locked.parent = Asset.objects.get(pk=locked.parent_id)
    return locked


def _lock_asset_by_id(asset_id: Any) -> Asset:
    locked = Asset.objects.select_for_update(no_key=True).get(pk=asset_id)
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


def _active_policies_for(query: Q, *, for_update: bool = False) -> list[ReservationPolicy]:
    queryset = ReservationPolicy.objects.filter(active=True).filter(query).order_by("id")
    if for_update:
        queryset = queryset.select_for_update()
    return list(queryset[:2])


def _resolve_effective_policy(asset: Asset, *, for_update: bool) -> ReservationPolicy:
    candidates: list[tuple[str, Q]] = [("asset", Q(asset=asset))]
    if asset.parent_id:
        candidates.append(("parent", Q(asset=asset.parent)))
    candidates.append(("global", Q(asset__isnull=True)))

    for _level, query in candidates:
        policies = _active_policies_for(query, for_update=for_update)
        if len(policies) > 1:
            _raise(POLICY_AMBIGUOUS, "Multiple active policies match at the same priority.")
        if len(policies) == 1:
            return policies[0]

    _raise(POLICY_NOT_CONFIGURED, "No active reservation policy applies to this asset.")
    raise AssertionError("unreachable")


def resolve_effective_policy(asset: Asset) -> ReservationPolicy:
    return _resolve_effective_policy(asset, for_update=False)


def lock_effective_policy(asset: Asset) -> ReservationPolicy:
    return _resolve_effective_policy(asset, for_update=True)


def _validate_time_range(start_at: datetime, end_at: datetime, now: datetime) -> timedelta:
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
        start_at__gt=now,
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


def _raise_if_blackout_overlap(asset: Asset, start_at: Any, end_at: Any) -> None:
    if MaintenanceBlackout.objects.filter(
        asset=asset,
        active=True,
        start_at__lt=end_at,
        end_at__gt=start_at,
    ).exists():
        _raise(BLACKOUT_CONFLICT, "Reservation conflicts with a maintenance blackout.")


def _is_named_reservation_constraint(exc: IntegrityError) -> bool:
    cause = getattr(exc, "__cause__", None)
    constraint_name = getattr(getattr(cause, "diag", None), "constraint_name", None)
    return constraint_name == Reservation.EXCLUSION_CONSTRAINT_NAME


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
    now = timezone.now() if now is None else now
    now_utc = _instant(now, field_name="now")
    start_utc = _instant(start_at, field_name="start_at")
    end_utc = _instant(end_at, field_name="end_at")
    correlation = _correlation(correlation_id)

    with transaction.atomic():
        principal = _lock_principal(requested_by_user)
        locked_asset = _lock_asset(asset)
        if not user_can_book_asset(principal, locked_asset):
            _raise(
                BOOKING_NOT_AUTHORIZED,
                "The principal is not authorized to book this asset.",
            )
        _validate_asset(locked_asset)
        policy = lock_effective_policy(locked_asset)
        _enforce_policy(
            policy=policy,
            principal=principal,
            start_at=start_utc,
            end_at=end_utc,
            purpose=purpose,
            now=now_utc,
        )
        _raise_if_blackout_overlap(locked_asset, start_utc, end_utc)
        _raise_if_asset_overlap(locked_asset, start_utc, end_utc)

        reservation = Reservation(
            asset=locked_asset,
            requested_by_user=principal,
            source=source,
            status=Reservation.STATUS_CONFIRMED,
            start_at=start_utc,
            end_at=end_utc,
            effective_end_at=end_utc,
            purpose=purpose,
        )
        reservation.full_clean(validate_constraints=False)

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
                "start_at": start_utc.isoformat(),
                "end_at": end_utc.isoformat(),
            },
        )
        return ReservationMutationResult(reservation=reservation, correlation_id=correlation)


def _authorized_for_existing_reservation(
    requester: Any, reservation: Reservation, *, capability: str
) -> bool:
    """Active human owner, or the explicit cross-user lifecycle capability.

    The owner path keeps owner lifecycle completely independent of booking
    capability or asset group membership (a service account can never use
    it); the capability path evaluates the freshly row-locked requester, so
    group/permission removal takes effect immediately. ``is_staff`` no
    longer authorizes anything here.
    """
    if requester.pk == reservation.requested_by_user_id and not getattr(
        requester, "is_service_account", False
    ):
        return True
    return has_reservation_permission(requester, capability)


def cancel_reservation(
    *,
    reservation: Reservation,
    requested_by_user: Any,
    reason: str = "",
    source: str = Reservation.SOURCE_WEB,
    now: Any | None = None,
    correlation_id: uuid.UUID | None = None,
) -> ReservationMutationResult:
    now = timezone.now() if now is None else now
    now_utc = _instant(now, field_name="now")
    correlation = _correlation(correlation_id)

    with transaction.atomic():
        requester = _lock_principal(requested_by_user)
        locked = (
            Reservation.objects.select_for_update(of=("self",))
            .select_related("requested_by_user")
            .get(pk=reservation.pk)
        )
        if not _authorized_for_existing_reservation(
            requester, locked, capability="cancel_others_reservations"
        ):
            _raise(RESERVATION_NOT_OWNED, "Requester cannot cancel this reservation.")
        locked_asset = _lock_asset_by_id(locked.asset_id)
        start_utc = _instant(locked.start_at, field_name="start_at")
        if locked.status != Reservation.STATUS_CONFIRMED or start_utc <= now_utc:
            _raise(RESERVATION_NOT_CANCELLABLE, "Reservation is not cancellable.")
        policy = lock_effective_policy(locked_asset)
        cutoff_at = start_utc - timedelta(minutes=policy.cancellation_cutoff_minutes)
        if now_utc > cutoff_at:
            _raise(CANCELLATION_CUTOFF, "Reservation is past the cancellation cutoff.")

        locked.status = Reservation.STATUS_CANCELLED
        locked.cancelled_at = now_utc
        locked.cancelled_by = requester
        locked.cancellation_reason = reason
        locked.effective_end_at = locked.end_at
        locked.full_clean()
        _service_save(locked)
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
    now = timezone.now() if now is None else now
    now_utc = _instant(now, field_name="now")
    correlation = _correlation(correlation_id)

    with transaction.atomic():
        requester = _lock_principal(requested_by_user)
        locked = (
            Reservation.objects.select_for_update(of=("self",))
            .select_related("requested_by_user")
            .get(pk=reservation.pk)
        )
        if not _authorized_for_existing_reservation(
            requester, locked, capability="release_others_reservations"
        ):
            _raise(RESERVATION_NOT_OWNED, "Requester cannot release this reservation.")
        _lock_asset_by_id(locked.asset_id)
        start_utc = _instant(locked.start_at, field_name="start_at")
        effective_end_utc = _instant(locked.effective_end_at, field_name="effective_end_at")
        if locked.status != Reservation.STATUS_CONFIRMED or not (
            start_utc < now_utc < effective_end_utc
        ):
            _raise(RESERVATION_NOT_RELEASABLE, "Reservation is not releasable.")

        locked.status = Reservation.STATUS_RELEASED
        locked.released_at = now_utc
        locked.effective_end_at = now_utc
        locked.full_clean()
        _service_save(locked)
        append_audit_event(
            action=AuditEvent.ACTION_RESERVATION_RELEASED,
            target_type="reservation",
            target_id=locked.id,
            correlation_id=correlation,
            source=source,
            actor_user=requester,
            metadata={"asset_id": str(locked.asset_id), "released_at": now_utc.isoformat()},
        )
        return ReservationMutationResult(reservation=locked, correlation_id=correlation)


MUTABLE_POLICY_FIELDS = {
    "name",
    "asset",
    "min_duration_minutes",
    "max_duration_minutes",
    "booking_horizon_days",
    "min_lead_minutes",
    "cancellation_cutoff_minutes",
    "max_upcoming_per_principal",
    "max_concurrent_per_principal",
    "purpose_required",
}


def _validate_policy_update_fields(values: dict[str, Any]) -> None:
    invalid = sorted(set(values) - MUTABLE_POLICY_FIELDS)
    if invalid:
        _raise(
            INVALID_POLICY_UPDATE,
            f"Policy update contains immutable or unknown field(s): {', '.join(invalid)}.",
        )


def create_policy(
    *,
    actor_user: Any,
    source: str = AuditEvent.SOURCE_ADMIN,
    correlation_id: uuid.UUID | None = None,
    **values: Any,
) -> PolicyMutationResult:
    correlation = _correlation(correlation_id)
    with transaction.atomic():
        actor = _lock_capable_actor(actor_user, "manage_booking_policies")
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
        actor = _lock_capable_actor(actor_user, "manage_booking_policies")
        _validate_policy_update_fields(values)
        locked = ReservationPolicy.objects.select_for_update().get(pk=policy.pk)
        for field, value in values.items():
            setattr(locked, field, value)
        locked.full_clean()
        _service_save(locked)
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
        actor = _lock_capable_actor(actor_user, "manage_booking_policies")
        locked = ReservationPolicy.objects.select_for_update().get(pk=policy.pk)
        locked.active = False
        locked.full_clean()
        _service_save(locked)
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


def overlapping_blocking_reservations_queryset(
    *,
    asset: Asset,
    start_at: datetime,
    end_at: datetime,
) -> QuerySet[Reservation]:
    start_utc = _instant(start_at, field_name="start_at")
    end_utc = _instant(end_at, field_name="end_at")
    return (
        Reservation.objects.filter(
            asset=asset,
            status__in=[Reservation.STATUS_CONFIRMED, Reservation.STATUS_RELEASED],
            start_at__lt=end_utc,
            effective_end_at__gt=start_utc,
        )
        .select_related("requested_by_user", "asset")
        .order_by("start_at", "id")
    )


def overlapping_blocking_reservations(
    *,
    asset: Asset,
    start_at: datetime,
    end_at: datetime,
) -> list[Reservation]:
    return list(
        overlapping_blocking_reservations_queryset(asset=asset, start_at=start_at, end_at=end_at)
    )


def create_blackout(
    *,
    asset: Asset,
    actor_user: Any,
    reason: str,
    start_at: datetime,
    end_at: datetime,
    confirmed_overlap: bool = False,
    source: str = AuditEvent.SOURCE_ADMIN,
    correlation_id: uuid.UUID | None = None,
) -> BlackoutMutationResult:
    correlation = _correlation(correlation_id)
    start_utc = _instant(start_at, field_name="start_at")
    end_utc = _instant(end_at, field_name="end_at")
    if end_utc <= start_utc:
        _raise(INVALID_TIME_RANGE, "Blackout end must be after start.")

    with transaction.atomic():
        actor = _lock_capable_actor(actor_user, "manage_maintenance_blackouts")
        locked_asset = _lock_asset(asset)
        overlaps = overlapping_blocking_reservations(
            asset=locked_asset,
            start_at=start_utc,
            end_at=end_utc,
        )
        if overlaps and not confirmed_overlap:
            _raise(BLACKOUT_CONFLICT, "Blackout overlaps existing reservations.")
        blackout = MaintenanceBlackout(
            asset=locked_asset,
            created_by=actor,
            reason=reason.strip(),
            start_at=start_utc,
            end_at=end_utc,
            active=True,
        )
        blackout.full_clean()
        blackout.save()
        append_audit_event(
            action=AuditEvent.ACTION_BLACKOUT_CREATED,
            target_type="maintenance_blackout",
            target_id=blackout.id,
            correlation_id=correlation,
            source=source,
            actor_user=actor,
            metadata={
                "asset_id": str(locked_asset.id),
                "asset_slug": locked_asset.slug,
                "start_at": start_utc.isoformat(),
                "end_at": end_utc.isoformat(),
                "overlapping_reservations": len(overlaps),
            },
        )
        return BlackoutMutationResult(blackout=blackout, correlation_id=correlation)


def deactivate_blackout(
    *,
    blackout: MaintenanceBlackout,
    actor_user: Any,
    source: str = AuditEvent.SOURCE_ADMIN,
    correlation_id: uuid.UUID | None = None,
) -> BlackoutMutationResult:
    correlation = _correlation(correlation_id)
    with transaction.atomic():
        actor = _lock_capable_actor(actor_user, "manage_maintenance_blackouts")
        locked = MaintenanceBlackout.objects.select_for_update().get(pk=blackout.pk)
        locked.asset = Asset.objects.get(pk=locked.asset_id)
        if locked.active:
            locked.active = False
            locked.deactivated_at = timezone.now()
            locked.deactivated_by = actor
            locked.full_clean()
            _service_save(locked)
            append_audit_event(
                action=AuditEvent.ACTION_BLACKOUT_DEACTIVATED,
                target_type="maintenance_blackout",
                target_id=locked.id,
                correlation_id=correlation,
                source=source,
                actor_user=actor,
                metadata={"asset_id": str(locked.asset_id), "asset_slug": locked.asset.slug},
            )
        return BlackoutMutationResult(blackout=locked, correlation_id=correlation)
