<!-- OAP-META
{
 "id": "017-a",
 "round": "a",
 "base_sha": "bb06f81cbae815cbee9550af2a4ee7df3902137b",
 "issue_number": 33,
 "branch": "codex/33-oap-017-a-restore-drill",
 "pr_mode": "CREATE_OR_RESUME",
 "previous_round": null,
 "allowed_paths": [
  "src/slaif_reservation/api/management/commands/restore_drill.py",
  "src/slaif_reservation/api/management/commands/_postgres_tools.py",
  "tests/",
  ".github/workflows/ci.yml",
  "docs/runbooks/backup-and-restore.md",
  "docs/runbooks/internal-alpha-pilot-preparation.md",
  "oap/orders/017-a-restore-drill.md",
  "oap/active",
  "oap/reports/017-a-restore-drill.md"
 ],
 "forbidden_resources": [
  "any change to existing backup_database/restore_database/operational_check CLI behavior or documented contract (reuse by import is allowed; behavior changes are not)",
  "model, API, template, settings or migration changes; any product behavior change",
  "new dependencies or removed dependencies",
  "any workflow change beyond the single documented pg-tools install step in the test job (scope item 3)",
  "any doc change beyond scope item 4 (two runbook files)",
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

# 017-a — Codify and prove the isolated backup/restore drill

## Goal

M-LOCAL-PILOT-EVIDENCE requires recovery evidence: "real local dump/restore
must prove restoration" (S-19) and the pilot success criteria require an
isolated restore drill before any real pilot data is accepted. Today the
backup/restore commands exist (pg_dump/pg_restore, custom format) but are
tested only on dry-run/refusal paths; the runbook describes the drill as a
procedure, not a codified executable; and no real dump→restore round trip is
proven anywhere. This round codifies an isolated restore drill as a
management command and proves it with a real round-trip test against real
PostgreSQL 17 in the CI test job. No product behavior change, no deployment,
no ICA, no milestone claim (this produces the recovery-evidence pillar only).

## Durable provenance and requirements

- H: in-session human principal instruction 2026-09-14 — resume product
  development automatically after the security remediation; select the next
  smallest product PR that materially advances the real reservation-system
  MVP/pilot; prefer work that directly enables actual users over OAP
  machinery; no ICA now; bootstrap drafts 016-a..020-a are not a mandatory
  queue (topic selection is strategic, recorded 2026-09-14).
- E: origin/main bb06f81cbae815cbee9550af2a4ee7df3902137b (016-a quiescent,
  INACTIVE, CI green at merged head 7d6e4d8).
  src/slaif_reservation/api/management/commands/backup_database.py and
  restore_database.py (pg_dump --format=custom / pg_restore --clean
  --if-exists --no-owner; dry-run default; refuse missing tool/URL; never
  print password). tests/test_operational_hardening.py lines 296-343 (only
  refusal and dry-run paths tested; no real dump/restore).
  docs/runbooks/backup-and-restore.md "Restore Drill" (procedure only:
  restore into isolated DB, operational_check, compare row counts).
  docs/runbooks/internal-alpha-pilot-preparation.md "Pilot Success Criteria"
  (drill "planned", not codified or proven). .github/workflows/ci.yml test
  job (postgres:17 service as superuser `slaif` on localhost:5432; host has
  no pg_dump/pg_restore by default).
- A: S-19 (evidence discipline: real dump/restore proves restoration),
  S-12 (one proof-sized objective), S-15 (report boundary).
- C: S-16 (exact-head review) / S-17 (delegated development merge; main
  workflows verified CI-only, no deployment side effects).
Requirements: SAR-032 (evidence before readiness), SAR-033 (preserve
existing project — no product behavior change), SAR-035 (private
infrastructure boundary — local disposable PostgreSQL only), recovery pillar
(recovery that preserves work and prevents duplicate execution).

## Current reconciled state and prerequisites

- Base main (local and remote): bb06f81cbae815cbee9550af2a4ee7df3902137b.
  Worktree must be clean on main before starting; `oap/active` absent
  (INACTIVE).
- Known constraint facts (verify, do not assume): psycopg is already a
  project dependency; the CI test job provides DATABASE_URL and
  TEST_DATABASE_URL pointing at the postgres:17 service (user `slaif`,
  superuser in the service image, therefore able to CREATE/DROP other
  databases on that server); the host runner has no pg client tools by
  default; the named GiST exclusion constraint on the reservation table
  already exists (verify its exact name in the model); API token
  verification is one-way (HMAC verifier stored, plaintext never persisted).
- The drill must run entirely on loopback/disposable infrastructure. The
  local developer equivalent is any disposable PostgreSQL instance where the
  connecting user has CREATEDB (state this in the test docstring and
  runbook).

## Ordered read set

Standard compact read set, plus: backup_database.py, restore_database.py,
_postgres_tools.py; tests/test_operational_hardening.py (backup/restore
sections); docs/runbooks/backup-and-restore.md; docs/runbooks/
internal-alpha-pilot-preparation.md (success criteria); .github/workflows/
ci.yml (test job); the models and service functions needed for seeding and
row-count assertions (user, asset, reservation policy, reservation,
maintenance blackout, audit event, API token, idempotency record) and the
API token verifier path used by the round-trip assertion.

## Scope and allowed paths

1. New command `restore_drill.py` under
   src/slaif_reservation/api/management/commands/ (dry-run default,
   consistent with sibling commands):
   - Arguments: `--source-url` (default: DATABASE_URL), `--target-url`
     (required), `--workdir` (default: a documented ignored build
     directory), `--apply`.
   - Refusals (apply and dry-run): unparseable/non-PostgreSQL URLs; target
     database name equal to source database name on the same server or any
     target that is not distinct from the source database; target database
     already exists on the target server (the drill must never drop or
     restore over pre-existing data — isolation means drill-created);
     missing pg_dump or pg_restore; unwritable workdir.
   - `--apply` flow (all real, no mocks):
     a. pg_dump --format=custom from source to `<workdir>/drill.dump`,
        reusing backup_database logic by import (no duplication of the
        subprocess/env logic).
     b. Connect to the target server's maintenance database and
        `CREATE DATABASE <target>` (the drill records that it created it).
     c. pg_restore --clean --if-exists --no-owner from the artifact into
        the target database, reusing restore_database logic by import.
     d. Verify and print structured key=value evidence (no passwords, no
        full URLs with credentials):
        - row-count equality source vs target for: users, assets,
          reservation policies, reservations, maintenance blackouts, audit
          events, API tokens, idempotency records, django_migrations (exact
          model names from the code);
        - restored reservation table: the named GiST exclusion constraint
          exists and actually blocks a conflicting overlapping reservation
          insert (attempt it, expect the named IntegrityError, roll back);
        - API token round trip: at least one restored token authenticates
          through the real verifier path using the restored DB's stored
          verifier (not by re-deriving from any plaintext);
        - point-in-time property: a reservation created on the source
          AFTER the backup is absent from the target;
        - source untouched: source row counts unchanged before/after and
          all pre-drill reservations still present on the source;
        - migrations applied: target django_migrations equals source.
     e. Scoped cleanup: `DROP DATABASE <target>` (only the drill-created
        one) and remove the workdir. On any failure: print the failure
        truthfully, attempt scoped cleanup, and retain the artifact path in
        the error output for operator inspection (without credentials).
   - dry-run: perform all validations except execution; print the plan and
     `validated=true`; zero side effects (no artifact, no target DB).
2. Tests in a new `tests/test_restore_drill.py`, running against the real
   PostgreSQL 17 (the CI test job's service database; the target database is
   created on that same server by the drill itself):
   - Real round trip: seed the source through real product entry points
     (bootstrap asset import, policy/reservation/blackout through the
     service functions, an API token through its real creation path, audit
     events as byproducts), run the drill with `--apply`, and assert every
     verification in scope item 1d (all row-count equalities, exclusion
     constraint blocks, token round trip, post-backup absence, source
     untouched, migrations applied) plus cleanup (target database absent,
     workdir removed).
   - Negative paths: target equal to source refused; pre-existing target
     database refused (and that database left byte-identical/untouched);
     dry-run side-effect free (no artifact, no target DB, no source write);
     missing pg tools refused (PATH simulation); no password or credential
     string appears anywhere in captured stdout/stderr.
3. .github/workflows/ci.yml: exactly one added step in the test job
   installing pg_dump/pg_restore on the host, compatible with dumps produced
   by PostgreSQL 17 (prefer the 17 client; if a different client version is
   used, the report must evidence that it reads the server-17 dump). Keep
   the step minimal and documented in a comment.
4. Docs (factual updates only):
   - docs/runbooks/backup-and-restore.md: the "Restore Drill" section now
     documents the codified command with exact invocations (source/target/
     workdir), its refusals, and its verification output; the manual
     pg_dump/pg_restore procedure remains as fallback; the "never restore
     over production without a separate human-approved incident plan"
     warning stays.
   - docs/runbooks/internal-alpha-pilot-preparation.md: update the one pilot
     success-criterion line that currently says the isolated restore drill
     is "planned" so it references the codified drill command. No other
     re-scope.

## Non-goals

- No model/API/template/settings/migration changes; no product behavior
  change; no new dependencies (reuse the existing project dependency
  psycopg or the existing tool helpers).
- No OAP/governance changes, no workflow-canary work, no ICA, no milestone
  completion claim.
- No deployment, no real/production database, no real data, no lab/Neumann
  contact, no public exposure.
- No merge, auto-merge, approval or settings change. History (015-b, 016-a
  rounds) is immutable; other drafts/objectives are not in scope.

## Numbered acceptance criteria

1. The report records the inspected pre-change state: exact CLIs of the
   current backup/restore commands, existing test coverage (dry-run/refusal
   only), the exact runbook "Restore Drill" text, the CI test job database
   configuration and the host's absence of pg client tools.
2. `restore_drill` exists, is dry-run by default, implements every refusal
   and the `--apply` flow of scope item 1, reuses the existing command logic
   by import, and changes no existing command's CLI or behavior (prove by
   diff).
3. The real round-trip test passes against real PostgreSQL 17 in the CI
   test job (not skipped) and locally (evidence in the report): all
   scope-item-1d verifications asserted, cleanup asserted.
4. Negative tests pass: target==source, pre-existing target, dry-run
   side-effect-free, missing tools, no credential leakage.
5. At the exact implementation head: full pytest suite, quality (ruff
   check, ruff format --check, mypy), makemigrations --check --dry-run,
   manage.py check, operational_check, spectacular --validate
   --fail-on-warn, and the CI container job all green; the CI test job
   includes the new pg-tools step and the drill test runs and passes in CI.
6. The runbook changes are exactly scope item 4; no other doc changes.
7. The diff touches only allowed_paths; zero product behavior change; zero
   new dependencies; zero migrations.

## Deferred human adjudication

- Decision: NONE
