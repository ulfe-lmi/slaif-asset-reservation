<!-- OAP-META
{
 "kind": "report",
 "id": "019-a",
 "order_path": "oap/orders/019-a-readiness-boundaries.md",
 "order_sha256": "89f0675230a23dae36c88492ca2a8543a36233a6ceadd9fae274538a720dfaa3",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 37,
 "pr_number": 38,
 "branch": "codex/37-oap-019-a-readiness-boundaries",
 "implementation_head": "71ad4d916cb798c491eecf83b6b83219d283755a",
 "base_sha": "51a2c8ca03963d63145e3f23349a88c766446236",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "71ad4d916cb798c491eecf83b6b83219d283755a",
  "runs": [
   {"run_id": 34804010244, "workflow": "CI", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success"}},
   {"run_id": 34804010262, "workflow": "oap", "jobs": {"oap-harness": "success"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 019-a report — pilot readiness check: prove the failure boundaries

Order digest: 89f0675230a23dae36c88492ca2a8543a36233a6ceadd9fae274538a720dfaa3
(committed `oap/orders/019-a-readiness-boundaries.md`; byte-identical to the
materialized `.FINAL` source — re-hashed `89f06752…dfaa3` both before and
after the rename to the canonical path).

Implementation head SHA: 71ad4d916cb798c491eecf83b6b83219d283755a

Report publication commit: SELF

**Result: COMPLETE** — all seven scoped failure boundaries of
`pilot_readiness_check` are now pinned by new boundary tests. Every boundary
behaved as scoped; no product defect was exposed, no product code was
changed, no test was weakened. The readiness gate now has evidence that it
fails where it must fail (SAR-032).

## Reconciliation at start (C-05/C-06/CP-03)

- Ordered reads: root router → `oap/coding-instructions/AGENTS.md` →
  `ARCHITECTURE-for-agents.md` → `OAP-COMMUNICATION-coding-agent.md` → exact
  active order → `SECURITY-CORE.md`/`TESTING-CORE.md` → ordered subtree
  excerpts (command in full, test file in full, audit constants,
  User/Asset/ReservationPolicy fields, token service, existing test
  helpers).
- `oap/active` = exactly `019-a` + LF (6 bytes, `0a`-terminated);
  `python3 oap/bin/check_state.py --repo .` →
  `state=ACTIVE_PENDING detail=valid final order is active; awaiting
  wake-up/invocation`, order `019-a` round `a`, `pr=None`, branch
  `codex/37-oap-019-a-readiness-boundaries`. Wrapper had already consumed the
  control OK; not consumed again.
- Local main = remote `origin/main` = `51a2c8ca03963d63145e3f23349a88c766446236`
  (= the order's `base_sha`; 018-a quiescent on top of merged PR #36 at
  `f00b227`). Worktree clean except the materialized order (untracked
  `oap/orders/019-a-readiness-boundaries.FINAL.md`) and the pointer
  (untracked `oap/active`). Fresh round: no local or remote branch and no PR
  existed for this objective → `pr_mode=CREATE_OR_RESUME` resolved to
  CREATE.
- The order's meta `allowed_paths` names
  `oap/orders/019-a-readiness-boundaries.md` while the wrapper materialized
  `oap/orders/019-a-readiness-boundaries.FINAL.md`; same convention as 018-a —
  the `.FINAL` source was renamed to the canonical path with the digest
  verified identical before and after.

## Inspected pre-change state (criterion 1) — PASSED

Pre-change test file: `tests/test_pilot_readiness_check.py`,
sha256 `91d6cf36efe32d8a09c9d5802c341f24171eda72e35b0f5ae3962f709336d298`,
7974 bytes, seven tests:

1. `test_pilot_readiness_empty_database_strict_failure_and_non_strict_success`
2. `test_pilot_readiness_minimal_ready_state_passes_strict`
3. `test_pilot_readiness_assets_without_effective_policy_warn_but_do_not_fail_strict`
4. `test_pilot_readiness_json_schema_counts_and_redaction`
5. `test_pilot_readiness_reports_expired_idempotency_warning`
6. `test_pilot_readiness_command_is_read_only_for_application_tables`
7. `test_pilot_readiness_migration_failure_is_a_hard_gate`

`src/slaif_reservation/api/management/commands/pilot_readiness_check.py`
(244 lines at base), exact gate list with levels (all sorted by id in the
report; `required_count_check`/`warning_count_check` at lines 221/230):

- Required (status `fail` when failing): `active_staff_user` (line 151),
  `active_reservable_exclusive_asset` (line 156), `active_reservation_policy`
  (line 161), `database_migration_ready` (explicit check, line 167).
- Warning (status at most `warn`): `ordinary_pilot_users` (line 176),
  `assets_without_effective_policy` (explicit check),
  `recent_audit_events` (line 194), `expired_idempotency_records` (explicit
  check), `successful_blackout_exercise` (line 212).
- `--strict` exits non-zero only when `report["status"] == "fail"`
  (`handle`); `--json` emits `json.dumps(..., sort_keys=True)` (deterministic).

Code lines proving each counter's filter (base file, line numbers):

- Service-account exclusion and active flags (users): lines 91–104 —
  `active_staff_users` = `is_active=True, is_staff=True,
  is_service_account=False`; `active_human_users` = `is_active=True,
  is_service_account=False`; `active_non_staff_human_users` = `is_active=True,
  is_staff=False, is_service_account=False`.
- Active reservable exclusive assets: lines 85–89 — `active=True,
  reservable=True, booking_mode=Asset.BOOKING_EXCLUSIVE` (`BOOKING_EXCLUSIVE
  = "exclusive"`, the only booking mode in `assets/models.py` line 42).
- Active policies: line 105–106 — `ReservationPolicy.objects.filter(active=True)`
  (model default `active=True`, `reservations/models.py` line 68).
- Audit window: line 20 `RECENT_AUDIT_WINDOW = timedelta(days=7)`; lines 81
  and 112–114 — `recent_audit_cutoff = now - RECENT_AUDIT_WINDOW` and
  `occurred_at__gte=recent_audit_cutoff`.
- Blackout-exercise action filter: lines 115–117 — `action=
  AuditEvent.ACTION_BLACKOUT_CREATED` (`maintenance_blackout.created`,
  `audit/models.py` line 53), with **no** time filter; the deactivated action
  `maintenance_blackout.deactivated` (line 54) is a distinct constant.
- Token buckets: lines 82–84 — active = `revoked_at__isnull=True,
  expires_at__gt=now`; expired = `revoked_at__isnull=True,
  expires_at__lte=now`; revoked = `revoked_at__isnull=False` — three mutually
  exclusive buckets; `api_tokens_present` = `ApiToken.objects.count()`
  (line 118, all rows).
- Migration-readiness exception catch: lines 141–146 — `try:
  connection.ensure_connection(); return not unapplied_migrations_exist()
  except Exception: return False`.
- Uncovered-policy exception catch: lines 131–137 — for each active
  reservable exclusive asset, `try: reservation_services.resolve_effective_policy(asset)
  except Exception: missing += 1` (any exception, including
  `POLICY_AMBIGUOUS`, counts the asset as uncovered).

## What changed (commit 71ad4d9, 3 files, +445/−0, all on allowed_paths)

- `tests/test_pilot_readiness_check.py` (+265/−0): ten new boundary tests
  appended after the existing file; the original 7974 bytes are a strict
  byte prefix of the new 17802-byte file (verified programmatically; `git
  diff` shows zero deleted lines), so the seven pre-existing tests are
  byte-identical. New tests, mapped to the order's scope items:
  1. `test_pilot_readiness_database_connection_failure_is_a_hard_gate`
     (scope 1) — module-level `connection` replaced by a stub whose
     `ensure_connection` raises `django.db.OperationalError` (via
     `monkeypatch.setattr(command_module, "connection", ...)`, the same
     module-patching technique the pre-existing migration test uses for
     `unapplied_migrations_exist`): status `fail`, `database_migration_ready`
     level `fail`, every other check non-failing, `--strict` raises
     `CommandError`, no unhandled exception — the `try/except → False`
     boundary (lines 141–146) is proven.
  2. `test_pilot_readiness_service_account_staff_cannot_satisfy_human_staff_gate`
     (scope 2a) — a service-account staff user only (real asset/policy/audit
     evidence otherwise): `active_staff_users == 0`, `active_staff_user`
     level `fail`, status `fail`, all other checks non-failing.
  3. `test_pilot_readiness_non_staff_service_account_is_no_human_user`
     (scope 2b) — a non-staff service account only: `counts.active_human_users
     == 0`, `ordinary_pilot_users` level `warn`.
  4. `test_pilot_readiness_inactive_staff_user_fails_human_staff_gate`
     (scope 3a) — inactive staff user only: `active_staff_user` level `fail`,
     all other checks non-failing.
  5. `test_pilot_readiness_inactive_or_non_reservable_asset_fails_asset_gate`
     (scope 3b) — one inactive asset (`active=False, reservable=False`, the
     only shape the `asset_inactive_not_reservable` constraint allows) plus
     one active non-reservable asset, global policy, real users/audit:
     `active_reservable_exclusive_assets == 0`,
     `active_reservable_exclusive_asset` level `fail`, all other checks
     non-failing.
  6. `test_pilot_readiness_inactive_policy_fails_policy_gate` (scope 3c) —
     inactive exact-asset policy only: `active_reservation_policies == 0`,
     `active_reservation_policy` level `fail`, all other checks non-failing.
  7. `test_pilot_readiness_blackout_deactivation_is_not_exercise_evidence`
     (scope 4) — the only audit event is `ACTION_BLACKOUT_DEACTIVATED`:
     `successful_blackout_audit_events == 0`, `successful_blackout_exercise`
     level `warn`, while `recent_audit_events == 1` passes — the event is
     recent-audit evidence but cannot masquerade as blackout-exercise
     evidence.
  8. `test_pilot_readiness_old_blackout_event_expires_from_recent_window_only`
     (scope 5) — a single `ACTION_BLACKOUT_CREATED` event 8 days old
     (strictly outside the 7-day window): `recent_audit_events == 0` (level
     `warn`) while `successful_blackout_audit_events == 1` (level `pass`) —
     the window asymmetry is pinned; overall status `warn`.
  9. `test_pilot_readiness_token_buckets_partition_and_do_not_gate_status`
     (scope 6) — one active, one expired, one revoked token:
     `api_tokens_present == 3`, `api_tokens_active == 1`,
     `api_tokens_expired == 1`, `api_tokens_revoked == 1`, status `pass`
     with every check passing — token counts are informational, not gates.
     The expired token is aged with a raw-SQL `UPDATE` in the same pattern
     as `set_token_timestamps` in `tests/test_api_tokens.py`, because the
     `api_token_expires_after_created` check constraint
     (`accounts/models.py` line 145) forbids an ORM save with
     `expires_at` before `created_at`; the revoked token is revoked through
     the product service `revoke_api_token`.
  10. `test_pilot_readiness_ambiguous_policy_counts_as_uncovered` (scope 7) —
      an active reservable exclusive asset whose policy resolution raises the
      product's own `POLICY_AMBIGUOUS` `ReservationDomainError` (the exact
      error `services.py` line 149 raises on same-priority ambiguity):
      `assets_without_effective_policy == 1`, level `warn`, exact detail
      "1 active reservable exclusive asset(s) lack an effective policy",
      status `warn` — ambiguity is reported, not silently passed.
- `oap/orders/019-a-readiness-boundaries.md` (+179): canonical order bytes
  (rename of the materialized `.FINAL`; digest identical).
- `oap/active` (+1): pointer `019-a` + LF.

No other file changed. `src/`, `docs/`, `deploy/`, `.github/`, `data/`,
other test files, and dependencies are untouched (criterion 5).

## Numbered acceptance evidence

1. **Pre-change state** — PASSED: see "Inspected pre-change state" above
   (seven test names, exact gate list with levels, counter filter lines).
2. **New boundary tests present, passing, pre-existing byte-identical** —
   PASSED: ten new tests (scope items 1–7, with item 2 and item 3 each
   proving two/three sub-cases) appended to
   `tests/test_pilot_readiness_check.py`; focused run at implementation head
   on real PostgreSQL 17: `17 passed` (7 pre-existing + 10 new). Byte-identity
   proof: pre-change file sha256 `91d6cf36…36d298` (7974 bytes); post-change
   file sha256 `10ed0244…84a` (17802 bytes) starts with the pre-change bytes
   (programmatic prefix check), and `git diff --stat` shows
   `265 insertions(+), 0 deletions`.
3. **Full verification green at the exact implementation head** — PASSED:
   local at `71ad4d916cb798c491eecf83b6b83219d283755a` (owned disposable
   PostgreSQL 17.11, container `slaif-oap019-pg17`, loopback
   `127.0.0.1:54330`, synthetic credentials from the local synthetic `.env`):
   full suite `597 passed in 168.58s` (baseline at base: `587 passed`);
   `uv sync --locked --all-groups` ok; `ruff check .` all checks passed;
   `ruff format --check .` 181 files already formatted; `mypy src` success
   (119 source files, no issues); `manage.py check` no issues;
   `makemigrations --check --dry-run` no changes; `pip-audit` no known
   vulnerabilities; `git diff --check` clean; `spectacular --file
   build/openapi/schema.yaml --validate --fail-on-warn` ok;
   `operational_check` → `migrations=ok static=ok bootstrap=ok
   idempotency_cleanup_command=ok operational_check=ok` (bootstrap import:
   `excluded=1 conflicted=0`, the excluded entry preserved). CI at the exact
   head: quality/test/security/container + oap-harness all `success`; the CI
   test job log shows `tests/test_pilot_readiness_check.py .................`
   (17 dots — the new tests run) and `597 passed in 95.92s` (new tests
   counted in the pass total).
4. **No untruthful criterion 2** — not needed: criterion 2 held; no product
   change, no weakened test. (One scoped state turned out to be
   schema-impossible — see "D0 decisions", deviation D-01 — and was pinned
   through the product's own ambiguity error with the order's exact
   assertions, per the codebase's own precedent for this branch.)
5. **Diff touches only allowed_paths** — PASSED: commit `71ad4d9` changes
   exactly `tests/test_pilot_readiness_check.py`,
   `oap/orders/019-a-readiness-boundaries.md`, `oap/active` — all in the
   order's `allowed_paths`.

## Commands (exact, as run at implementation head 71ad4d9)

```
# local disposable environment (SAR-031; owned, explicit identity; removed after the round)
docker run -d --name slaif-oap019-pg17 -p 127.0.0.1:54330:5432 \
    -e POSTGRES_USER=<synthetic> -e POSTGRES_PASSWORD=<synthetic> \
    -e POSTGRES_DB=slaif_reservation postgres:17   # PostgreSQL 17.11
psql "$DATABASE_URL" -c 'select version();'        # health + version proof

uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy src
git diff --check
uv run --env-file .env python manage.py check
uv run --env-file .env python manage.py makemigrations --check --dry-run
uv run --env-file .env python manage.py migrate --noinput
uv run --env-file .env python manage.py import_bootstrap_assets --input data/bootstrap/assets.yaml
mkdir -p build/openapi && uv run --env-file .env python manage.py \
    spectacular --file build/openapi/schema.yaml --validate --fail-on-warn
uv run --env-file .env python manage.py operational_check
uv run pip-audit
env -u OAP_ROLE uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test -q \
    tests/test_pilot_readiness_check.py          # baseline 7 passed; final 17 passed
env -u OAP_ROLE uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test -q
                                                 # baseline 587 passed; final 597 passed
python3 oap/bin/check_state.py --repo .          # state=ACTIVE_PENDING, order 019-a
```

## CI observed before authoring (implementation head)

At `71ad4d916cb798c491eecf83b6b83219d283755a` (observed before this report
was written): CI run `34804010244` — quality `success` (20s), test `success`
(2m48s), security `success` (19s), container `success` (52s); oap run
`34804010262` — oap-harness `success` (35s). No missing/skipped/cancelled
checks. The test job log: `tests/test_pilot_readiness_check.py
...............` (17 dots) and `597 passed in 95.92s`. Report-head CI is
separate and not observed at authoring (recorded as such in the meta);
post-publication observations belong to the private receipt, not this
report.

## Security, data, dependencies and local tools

- No credential, verifier, pepper, token, password, session, or private
  locator appears in this report or in any test assertion; the token test
  asserts counts only (the pre-existing redaction test remains the
  leak-check). The local DB used synthetic credentials from the local
  synthetic `.env` and ran on a loopback-only port.
- No deployment, no real/production database, no lab/Neumann/SmartScheduling
  contact, no DNS/TLS/firewall change, no repository visibility or
  branch-protection change. The only mutating GitHub operations were pushing
  this branch and opening PR #38 for this objective.
- No new or removed dependencies (`uv sync --locked` unmodified `uv.lock`);
  no product code, settings, migration, template, or API change.
- Local tools: Docker 29.1.3 (container runtime for the owned disposable
  PostgreSQL 17.11), psql (client), `gh` (read + the two authorized
  publication operations). No model provider calls for product logic; no
  Playwright/browser run was required by this order.

## D0 decisions (routine in-scope mechanics, C-07)

- **D-01 (scope 7 mechanism, documented deviation)**: the order's literal
  example state — "two active global policies" (two active policies at the
  same priority) — is impossible under the enforced schema:
  `reservation_policy_one_active_per_asset` (`reservations/models.py` line
  116, partial unique on `asset` where `active=True`) and
  `reservation_policy_one_active_global` (line 121, partial unique on the
  NULL-asset row where `active=True`) are PostgreSQL-enforced, so no
  ORM or raw-SQL path can create two live policies at any one resolution
  level (exact asset, parent, or global). The scoped boundary — "ambiguity
  is reported, not silently passed" — was therefore pinned by making the
  command's resolver reference raise the product's own
  `POLICY_AMBIGUOUS` `ReservationDomainError` (the exact error
  `services.py` line 149 raises on same-priority ambiguity) via
  `monkeypatch`, with the order's exact assertions (count 1, WARN, exact
  detail, status `warn`). Precedent: the codebase's own
  `tests/test_reservations_services.py::test_equal_priority_policy_ambiguity_
  fails_closed` pins the identical branch with the identical technique.
  This is a test-mechanics decision (how to reach the code path), not a
  product-meaning decision; no product behavior is altered and no assertion
  was weakened.
- **D-02 (expired token aging)**: aged the test token with a raw-SQL
  `UPDATE` (same pattern as `set_token_timestamps` in
  `tests/test_api_tokens.py`) because the `api_token_expires_after_created`
  check constraint forbids an ORM save with a past expiry; the revocation
  path used the product service `revoke_api_token`.
- **D-03 (order publication)**: renamed the materialized
  `oap/orders/019-a-readiness-boundaries.FINAL.md` to the canonical allowed
  path (byte-identical, digest re-verified), per the 018-a convention.
- **D-04 (PR identity)**: the order's `issue_number` is 37; GitHub assigned
  PR number 38 to this objective's PR (the issue/PR numbering has run
  offset since the conversion — e.g., 018-a: issue 35 → PR 36). The report
  records the actual PR number.

Observation for strategy (not a defect claim, no product change made):
because of D-01's two constraints, the `POLICY_AMBIGUOUS` branch in
`_resolve_effective_policy` (`services.py` lines 148–149) is currently
unreachable on schema-conformant data — it is defensive. The readiness
command's own boundary (any resolver exception ⇒ counted as uncovered) is
what the new test pins, and it behaves exactly as the order's known facts
state.

## Limits and uncertainty

- Evidence labels used here are all `PASSED` for things actually executed
  successfully; report-head CI is explicitly **NOT YET OBSERVED AT
  AUTHORING** and is not claimed.
- The new tests prove the command's counter/filter boundaries against real
  PostgreSQL 17; they do not re-prove the underlying reservation
  exclusivity, auth, or privacy boundaries (those suites are unchanged and
  green in the full run).
- The ambiguity boundary is pinned through the product's error type because
  the literal two-active-policy state is schema-impossible (D-01); if
  strategy reads scope 7 to require a live two-policy state, that state
  cannot exist without a schema change, which this order forbids.
- Local full-suite and CI runs are separate executions; both were observed
  green at the same head. The owned container `slaif-oap019-pg17` is
  rehearsal-identical disposable infrastructure and is removed at round
  end; no other local state is adopted or destroyed.
- No merge, auto-merge, approval, or milestone claim by coding. This report
  is not strategic acceptance, not release acceptance, and not ICA
  acceptance (SAR-032/SAR-038): strategy reviews PR #38 at the exact head
  and performs the delegated development merge if accepted; readiness for a
  real pilot remains the strategy's and the human's call.

## Deferred human adjudication

- Decision: NONE
