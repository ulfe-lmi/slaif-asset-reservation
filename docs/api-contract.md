# API v1 Design Contract

**Status:** pre-alpha implementation contract; asset read endpoints are implemented with a temporary
staff-session limitation
**Base path:** `/api/v1/`

The implemented OpenAPI document generated from code becomes the mechanical schema source of truth. This document defines intended semantics and must remain aligned with implementation.

## 1. Principles

- same domain services as the human UI;
- bearer-token authentication for agents;
- HTTPS only outside local development;
- stable opaque UUIDs;
- ISO 8601 aware timestamps;
- idempotent mutations;
- problem-details-style errors;
- predictable pagination and filtering;
- no HTML scraping or browser-session requirement;
- no secret values in responses after token creation.

## 2. Authentication

```http
Authorization: Bearer sar_<public-prefix>_<secret>
```

The exact token grammar may change before beta, but it must include a recognizable non-secret prefix and sufficient entropy. The server stores no plaintext bearer token.

A token is evaluated for:

- active owner/service account;
- revocation;
- expiry;
- scope;
- optional project and resource restrictions.

Initial scopes:

```text
assets:read
availability:read
reservations:read
reservations:create
reservations:cancel
reservations:release
```

## 3. Idempotency

Agent mutation requests must send:

```http
Idempotency-Key: <client-generated opaque value>
```

Rules:

- key is scoped to authenticated principal and action;
- same key and same canonical request returns the original result;
- same key and different request returns `409 idempotency_conflict`;
- keys have a documented retention period;
- token or request bodies are never stored as idempotency evidence.

## 4. Correlation

Clients may send `X-Request-ID`; the server validates format or creates one. Every response returns a correlation identifier. Audit events reference it.

## 5. Errors

Example:

```json
{
  "type": "https://reservation.example/problems/reservation-conflict",
  "title": "Reservation conflicts with an existing reservation",
  "status": 409,
  "detail": "The requested asset is not available for the complete time range.",
  "code": "reservation_conflict",
  "instance": "/api/v1/reservations",
  "correlation_id": "0197..."
}
```

Stable initial codes include:

- `authentication_required`
- `invalid_token`
- `token_expired`
- `insufficient_scope`
- `permission_denied`
- `asset_not_found`
- `asset_inactive`
- `asset_not_reservable`
- `invalid_time_range`
- `policy_denied`
- `reservation_conflict`
- `reservation_not_found`
- `invalid_reservation_state`
- `idempotency_conflict`
- `rate_limited`

Do not expose ORM, SQL, constraint, stack-trace, or secret details.

## 6. Endpoints

### `GET /api/v1/me`

Returns the effective principal and safe token context.

```json
{
  "principal": {
    "id": "uuid",
    "type": "user",
    "display_name": "Example User"
  },
  "token": {
    "id": "uuid",
    "name": "local-codex",
    "scopes": ["assets:read", "reservations:create"],
    "expires_at": "2026-07-01T00:00:00Z"
  }
}
```

Never return the bearer token or verifier.

### `GET /api/v1/assets/`

Implemented in Work Order 0002 as a read-only staff-session endpoint. This is a temporary
pre-alpha limitation: `SessionAuthentication` plus staff permission is required until scoped bearer
tokens are implemented. Anonymous and ordinary non-staff users cannot read inventory data.

Implemented filters:

- `kind`
- `parent` UUID
- `tag`
- `active`
- `reservable`
- `q` text search over safe display fields

Example item:

```json
{
  "id": "uuid",
  "slug": "neumann-gpu-2",
  "name": "Neumann GPU 2",
  "kind": "gpu",
  "parent": {
    "id": "uuid",
    "slug": "neumann",
    "name": "Neumann"
  },
  "active": true,
  "reservable": true,
  "timezone": "Europe/Ljubljana",
  "capabilities": {
    "vendor": "NVIDIA",
    "model": "A100-SXM4-80GB",
    "memory_gib": 80
  }
}
```

Capabilities are administrator-verified before clients may rely on normalized values.

Implemented response fields are limited to:

- `id`, `slug`, `name`, `kind`, `parent`, `description`, `timezone`, `active`, `reservable`,
  `verification_required`, `tags`, and normalized `capabilities`.

The API never serializes `physical_locator`, legacy IDs, raw legacy metadata, or internal notes.
Invalid filter values return HTTP 400 without ORM/SQL/stack details. Pagination uses DRF
limit/offset pagination with a default limit of 50 and maximum limit of 100.

### `GET /api/v1/assets/{asset_id}/`

Implemented in Work Order 0002 with the same temporary staff-session limitation and safe field set.
The detail identifier is the opaque asset UUID.

Returns one authorized asset. Hidden and unauthorized assets should use a non-disclosing not-found response where appropriate.

### `GET /api/v1/assets/{asset_id}/availability`

Deferred/not implemented in Work Order 0002. This section describes the intended future contract
for a later availability slice.

Query:

```text
from=<timestamp>
to=<timestamp>
duration_minutes=<positive integer, optional>
```

Response design:

```json
{
  "asset_id": "uuid",
  "from": "2026-06-20T08:00:00Z",
  "to": "2026-06-20T18:00:00Z",
  "timezone": "Europe/Ljubljana",
  "intervals": [
    {
      "start_at": "2026-06-20T08:00:00Z",
      "end_at": "2026-06-20T10:30:00Z"
    }
  ]
}
```

Availability is advisory. A later create request may still lose a race.

### `GET /api/v1/reservations`

Ordinary tokens see own reservations unless an explicitly granted read scope/policy permits more.

Filters:

- `asset`
- `status`
- `from`
- `to`
- `project`
- `upcoming=true`

### `POST /api/v1/reservations`

Requires `reservations:create` and `Idempotency-Key`.

```json
{
  "asset_id": "uuid",
  "start_at": "2026-06-20T10:00:00+02:00",
  "end_at": "2026-06-20T10:30:00+02:00",
  "purpose": "Vision-model inference test",
  "project_id": null
}
```

Success: `201 Created` with location and reservation.

```json
{
  "id": "uuid",
  "asset": {
    "id": "uuid",
    "slug": "neumann-gpu-2",
    "name": "Neumann GPU 2"
  },
  "status": "confirmed",
  "start_at": "2026-06-20T08:00:00Z",
  "end_at": "2026-06-20T08:30:00Z",
  "effective_end_at": "2026-06-20T08:30:00Z",
  "purpose": "Vision-model inference test",
  "source": "api",
  "created_at": "2026-06-19T12:00:00Z"
}
```

Conflict: `409 reservation_conflict`. Policy rejection: `403` or `422` according to the accepted implementation convention; choose one consistently and document it.

### `GET /api/v1/reservations/{reservation_id}`

Returns an authorized reservation and lifecycle timestamps.

### `POST /api/v1/reservations/{reservation_id}/cancel`

Cancels a future reservation. Requires idempotency.

```json
{
  "reason": "Job no longer needed"
}
```

Repeated cancellation with the same key returns the prior result. An already started reservation cannot be cancelled through this action; use release.

### `POST /api/v1/reservations/{reservation_id}/release`

Releases an active reservation early. Requires idempotency.

```json
{
  "reason": "Work completed"
}
```

The response shows `released_at` and the original/effective end semantics. Releasing another principal's reservation is forbidden unless an explicit administrative interface permits it.

## 7. Planned post-MVP endpoints

### Atomic allocation

```http
POST /api/v1/allocations
```

Conceptual request:

```json
{
  "filter": {
    "parent_slug": "neumann",
    "kind": "gpu",
    "capabilities": {"memory_gib__gte": 80}
  },
  "duration_minutes": 30,
  "earliest_start": "2026-06-20T08:00:00Z",
  "latest_end": "2026-06-20T10:00:00Z",
  "purpose": "Automated inference"
}
```

The server selects and reserves one matching asset atomically. Do not implement this until exact reservation correctness is proven.

### Reservation verification for gateways

A private service-to-service endpoint may return a minimal allow/deny decision. It requires separate audience-bound authentication and is not the ordinary user API.

### Extension

Reservation extension is deferred because it must be atomic, policy-aware, and conflict-safe.

## 8. Pagination

Use one consistent style for collection endpoints. The scaffold/API PR must choose either DRF limit/offset or cursor pagination and document maximum page size. Cursor pagination is preferred for audit/event feeds; simple limit/offset is acceptable for small inventory collections.

## 9. Rate limiting

Initial application-level throttling should protect authentication, token use, and mutation endpoints without pretending to be full DDoS protection. The reverse proxy applies request limits. Rate-limit responses use `429` and `Retry-After` where meaningful.

Do not depend on in-process counters for a multi-worker hard security guarantee. If distributed throttling becomes necessary, introduce shared state through an ADR.

## 10. Versioning and compatibility

- No breaking semantic or schema change within `/api/v1/` after beta without a migration/deprecation plan.
- Additive fields may appear; clients must ignore unknown fields.
- Enum additions require review because strict clients may break.
- Dates are always aware timestamps.
- IDs are opaque.
- OpenAPI generation is tested in CI.

## 11. Agent reference workflow

```text
GET assets matching requirements
GET availability for candidate asset
POST reservation with Idempotency-Key
on 409: choose another slot/asset and retry with a new key
run work through a separate mechanism
POST release with a new Idempotency-Key
```

The client must retain reservation IDs and must not infer entitlement from a successful availability read.
