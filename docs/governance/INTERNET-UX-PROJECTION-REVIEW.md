# INTERNET-UX-PROJECTION-REVIEW — A-15 coverage and measured coding context

Orders: 032-a (initial, 2026-10-04), 032-b (strategic second pass on the same objective,
2026-10-04; not an ICA) and 032-c (D0 single-phrase negation correction of the SAR-041
clause, 2026-10-04; not an ICA). This is a **semantic coverage record and measured context
record** for the selected Internet/UX target. It is a deliberate semantic comparison, not
an ICA, and it grants no authority beyond what the orders grant.

## 1. Scope of this review

- Canonical source after these orders: root `ARCHITECTURE.md` (2026-10-04 edition),
  SHA-256 `06dd0f50e778b9843e2a709caa0ae1f0c97f48baee726f4e3a1397cc6a198d8c` — unchanged by
  032-b (identity carried from 032-a, not a hash rewrite).
- Compact projection after 032-c: `ARCHITECTURE-for-agents.md`,
  SHA-256 of its content at measurement: `26d26dac79043ed6b7b1e2ce4e134c5e6ccd6e9504f41f65339c76672bf59483`.
- Preceding projection after 032-b (superseded SAR-041 wording; historical):
  SHA-256 `09d2157df1a57a312071f818fcb2600bee65abce213aa268f657fb67ab3b3cf3`.
- `PLAN.md` after 032-b: SHA-256
  `b19219e2d727af5a9554e011ba45a786f1bb61f25c001011fc18006cae665d08`.
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
| Qualification and human gate: real unit/integration, PostgreSQL concurrency/rollback, browser HTTP auth/CSRF/privacy, real Gunicorn positive plus old-sync negative, disposable Internet-shaped HTTPS proxy, shared abuse controls, production-settings negatives, container/Compose/health, fresh+upgrade policy init, default/custom branding; full browser-surface inventory; real Playwright capture/view/iterate at ~1440/1024/768/390 desktop/mobile default/custom with mandatory STRATEGIC visual review; durable semantic assertions; privacy-safe screenshots; standard five exact-head checks + links/pip audit; exact source/revision/evidence statuses, no mocked-boundary pass; final fresh isolated full-architecture ICA over SAR-001–SAR-047 at exact merged revision AFTER implementation; old internal audit historical; repair then FULL architecture-to-current-main re-audit; human owns acceptance/release/real exposure/DNS/TLS/firewall/identity/secrets; development evidence may present one exact revision to D2, never deploy | A-15 final paragraph; SAR-038 (governance facet) | `Selected target qualification (A-15)` clause (added by 032-b); the header scope line is a classification, not the verification clause |

Coverage statement: every normative paragraph of root A-15 maps to at least one stable
requirement ID above, and every new ID (SAR-039–SAR-047) appears as a compact clause in the
projection. 032-b strengthened the SAR-039–SAR-047 clauses with their explicit facet
conditions, added the `Selected target qualification (A-15)` clause carrying the
verification scope, browser-surface inventory and ICA sequence directly, and removed the
repeated per-row filler (the header classification applies to all new rows). The original 38
projection clauses remain byte-identical; the projection's API-boundaries section still
carries only the A-15 "disabled by default, staff-only when enabled" clause for
`/api/schema/` and `/api/docs/`.

## 3. Strategy-only decisions (explicit; properly scoped future D0 decisions, each decided only when its objective is strategy-issued)

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
7. (Resolved by 032-b, superseding the 032-a open question) Bounded search of the repository
   found no foreign Gunicorn fix; the old sync starvation was independently reproduced and
   remediated by 031-a/PR62, merged on main. Preserve any foreign fix if later found.
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
| `ARCHITECTURE-for-agents.md` | 19974 | 20000 |
| `OAP-COMMUNICATION-coding-agent.md` | 4105 | 10000 |
| `oap/coding-instructions/SECURITY-CORE.md` | 1410 | — |
| `oap/coding-instructions/TESTING-CORE.md` | 1947 | — |
| **Total (excluding order/code)** | **34897** | **50000** |

Projection alone: 19974 bytes ≤ 20000 (measured margin 26 bytes — small, not a large
margin; further growth will need explicit faithful redistillation, not truncation). Routine
read set: 34897 bytes ≤ 50000. Conservative wider sum (projection + PLAN.md + this review,
all post-032-c bytes) also stays under 50000 bytes (49710 bytes). The 032-a, 032-b and
032-c order files themselves are order-scoped, not part of the routine transitive set, per
the generation-1 convention.

Tokens: **UNMEASURED** — no qualified tokenizer for the configured model was run; character
estimates are not presented as exact counts (same convention as generation 1).

## 5. Method and limitations

- The projection was compiled after the full canonical source was applied; the embedded
  full-source SHA-256 was computed from the authorized final bytes.
- Semantic comparison (clause-by-clause against root A-14/A-15) was performed deliberately; the
  38 original clauses are byte-identical to the pre-order projection. This is not an ICA and
  certifies nothing at runtime.
- No hidden mandatory read of full architecture, PLAN or history is introduced by these
  orders: the routine read set is exactly the table above plus the exact active order when one
  exists; root A-15 is reference-only for coding.
- No new framework, harness or test platform was introduced; no product, runtime, test,
  dependency, migration or archived byte changed.
- All SAR-039–SAR-047 rows are initially UNPROVEN; they are selected-target obligations, not
  implemented controls, and remain so until a fresh isolated ICA at the exact merged revision.
- 032-b (strategic second pass, not an ICA): the SAR-039–SAR-047 clauses now state their
  explicit facet conditions; the qualification facet maps to the new `Selected target
  qualification (A-15)` clause instead of a header-only classification; the PLAN sequence row
  is corrected (runtime delivered by PR62, not backlog; architecture-contract slice
  documentation-only; the proxy row owns deployment configuration in a future order); the
  M-LOCAL milestone is recorded as historical/superseded, not queued replay. The canonical
  full-source SHA-256 is unchanged from 032-a; the projection was recompiled by clause-level
  replacement so the 38 original clauses stay byte-identical. Semantic limitations: the
  compact clauses are faithful condensations of the A-15 facets — the full facet wording
  remains in root A-15 (reference only) and in this mapping; byte ceilings are measured on
  committed bytes, tokens remain UNMEASURED.

## 6. 032-c correction (superseding note)

- The preceding compact wording of the SAR-041 clause, `no silent overwrite, reactivation
  supported;`, was incorrect and is superseded by this precise correction: the full
  architecture's default fresh-install policy requires existing operator policies
  (including deliberate inactive configuration) to be preserved, so initialization must not
  silently reactivate operator-inactive booking authority. 032-c replaces that single
  phrase with `no silent overwrite or reactivation;`. No reactivation feature is added and
  no future operator workflow is inferred.
- The 032-b projection hash
  `09d2157df1a57a312071f818fcb2600bee65abce213aa268f657fb67ab3b3cf3` is preserved above as
  historical; sections 1 and 4 carry the actual recomputed post-032-c identity and byte
  measurements. The 032-b review byte figure (12353) differed by 2 bytes from the actually
  committed review (12355); this record reports the actual committed bytes.
- Projection byte change: 19982 -> 19974 (-8 bytes) from the one-phrase replacement; every
  other normative clause is byte-identical (clause-level comparison against the committed
  pre-032-c bytes). The margin against the 20000-byte ceiling is small, not large; further
  growth will need explicit faithful redistillation, not truncation.
- The old semantic mapping and historical records in this file are preserved without
  renumbering; only the superseded wording, its hash and the byte measurements are amended.
