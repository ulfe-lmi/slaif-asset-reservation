# API v1 Design Contract

**Status:** implemented contract for the controlled authenticated pilot. Staff asset list/detail endpoints, bearer `/me`,
bearer advisory availability, bearer owner reservation endpoints, the explicit read-only
cross-user `all-reservations` list/detail surface, shared API abuse budgets, and exact-asset
group booking eligibility are implemented. Token lifecycle APIs, administrative APIs, projects,
and memberships remain deferred.

**Base path:** `/api/v1/`

The generated OpenAPI document is the mechanical schema source of truth. This document records the
intended semantics that must stay aligned with implementation.

## Principles

- Human UI and API clients use the same reservation domain services.
- Bearer-token authentication is enabled only on the implemented token-authenticated endpoints.
- The legacy staff-session asset list/detail endpoints require a current
  active human staff session.
- IDs are opaque UUIDs.
- API timestamps are aware ISO-8601 instants and are serialized as UTC.
- Mutation endpoints require idempotency.
- Creation permits a start up to 10 minutes before submission when the effective
  policy has zero lead time. Positive policy lead times remain enforced, and the
  end must always be in the future. The same rule applies to browser bookings.
- Errors use privacy-safe problem-details JSON.
- Responses never expose bearer tokens, verifiers, peppers, physical locators, raw provenance, audit
  internals, or another user's identity/purpose.

## Authentication and Scopes

```http
Authorization: Bearer sar_<token_uuid_hex>_<secret>
```

The server stores only an HMAC-SHA-256 verifier using the dedicated API-token pepper. The bearer
authenticator is not registered globally.

Implemented bearer scopes:

```text
assets:read
availability:read
reservations:read
reservations:create
reservations:cancel
reservations:release
reservations:read_all
```

Current scope usage:

- `availability:read` for asset availability;
- `reservations:read` for reservation list/detail (owner-only);
- `reservations:create` for reservation creation;
- `reservations:cancel` for cancellation;
- `reservations:release` for early release;
- `reservations:read_all` for the explicit cross-user list/detail surface.

The existing `/api/v1/assets/` and `/api/v1/assets/{asset_id}/` endpoints still require a current
active human staff session. Bearer `assets:read` does not grant those
endpoints in this slice.

`reservations:read` remains **owner-only**: even a token that also carries
`reservations:read_all` (or a staff/superuser owner with every application
capability) sees only the owner's own records on the owner endpoints.
`reservations:read_all` authorizes only the separate
`/api/v1/all-reservations/` routes described below, and only together with
the owner's current `reservations.view_all_reservations` application
capability (see [Dual gate](#dual-gate-for-reservationsread_all)).

**Issuance ceilings.** A token may be created with `reservations:read_all`
only while its owner currently holds `reservations.view_all_reservations`,
and with `reservations:create` only while the owner currently holds
`reservations.book_assets`. The check runs on the fresh row-locked owner
inside the issuance service, before any token ID, secret, verifier,
persistence or audit write; a denial writes nothing. Existing tokens keep
their stored scopes: after a later capability removal a stored
`read_all`/`create` scope no longer works on protected operations (rechecked
per request) while the token still authenticates, uses its remaining
owner scopes, and revokes normally. No scope backfill, mutation or
re-scoping exists.

The human UI displays human-readable scope labels (for example
"Create reservations" for `reservations:create` and "Read other people's
reservations (read-only)" for `reservations:read_all`) on the token
creation form and the token list, and on the one-time token display. The
token creation form offers only the scopes the server-request owner can
currently issue (a capability-less account never sees the privileged
choice), and adds a plain-language effect line per scope; the list and the
one-time display show labels only. Stored values, form values and wire
values are always the exact machine strings above; nothing in the UI
changes the scope contract.

### Dual gate for `reservations:read_all`

The cross-user routes require **both** authorities, rechecked per request:

1. the token's `reservations:read_all` scope (missing scope returns the
   existing `403 insufficient_scope`); and
2. the token owner's **current** `reservations.view_all_reservations`
   application permission, evaluated through the shared active-human
   helper on the request-time owner (missing capability returns the
   existing `403 permission_denied`).

There is no process-global grant cache: group or permission removal takes
effect on the token's next request. Both checks run BEFORE any reservation
row is fetched, so an unauthorized caller cannot infer the existence of a
record. Staff status, Administration model View permissions and `book_assets`
alone never qualify; a trusted active superuser passes the capability gate
through Django permission semantics but still needs the new scope. Every
response of these routes (success, error and 405) carries
`Cache-Control: private, no-store` and a `Vary` header including
`Authorization`; old endpoint headers are unchanged.

## Idempotency

Mutation endpoints require:

```http
Idempotency-Key: <client-generated opaque value>
```

Key rules:

- 8 through 128 printable ASCII characters;
- no whitespace or control characters;
- not a secret.

Records are scoped by owner, API token, action, and key. The server stores a SHA-256 hash of a
canonical JSON request containing action, method, path, and parsed body. It does not store bearer
tokens, Authorization headers, raw request bodies, cookies, CSRF values, token secrets, verifiers,
peppers, or passwords.

For the same owner, token, action, and key:

- same canonical request returns the stored safe response without another mutation or audit event;
- different canonical request returns `409 idempotency_conflict` without mutation.

Different owners or tokens may reuse the same key independently. Records carry a 24-hour retention
target. Until cleanup exists, stored rows remain authoritative. A matching expired row returns
`409 idempotency_expired` without replay, mutation, or another audit event. Replayed successful
reservation creation preserves the original status, safe body, original correlation ID, replay
headers, and the original safe `Location` header.

## Correlation

Clients may send `X-Request-ID` as a UUID. Invalid values are ignored and replaced. Bearer API
responses include a correlation UUID, and successful reservation mutations pass that UUID into the
domain service and audit event.

## Problem Details

Problem responses include:

```json
{
  "type": "https://slaif.local/problems/reservation_conflict",
  "title": "Reservation Conflict",
  "status": 409,
  "code": "reservation_conflict",
  "detail": "The requested time is no longer available.",
  "correlation_id": "00000000-0000-0000-0000-000000000000"
}
```

Stable codes include authentication, scope, booking-authorization, validation, idempotency, asset,
policy, and reservation domain errors such as `authentication_required`, `invalid_token`,
`insufficient_scope`, `booking_not_authorized`,
`idempotency_required`, `invalid_idempotency_key`, `idempotency_conflict`,
`idempotency_expired`, `validation_error`, `asset_not_found`, `reservation_not_found`,
`policy_not_configured`, `policy_ambiguous`, `reservation_conflict`,
`blackout_conflict`, `reservation_not_cancellable`, `cancellation_cutoff`,
and `reservation_not_releasable`. A reservation creation attempt that
overlaps an active maintenance blackout returns `409 blackout_conflict`
(detail "The requested time is unavailable."); the blackout's operational
text is not disclosed.

Problem responses do not include ORM exception text, SQL, constraint names, stack traces, token
lookup details, or secret material.

## Endpoints

### `GET /api/v1/`

Anonymous root describing the implemented endpoint families (links only,
no data). The cross-user `all-reservations` routes are bearer endpoints
documented below; they are not part of this static link list. In a browser
this endpoint is served by the product-branded Browsable API titled "SLAIF
Asset Reservation API"; the JSON contract is unchanged.

### `GET /api/v1/me/`

Requires a valid bearer token and no additional action scope: the view
declares `required_scopes = ()`, so any valid token may call this identity
endpoint (anonymous requests are rejected with the standard authentication
failure). Returns safe principal and token context:

```json
{
  "principal": {"id": "uuid", "display_name": "Example User"},
  "token": {
    "id": "uuid",
    "display_prefix": "sar_0123456789ab...",
    "scopes": ["reservations:read"],
    "expires_at": "2026-07-01T00:00:00Z",
    "last_used_at": "2026-06-30T12:00:00Z"
  },
  "correlation_id": "uuid"
}
```

Email, staff flags, bearer plaintext, verifier, and pepper are never returned.

### `GET /api/v1/assets/`

Staff-session-only inventory list. Implemented filters are `kind`, `parent`, `tag`, `active`,
`reservable`, and `q`. Pagination is DRF limit/offset with default 50 and maximum 100. Safe fields
exclude physical locators, legacy IDs, raw provenance, and internal notes.

### `GET /api/v1/assets/{asset_id}/`

Staff-session-only inventory detail using the opaque asset UUID.

### `GET /api/v1/assets/{asset_id}/availability/`

Requires bearer authentication and `availability:read`.

Query parameters:

- `date`: ISO local date, optional;
- `days`: integer 1 through 7, optional;
- `timezone`: IANA timezone, optional; defaults to owner timezone.

The response includes an asset summary, display timezone, UTC window start/end, advisory notice,
safe policy minimum duration, privacy-safe busy intervals, and free intervals with latest valid
start. Other users and active maintenance blackouts are labelled only as unavailable; their
identities, email, purposes, cancellation reasons, reservation UUIDs, and blackout reasons are not
exposed. Availability remains advisory.
Missing asset UUIDs return `404 asset_not_found`.

### `GET /api/v1/reservations/`

Requires bearer authentication and `reservations:read`. Returns only the token owner's reservations.
Filters:

- `asset` UUID;
- `status`;
- `lifecycle`;
- `from`;
- `to`;
- `limit`;
- `offset`.

### `POST /api/v1/reservations/`

Requires bearer authentication, `reservations:create`, and `Idempotency-Key`. Request:

```json
{
  "asset_id": "uuid",
  "start_at": "2026-07-01T08:00:00Z",
  "end_at": "2026-07-01T09:00:00Z",
  "purpose": "API job"
}
```

`start_at` and `end_at` must include an explicit UTC offset. Local wall time and DST fold fields are
not accepted by the API. The view calls only `create_reservation(..., source="api")`.

The owner's CURRENT `reservations.book_assets` capability and exact-asset group
eligibility are rechecked on every creation request BEFORE any cached
idempotent creation response is returned, and again inside the authoritative
row-locked service for actual new writes. A missing or revoked capability or
group membership returns `403 booking_not_authorized` even when the original
accepted creation is still cached; restoring the grant makes the same-key
replay return the original status, body and correlation. The existing
missing-asset `404 asset_not_found` callback and its idempotent recording are
unchanged.

Success returns `201`, `Location`, reservation representation, and `correlation_id`.

### `GET /api/v1/reservations/{reservation_id}/`

Requires bearer authentication and `reservations:read`. Returns only an owned reservation. Other-user
or guessed UUIDs return non-disclosing `404 reservation_not_found`.

### `POST /api/v1/reservations/{reservation_id}/cancel/`

Requires bearer authentication, `reservations:cancel`, owner access, and `Idempotency-Key`. Accepts
optional `reason` up to 1000 characters. Calls only `cancel_reservation(..., source="api")`.
Other-user or guessed UUIDs return non-disclosing `404 reservation_not_found`.

### `POST /api/v1/reservations/{reservation_id}/release/`

Requires bearer authentication, `reservations:release`, owner access, and `Idempotency-Key`. Calls
only `release_reservation(..., source="api")`.
Other-user or guessed UUIDs return non-disclosing `404 reservation_not_found`.

### `GET /api/v1/all-reservations/`

Requires bearer authentication, the `reservations:read_all` scope, and the
owner's current `view_all_reservations` capability (dual gate above).
Read-only cross-user list with the minimal explicit representation
(see [Representation](#representation)). Supports the existing validated
filters and pagination:

- `asset` UUID;
- `status`;
- `lifecycle`;
- `from` — lower **overlap** bound: `effective_end_at > from` (strict,
  half-open);
- `to` — upper **overlap** bound: `start_at < to` (strict, half-open);
- `limit` (default 50, max 100);
- `offset`.

The list envelope is `count`/`next`/`previous`/`results` plus
`correlation_id`. The list includes historical and inactive assets and
reservation owners: booking-eligibility or account-status changes never
delete or rewrite accepted records, and the active-human restriction
applies to the token owner, not to reservation history owners. Missing or
invalid filter values return the existing `400 validation_error`.
`POST`/`PUT`/`PATCH`/`DELETE` are refused with `405` and no nested
cancel/release routes exist under this prefix; the standard safe
`HEAD`/`OPTIONS` methods may exist.

### `GET /api/v1/all-reservations/{reservation_id}/`

Same dual gate. Returns one cross-user reservation by opaque UUID using
the same minimal representation plus a `correlation_id` field consistent
with the `X-Request-ID` header. Missing UUIDs return the existing
`404 reservation_not_found`; unauthorized callers receive the `403` gate
responses and cannot infer the record's existence.

### Representation

Each cross-user row is the exact allow-list below — nothing else is
rendered, for any caller, including superusers:

```json
{
  "id": "uuid",
  "asset": {"id": "uuid", "slug": "gpu-01", "name": "GPU 01", "kind": "gpu"},
  "owner": {"id": "uuid", "external_identifier": "12345678"},
  "status": "confirmed",
  "lifecycle": "active",
  "start_at": "2026-07-01T08:00:00Z",
  "end_at": "2026-07-01T09:00:00Z",
  "effective_end_at": "2026-07-01T09:00:00Z",
  "released_at": null,
  "cancelled_at": null,
  "blocking_interval": {"start_at": "2026-07-01T08:00:00Z", "end_at": "2026-07-01T09:00:00Z"}
}
```

- `owner.id` is the stable account UUID; `owner.external_identifier` is the
  opaque external identifier string, `null` when unset. Numeric strings
  and leading zeroes are preserved verbatim (max 128 characters,
  case-sensitive). The owner's current identifier is account-mapping
  metadata, not a snapshot and not a credential. When the identifier is
  `null` the consumer cannot infer any machine identity from the row;
  `owner.id` is only an explicit external mapping key you may choose to
  store - it is never an automatic Linux UID or host-identity fallback.
- `lifecycle` is the derived lifecycle (`active`, `upcoming`, `completed`,
  `cancelled`, `released`).
- `start_at`/`end_at` are the original (immutable) times;
  `effective_end_at` carries the half-open release history.
- `blocking_interval` is the half-open `[start_at, effective_end_at)`
  interval for confirmed and released records (`null` for cancelled): it
  is historical/future interval semantics, **not** a promise of currently
  active or login access. A released record's consumed prefix remains
  original-end evidence; cancelled records never block.

Excluded by construction: owner email/display name/profile/active/staff/
superuser flags and groups, passwords/verifiers/token material, purposes,
cancellation and blackout free text, physical locators, asset
capabilities/timezone, reservation `source`/`created_at`, and any other
field outside the allow-list. The existing owner representations are
compatible and unchanged, and the staff asset inventory/docs boundaries
are unchanged (no bearer asset discovery).

**Enforcer guidance (external integrations):** map
`owner.external_identifier` opaquely (a `null` identifier means no machine
identity can be inferred; `owner.id` is only an explicit external mapping
key, not an automatic Linux UID fallback); evaluate
`blocking_interval` as an aware `[start, end)` half-open range at your
chosen instant (cancelled `null` never blocks; a released prefix is
history, not current availability); and remember the mapping may change
over time. The external enforcer owns account enablement, enforcement,
polling, caches/refresh and outages; there is no promise of an atomic
full-pagination snapshot. The `read_all` scope is not a permission to an
API user directory, to free text or to audit inspection, and reservation
entitlement or this identifier is never a login right.

## Deferred

- `/api/v1/tokens/` creation/revocation;
- `/api/v1/me` without trailing slash;
- administrative reservation APIs;
- cross-user bearer mutation APIs (the read-all surface is read-only);
- projects, memberships, and resource authorization beyond exact-asset
  group booking eligibility and the explicit read-all gate above;
- availability rules, blackouts, maintenance calendar API;
- management APIs;
- service-account/admin token issuance;
- execution gateway integration.

## Abuse limits and retry

API traffic has shared source, authenticated-account and token budgets.
Defaults are1,200/600/300 requests per minute respectively; the account budget
covers all its tokens. A blocked request returns429 `rate_limited`, `Retry-After`,
`Cache-Control: no-store` and the normal correlation
fields; on the `all-reservations` route family the early denials carry
`private, no-store` plus a `Vary` header including `Authorization`,
matching the in-view responses. Wait before retrying
and retain the same idempotency key for a mutation retry. Security-counter
failure returns503 `service_unavailable`; it does not accept the mutation.
These controls also bound invalid or missing bearer attempts. See
[the shared budget contract](decisions/0016-shared-abuse-controls.md).
