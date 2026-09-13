# oap/ — Concentrated OAP local control plane (slim, operational)

Generation 1 was simplified by round 015-a (issue #29, the first operational
round and the M-CONVERSION round-trip canary) to the smallest understandable
orchestration layer. The bootstrap/materialization machinery was archived
byte-identical under `docs/bootstrap/archive/` (see its ARCHIVE-NOTE.md); the ICA
protocol and drafts live under `docs/audit/`.

Layout (see root `AGENTS.md` router and `docs/OAP-RUNBOOK.md` for operation):

- `coding-instructions/` — dense executor law (AGENTS.md) + compact cores.
- `strategic-instructions/` — full versioned strategic law, full strategic
  communication, init material, initial roadmap and expanded drafts.
- `governance/` — HUMAN-AUTHORITY.example.json (trust example, not authorization).
- `templates/` — work order, report, CRITICAL entry and human adjudication templates.
- `prompts/` — tiny role prompts used by launchers.
- `bin/` — helper contracts (OAP-PROTOCOL OP-15) plus shared `oaplib.py`:
  `publish_order.py` (two recoverable publication writes), `oap_launch.py`
  (fresh-per-round coding / long-lived strategic wrappers, setup tmux),
  `check_state.py`, `append_critical.py`, `verify_report.py` (exactly three
  checks), `oap_fifo.py`, `oap_doctor.py` (structural + operational), and
  `check_ica.py` (milestone-use, off the normal round path).
- `orders/`, `reports/` — immutable publication destinations.
- `active` — the pointer: exactly one order ID + LF, or absent (inactive).
- `RECOVERY.md` — the state machine and recovery protocol.

Final order schema (slim, ten fields): `id`, `round`, `base_sha`, `issue_number`,
`branch`, `pr_mode`, `previous_round`, `allowed_paths`, `forbidden_resources`,
plus exactly one DHA body declaration. Already-published 25-field superset
orders remain valid.

Invariants: orders/reports are immutable once published; the active pointer is
exactly one order ID + LF or absent; CRITICAL.md at repository root is the only
DHA register; the strategic home keeps private state and never an editable
canonical copy. No operational CLAUDE.md or Claude launcher exists in this
profile. Coding never merges; the development merge gate and ICA/human
milestone acceptance remain separate.
