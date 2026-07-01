# Runbook: Management Blackout Process

Maintenance blackouts are coarse operational unavailability. They are not a full operating-hours or
maintenance-calendar model.

1. Staff user opens `/manage/blackouts/`.
2. Create a blackout with asset, local start/end, timezone, and reason.
3. Review the affected-reservation preview. Existing reservations are not automatically cancelled
   or released.
4. If overlapping reservations exist, explicitly confirm creation.
5. Communicate with affected users outside the application if needed.
6. Deactivate the blackout when no longer applicable.

Ordinary member and API availability see blackout time only as unavailable. They do not see the
blackout reason, creator, affected user identities, purposes, or audit internals.
