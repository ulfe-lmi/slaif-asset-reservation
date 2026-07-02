# ADR 0013: SmartScheduling Migration Tooling

**Status:** accepted
**Date:** 2026-07-01

## Context

SLAIF replaces the SmartScheduling salon-oriented model with an asset reservation authority. The
repository already contains a sanitized public asset bootstrap, but it does not contain private
SmartScheduling people or appointment exports. A future human-supervised migration may need tooling
to inspect and rehearse legacy data, yet the repository and CI must remain free of private client
data, cookies, screenshots, traces, or live-service automation.

## Decision

Work Order 0009 implements a synthetic-fixture-driven migration toolchain only. The accepted input
format is `slaif-smartscheduling-synthetic-v1` in local JSON/YAML files. It contains fake resources,
fake people, and fake appointments. Commands reject URLs, unsupported extensions, malformed
timestamps, duplicate legacy IDs, unknown private fields, unknown statuses, impossible intervals,
and ambiguous or nonexistent local wall times unless an explicit fold is supplied.

Legacy appointment local times are interpreted in an explicit operator-supplied IANA timezone and
are normalized to UTC instants before planning or import. Imported reservations use
`source="migration"`, preserve `start_at`, `end_at`, and `effective_end_at=end_at`, and keep
completed lifecycle derived from time rather than a stored completed status. Future confirmed
appointments must respect current asset state, effective policies, active blackouts, and PostgreSQL
reservation exclusivity. Past completed appointments use a documented migration exception from
ordinary no-past booking so historical truth can be represented; they still pass model validation
and database conflict checks.

Legacy cancellations and no-shows are reported as skipped and do not create blocking reservations.
Known unsupported statuses, such as waitlisted appointments, are reported as unsupported. Unknown
statuses fail parser validation. The tool does not auto-create production users, policies, or
assets by default. User mapping is explicit from legacy person ID to existing SLAIF user UUID. Asset
mapping uses existing `legacy_source`/`legacy_id`, then explicit mapping, then documented slug
fallback when unambiguous.

Durable import evidence uses `LegacyImportBatch` and `LegacyImportRecord`. These records store
source name, checksums, synthetic/private flag, safe counts, status, imported reservation links, and
normalized record hashes. They do not store raw export rows, phone numbers, raw email addresses,
client notes, cookies, tokens, screenshots, traces, or browser storage. Idempotency is scoped to
`legacy_source + legacy_id`: repeating the same normalized record reports `already_imported`, while
changed data for an imported legacy ID reports `legacy_changed` and is not overwritten.

Dry-run plans are advisory. Apply revalidates each would-create record inside the apply transaction
before writing: the legacy import record lookup, mapped asset, mapped user, selected effective
policy, active blackout overlap, and current blocking reservation overlap are checked again. If
authoritative state changed after planning, apply skips that record with the final deterministic
classification rather than importing stale data. PostgreSQL reservation exclusivity remains the
final arbiter of reservation-vs-reservation races. The apply JSON report is therefore the
authoritative final import artifact for that run; it includes `mode="apply"`, the import batch ID,
final counts, final per-record classifications, and reservation IDs only for imported or already
imported records.

Successful imported reservations append ordinary `reservation.created` audit events with
`source="migration"` and safe metadata: legacy source, legacy ID, import batch ID, asset ID, and
time range. Audit metadata never includes purpose text, private notes, raw user data, credentials,
or export payloads. If audit append fails, the reservation and import record roll back.

## Consequences

The repository can prove parser, planner, command, idempotency, conflict, blackout, and rollback
behavior with synthetic data in CI. A real migration still requires a human-controlled export
process, private storage outside Git, backup before apply, reconciliation of unmapped people and
resources, and a rehearsal against a disposable database. This decision explicitly excludes
scraping, live SmartScheduling browser automation, private export commits, production import,
auto-created users, automatic conflict resolution, and production cutover.
