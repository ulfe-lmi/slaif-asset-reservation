<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "054-b",
  "objective": 54,
  "round": "b",
  "slug": "calendar-review-closure",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "1e469af959ef69e3624390ec591929b84f6c6774",
  "issue_number": 111,
  "branch": "codex/111-oap-054-a-asset-reservation-calendar",
  "pr_mode": "AMEND",
  "pr_number": 112,
  "previous_round": "054-a",
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "4566e797b709b71f13b2929572a2d1145d15a5a7ab8b41db50ebfdab962628cd",
    "PLAN.md": "8298ef941d02b05c304c48b46734ad678aff80b9ab4e62ca0814b6f03007277f",
    "ARCHITECTURE-for-agents.md": "41c32e0b0d6427a173dfe0b722446ae8ee311f3880929db65ed0245309b3a59e",
    "src/slaif_reservation/management_ui/views.py": "a4214a0262c442d8ba2287bc1f7e2fd2b53990a9546bd8a40c272b40c128e06e",
    "src/slaif_reservation/management_ui/templates/management_ui/reservation_calendar.html": "708cf0f5ccb8fa0ff22c728fca97f3072cc0db74b3c52d416ba2f6d1131bbe7a",
    "tests/test_reservation_calendar.py": "8a9ed41d89f0f4060a2733a04370d87745bed5a0d399d035d8275195dfb43aab",
    "uv.lock": "d66d27aaf77fb282b90599c333d005194c6bac43396047e3d72fe3332d38605a",
    "docs/authorization.md": "dd0785a35c13fd9297963b906f2c7f1c15c436dd1e0b86b11e2960ab5cb8de9d"
  },
  "requirements": ["SAR-012", "SAR-013", "SAR-019", "SAR-050"],
  "allowed_paths": [
    "src/slaif_reservation/management_ui/views.py",
    "src/slaif_reservation/management_ui/templates/management_ui/reservation_calendar.html",
    "tests/test_reservation_calendar.py",
    "tests/browser/test_reservation_calendar_browser.py",
    "docs/authorization.md",
    "uv.lock",
    "oap/active",
    "oap/orders/054-b-calendar-review-closure.md",
    "oap/reports/054-b-calendar-review-closure.md"
  ],
  "forbidden_resources": [
    "No model/migration/domain service/API/token/permission/auth, database/proxy/settings/Docker/Compose/runtime/deployment or broad visual change. No pyproject constraint change unless a genuine resolver failure is reported to strategy before widening scope.",
    "Do not edit prior 054-a order/report, older historical records, architecture/projection/PLAN/CRITICAL/OAP helpers, unrelated docs/tests, or more dependency versions than required for the certifi advisory.",
    "No real deployment/exposure, private data, identities/secrets, DNS/TLS/firewall, production DB, lab/Neumann resources, foreign Docker/process cleanup, merge/automerge by CODING."
  ],
  "provenance": [
    {"marker": "H", "source": "Human 2026-10-20 read-only one/four-week asset calendar and explicit CODING agent request", "section_or_evidence": "Same selected feature/issue111/PR112; accurate calendar time and approved cross-user read boundary required. Human previously directed one consolidated corrective round and exact-head CI rather than piecemeal fixes."},
    {"marker": "A", "source": "ARCHITECTURE.md A-16/SAR-050, SAR-012/013/019; OP-10/11; repository CI security job", "section_or_evidence": "Authorized calendar may present cross-user occupied time under view_all only. Security job pip-audit is mandatory and failed; no waiver or dependency exception. Old report remains immutable PARTIAL."},
    {"marker": "E", "source": "Frozen 054-a implementation 026aea744f0a134d2516a2a5bd1728b3a244adc2 / remote verified report 820455f333690d8e4c35fbfa4cdd905a331c30d4, PR112", "section_or_evidence": "Exact implementation CI quality/test/container/oap success (1295 product passes), security failure on certifi 2026.6.17 PYSEC-2026-4320 fixed by 2026.10.19; unchanged base lock. Report-head security also fails, other jobs require terminal observation. Official PyPA advisory published 2026-10-20: https://github.com/pypa/advisory-database/blob/main/vulns/certifi/PYSEC-2026-4320.yaml"},
    {"marker": "I", "source": "Strategic one-pass frozen diff/source review and UTC-to-Europe/Ljubljana diagnostic", "section_or_evidence": "Views computes last displayed day by subtracting 24h from UTC end: 2027-03-29 00:00 CEST becomes 2027-03-27 23:00 CET, mislabels Sunday 28 Mar as Saturday 27 Mar. _calendar_interval_days sets ends_on_day from CLIPPED last_day, falsely marks an interval extending beyond the selected window as ending on its final visible day. Overflow fallback uses existing list's start-time from/to filters, so bookings started before the window but still occupying it are omitted despite 'complete window' wording. docs/authorization says 'viewer's display name' where code shows booking OWNER's name."},
    {"marker": "C", "source": "No CRITICAL entry; routine deterministic review correction and live official certifi fix", "section_or_evidence": "D0/DHA NONE. Consolidate the three demonstrated calendar defects plus necessary security-gate repair in one b round on the same PR; no broad dependency refresh. Strongest objection: wrong time/omission could mislead staff about availability, and vulnerable trust bundle blocks qualified CI. Regression tests and exact-head five-check gate mitigate."}
  ],
  "decision_class": "D0",
  "target_gate": "Accept the existing read-only calendar development PR only after exact-head correct rendering, secure lock, five green CI checks and independent strategic review; no real deployment/release",
  "expected_report_path": "oap/reports/054-b-calendar-review-closure.md",
  "tests": [
    "Add focused regression for spring-forward Europe/Ljubljana selected week: window label must end on the last local Sunday, not Saturday; cover one-week and four-week local-date end labels. Use local date arithmetic for the displayed label, never a 24h UTC subtraction.",
    "Add focused regression for a reservation continuing after the displayed window: its last visible chip must show continuation, not an apparent end time; preserve exact half-open boundary behavior for a true local-midnight ending.",
    "Correct capped-results fallback to a truthful complete asset-history link (asset filter without start-only window filters) or equally proven complete overlap semantics; test that a pre-window-start booking still appears through the fallback and wording does not promise a filtered complete window falsely. Correct owner-vs-viewer description in docs/authorization.md.",
    "Upgrade ONLY certifi in uv.lock to at least 2026.10.19 using a locked resolver; prove lockfile diff confined to certifi metadata/artifact hashes, uv sync --locked succeeds, pip-audit passes and container build/CI security passes. No ignore/waiver of PYSEC-2026-4320.",
    "Rerun focused calendar Django and relevant Chromium at desktop/mobile, retain four privacy-safe screenshots in an owned private path for strategic visual review (batches <=2), visually inspect them, run ruff/format/mypy, no-migrations, diff/links. Normal full five CI checks at new implementation and report heads; earlier 054-a report CI recorded honestly."
  ]
}
-->

# 054-b — close calendar review and security gate

## Goal / exact boundary

Same issue111/PR112/branch as frozen 054-a. Root reviewed that complete frozen implementation/report once. The user-visible calendar and its core authorization/interval behavior are in place, but three bounded presentation truths and the current security CI gate remain unresolved. Fix exactly these, then preserve the earlier immutable PARTIAL report. This suffix is a necessary same-PR acceptance correction, not a new feature, authorization model or infrastructure objective.

## Numbered acceptance

1. **Local calendar week label is correct across DST.** Use the selected Monday plus `7*weeks-1` local calendar days for the last visible date. Current `window_end - timedelta(days=1)` works for most weeks but is wrong at spring-forward: Europe/Ljubljana week starting 2027-03-22 ends Sunday 2027-03-28, yet current label computes Saturday 2027-03-27. Test both one and four weeks spanning DST. Keep query endpoints as aware instants from local midnights; only the displayed last-day label changes.
2. **Clipped interval continuation is honest.** A booking that spans past the displayed last Sunday may have a chip on that day, but must not be labelled as ending there with its later `end_local` clock time. Calculate `ends_on_day` from the interval's true effective local end day (respecting midnight half-open semantics), not the day clipped to the display window. Test a future effective end beyond the week/four-week view and a true midnight end, including released consumed end if relevant. Keep confirmed/released/cancelled selector and owner privacy unchanged.
3. **Overflow fallback is complete and labelled correctly.** Existing All reservations `from`/`to` filters select by reservation START; the current capped-calendar link cannot find a reservation starting before the window and still occupying it. Change the fallback to a truthful asset-filtered history route without those start-only date filters (or a separately proven equivalent within this narrow scope), and say it contains complete asset history, not the complete window. Test that a pre-window-start overlapping reservation is reachable through the link despite cap. Correct docs/authorization.md to say booking OWNER display name, not viewer name; keep permission matrix/upgrade instructions intact.
4. **Mandatory security CI repair.** The unchanged lock pins `certifi==2026.6.17`, which pip-audit now reports under `PYSEC-2026-4320`; PyPA's current advisory fixes in `2026.10.19`. Update only the certifi resolution/artifact entries in `uv.lock` to a non-vulnerable published version, verify `uv sync --locked --all-groups` and `uv run pip-audit` (no advisory ignore), and identify any substantive resolver side effect before extending scope. `pyproject.toml` and all other dependencies stay unchanged. Container build and security CI must be green at the new head.
5. **Exact evidence and UX.** Focused Django/browser tests for these corrections and the existing calendar permission suite; desktop 1440 and mobile 390 screenshots for one/four-week view retained in an owned private path and visually inspected in batches <=2. Existing 054-a tests and relevant management/asset checks remain green. Ruff/format/mypy/check/no-migrations/diff/doc-links; normal full CI (quality/test/security/container/oap-harness) at final implementation and report heads. No product release claim or real deployment.

## Recovery / reporting

Start a FRESH CODING context via the existing right-pane wrapper, which sources supervision `codex.sh` from the development checkout and uses explicit `--yolo --profile qwen-neumann`. Amend PR112; no new issue/PR. Full earlier 054-a report-head checks must first be observed and recorded; a red security job is a failure, not waived. Focused tests during edit, full required exact-head suite after relevant changes. Freeze literal implementation SHA, publish only `oap/reports/054-b-calendar-review-closure.md` in the last report-only child with SELF, remote-verify and signal FIFO OK. Strategy reviews corrective diff plus prior whole review, five exact-head checks, then conditionally merges under existing development authority if accepted. No ICA milestone claim, D2 action or coding merge.

## Deferred human adjudication
- Decision: NONE
