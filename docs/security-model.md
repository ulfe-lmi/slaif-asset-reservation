# Security Model

**Status:** baseline threat model; update when trust boundaries change

## 1. Protected assets

- reservation integrity and availability;
- user identities and group/project membership;
- API bearer tokens and human sessions;
- administrator authority;
- asset inventory and physical identifiers;
- audit evidence;
- personal data associated with accounts/reservations;
- database backups and production configuration;
- future gateway trust credentials.

The application must not store machine SSH private keys, SmartScheduling credentials/cookies, OpenAI credentials, or arbitrary workload secrets.

## 2. Trust boundaries

1. Untrusted browser/network to reverse proxy.
2. Browser session and CSRF boundary to Django web views.
3. Bearer-token client to DRF API.
4. Application process to PostgreSQL.
5. Administrative user to privileged operations.
6. CI/Codex execution environment to repository and test services.
7. Future execution gateway to internal reservation verification.
8. Backup storage and restore operator.

## 3. Primary threats and controls

| Threat | Required controls |
|---|---|
| Account takeover | strong password policy for local auth, future OIDC, secure session cookies, login rate limits, admin protection |
| API token theft | high entropy, one-time display, one-way verifier, scopes, expiry, easy revocation, token redaction |
| Cross-site request forgery | Django CSRF middleware, same-site secure cookies, no unsafe GET mutations |
| IDOR / object access | centralized object-level authorization and non-disclosing not-found behavior where appropriate |
| Double booking race | PostgreSQL exclusion constraint and real concurrent integration tests |
| Booking hoarding | duration/horizon/concurrency policy, rate limits, audit, administrator controls |
| Privilege escalation | explicit roles/scopes, deny by default, no implicit admin API, tests for every role boundary |
| Audit tampering | append-only application model, restricted database role, backup, no ordinary delete/update path |
| Secret leakage in logs | structured allowlist logging, token/cookie/header filtering, tests and scans |
| Personal-data overcollection | email-centered identity, no required phone, approved retention and migration scope |
| Malicious metadata/XSS | server-side validation, template autoescaping, output encoding, safe Markdown policy if ever added |
| SQL injection | Django ORM/parameters, no unsafe string SQL, reviewed migrations |
| Dependency compromise | locked dependencies, minimal production set, Dependabot/automated review when configured, audit in CI |
| Denial of service | reverse-proxy limits, pagination, bounded queries, API throttling, DB indexes, no expensive anonymous endpoints |
| Time manipulation | server authoritative clock, aware timestamps, controlled test clock, no client-derived current time |
| Gateway spoofing, future | separate service credentials, audience restriction, short-lived signed decision or authenticated lookup |
| Agent scope creep during development | disposable runtime, no production secrets, `AGENTS.md`, branch protection, human merge authority |

## 4. Human sessions

Production settings must include, as applicable:

- `DEBUG = False`;
- explicit `ALLOWED_HOSTS` and trusted origins;
- secure, HTTP-only session and CSRF cookies;
- appropriate SameSite policy;
- HSTS after HTTPS is verified;
- secure proxy header configuration;
- session rotation on login and privilege change;
- logout and server-side invalidation where practical;
- admin access restricted by role and optionally network/VPN.

Local-auth password reset/email workflows must not reveal whether an account exists.

## 5. API token design

### Creation

- generate with a cryptographically secure random source;
- use enough entropy to resist offline guessing;
- include a non-secret prefix/identifier for lookup and operator display;
- display plaintext once;
- write only a verifier, prefix, owner, scopes, restrictions, and lifecycle metadata;
- audit creation without token plaintext.

### Verification

- never log the Authorization value;
- derive verifier using a dedicated server-side secret/pepper or reviewed password-hash design;
- constant-time compare;
- check expiry, revocation, owner state, scopes, and restrictions;
- fail closed if token configuration is incomplete;
- update last-use metadata safely and asynchronously only if later infrastructure supports it; authentication must not fail solely because last-use recording fails.

### Revocation and rotation

- immediate revocation;
- owner and admin views show prefix only;
- rotate by creating a new token, updating the client, and revoking the old token;
- no plaintext recovery endpoint;
- documented incident procedure before beta.

## 6. Authorization model

Authorization is action-specific. A principal may be able to see an asset but not reserve it, or read own reservations but not another user's purpose.

Every reservation command evaluates:

- principal active state;
- human role or token scopes;
- project/group membership;
- token resource restrictions;
- asset active/reservable state;
- effective policy;
- ownership for cancel/release;
- current time and lifecycle state.

Django admin permission is not automatically equivalent to domain authorization for custom APIs.

Work Order 0003 implements the internal reservation command layer and keeps reservation HTTP
mutations deferred. Successful reservation and policy mutations append `AuditEvent` rows in the same
database transaction. Creation locks the requesting principal, authoritative asset, and selected
effective policy. Cancellation locks requester, reservation, asset, and selected policy before
cutoff evaluation. Release is entitlement-reducing and does not depend on the asset or policy still
being active. PostgreSQL enforces exclusive overlap with the named
`reservation_no_overlap_per_asset` constraint; only that exact diagnostic constraint name is
translated to `reservation_conflict`.

Audit metadata validation rejects forbidden keys recursively through nested dictionaries and lists,
with case-insensitive key comparison and hyphen/space normalization. Forbidden metadata includes
passwords, tokens, cookies, authorization values, raw request bodies, email addresses, reservation
purpose, cancellation reason text, and private physical locators. Audit events are append-only
through ordinary model, queryset, bulk-update, delete, and admin workflows, but this remains
application/ORM enforcement, not tamper-proof protection against privileged database operators.
Retention, database-role separation, and backup hardening remain operational work.

## 7. Privacy and data minimization

Core personal data:

- display name;
- institutional/contact email;
- project/group membership;
- reservation purpose and lifecycle;
- safe audit metadata.

Not required by default:

- phone number;
- home address;
- personal notes;
- copied SmartScheduling client records;
- raw IP retention without policy.

Before production, document:

- lawful/organizational basis and user notice;
- retention periods;
- who may view purposes and audit logs;
- export/correction/deactivation process;
- backup retention;
- incident contact.

This document defines engineering controls, not legal certification.

## 8. Logging

Use structured logs with an allowlist of fields:

- timestamp;
- level;
- request/correlation ID;
- route name and method;
- response status and duration;
- safe principal UUID and token UUID/prefix;
- domain action and result code;
- safe asset/reservation UUID.

Forbidden:

- Authorization header;
- session/CSRF cookie;
- password or reset token;
- API token plaintext/verifier;
- full environment variables;
- database URL credentials;
- raw private request body;
- private legacy export rows.

Add tests that capture logs on authentication and failure paths.

## 9. Database and backup

- application DB role uses only required privileges;
- migrations use a controlled deployment role if separation is practical;
- PostgreSQL is private to the app/server network;
- backups are encrypted or stored in a protected institutional location;
- restore procedure is tested before beta;
- production data is not copied into Codex/CI environments;
- test fixtures are synthetic.

## 10. Web/API headers and transport

Reverse proxy and app must set or support:

- HTTPS redirects;
- HSTS after validation;
- `X-Content-Type-Options: nosniff`;
- frame-ancestor/Clickjacking protection;
- a Content Security Policy appropriate to local assets;
- conservative referrer policy;
- request body and header limits;
- CORS disabled by default or explicitly allowlisted for approved machine clients; ordinary non-browser agents do not require CORS.

## 11. Development and CI boundary

Codex and CI environments:

- contain no production credentials or personal exports;
- use disposable PostgreSQL data;
- may install development tools;
- cannot deploy or merge;
- use least-privilege GitHub tokens;
- must not print secrets from repository settings;
- report dependency/audit findings honestly.

## 12. Security tests before alpha

- unauthenticated and insufficient-scope API matrix;
- object-level access to assets/reservations;
- CSRF on every browser mutation;
- token expiry/revocation/owner-deactivation;
- token absent from DB plaintext and logs;
- request header redaction;
- concurrent overlap race;
- idempotency replay/different-body conflict;
- XSS/escaping for user-entered purpose;
- admin-only operations;
- secure production setting checks;
- dependency audit with findings triaged.

## 13. Release gates

The project may not claim production readiness until:

- threat model is re-reviewed against implemented code;
- authentication method for production is accepted;
- secrets handling is documented and tested;
- backup/restore drill succeeds;
- HTTPS and production security settings are verified;
- high-risk authorization and race tests pass;
- dependency/security scans are reviewed;
- incident and token-rotation runbooks exist;
- a human security/release decision is recorded.
