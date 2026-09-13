# DISTILLATION-MAP — full law to compact executor projection

Generation 1. Canonical full strategic source: `oap/strategic-instructions/AGENTS.md`
(S-01..S-24); dense coding projection: `oap/coding-instructions/AGENTS.md` (C-01..C-16);
compact architecture: `ARCHITECTURE-for-agents.md` (source SHA-256 `%s`);
compact communication: `OAP-COMMUNICATION-coding-agent.md` (CP-01..CP-09).
Every strategic obligation is either mapped to compact clause(s) or explicitly marked
not executor-applicable with a reason. Mechanical checks verify IDs/coverage/bytes; the
semantic comparison was deliberately reviewed at materialization (see receipt) and is NOT
an independent audit.

## S -> C obligation map

| Strategic clause | Obligation summary | Compact clause(s) | Executor applicability / rationale |
|---|---|---|---|
| S-01 — Role and durable identity | STRATEGIC role identity persists across incarnations; repository inspection does not transfer authority; private copy installed from versioned source. | C-01 | Fully executor-applicable: role retention, no transfer by inspection, private copy provenance. |
| S-02 — Human ownership and evidence hierarchy | Human owns meaning/risk/D2/DHA/target/release; evidence hierarchy remote>orders>runtime>notification>claims. | C-03 | Fully applicable: authority split and evidence hierarchy; strategic-only nuance (stale-PR discipline) preserved in C-02/C-06. |
| S-03 — Startup and recovery read set | Ordered startup read set; CRITICAL loaded at startup/dilemmas/gates, not always-injected. | C-04, C-05 | Executor read order in C-04; strategic full read set not executor-applicable (marked, not dropped). |
| S-04 — Preserve the existing product | WO0001-0013 are history; preserve remote/ancestry/ADRs/bytes/SAR invariants; no recreation or Neumann/SmartScheduling work. | C-02, C-10 | Fully applicable: historical WO0001-0013, bytes, invariants, no recreation. |
| S-05 — Architecture stewardship | One canonical architecture/plan; stable requirement IDs; scope cannot disappear; never paper over contradictions. | C-10 | Stewardship duties strategy-only (marked not executor-applicable); executor keeps invariant preservation and drift stop. |
| S-06 — D0 and diagnosis | D0 decide/verify/continue; bounded diagnosis; first failing boundary; supersede interpretations explicitly. | C-07 | Fully applicable: routine decisions, first-failing-boundary discipline. |
| S-07 — D1 is a duty to choose safely | D1: investigate alternatives, choose, mitigate, test, order complete CRITICAL entry; never use D1 to waive controls. | C-07, C-08 | Strategy choice duty marked strategy-only; executor NEVER chooses/admits D1 (C-07) and handles exact APPEND bytes (C-08). |
| S-08 — D2 and protected resources | D2 list for this project; analyze/recommend only; no crossing without attributable human authorization. | C-07, C-09 | Fully applicable: project-specific D2 list in DECISION-POLICY; executor must not cross. |
| S-09 — Exact DHA admission | All-five admission conditions; exclusions; empty register is not risk acceptance. | C-08 | Admission conditions strategy-owned; executor sees exact byte/digest/prefix contract only. |
| S-10 — Exact DHA authoring and mutation | Strategy owns ID/admission/wording; exact payload+digest+prior identity; no invented PRs; coding appends ordered bytes only. | C-08 | Fully applicable to the append side; authoring side strategy-only (marked). |
| S-11 — Human adjudication is attributable | Four exact disposition values; latest attributable ACCEPTED clears scoped gate; names are not proof; no agent disposition. | C-08, C-15 | Executor: never adjudicate, never dispose; provenance values in templates; full verification policy strategy/human (marked). |
| S-12 — Work orders and provenance | One proof-sized objective per branch/PR; H/A/E/I/C concrete; drafts DRAFT UNTIL STRATEGIC RECONCILIATION; no fake metadata. | C-04, C-05, C-11 | Executor consumes FINAL orders with provenance; authoring side strategy-only. |
| S-13 — Publication and serialization | Strategy publishes order then pointer under one lock; signal after both; pointer/ID selection only; no reactivation. | C-05, C-11, C-13 | Executor side: commit exact order/pointer bytes, PR before report; serialization owned by strategy helpers (marked). |
| S-14 — Fresh coding and persistent strategy | Fresh coding per round; strategy continuity; no model polling; duplicate/restart reconciles same objective; explicit quit. | C-05, C-06, C-08, C-13 | Fully applicable: fresh round, no renumbering, duplicate suppression, quit. |
| S-15 — Implementation and report boundary | PR before report; literal implementation head; report-only SELF commit; post-push private verification; no further mutation. | C-11, C-12 | Fully applicable: full sequence and literal report lines. |
| S-16 — Exact-head strategic review | Independent exact-head review; required CI at reviewed head; changed head invalidates; strongest reason not to merge. | — (strategy-only) | Not executor-applicable: review duties; executor supplies truthful evidence (C-14). |
| S-17 — Conditional development merge | Delegated development merge only under attributable scoped activation; side-effect check; coding never merges. | C-03 | Merge authority strategy-only under delegation; executor NEVER merges/auto-merges (C-03, C-16). |
| S-18 — Adoption before operation | Bootstrap local candidate only; adoption PR human-merged; no self-approval; quiescent refresh; existing state preserved. | C-16 | Fully applicable: distinct roles, no bootstrap activation, human adoption gate. |
| S-19 — Evidence discipline and runtime safety | Named commands/revision/results; real boundaries for real claims; disposable resources; no destructive baseline tests on valuable checkout. | C-09, C-14, C-15 | Fully applicable: status labels, real-boundary evidence, privacy, disposable resources. |
| S-20 — Projection stewardship | Author full law first; preserve obligation facets; map or mark; measure context; no hidden full-source links; second pass is not ICA. | C-04, C-10 | Authoring side strategy-only (marked); executor enforces read set and drift stop. |
| S-21 — Privacy and secret handling | No credentials/private exports in any artifact; private role homes; clean URLs; redacted output; visibility change is D2. | C-15 | Fully applicable. |
| S-22 — Combined risk and target scope | Combined exposure review; keep acceptance/demo/confidence/judgment/target/release separate; no count-as-functionality. | — (strategy-only) | Not executor-applicable: accumulated-risk review; executor keeps per-order scope (C-10). |
| S-23 — Independent closure audit | ICA mandatory pre-milestone; fresh isolated context or independent human; full architecture + exact revision; honest provenance. | C-16 | Auditor context duties marked not executor-applicable; executor never self-certifies (C-14/C-16). |
| S-24 — Handoffs and termination | Durable private handoffs; no secrets/canonical copies; lost notification = review; quit follows RECOVERY.md. | C-08, C-13, C-16 | Executor side: recovery transitions, quit, handoff references; strategic handoff content strategy-only. |

## Legacy root AGENTS.md obligations (pre-conversion, archived)

| Legacy obligation (archived AGENTS.md / docs) | Where preserved in the new law |
|---|---|
| Product promise: authoritative, auditable, policy-compliant, conflict-free reservations | Root ARCHITECTURE.md A-01/A-06 + SAR-001/SAR-007/SAR-009; coding C-02 |
| Read discovery/architecture/domain/API/security/testing docs + assigned work order before changing behavior | C-04 ordered read set (compact); order-scoped full reads permitted by the order |
| Live repository and accepted ADRs are authoritative; report work-order/main discrepancies | C-02/C-06 reconcile remote before edit; C-07 report boundary |
| Product boundaries: no execution/SSH/power/billing/SaaS/SPA/brokers; no salon-concept reproduction | ARCHITECTURE.md A-01/A-02 + SAR-002/SAR-036; C-02 non-goals |
| Accepted technical baseline (Python 3.13/Django 5.2/DRF 3.16/PostgreSQL 17/uv.lock) and no opportunistic upgrades | SAR-022; C-10 |
| Testing discipline: exact commands, real PostgreSQL/browser, negative paths, no skipped-as-passed | TESTING.md + TESTING-CORE (TC-01..TC-06); C-14 |
| Secrets/personal data never in commits/issues/PRs/fixtures/logs | SECURITY.md + SECURITY-CORE (SC-01..SC-05); C-15 |
| Human retains every merge (old workflow) | Superseded only after adoption+activation: S-17/C-03 conditional development merge; adoption PR remains human-merged (ADR 0014) |
| ADR required for architectural/security-boundary/persistence/auth/deployment changes | S-05 stable IDs + ADR 0014 process; D0/D1/D2 policy (docs/DECISION-POLICY.md) |

## RC / OP / BA coverage

| Source | Clauses | Compact/helper realization |
|---|---|---|
| ROLE-CONTEXT | RC-01..RC-05 | Four-role routing (root router), client qualification (docs/AGENT-ROLE-SETUP.md), read sets/budgets (C-04, CONTEXT-BUDGET.md), distillation artifacts (this file, CONTEXT-BUDGET.md, MANIFEST.json), integrity domains (MANIFEST.json + lock + dynamic state separation) |
| OAP-PROTOCOL | OP-01..OP-16 | OAP-COMMUNICATION-coding-agent.md CP-01..CP-09 for the executor side; full OP text installed at oap/strategic-instructions/OAP-COMMUNICATION-strategic.md; helpers per OP-15 table |
| BOOTSTRAP-ACCEPTANCE | BA-00..BA-52 | tests/oap executable suite; each case names its test module in the receipt |
| ARCHITECTURE | SAR-001..SAR-038 | ARCHITECTURE-for-agents.md carries all 38 mapped invariants; oap/COMPLETENESS.md and oap/audit/ICA-REQUIREMENT-MATRIX-TEMPLATE.md carry closure rows |
| Legacy source obligations | see table above | preserved, not silently dropped |

## Review notes (semantic second pass, generator-performed)

- Every S-clause above was compared clause-by-clause against C-01..C-16; strategy-only
  facets are marked, none deleted.
- No compact file mandates reading full PLAN/ARCHITECTURE/strategy/source books or the
  historical register (verified mechanically in tests/oap and by link scan).
- Hash checks bind identity only; this map is coverage evidence, not proof of
  losslessness, D1 correctness or human authority.
