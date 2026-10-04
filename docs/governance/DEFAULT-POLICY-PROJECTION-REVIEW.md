# DEFAULT-POLICY-PROJECTION-REVIEW — 035-a successor mapping and measured context

Order: 035-a (fresh-install default reservation policy, 2026-10-05). This is the
**successor semantic mapping and context review** for the single A-15 amendment
issued by 035-a. It is a deliberate semantic comparison record, not an ICA, and
grants no authority beyond the order. The historical A-15 coverage mapping in
`INTERNET-UX-PROJECTION-REVIEW.md` (orders 032-a/b/c) is preserved unchanged;
nothing in the historical 032 coverage is rewritten or renumbered here.

## 1. Scope of this review

- Canonical source after 035-a: root `ARCHITECTURE.md`, SHA-256
  `f8a8df265d4dd452969d4bee874045c8f8a8261f9c87c96ba4c049a7dddf320d` — changed
  by exactly the one A-15 policy paragraph replacement the order mandates;
  SAR-001–SAR-047 section bodies, all other clauses and the 2026-09 baseline
  observations are byte-identical (paragraph-level comparison against the
  pre-order source SHA-256
  `06dd0f50e778b9843e2a709caa0ae1f0c97f48baee726f4e3a1397cc6a198d8c`).
- Compact projection after 035-a: `ARCHITECTURE-for-agents.md`,
  SHA-256 `653783d37e1260db8f5156b89b790bb497014756886693349f9bd1cc523fb38b`.
- `PLAN.md`: SHA-256
  `b19219e2d727af5a9554e011ba45a786f1bb61f25c001011fc18006cae665d08` —
  unchanged.
- The projection embeds the current full-source SHA-256 identity (updated to
  the actual post-amendment digest) and preserves the initial projection
  source SHA-256 (`9e7c60e4...`) as historical provenance.

## 2. Successor semantic mapping (old SAR-041 wording -> 035-a wording)

The 032-c clause stated the *obligation* in target form (auto-create on fresh
initialization, defaults "set by strategy later", idempotent/atomic/
upgrade-safe, manual fresh-policy creation disallowed). The 035-a clause states
the *decided implementation contract* that the amendment fixes:

| Facet | 032-c clause (historical) | 035-a clause (current) |
|---|---|---|
| Mechanism | "Fresh initialization auto-creates" (path unspecified: migration, safe initializer or bootstrap allowed) | `initialize_default_policy` command runs after `migrate`; explicit trusted CLI, never migration/startup/HTTP |
| Defaults | horizon 7 days by START, max 2880 minutes, no operating-hour window, lead 0, cutoff 0, purpose optional; other required fields "clear defaults" pending strategy | fully fixed: duration 1..2880 minutes, START horizon 7 days, no hours, lead/cutoff 0, purpose optional, upcoming 50 and proposed-interval overlap 8 per principal across assets and tokens |
| Overlap semantics | not stated | overlap counts intersecting blocking records, not a simultaneous-occupancy sweep |
| Idempotence/races | "idempotent, atomic, upgrade-safe, unique active-global" | repeats/races unique; atomic; any existing policy (incl. inactive/specific) prevents writes/reactivation/audit |
| Audit | not stated | atomic `reservation_policy.created` coupling, audit rollback tested |
| Manual policy step | "manual policy creation on normal fresh install disallowed" | "no ... manual fresh-policy step"; staff mutations unchanged |
| Caps | "required caps visible/documented" | unchanged obligation, now with concrete values |

No facet was dropped; the change is an obligation -> decided-contract
specialization. The root A-15 paragraph carries the full wording; the compact
clause remains a faithful condensation.

## 3. Context review (what 035-a touched and verified)

- Root `ARCHITECTURE.md`: one normative paragraph replaced (starts
  "Supported fresh initialization runs `initialize_default_policy`"); the
  historical 2026-09 baseline note in the `**Policies.**` paragraph and the
  SAR-041 audit-matrix row (source "human requirement 2 (2026-10-04); A-15")
  remain as written; the matrix row's "Initial independent-closure
  classification: UNPROVEN" stays in force — this implementation round is
  development evidence, not ICA, and the fresh isolated all-47 ICA at the
  exact merged revision remains required.
- Projection: clause-level replacement of the single SAR-041 line plus the
  header full-source digest; the other 46 clauses and sections are
  byte-identical to the pre-order projection
  (`26d26dac79043ed6b7b1e2ce4e134c5e6ccd6e9504f41f65339c76672bf59483`).
- No new mandatory full-source reads: the routine coding read set remains the
  table in section 4 plus the exact active order; root A-15 stays reference
  only for coding.

## 4. Measured context (exact UTF-8 bytes, measured on the committed files)

Transitive mandatory coding read set per the generation-1 convention
(archived `docs/bootstrap/archive/CONTEXT-BUDGET.md`): the routine coding read
set excluding the active order and product code:

| Component (installed path) | Exact bytes | Byte ceiling |
|---|---:|---:|
| `AGENTS.md` | 1058 | 2048 |
| `oap/coding-instructions/AGENTS.md` | 6403 | 12000 |
| `ARCHITECTURE-for-agents.md` | 19979 | 20000 |
| `OAP-COMMUNICATION-coding-agent.md` | 4105 | 10000 |
| `oap/coding-instructions/SECURITY-CORE.md` | 1410 | — |
| `oap/coding-instructions/TESTING-CORE.md` | 1947 | — |
| **Total (excluding order/code)** | **34902** | **50000** |

Projection alone: 19979 bytes ≤ 20000 (margin 21 bytes — small; further
growth will need explicit faithful redistillation, not truncation). Routine
read set: 34902 bytes ≤ 50000. Conservative wider sum (projection + PLAN.md +
this review) is 41897 bytes ≤ 50000. The 035-a order file itself is
order-scoped, not part of the routine transitive set, per the generation-1
convention.

Tokens: **UNMEASURED** — no qualified tokenizer for the configured model was
run; character estimates are not presented as exact counts (same convention
as generation 1).

## 5. Method and limitations

- The amendment was applied as an exact byte replacement from the order text;
  the embedded full-source SHA-256 was computed from the authorized amended
  bytes, not carried forward superficially.
- Semantic comparison (old vs new clause, and against root A-15) was performed
  deliberately as mapped in section 2. This is not an ICA and certifies
  nothing at runtime; SAR-041 remains UNPROVEN until the fresh isolated
  all-47 ICA at the exact merged revision.
- No product code, migration, dependency or archived byte changed by this
  governance step; the implementation itself lives in the 035-a code and test
  evidence reported separately.
