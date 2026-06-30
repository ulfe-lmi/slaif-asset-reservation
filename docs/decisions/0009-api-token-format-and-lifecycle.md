# ADR 0009: API Token Format and Lifecycle

**Status:** Accepted
**Date:** 2026-06-24

## Context

Work Orders 0001-0004 established human sessions, asset inventory, reservation services, audit
evidence, and the human MVP. Software agents now need separately revocable credentials, but token
access must not be enabled on API endpoints until scoped permissions and idempotency records are
implemented in Work Order 0006.

## Decision

The initial bearer token grammar is:

```text
sar_<token_uuid_hex>_<secret>
```

`token_uuid_hex` is the token UUID without hyphens. It is a public database lookup locator, not a
secret. The human-visible non-secret prefix is `sar_<first 12 UUID hex characters>...`.

The secret is generated with a cryptographically secure construction providing at least 256 bits of
randomness. The database stores no complete bearer token and no plaintext secret. It stores an
HMAC-SHA-256 verifier over the complete bearer token using `SLAIF_API_TOKEN_PEPPER`, a dedicated
server-side pepper distinct from Django `SECRET_KEY`. Verification uses constant-time comparison.

Production settings fail closed when the pepper is absent, shorter than 32 UTF-8 bytes, equal to
`SECRET_KEY`, or equal to any committed development/test placeholder, including whitespace-padded
forms. Replacing the single pepper invalidates all existing tokens until a future key-ring or
rotation design is accepted.

Initial scopes are the immutable allowlist:

```text
assets:read
availability:read
reservations:read
reservations:create
reservations:cancel
reservations:release
```

Scopes are canonicalized as a sorted unique JSON list. There are no admin, wildcard, cross-user,
project, or resource-restriction scopes in this slice.

Token expiry is mandatory. `API_TOKEN_MAX_LIFETIME_DAYS` defaults to 90 days and may be configured
from 1 through 365. Expiry is exclusive: at `expires_at`, authentication fails. Revocation is
immediate, owner-only in this slice, idempotent, and preserves verifier, scopes, expiry, prefix, and
history. `last_used_at` is best-effort metadata and must not make otherwise successful
authentication fail.

Token plaintext is displayed once in the owner web UI. It is not stored in the session, messages,
database, logs, audit metadata, URLs, hidden inputs, cookies, local storage, session storage, or
HTML data attributes. The one-time response keeps `Cache-Control: no-store, private`, `Pragma:
no-cache`, and `Referrer-Policy: no-referrer`, and a small local script clears the visible token
element on `pagehide`/bfcache restoration so browser history cannot recover the plaintext when a
browser preserves the page. Creation and revocation write audit events with only safe metadata:
display prefix, canonical scopes, and expiry.

Credential-bearing result, parser, and one-time display objects must not expose bearer tokens or
secret segments through `repr`, equality comparisons, or Django exception reports. Functions that
temporarily hold bearer credentials, token secrets, verifiers, or peppers mark those locals
sensitive. Authentication redacts the request Authorization header before any downstream
unexpected exception can render a Bearer attempt.

Audit metadata validation rejects token-secret key concepts recursively at every nesting depth,
including token secret, verifier, pepper, bearer token, API token plaintext, and Authorization
header variants. It also rejects complete SLAIF bearer-token-shaped string values under otherwise
innocuous keys while allowing safe display prefixes such as `sar_0123456789ab...`.

The ORM boundary blocks ordinary overwrite, queryset update/delete, bulk create/update, instance
delete, and reconstructed-object overwrite paths, including paths through the model base manager.
Service-authorized lifecycle writes still compare immutable history fields against the stored row
before saving; only revocation fields together or `last_used_at` may change. Creation authorization
is distinct from lifecycle-update authorization. This is application/ORM protection, not a
database-trigger guarantee against privileged database operators.

The custom DRF bearer authenticator is implemented in this slice for direct verification tests, but
it is not registered globally and is not enabled on the asset API, API root, schema/docs, or any
reservation route. It parses the HTTP authentication scheme case-insensitively while preserving
genuine non-Bearer `Authorization` headers byte-for-byte for later authenticators. Work Order 0006
will bind bearer authentication, scope permissions, and idempotency records to API endpoints.

## Consequences

- Tokens have a simple auditable lifecycle without storing recoverable plaintext.
- Agents can prepare credentials before API mutation routes exist.
- Operators must protect `SLAIF_API_TOKEN_PEPPER`; losing or replacing it invalidates existing
  tokens.
- A future rotation/key-ring ADR is required before supporting multiple active peppers or verifier
  algorithms.
