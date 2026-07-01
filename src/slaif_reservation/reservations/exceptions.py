from __future__ import annotations


class ReservationDomainError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


POLICY_NOT_CONFIGURED = "policy_not_configured"
POLICY_AMBIGUOUS = "policy_ambiguous"
POLICY_MUTATION_NOT_AUTHORIZED = "policy_mutation_not_authorized"
INVALID_POLICY_UPDATE = "invalid_policy_update"
PRINCIPAL_INACTIVE = "principal_inactive"
ASSET_INACTIVE = "asset_inactive"
ASSET_NOT_RESERVABLE = "asset_not_reservable"
UNSUPPORTED_BOOKING_MODE = "unsupported_booking_mode"
INVALID_TIME_RANGE = "invalid_time_range"
RESERVATION_IN_PAST = "reservation_in_past"
LEAD_TIME_VIOLATION = "lead_time_violation"
BOOKING_HORIZON_VIOLATION = "booking_horizon_violation"
DURATION_TOO_SHORT = "duration_too_short"
DURATION_TOO_LONG = "duration_too_long"
PURPOSE_REQUIRED = "purpose_required"
MAX_UPCOMING_EXCEEDED = "max_upcoming_exceeded"
MAX_CONCURRENT_EXCEEDED = "max_concurrent_exceeded"
RESERVATION_CONFLICT = "reservation_conflict"
BLACKOUT_CONFLICT = "blackout_conflict"
RESERVATION_NOT_OWNED = "reservation_not_owned"
RESERVATION_NOT_CANCELLABLE = "reservation_not_cancellable"
CANCELLATION_CUTOFF = "cancellation_cutoff"
RESERVATION_NOT_RELEASABLE = "reservation_not_releasable"
