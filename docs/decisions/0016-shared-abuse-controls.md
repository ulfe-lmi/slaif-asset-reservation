# Shared authentication and API abuse controls

Use atomic PostgreSQL counters in the existing monolith. Per-process memory
would multiply allowances by the worker count. Ordinary cache-based DRF
throttles use non-atomic operations; adding Redis or proxy plugins would add
another production dependency without improving this bounded deployment path.

Counters use a scoped HMAC key, fixed window and indexed expiry. They store
neither client addresses, email identities nor bearer credentials. PostgreSQL
UPSERT serializes increments; counts saturate at the limit plus one. Login
routes share source and normalized identity budgets. All API requests consume
a source budget before authentication, and valid tokens consume both account
and token budgets. Rejected requests cannot create domain mutations or
successful idempotency records.

The default allowances are configurable positive integers:

| Budget | Allowance | Window |
|---|---:|---:|
| Member and Administration login, source | 30 attempts | 5 minutes |
| Member and Administration login, identity | 10 attempts | 5 minutes |
| API, source | 1,200 requests | 1 minute |
| API, account across its tokens | 600 requests | 1 minute |
| API, individual token | 300 requests | 1 minute |

Fixed windows permit a boundary burst. Shared NATs can share the source
allowance; operators can raise it deliberately. No account flag/password is
changed and no permanent account lockout exists. HTTP429 gives Retry-After,
no-store and a stable API problem/correlation. Counter failure denies protected
operations with a generic503; liveness does not depend on counters or the DB.
Connection waits default to5seconds; production accepts1–30seconds. Counter
transactions bound row-lock/statement waits to1/2seconds.

One in128 counter operations attempts cleanup of at most100 expired rows.
`purge_expired_abuse_buckets` is read-only by default; `--apply --batch-size`
removes a bounded batch of expired records. No scheduler or monitoring service
is installed. Operators should inspect retention and run cleanup as needed.

These are application abuse controls, not distributed or volumetric DDoS
protection. They depend on the documented trusted proxy/client identity and
operator-controlled service host. Real Internet exposure remains a human gate.
