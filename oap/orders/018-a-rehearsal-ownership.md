<!-- OAP-META
{
 "id": "018-a",
 "round": "a",
 "base_sha": "ca61095a8cc36155b984f34fbf5ae5d4034d2951",
 "issue_number": 35,
 "branch": "codex/35-oap-018-a-rehearsal-ownership",
 "pr_mode": "CREATE_OR_RESUME",
 "previous_round": null,
 "allowed_paths": [
  "deploy/rehearse_internal_alpha_deployment.sh",
  "tests/",
  "docs/runbooks/internal-alpha-pilot-readiness.md",
  "oap/orders/018-a-rehearsal-ownership.md",
  "oap/active",
  "oap/reports/018-a-rehearsal-ownership.md"
 ],
 "forbidden_resources": [
  "product code under src/, templates, settings, models, migrations, or API behavior changes",
  "compose files, Dockerfile, deploy/env.production.example, deploy/Caddyfile.example, or any production deployment configuration change",
  "new dependencies (host tools: docker, curl, python3 only, as already required by the script)",
  "automatic or implicit destruction of any container, volume, network, or compose project that is not provably rehearsal-owned (prefix + compose project label), or any auto-kill of a port occupant",
  "changing the script's existing refusal behaviors (env.production / secrets refusal, port validation, runtime-user check, image asset checks)",
  "any workflow change under .github/",
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

# 018-a — Rehearsal resource ownership: crash-safe recovery of
# disposable rehearsal infrastructure

## Goal

The deployment rehearsal is the repeated local dry-run that pilot
preparation depends on. Its compose project is named
`slaif-alpha-rehearsal-$$` (unique per run) and cleanup is trap-based
(EXIT only), so resources left by a killed or abandoned run (SIGKILL,
crash, power loss) are never cleaned by later runs, and a live orphaned
app container on the default port 18080 blocks the next rehearsal with
an opaque port-binding failure. This round makes the rehearsal
recovery-safe for the resources it owns: ownership-scoped detection,
explicit operator-invoked cleanup, an actionable port precheck, and a
read-only status mode — with tests through the existing fake-docker
harness and a factual runbook update. No product behavior change.

## Durable provenance and requirements

- H: in-session human principal instruction 2026-09-14 — continue the
  strategy → coding → review → merge loop autonomously; select the next
  smallest product PR that materially advances the real reservation-system
  MVP/pilot; prefer work that directly enables actual users over OAP
  machinery.
- E: origin/main ca61095a8cc36155b984f34fbf5ae5d4034d2951 (017-a
  quiescent, INACTIVE, CI green at merged head 1ea7ffd).
  deploy/rehearse_internal_alpha_deployment.sh — project name
  `slaif-alpha-rehearsal-$$` (line in the header block), `trap cleanup
  EXIT` (cleanup covers env file, password file, tmp dir, and
  `compose down -v --remove-orphans` only when `compose_started=1`); no
  scan for, or recovery of, residue from previously crashed runs; no port
  precheck (the app `compose up -d app` is the first action that could
  fail on a port conflict). tests/test_operational_hardening.py —
  fake-docker harness (`fake_docker` writes a stub `docker` bash script
  that logs invocations and renders the expected config JSON; existing
  rehearsal tests are config-only and refusal-path tests).
  docs/runbooks/internal-alpha-pilot-readiness.md — the operator-facing
  rehearsal runbook.
- A: S-12 (one proof-sized objective), S-15 (report boundary).
- C: S-16 (exact-head review) / S-17 (delegated development merge; main
  workflows verified CI-only).
Requirements: SAR-033 (preserve existing project — the rehearsal's
existing refusal behaviors and production-shaped checks remain intact),
recovery pillar (recovery that preserves work and prevents duplicate
execution), SAR-032 (evidence before readiness — the pilot-readiness
gate must be runnable repeatedly).

## Current reconciled state and prerequisites

- Base main (local and remote): ca61095a8cc36155b984f34fbf5ae5d4034d2951.
  Worktree must be clean on main before starting; `oap/active` absent
  (INACTIVE).
- Known facts (verify, do not assume): compose labels its own resources
  (containers carry `com.docker.compose.project`,
  `com.docker.compose.service`, `com.docker.compose.version`); the
  script's default host port is 18080 (`SLAIF_REHEARSAL_PORT`); the
  script already validates the port is numeric and renders exactly one
  published app port; the fake-docker test harness intercepts all docker
  invocations via PATH and records them in a log file the tests assert
  on.

## Ordered read set

Standard compact read set, plus: deploy/rehearse_internal_alpha_deployment.sh
(in full), tests/test_operational_hardening.py (the rehearsal tests and
the fake-docker harness), docs/runbooks/internal-alpha-pilot-readiness.md,
compose.production.example.yaml (read-only: which services/labels/volumes
the rehearsal starts), and the `docker compose`/`docker` CLI surface the
script will use (verify against the docker version's actual output
shapes on the local host before coding the parsers).

## Scope and allowed paths

1. deploy/rehearse_internal_alpha_deployment.sh — ownership-scoped
   recovery, without changing any existing behavior:
   - New ownership definition: a resource is rehearsal-owned iff it is a
     compose container whose `com.docker.compose.project` label value
     starts with the script's project prefix `slaif-alpha-rehearsal-`
     (the default pattern `slaif-alpha-rehearsal-$$` and any
     `SLAIF_REHEARSAL_PROJECT` value the script itself used, which always
     starts with that prefix; a foreign project that merely contains the
     substring elsewhere is not owned). The prefix constant is defined
     once in the script.
   - New `--status` mode (read-only, no docker mutation at all): list
     rehearsal-owned projects with their containers (names, state, age),
     plus a clear "none found" line; exit 0 whether or not residue is
     found.
   - New `--cleanup-owned` mode (destructive, explicit only): remove
     rehearsal-owned projects (`down -v --remove-orphans` per owned
     project, or equivalent scoped removal), print exactly which project
     IDs/names were removed and verify absence afterwards (re-scan;
     report "cleanup=ok" only when the re-scan is empty). Resources not
     matching the ownership rule are never touched. No `--cleanup-owned`
     combination with a full rehearsal run: it is its own mode.
   - Startup scan (full mode, before `compose up -d db`): enumerate
     rehearsal-owned projects. If any exist, refuse to start with an
     actionable message that names each owned project and the exact
     recovery command (`deploy/rehearse_internal_alpha_deployment.sh
     --cleanup-owned`); exit non-zero; no `up`/`build` beyond what is
     already required before the scan point. No automatic destruction.
   - Port precheck (full mode, before starting the app): if the
     configured host port is occupied, determine the occupant class:
     (a) occupant is a rehearsal-owned container (by the ownership rule)
     -> refuse with an actionable message pointing at `--cleanup-owned`;
     (b) occupant is anything else -> refuse with a clear
     "port in use by a non-rehearsal process; choose another
     SLAIF_REHEARSAL_PORT" message. No auto-kill in either case. The
     precheck must not false-positive on the rehearsal's own db service
     (which never publishes the app port).
   - Usage text updated for the new modes; the `--config-only` path
     unchanged.
2. Tests (extend tests/test_operational_hardening.py or add a focused
   new test module under tests/ — coding decides, but all rehearsal
   tests keep the fake-docker harness pattern; no real containers,
   images, or daemon state in CI):
   - fake docker extended (or a second stub) so it can simulate: a
     pre-existing rehearsal-owned project (e.g. responds to
     `ps`/`compose ls`/`inspect` with a container carrying
     `com.docker.compose.project=slaif-alpha-rehearsal-99999`), a
     foreign project (label `com.docker.compose.project=other-project`),
     and a port occupant (owned vs foreign).
   - Full mode with a pre-existing rehearsal-owned project: refuses with
     the actionable message, and the docker log proves no `up` was
     attempted (and no `down` was attempted by the run itself).
   - `--cleanup-owned`: removes exactly the rehearsal-owned project
     (log shows the scoped down for the owned project ID only); the
     decoy foreign project survives (log proves no down/inspect-driven
     removal for it); re-scan reports empty; "cleanup=ok" printed.
   - `--cleanup-owned` with nothing to clean: exits 0, no-op, reports
     none found.
   - `--status`: read-only (log proves zero mutation invocations),
     lists the simulated owned project, exits 0 with and without
     residue.
   - Port occupied by rehearsal-owned occupant: refuses with the
     cleanup-owned pointer; port occupied by foreign occupant: refuses
     with the non-rehearsal message; both without any kill.
   - Regression: the four existing rehearsal tests (config-only x2,
     env refusal, env stays ignored) still pass unchanged.
3. docs/runbooks/internal-alpha-pilot-readiness.md — factual update:
   document `--status` and `--cleanup-owned`, and the crash/orphan
   recovery procedure (a run killed or lost leaves residue; check with
   `--status`; remove with `--cleanup-owned`; a foreign port occupant
   requires choosing SLAIF_REHEARSAL_PORT). Keep all existing content
   that remains true.

## Non-goals

- No product behavior, model, API, template, settings, or migration
  change; no compose file, Dockerfile, or production config change.
- No new dependencies; no changes under .github/.
- No OAP/governance changes, no canary work, no ICA, no milestone claim.
- No deployment, no real data, no lab/Neumann contact.
- No automatic destruction of any resource; no auto-kill of port
  occupants. No merge, auto-merge, approval or settings change.

## Numbered acceptance criteria

1. The report records the inspected pre-change state: the exact project
   naming line, the trap/cleanup block, the absence of any orphan scan
   or port precheck at base, and the fake-docker harness shape.
2. The script implements the ownership rule (prefix + compose project
   label), `--status`, `--cleanup-owned`, the startup scan refusal, and
   the port precheck exactly as scoped; all pre-existing refusal
   behaviors and checks are unchanged (prove by diff and by the
   regression tests).
3. The new tests pass in the CI test job (fake docker; no real
   containers): startup refusal (no `up` in the log), cleanup-owned
   scoped removal with decoy survival and empty re-scan, no-op
   cleanup, status read-only, owned vs foreign port refusals.
4. The four existing rehearsal tests pass unchanged; the full pytest
   suite, quality gates (ruff check, ruff format --check, mypy),
   makemigrations --check --dry-run, manage.py check, operational_check,
   spectacular --validate --fail-on-warn, and the CI container job are
   all green at the exact implementation head.
5. The runbook change is exactly the factual update of scope item 3; no
   other doc changes.
6. The diff touches only allowed_paths; zero product behavior change.

## Deferred human adjudication

- Decision: NONE
