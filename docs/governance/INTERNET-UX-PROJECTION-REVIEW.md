# INTERNET-UX-PROJECTION-REVIEW — A-15 coverage and measured coding context

Order: 032-a (2026-10-04). This is a **semantic coverage record and measured context record** for
the selected Internet/UX target. It is a deliberate semantic comparison, not an ICA, and it
grants no authority beyond what the order grants.

## 1. Scope of this review

- Canonical source after this order: root `ARCHITECTURE.md` (2026-10-04 edition),
  SHA-256 `06dd0f50e778b9843e2a709caa0ae1f0c97f48baee726f4e3a1397cc6a198d8c`.
- Compact projection after this order: `ARCHITECTURE-for-agents.md`,
  SHA-256 of its content at measurement: `1b271b2fa41c57126d7e47e6ec4f6155e07dd7e2bbc873fc0227a16476227175`.
- `PLAN.md` after this order: SHA-256
  `c39f3f82b8493f751cb57388b46e4f61e1be1c82be1c9613ec09c3715634d0fc`.
- The projection embeds the current full-source SHA-256 identity and preserves the initial
  projection source SHA-256 (`9e7c60e4...`) as historical provenance.
- The generation-1 context budget record is preserved unchanged at
  `docs/bootstrap/archive/CONTEXT-BUDGET.md` (byte ceilings 50000 total / 20000 projection,
  tokens UNMEASURED). This document is its current successor for this target; it does not
  overwrite or renumber the archived record.

## 2. A-15 obligation -> requirement ID -> compact clause mapping

| A-15 obligation facet (root A-15, 2026-10-04) | Requirement ID (root A-14 map) | Compact projection clause |
|---|---|---|
| Product meaning: Internet-reachable authenticated service, normal HTTPS endpoint, friendly SLAIF browser experience; accounts administrator-created; landing is the only new anonymous surface; reachability does not imply anonymity or maturity; all prior guarantees continue | M-INTERNET-UX-PILOT (PLAN P-06) | Header scope + SAR-042 entry clause |
| Qualified topology: proxy/TLS -> loopback non-root Gunicorn -> private PostgreSQL17 (Linux amd64/x86_64); Gunicorn/PostgreSQL never directly published; Caddy baseline unless bounded investigation selects safer simpler proxy; trust only configured proxy peers; reject/ignore attacker forwarding; client IP/TLS header normalization; explicit hosts/CSRF origins; debug off; secure cookies; SSL redirect; HSTS deliberate opt-in; safe errors/headers; docs/schema disabled by default, staff-only when enabled; safe health; safe logs; fail-closed secrets; private DB/network; non-LAN administration | SAR-039 | `SAR-039 / Internet HTTPS/proxy boundary` |
| Shared abuse control: bound ordinary AND administration login and unauthenticated/invalid-bearer and authenticated API traffic; cross-worker/process coordination; configurable rates, trusted-client identity, expiry/cleanup, safe failure; no permanent lockout; stable API errors, owner privacy, CSRF, idempotency; multi-process/negative-path tests; proxy read/idle/body bounds | SAR-040 | `SAR-040 / Shared authentication and API abuse control` |
| Default fresh-install policy: `default` active global fallback (asset NULL; horizon 7 days by START; max 2880 minutes; no operating-hour window; lead 0; cutoff 0; purpose optional); clear defaults for other required fields; visible/documented upcoming-concurrent limits; idempotent, atomic, upgrade-safe, unique active-global; manual policy creation on normal fresh install disallowed | SAR-041 | `SAR-041 / Default fresh-install policy` |
| Public product entry: anonymous landing identity + Login + Administration, no private data; Administration enters administration login; role navigation without redirect loops; login excludes invalid/inactive/service-account identities | SAR-042 | `SAR-042 / Public product entry` |
| Browser product identity: SLAIF Asset Reservation / SLAIF-branded Administration across all user/admin/error/title/footer/breadcrumb surfaces; never visible Django/framework branding; structural admin customization; protected models explained | SAR-043 | `SAR-043 / Browser product identity` |
| Explained accessible forms: systematic member/staff/admin field + filter coverage; units/effects, horizon START semantics, lead/cutoff, resolution, purpose, DST occurrence relevance, human token scopes, high-impact actions, protected admin editing; labels/aria associations; no clutter; no weakened validation; humanized duration display, unchanged storage units | SAR-044 | `SAR-044 / Explained accessible forms` |
| Safe operator appearance overrides: self-contained defaults; read-only Docker/no-rebuild branding (logo/favicon/images/CSS after defaults); no source fork/image rebuild; no server-side template execution, remote JS, arbitrary file exposure or unsafe mount adoption; documented MIME/path/symlink/size/failure boundaries; default and custom fixtures Playwright tested | SAR-045 | `SAR-045 / Safe operator appearance overrides` |
| SLAIF design and visual qualification: current reference inspection (slaif.si/doc.slaif.si/edu.slaif.si/trainings); coherent accessible responsive CSS-token system; fixtures at ~1440/1024/768/390 default/custom; durable semantic assertions; no brittle pixel snapshots unless stable; privacy-safe screenshots; strategy visual iteration | SAR-046 | `SAR-046 / SLAIF design and visual qualification` |
| Threaded Gunicorn responsiveness: deliberate threaded pool consistently; six held idle/slow clients with bounded health/login response; old-sync negative control failing or equivalent sensitivity proof; owned cleanup on failure; documented worker/thread/keepalive rationale; buffering/time-limited HTTPS proxy retained; predecessor 031-a/PR62 gthread baseline observed (indexed, not ICA) | SAR-047 | `SAR-047 / Threaded Gunicorn responsiveness` |
| Qualification and human gate: real unit/integration, PostgreSQL concurrency/rollback, browser auth/CSRF/privacy, Gunicorn six-client regression, disposable Internet-shaped HTTPS proxy, production-settings negatives, container/config/health, fresh+upgrade policy init, default/custom branding; real Playwright capture/view/iterate; standard five exact-head checks + links/pip audit; final fresh isolated ICA over SAR-001–SAR-047 at exact merged revision; old internal-pilot ICA cannot qualify this target; human owns acceptance/release/real exposure/DNS/TLS/firewall/identity/secrets; development evidence may present one exact revision to D2, never deploy | A-15 final paragraph; SAR-038 (governance facet) | Header scope line ("real Internet exposure remains human D2"; "initially UNPROVEN until a fresh ICA") |

Coverage statement: every normative paragraph of root A-15 maps to at least one stable
requirement ID above, and every new ID (SAR-039–SAR-047) appears as a compact clause in the
projection. The original 38 projection clauses were preserved byte-identical; the projection's
API-boundaries section gained only the A-15 "disabled by default, staff-only when enabled"
clause for `/api/schema/` and `/api/docs/`.

## 3. Strategy-only decisions (explicit; not decided by this round)

1. Actual values of the default policy's other required fields — set by strategy in the
   initialization objective after semantic inspection (A-15 policy paragraph).
2. Proxy selection beyond the Caddy baseline, if bounded investigation finds a simpler safe
   optional configuration (A-15 topology paragraph).
3. Concrete abuse-control rate values, trusted-client identity scheme, expiry/cleanup
   parameters (A-15 abuse paragraph).
4. HSTS stays a documented deliberate opt-in; enabling it requires its own human/strategy
   decision with real certificate/domain qualification.
5. Visual iteration: strategy visually inspects qualification screenshots and orders
   iterations when quality is poor (A-15 qualification paragraph).
6. Issuance, ordering, base and PR mode of every future development order in the PLAN P-06
   draft sequence (all DRAFT UNTIL STRATEGIC RECONCILIATION; no PR/SHA exists).
7. Whether the merged 031-a gthread baseline is treated as the "foreign fix" to preserve or as
   the observed baseline to build on, when the runtime objective is issued.
8. Human-only (not strategy): milestone acceptance, release, real Internet exposure,
   DNS/TLS/firewall, identity, secrets and private data (D2).

## 4. Measured context (exact UTF-8 bytes, measured on the committed files)

Transitive mandatory coding read set per the generation-1 convention (archived
`docs/bootstrap/archive/CONTEXT-BUDGET.md`): the routine coding read set excluding the active
order and product code:

| Component (installed path) | Exact bytes | Byte ceiling |
|---|---:|---:|
| `AGENTS.md` | 1058 | 2048 |
| `oap/coding-instructions/AGENTS.md` | 6403 | 12000 |
| `ARCHITECTURE-for-agents.md` | 17328 | 20000 |
| `OAP-COMMUNICATION-coding-agent.md` | 4105 | 10000 |
| `oap/coding-instructions/SECURITY-CORE.md` | 1410 | — |
| `oap/coding-instructions/TESTING-CORE.md` | 1947 | — |
| **Total (excluding order/code)** | **32251** | **50000** |

Projection alone: 17328 bytes ≤ 20000. Read set: 32251 bytes ≤ 50000. Both ceilings hold with
margin. The 032-a order file itself (22034 bytes) is order-scoped, not part of the routine
transitive set, per the generation-1 convention.

Tokens: **UNMEASURED** — no qualified tokenizer for the configured model was run; character
estimates are not presented as exact counts (same convention as generation 1).

## 5. Method and limitations

- The projection was compiled after the full canonical source was applied; the embedded
  full-source SHA-256 was computed from the authorized final bytes.
- Semantic comparison (clause-by-clause against root A-14/A-15) was performed deliberately; the
  38 original clauses are byte-identical to the pre-order projection. This is not an ICA and
  certifies nothing at runtime.
- No hidden mandatory read of full architecture, PLAN or history is introduced by this order:
  the routine read set is exactly the table above plus the exact active order when one exists.
- No new framework, harness or test platform was introduced; no product, runtime, test,
  dependency, migration or archived byte changed.
- All SAR-039–SAR-047 rows are initially UNPROVEN; they are selected-target obligations, not
  implemented controls, and remain so until a fresh isolated ICA at the exact merged revision.
