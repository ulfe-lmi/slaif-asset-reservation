# oap/ — Concentrated OAP local control plane (candidate, inactive)

Generation 1, 2026-09-13. This tree is local candidate governance for the Codex-only
Concentrated OAP conversion. **Nothing here is active**: `oap/active` is absent,
`oap/orders/` and `oap/reports/` hold no execution state, and activation in
`runtime.env.example`/the private strategic-home copy is disabled.

Layout (see root `AGENTS.md` router and `docs/OAP-RUNBOOK.md` for operation):

- `coding-instructions/` — dense executor law (AGENTS.md) + compact cores.
- `strategic-instructions/` — full versioned strategic law, full strategic
  communication, init material, initial roadmap and expanded **inactive** drafts.
- `governance/` — MANIFEST.json (source/projection/installed identities),
  DISTILLATION-MAP.md (obligation coverage), CONTEXT-BUDGET.md (measured bytes),
  HUMAN-AUTHORITY.example.json (trust example, not authorization).
- `templates/` — work order, report, review checklist, CRITICAL entry, human
  adjudication and handoff templates.
- `audit/` — ICA protocol, templates and inactive request drafts.
- `prompts/` — tiny role prompts used by launchers.
- `bin/` — helper contracts (OAP-PROTOCOL OP-15) plus shared `oaplib.py` and the
  materialization engine. Default behavior is dry-run/no-op.
- `orders/`, `reports/` — immutable publication destinations; empty at bootstrap.
- `bootstrap-sources.lock.json` — locked identities of the bootstrap input snapshots.

Invariants: orders/reports are immutable once published; the active pointer is exactly
one order ID + LF or absent; CRITICAL.md at repository root is the only DHA register;
the strategic home keeps private state and never an editable canonical copy. No
operational CLAUDE.md or Claude launcher exists in this profile.
