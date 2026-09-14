<!-- OAP-META
{
 "id": "019-a",
 "round": "a",
 "base_sha": "51a2c8ca03963d63145e3f23349a88c766446236",
 "issue_number": 37,
 "branch": "codex/37-oap-019-a-readiness-boundaries",
 "pr_mode": "CREATE_OR_RESUME",
 "previous_round": null,
 "allowed_paths": [
  "tests/test_pilot_readiness_check.py",
  "oap/orders/019-a-readiness-boundaries.md",
  "oap/active",
  "oap/reports/019-a-readiness-boundaries.md"
 ],
 "forbidden_resources": [
  "any change under src/ (no product behavior, model, API, template, settings, or migration changes; this round is evidence-only)",
  "any change to the pilot_readiness_check command or its gates/levels/counts semantics",
  "any weakening, skipping, or loosening of a boundary test to make it pass",
  "any change under docs/, deploy/, .github/, data/, or other test files",
  "new dependencies or removed dependencies",
  "deployment of any kind; real/production databases; real lab/Neumann machines; real SmartScheduling data",
  "credentials, auth files, sessions, tokens, auth homes",
  "DNS/TLS/firewall changes, public exposure, repository visibility or branch-protection changes",
  "any mutating GitHub operation except pushing this branch and opening this objective's PR",
  "merging or auto-merging any PR (merge is strategy's delegated act after review)",
  "ICA activity, milestone completion claims, or work from other drafts/objectives",
  "model provider endpoints other than the configured qwen-neumann role profile"
 ]
}
-->

# 019-a — Pilot readiness check: prove the failure boundaries

## Goal

`pilot_readiness_check` (WO0013) is the read-only gate an operator runs
before any real pilot; an operator must be able to trust that it FAILS when
it should fail. Seven tests exist (empty-DB fail + strict, minimal-ready
pass, uncovered-asset warn, JSON schema/redaction, expired-idempotency
warn, read-only, migration monkeypatch fail). This round proves the
remaining failure boundaries with new boundary tests only — no product
change. If a boundary test exposes a genuine product defect, the round
stops and reports the exact failing boundary (no product fix in this
round, no weakened test).

## Durable provenance and requirements

- H: in-session human principal instruction 2026-09-14 — continue the
  strategy → coding → review → merge loop autonomously until a genuine
  D2/human decision or the architecture-defined MVP/pilot gate; prefer work
  that directly enables actual users over OAP machinery.
- E: origin/main 51a2c8ca03963d63145e3f23349a88c766446236 (018-a
  quiescent, INACTIVE, CI green at merged head f00b227).
  src/slaif_reservation/api/management/commands/pilot_readiness_check.py
  (244 lines; reviewed 2026-09-14: required gates active_staff_user,
  active_reservable_exclusive_asset, active_reservation_policy,
  database_migration_ready; warning gates ordinary_pilot_users,
  assets_without_effective_policy, recent_audit_events,
  expired_idempotency_records, successful_blackout_exercise; status
  fail/warn/pass; --strict exits non-zero on fail only; --json
  deterministic). tests/test_pilot_readiness_check.py (7 tests; the
  boundaries listed in the goal are not covered).
- A: S-12 (one proof-sized objective), S-15 (report boundary), S-19
  (truthful evidence; name the exact failing boundary, never paper over).
- C: S-16 (exact-head review) / S-17 (delegated development merge; main
  workflows verified CI-only).
Requirements: SAR-032 (evidence before readiness — the readiness gate
itself must have proven failure boundaries), SAR-033 (preserve existing
project — zero product change).

## Current reconciled state and prerequisites

- Base main (local and remote): 51a2c8ca03963d63145e3f23349a88c766446236.
  Worktree must be clean on main before starting; `oap/active` absent
  (INACTIVE).
- Known facts (verify, do not assume): counts use `is_active=True,
  is_service_account=False` filters for staff/human users; active
  reservable exclusive assets use `active=True, reservable=True,
  booking_mode=BOOKING_EXCLUSIVE`; `database_migration_ready()` wraps
  `connection.ensure_connection()` + `unapplied_migrations_exist()` in
  `try/except Exception -> False`; `assets_without_effective_policy_count`
  counts an asset as missing when `resolve_effective_policy` raises ANY
  exception (including ambiguity); `recent_audit_events` uses
  `occurred_at >= now - 7 days` while `successful_blackout_exercise` has
  NO time filter and only counts `ACTION_BLACKOUT_CREATED`; token counts
  are three mutually exclusive buckets (active = unrevoked AND
  unexpired; expired = unrevoked AND expired; revoked).

## Ordered read set

Standard compact read set, plus: src/slaif_reservation/
api/management/commands/pilot_readiness_check.py (in full),
tests/test_pilot_readiness_check.py (in full), the AuditEvent action
constants, the User/Asset/ReservationPolicy model fields used by the
counters, and the existing test helpers in the test file (user/asset/
policy/audit_event factories, minimal_ready_state, run_json_command).

## Scope and allowed paths

New boundary tests in tests/test_pilot_readiness_check.py (extend the
existing file; reuse its factories and run_json_command; keep the seven
existing tests byte-identical):

1. DB connection failure: monkeypatch the module's `connection`
   `ensure_connection` to raise (e.g. django.db
   OperationalError); with an otherwise ready state, status must be
   `fail`, `database_migration_ready` check level `fail`, and `--strict`
   raises CommandError. The command must not crash with an unhandled
   exception.
2. Service accounts excluded from human gates:
   - a service-account staff user only (is_service_account=True) ->
     `active_staff_user` FAILS (a service account cannot satisfy the
     human staff gate);
   - a non-staff service account only -> `ordinary_pilot_users` WARNs and
     `counts.active_human_users == 0`.
3. Inactive rows excluded:
   - only an inactive staff user (is_active=False) -> `active_staff_user`
     FAILS;
   - only an inactive or non-reservable asset ->
     `active_reservable_exclusive_asset` FAILS;
   - only an inactive policy -> `active_reservation_policy` FAILS.
4. Blackout-exercise action filter: an audit event whose action is NOT
     `ACTION_BLACKOUT_CREATED` (e.g. the blackout-deactivated action) ->
     `successful_blackout_exercise` WARNs (count 0); the same event does
     not masquerade as blackout-exercise evidence.
5. Recent-audit window boundary: an `ACTION_BLACKOUT_CREATED` event
     strictly older than the 7-day window -> `recent_audit_events == 0`
     (WARN) while `successful_blackout_exercise` still PASSES (it has no
     time filter) — pin this asymmetry.
6. Token bucket partitioning: with one active, one expired (lifetime in
   the past), and one revoked token: `api_tokens_present == 3`,
   `api_tokens_active == 1`, `api_tokens_expired == 1`,
   `api_tokens_revoked == 1`, and status unaffected by token counts
   (tokens are informational, not gates).
7. Ambiguous policy counted as uncovered: an active reservable exclusive
   asset with TWO active policies at the same priority (e.g. two active
   global policies) -> `assets_without_effective_policy` counts it
   (WARN detail reflects the count), i.e. ambiguity is reported, not
   silently passed.

Non-negotiable: if any new test exposes a genuine product defect (the
boundary does NOT behave as scoped), do NOT change product code and do NOT
weaken the test. Stop, and publish a truthful PARTIAL/FAILED report naming
the exact failing boundary, the observed vs expected behavior, and the
minimal reproduction; strategy decides the follow-up.

## Non-goals

- No product behavior change of any kind; no src/ change; no docs change.
- No OAP/governance changes, no canary work, no ICA, no milestone claim.
- No deployment, no real data, no lab/Neumann contact.
- No merge, auto-merge, approval or settings change.

## Numbered acceptance criteria

1. The report records the pre-change state: the seven existing test
   names, the command's exact gate list with required/warning levels, and
   the code lines proving each counter's filter (service-account
   exclusion, active flags, audit window, blackout action filter, token
   buckets, exception-catch in migration readiness).
2. The new boundary tests (scope items 1–7) are present in
   tests/test_pilot_readiness_check.py, pass against the current product
   code, and the seven pre-existing tests are byte-identical (prove by
   diff).
3. Full pytest suite, quality gates (ruff check, ruff format --check,
   mypy), makemigrations --check --dry-run, manage.py check,
   operational_check, spectacular --validate --fail-on-warn, and the CI
   container + security jobs all green at the exact implementation head;
   the CI test job shows the new tests running (counted in the pass
   total).
4. If criterion 2 cannot hold truthfully: a PARTIAL/FAILED report with
   the exact failing boundary (observed vs expected, minimal repro), no
   product change, no weakened test.
5. The diff touches only allowed_paths.

## Deferred human adjudication

- Decision: NONE
