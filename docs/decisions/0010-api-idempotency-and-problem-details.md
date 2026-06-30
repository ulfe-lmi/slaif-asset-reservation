# ADR 0010: API Idempotency and Problem Details

## Status

Accepted for Work Order 0006.

## Context

Software agents need reservation APIs that can be retried safely after network failures. A retry must
not create duplicate reservations, duplicate audit events, or expose database internals. The API also
needs stable machine-readable errors that clients can map without scraping exception text.

## Decision

API mutation endpoints require an `Idempotency-Key` header. The key is a client-generated opaque
value, 8 through 128 printable ASCII characters, excluding whitespace and control characters. It is
not a secret and must not be used as authorization.

The server canonicalizes each mutation request as JSON containing:

- action code;
- HTTP method;
- request path;
- parsed request body.

The canonical JSON uses sorted keys and compact separators, then stores only a SHA-256 hash. Raw
request bodies, bearer tokens, `Authorization` headers, session cookies, CSRF values, token secrets,
verifiers, peppers, and passwords are never stored in idempotency records.

Idempotency is scoped to:

- owner user;
- API token;
- action;
- idempotency key.

For the same owner, token, action, and key:

- same canonical request returns the stored safe response and does not execute the domain mutation
  again;
- different canonical request returns `409 idempotency_conflict` and does not execute the mutation.

Different owners or tokens may reuse the same key independently. Records carry an `expires_at`
timestamp with a 24-hour retention target. Until cleanup is implemented, existing records remain
authoritative for replay/conflict decisions; expired rows are not silently reused.

Mutation handling runs inside `transaction.atomic()` and locks the idempotency row with
`select_for_update()`. Concurrent identical requests therefore produce one domain mutation and one
stored replay. Concurrent same-key/different-body requests produce one mutation and one
`idempotency_conflict`.

All API responses from bearer-token endpoints include a correlation UUID. A valid UUID
`X-Request-ID` is accepted; malformed values are replaced. The correlation ID is passed into
reservation domain services where available and appears in audit events for successful mutations.

Problem responses use JSON with:

- `type`;
- `title`;
- `status`;
- `code`;
- `detail`;
- `correlation_id`.

Problem responses never include ORM exception text, SQL, constraint names, stack traces, bearer
tokens, token IDs as failure hints, secrets, verifiers, peppers, or authorization headers.

Bearer authentication is enabled only on the new Work Order 0006 endpoints. The existing
staff-session asset list/detail API remains staff-session-only. Token lifecycle APIs, project or
resource restrictions, service-account/admin tokens, and administrative reservation APIs remain
deferred.

## Consequences

Clients can retry API mutations safely, but they must generate and retain idempotency keys for retry
windows. PostgreSQL remains the final arbiter of reservation conflicts; idempotency prevents duplicate
execution of the same API request, not business-rule conflicts with other requests.

Because expired idempotency rows are not cleaned up in this slice, operators will need a future
cleanup command or scheduled maintenance policy before long-running deployments.
