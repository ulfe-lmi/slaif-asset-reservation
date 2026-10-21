<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "054-a",
  "objective": 54,
  "round": "a",
  "slug": "asset-reservation-calendar",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "1e469af959ef69e3624390ec591929b84f6c6774",
  "issue_number": 111,
  "branch": "codex/111-oap-054-a-asset-reservation-calendar",
  "pr_mode": "CREATE_OR_RESUME",
  "pr_number": null,
  "previous_round": null,
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "4566e797b709b71f13b2929572a2d1145d15a5a7ab8b41db50ebfdab962628cd",
    "PLAN.md": "8298ef941d02b05c304c48b46734ad678aff80b9ab4e62ca0814b6f03007277f",
    "ARCHITECTURE-for-agents.md": "41c32e0b0d6427a173dfe0b722446ae8ee311f3880929db65ed0245309b3a59e",
    "src/slaif_reservation/management_ui/auth.py": "05c25ff3b3141dbcb706d74119dc79be59268be7f365c487294d277b8467d5ef",
    "src/slaif_reservation/management_ui/views.py": "a42703a3178792d1a140ff5578d2846ccb594f8798ef76c93fff9920113237a5",
    "src/slaif_reservation/management_ui/selectors.py": "ae616a009ab3e8d61a0013d3004d5853de3fea701ec44acfbb3f1aeca28392b2",
    "src/slaif_reservation/reservations/models.py": "8edc0046d2a23580945d1a996a090d27c3e3a8e458c7d2ccc4309066d0b2fba9"
  },
  "requirements": ["SAR-012", "SAR-013", "SAR-019", "SAR-043", "SAR-050"],
  "allowed_paths": [
    "src/slaif_reservation/management_ui/urls.py",
    "src/slaif_reservation/management_ui/views.py",
    "src/slaif_reservation/management_ui/selectors.py",
    "src/slaif_reservation/management_ui/templates/management_ui/reservation_calendar.html",
    "src/slaif_reservation/management_ui/templates/management_ui/reservation_list.html",
    "src/slaif_reservation/management_ui/templates/management_ui/_nav.html",
    "src/slaif_reservation/web/templates/web/asset_detail.html",
    "src/slaif_reservation/web/static/web/site.css",
    "tests/test_reservation_calendar.py",
    "tests/browser/test_reservation_calendar_browser.py",
    "docs/authorization.md",
    "docs/human-ui.md",
    "oap/active",
    "oap/orders/054-a-asset-reservation-calendar.md",
    "oap/reports/054-a-asset-reservation-calendar.md"
  ],
  "forbidden_resources": [
    "No reservation/asset/account models, migrations, exclusion constraints, policy/domain services, token scopes/API, permission definitions or auth changes. Existing access predicate only.",
    "No dependency/lockfile, JavaScript calendar framework, Docker/Compose/proxy/settings/deployment, bootstrap/legacy import, architecture/projection/governance changes or unrelated UI redesign.",
    "No real deployment/exposure, private data, identities/secrets, DNS/TLS/firewall, production DB, lab/Neumann resources, foreign Docker/process cleanup, merge/automerge by CODING."
  ],
  "provenance": [
    {"marker": "H", "source": "Human request 2026-10-20: asset reservation calendar, one-week and four-week views, explicitly use CODING agent", "section_or_evidence": "The human asked whether staff can see an asset calendar and authorized implementation. Preserve the just-accepted permission model rather than treating Staff as a new blanket grant."},
    {"marker": "A", "source": "ARCHITECTURE.md A-16 / SAR-050, SAR-012/013/019/043; PLAN.md P-08", "section_or_evidence": "Explicit cross-user browser visibility is gated by view_all_reservations; owner-only member surfaces and privacy-safe advisory availability remain separate. Calendar is another read-only presentation of those existing records, not new authority or milestone meaning."},
    {"marker": "E", "source": "main 1e469af959ef69e3624390ec591929b84f6c6774, merged PR104/PR110, existing management UI", "section_or_evidence": "All reservations list/detail already checks view_all_reservations and supports asset/status/time filters; asset detail shows privacy-safe busy/free intervals but no calendar. Existing 53-row ICA applies to that base only; new route needs exact-head tests and freshness review."},
    {"marker": "I", "source": "Read-only current source inspection 2026-10-20", "section_or_evidence": "Reservation has start_at/end_at/effective_end_at and confirmed/cancelled/released status; cancellation does not block, released consumed interval ends at effective_end_at. Existing management list links to protected detail and uses active-human authorization decorator. No calendar route or template exists."},
    {"marker": "C", "source": "Selected one-feature purpose / issue111; CRITICAL remains empty", "section_or_evidence": "D0: render a bounded, responsive calendar using existing permission and model fields. Strongest objection is cross-user identity or stale/cancelled time accidentally disclosed as current occupancy; exclude cancelled from occupied calendar, label released consumed time, and test denials and half-open boundaries."}
  ],
  "decision_class": "D0",
  "target_gate": "One reviewed development PR for read-only asset calendar; no new milestone acceptance, production release or real deployment",
  "expected_report_path": "oap/reports/054-a-asset-reservation-calendar.md",
  "tests": [
    "Focused Django tests: unauthorized anonymous/member/staff-without-grant/direct request denied; active nonstaff with view_all admitted; invalid/missing asset/date/weeks bounded; one/four week navigation; exact asset; cross-window/overnight/DST intervals; half-open end exclusion; released effective-end clipping; cancelled absence with history link; output cap if needed; zero writes.",
    "Focused Chromium on real HTTP/PostgreSQL: desktop and 390px mobile one/four-week flows, authorized owner/detail links, nav, privacy denial, no horizontal overflow/framework branding, screenshots visually inspected (at most two images per review batch).",
    "Relevant existing management/asset authorization tests plus ruff/format/mypy/check/diff, normal full CI at final implementation/report heads, exact report verification and reviewed expected-head merge. Avoid unrelated bespoke qualification without a concrete dependency."
  ]
}
-->

# 054-a — read-only calendar for one asset

## Goal and scope

Add a server-rendered management calendar for one selected asset. A viewer may switch between exactly one and four consecutive Monday–Sunday weeks, with previous/next controls and a current-week starting point. The dates and display times use the viewer's configured profile timezone, including DST boundaries. Use the existing `view_all_reservations` application permission and active-human eligibility; Staff status alone is insufficient. No new permission or reservation authority is selected.

## Numbered acceptance

1. **Authorization and navigation.** New GET route under `/manage/reservations/`, guarded by the same `management_required("view_all_reservations")` as All reservations. Deny unauthenticated, inactive/service-account and active Staff-without-grant direct requests before protected row lookup. Expose calendar link from the authorized All reservations view and from an asset detail only when the user already holds that permission; keep the member availability presentation owner-private. Read-only viewer has no cross-user mutation action. Existing protected detail links remain gated.
2. **Truthful calendar window.** Require an existing exact asset. Parse bounded GET inputs for week anchor and view length `1` or `4` only; reject malformed/out-of-range input without traceback/unbounded query. Default to current local week. Show Monday–Sunday headings and previous/next links preserving asset and view length; switch lengths without losing the selected week. Query overlapping `start_at < window_end` and `effective_end_at > window_start` in aware time. Render confirmed intervals and released consumed intervals only; cancelled reservations remain in the All reservations history and must not be shown as occupied. Preserve `[start,effective_end)` half-open semantics and time zone/DST conversion. Show owner, status, displayed interval, and protected detail link. Distinguish released from confirmed and include a concise calendar-vs-history explanation.
3. **Bounded and usable layout.** No new dependency or client-side calendar framework. Use coherent existing SLAIF tokens, semantic day headings and keyboard links. Keep one-week and four-week desktop views legible; on 390px mobile show deliberate vertical day layout with no document-width overflow. If result count is capped, state it plainly and link to the filtered All reservations list so no silent omission occurs. Limit all query/output work to the fixed selected window and selected asset.
4. **Evidence and documentation.** Focused Django test of positive/negative permission matrix, active-human boundary, exact-asset isolation, one/four-week navigation/validation, cross-window and multi-day intervals, DST/profile timezone, half-open boundary, released/cancelled semantics, no POST mutation and bounded output. Chromium test at desktop/mobile captures a privacy-safe screenshot for each width/view, exercises links and asserts no overflow/visible framework branding. Coding must inspect screenshots visually in batches of at most two images. Update only the relevant human UI and authorization docs with this read-only path and required grant. No README ledger.

## Verification and negative paths

Run focused tests while editing, the relevant existing management/asset authorization checks, then the normal full CI once at final implementation head and again as required at report head. Retain exact results and screenshots privately or as safe CI artifacts; no image payload bundle over 16. Check no model/migration/API/token/auth/dependency/runtime bytes changed and no new migrations. Include source-level route/grant/temporal-query review, `git diff --check`, Markdown links. Browser must not show owner identity to unauthorized callers. Existing member asset availability remains privacy-safe and existing All reservations remains complete historical list.

## Recovery and report

This is a new objective after merged 053-b and clean main; issue111, branch/base above. CODING starts fresh in the existing right tmux pane, sources supervision `codex.sh` from the development checkout before its qualified `codex --yolo --profile qwen-neumann` launch, and uses the OAP wrapper/FIFO. If interrupted, resume this same order/PR, never historical 053-b. CODING commits/pushes implementation and opens one PR with `Closes #111`, then freezes literal implementation SHA and publishes a report-only child with `Report publication commit: SELF`. Verify remote report/parent/head and send exactly FIFO OK. Strategy reviews exact head, full diff and current required CI, then conditionally merges under existing development authority; real deployment and human milestone judgment remain separate.

## Deferred human adjudication
- Decision: NONE
