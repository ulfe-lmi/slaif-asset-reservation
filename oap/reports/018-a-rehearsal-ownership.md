<!-- OAP-META
{
 "kind": "report",
 "id": "018-a",
 "order_path": "oap/orders/018-a-rehearsal-ownership.md",
 "order_sha256": "1e79aaa21e929c85fa7e8e21902840c60b3d9c961b4c24ccaa7e167b231b1b86",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 35,
 "pr_number": 36,
 "branch": "codex/35-oap-018-a-rehearsal-ownership",
 "implementation_head": "b83d8a57355a80482b473f57df06b58a57246227",
 "base_sha": "ca61095a8cc36155b984f34fbf5ae5d4034d2951",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "b83d8a57355a80482b473f57df06b58a57246227",
  "runs": [
   {"run_id": 34802239042, "workflow": "CI", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success"}},
   {"run_id": 34802238941, "workflow": "oap", "jobs": {"oap-harness": "success"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 018-a report — rehearsal resource ownership: crash-safe recovery of
# disposable rehearsal infrastructure

Order digest: 1e79aaa21e929c85fa7e8e21902840c60b3d9c961b4c24ccaa7e167b231b1b86
(committed `oap/orders/018-a-rehearsal-ownership.md`; byte-identical to the
materialized `.FINAL` source — the strategic workorder journal's
`order_written` event records the same sha256 for the `.FINAL` path, and the
renamed file re-hashed to the same digest after the move).

Implementation head SHA: b83d8a57355a80482b473f57df06b58a57246227

Report publication commit: SELF

**Result: COMPLETE** — the deployment rehearsal is now recovery-safe for the
resources it owns: an ownership rule (Compose project-label prefix), a
read-only `--status` mode, an explicit operator-invoked `--cleanup-owned`
mode, a startup residue-scan refusal, and a port precheck that classifies the
occupant — all proven through the existing fake-docker harness, with the four
pre-existing rehearsal tests passing unchanged. No product behavior change,
no compose/Dockerfile/production configuration change, no new dependencies,
nothing under `.github/` changed. PR #36 opened at the exact implementation
head before this report. DHA untouched (Decision: NONE).

## Reconciliation at start (C-05/C-06/CP-03)

- `oap/active` = `018-a` + LF (exactly one valid ID);
  `check_state.py --repo .` → `state=ACTIVE_PENDING` (valid final order
  active), order `018-a` round `a`, `pr=None`, branch
  `codex/35-oap-018-a-rehearsal-ownership`; `pr_mode` CREATE_OR_RESUME;
  single DHA declaration `Decision: NONE`.
- Local `main` = remote `origin/main` = `ca61095a8cc36155b984f34fbf5ae5d4034d2951`
  = the order's `base_sha` (re-verified with `git fetch` before any edit).
- No pre-existing branch `codex/35-oap-018-a-rehearsal-ownership`
  (local or remote) and no open PR for issue #35 → fresh CREATE (no resume
  state). Issue #35 is open with the matching title.
- Wrapper had already consumed the control OK (journal: `order_written`
  (sha256 `1e79aaa2…b1b86`), `published_not_signaled` (FIFO reader timeout),
  then `control_consumed` and `invoked` for 018-a); it was not consumed again
  (CP-03).
- The order's meta `allowed_paths` names
  `oap/orders/018-a-rehearsal-ownership.md` while the wrapper materialized
  `oap/orders/018-a-rehearsal-ownership.FINAL.md`. The `.FINAL` source was
  verified byte-identical to the committed canonical name (sha256
  `1e79aaa2…b1b86` before and after the rename; the journal's `order_written`
  event records the same digest for the `.FINAL` path), the canonical name
  was committed, and the `.FINAL` duplicate left the worktree with the rename
  (bytes durable in git and in the journal). This is the same convergence the
  017-a report documented for its `.FINAL` source, and it is required for the
  round to complete: `check_state.py` and `verify_report.py` each require
  exactly one order file matching the active ID.

## Inspected pre-change state (criterion 1) — PASSED

All facts verified directly at base `ca61095a8cc36155b984f34fbf5ae5d4034d2951`:

- **Project naming line**
  (`deploy/rehearse_internal_alpha_deployment.sh`, base line 49):
  `project="${SLAIF_REHEARSAL_PROJECT:-slaif-alpha-rehearsal-$$}"` — unique
  per run by process id.
- **Trap/cleanup block** (base lines 74–90 + line 91): `cleanup()` removes
  the synthetic env file, password file, and mktemp directory, and runs
  `docker compose … down -v --remove-orphans` only when `compose_started=1`;
  it is installed as `trap cleanup EXIT` — an EXIT-only trap, so a SIGKILL,
  crash, or power loss never runs it, and no later run scans for or recovers
  residue left by such a run.
- **No orphan scan, no port precheck at base**: the base script's only
  failure on a port conflict is the opaque bind failure inside
  `compose up -d app` (the first action that can hit it); there is no
  `docker ps`-based enumeration, no `--status`, no `--cleanup-owned`, and no
  usage text for any recovery mode. The default host port is 18080
  (`SLAIF_REHEARSAL_PORT`).
- **fake-docker harness shape**
  (`tests/test_operational_hardening.py`, base lines 39–63): `fake_docker()`
  writes a stub `docker` bash script that appends every invocation
  (`"$*"`) to `SLAIF_FAKE_DOCKER_LOG` and, for `compose … config --format
  json`, renders the expected config JSON (one published 127.0.0.1 app port)
  to both stdout and `SLAIF_FAKE_DOCKER_RENDERED_CONFIG`, then exits 0;
  otherwise every invocation (build, image inspect, run, compose up/down/
  run) exits 0 silently. Pre-existing rehearsal tests: two config-only tests
  (temporary env + cleanup; configured port without base port), one
  env-refusal test, one git-check-ignore test — config/refusal paths only,
  no inventory, no ports, no down simulation.

## What changed (commit b83d8a5, 5 files, +815/−13, all on allowed_paths)

1. `deploy/rehearse_internal_alpha_deployment.sh` (+222/−2) —
   ownership-scoped recovery, existing behavior otherwise intact:
   - One `project_prefix="slaif-alpha-rehearsal-"` constant; the default
     project now renders as `${project_prefix}$$` (semantically identical to
     the base literal). A resource is rehearsal-owned iff its
     `com.docker.compose.project` label starts with the prefix; a foreign
     project containing the substring elsewhere is not owned.
   - `--status` (read-only, zero Docker mutation): `docker ps -a --filter
     label=com.docker.compose.project` + prefix rule; prints
     `project=… container=… state=… age=…` per owned container (age computed
     from the `CreatedAt` field via the already-required python3) plus a
     `residue=found remove=…` line or the clear
     `no rehearsal-owned projects found` line; exit 0 either way.
   - `--cleanup-owned` (destructive, explicit, its own mode — the script
     takes exactly one mode argument, so it can never combine with a
     rehearsal run): unique owned projects in sorted order, `docker compose -f
     compose.production.example.yaml -p <project> down -v --remove-orphans`
     per project, printing each project before and after removal; re-scans
     afterwards and prints `cleanup=ok` only when the re-scan is empty
     (otherwise `cleanup=incomplete` + remaining projects, exit 1). No-op
     with `no rehearsal-owned projects found` and exit 0 when nothing is
     owned. Foreign projects are never matched, so they are never touched.
   - Full-mode startup scan, placed exactly at the order's anchor (after the
     pre-existing build/runtime-user/asset checks, immediately before
     `compose up -d db`): any owned project → refusal on stderr naming each
     project and the exact command
     `deploy/rehearse_internal_alpha_deployment.sh --cleanup-owned`, exit 1,
     no `up`/build beyond the pre-scan point, no `down`, no automatic
     destruction.
   - Full-mode port precheck, immediately before `compose up -d app`:
     python3 socket bind on `127.0.0.1:<SLAIF_REHEARSAL_PORT>` (free →
     continue; occupied → classify). Classification enumerates owned
     containers and reads each one's `NetworkSettings.Ports` via
     `docker inspect`; an owned container publishing the host port → refusal
     pointing at `--cleanup-owned`; otherwise →
     `host port … is in use by a non-rehearsal process; choose another
     SLAIF_REHEARSAL_PORT`. No auto-kill in either class. The rehearsal's own
     db container is owned but never publishes the app port (compose
     `expose` only), so the precheck cannot false-positive on it.
   - Usage text updated for the new modes and the ownership rule;
     `--config-only` path byte-for-byte unchanged (verified by diff and by
     the unchanged regression tests plus the real-docker run below).
   - Pre-existing refusal behaviors untouched (diff-verified):
     env.production/secrets refusal, port validation, runtime-user check,
     image asset checks, and all smoke-check logic.
2. `tests/test_operational_hardening.py` (+361/−1) — fake-docker harness
   extended (default behavior byte-identical, so the four pre-existing
   rehearsal tests pass unchanged): optional stateful container inventory
   (`cid|name|state|created|project|ports_json` rows) — `ps` prints the
   first five fields, `inspect` prints the ports JSON, `compose down -p`
   removes exactly that project's rows (decoys survive); optional
   per-`ps`-call phases (call 1 = startup scan, call 2 = port precheck) for
   deterministic precheck testing; simulated `image inspect` runtime user
   (default `10001:10001`). Seven new tests:
   - `test_rehearsal_full_mode_refuses_owned_residue_without_up_or_down` —
     full mode with pre-existing owned app+db and a foreign decoy: exit 1,
     stderr names the owned project + exact recovery command, foreign
     project never named, docker log proves no `up` and no `down`, temporary
     env/password files cleaned by the trap.
   - `test_rehearsal_cleanup_owned_removes_only_owned_project` — exactly one
     scoped down for the owned project (log proves it), the decoy foreign
     project survives in the state file, re-scan (second `ps`) runs,
     `cleanup=ok` printed.
   - `test_rehearsal_cleanup_owned_noop_without_residue` — exit 0, no-op,
     `none found`, zero down invocations, decoy state byte-identical.
   - `test_rehearsal_status_lists_owned_residue_read_only` — lists both owned
     containers with name/state/age, omits the foreign container, docker log
     contains exactly one `ps` invocation and no mutation keyword, state
     byte-identical.
   - `test_rehearsal_status_none_found_is_read_only` — exit 0, clear
     `none found` line, single `ps` invocation.
   - `test_rehearsal_port_precheck_refuses_owned_occupant` — real loopback
     listener occupies a dynamically chosen port; scan phase empty (startup
     scan passes, proving the precheck is the refusing boundary), precheck
     phase owns the port: refusal names the container/project and points at
     `--cleanup-owned`; `up -d db` happened, `up -d app` did not; no kill.
   - `test_rehearsal_port_precheck_refuses_foreign_occupant` — same shape,
     foreign occupant: the exact non-rehearsal message with the
     `SLAIF_REHEARSAL_PORT` guidance; no kill.
3. `docs/runbooks/internal-alpha-pilot-readiness.md` (+25) — one new
   factual section ("Rehearsal Residue And Port Recovery") after the
   Rehearsal Command section: the crash/orphan scenario, `--status`,
   `--cleanup-owned`, and the foreign port occupant →
   `SLAIF_REHEARSAL_PORT` rule. All pre-existing content retained.
4. `oap/orders/018-a-rehearsal-ownership.md` (+216) + `oap/active` (+1) —
   the round bytes (commit message records the sha256 and byte-identity,
   mirroring the 016-a/017-a convention).

## Numbered acceptance evidence

**1. Pre-change state recorded — PASSED.** See "Inspected pre-change state"
above; every fact (project naming line, trap/cleanup block, absence of any
orphan scan or port precheck at base, fake-docker harness shape) verified
directly at base `ca61095`.

**2. Script implements the ownership rule, `--status`, `--cleanup-owned`,
startup scan refusal, and port precheck exactly as scoped; pre-existing
refusals unchanged — PASSED.** Scope item 1 point-by-point in "What changed"
item 1; pre-existing refusal/check lines verified unchanged by
`git diff ca61095..b83d8a5 -- deploy/rehearse_internal_alpha_deployment.sh`
(only the usage block, the mode case, the project-prefix line, and the new
inserts) and by the four unchanged regression tests plus the real-docker
`--config-only` run (exit 0).

**3. New tests pass in the CI test job (fake docker, no real containers) —
PASSED.** CI test job at the head (run 34802239042, job 103847064806):
`587 passed in 118.42s`, 0 failed, 0 skipped — the 11 rehearsal tests
(4 pre-existing unchanged + 7 new fake-docker tests) are included. Local at
the head: same 11 tests `11 passed in 0.98s`
(`pytest -k rehearsal`), full suite `587 passed in 167.15s`.

**4. Four existing rehearsal tests pass unchanged; full suite and all gates
green at the exact implementation head — PASSED.** The four pre-existing
rehearsal test functions are byte-identical (diff shows only the harness
function, imports, and appended tests in that file) and pass. Local at head
`b83d8a5` (CI-equivalent environment, `OAP_ROLE` unset): `uv sync --locked
--all-groups` exit 0 (lock untouched); `uv run ruff check .` clean;
`uv run ruff format --check .` clean; `uv run mypy src` clean (119 files);
`manage.py check` — 0 issues; `makemigrations --check --dry-run` — "No
changes detected"; full pytest — **587 passed in 167.15s, 0 failed**;
`operational_check` — all dimensions ok; `spectacular --file
build/openapi/schema.yaml --validate --fail-on-warn` — exit 0; `pip-audit` —
"No known vulnerabilities found"; `git diff --check` clean. CI at the same
head: quality, test (587 passed), security, container all success.

**5. Runbook change is exactly the factual update of scope item 3 —
PASSED.** `git diff ca61095..b83d8a5 -- docs/` shows exactly one added
section in `docs/runbooks/internal-alpha-pilot-readiness.md` (+25 lines,
inserted after the `--config-only` block); no other doc file or line
changed.

**6. Diff touches only allowed_paths; zero product behavior change —
PASSED.** `git diff ca61095..b83d8a5 --stat` = exactly
`deploy/rehearse_internal_alpha_deployment.sh`,
`docs/runbooks/internal-alpha-pilot-readiness.md`,
`oap/orders/018-a-rehearsal-ownership.md`, `oap/active`,
`tests/test_operational_hardening.py` — all on `allowed_paths`. No `src/`,
no templates/settings/models/migrations, no compose file/Dockerfile/
production config, no `.github/`, no dependency change (SAR-022 preserved).

## CLI verification against the actual local Docker (order's ordered read set)

Verified on this host before coding the parsers (Docker 29.1.3, Compose
2.40.3, real daemon; all probes disposable and removed):

- `docker ps -a --filter label=com.docker.compose.project --format
  '{{.ID}}|{{.Names}}|{{.State}}|{{.CreatedAt}}|{{.Label
  "com.docker.compose.project"}}'` — pipe-separated rows; `CreatedAt` is
  local-time form `YYYY-MM-DD HH:MM:SS +ZZZZ TZNAME` (hence the python3
  strptime-based age, GNU `date` rejects the trailing tz abbreviation).
- `docker inspect <id> --format '{{json .NetworkSettings.Ports}}'` — e.g.
  `{"5432/tcp":null,"8000/tcp":[{"HostIp":"127.0.0.1","HostPort":"18099"}]}`;
  expose-only ports are `null`, so the db service never matches a host port.
- `docker compose -f <file> -p <project> down -v --remove-orphans` against a
  project created from a *different* compose file: removes exactly that
  project's containers/networks and leaves a decoy foreign project untouched.
- Port precheck shape: real socket bind on a free loopback port succeeds;
  with a listener present the bind fails with `errno 98` (EADDRINUSE).
- Real-daemon smoke of the new modes (disposable probe container carrying
  the full Compose label set, project `slaif-alpha-rehearsal-77777`, removed
  afterwards): `--status` listed it (`state=running age=2s`, exit 0);
  `--cleanup-owned` removed it via the scoped down, verified absence by
  re-scan, printed `cleanup=ok` (exit 0); `--status` afterwards reported
  `no rehearsal-owned projects found`; real-docker `--config-only` (the CI
  container job's invocation) exited 0 and left `deploy/` clean.

## CI observed before authoring (implementation head)

- CI run **34802239042** (workflow `CI`, head
  `b83d8a57355a80482b473f57df06b58a57246227`): quality success (job
  103847064872), test success (job 103847064806, `587 passed in 118.42s`),
  security success (job 103847064893), container success (job
  103847064716 — includes the real `--config-only` run and the image build +
  runtime-user + static/bootstrap asset checks).
- oap run **34802238941** (workflow `oap`, same head; triggered because the
  diff touches `oap/`): oap-harness success (job 103847064105).
- Report-head CI (post-report-commit): **NOT YET OBSERVED AT AUTHORING.**
  Post-publication verification (remote head/PR/report bytes/parent) is
  recorded in the private execution receipt (CP-07), not in this report.

## Security, data, dependencies and local tools

- No credentials, tokens, peppers, verifiers, cookies or private exports
  appear in this report or in any committed file. The synthetic rehearsal
  env/password values are the same pre-existing synthetic sentinels the base
  script already wrote (unchanged by this round).
- Local disposable infrastructure (SAR-031; owned, explicit identity): docker
  container `slaif-oap018-pg17` (`postgres:17` image, PostgreSQL 17.11),
  loopback-only `127.0.0.1:54330→5432`, synthetic CI-equivalent credentials,
  no volume — the product suite's disposable database, matching the 017-a
  pattern. It is owned by this round and is removed after this report's
  publication steps (`docker rm -f slaif-oap018-pg17`). The CLI-verification
  and mode-smoke probe containers (names `slaif-parser-probe*`,
  `slaif-parser-probe2-*`, `slaif-018smoke-app`, plus one temporary compose
  network/volume set under a `slaif-alpha-rehearsal-99999` test project)
  were all disposable, loopback-scoped, and removed during verification; a
  final `docker ps -a` showed no round-owned residue. No pre-existing host
  resources were touched (the two exited `slaif-155f-postgres-*` containers
  pre-date this round and were left as found). No production/lab/Neumann/
  SmartScheduling contact, no DNS/TLS/firewall changes, no public exposure.
- No new or removed project dependencies; `pyproject.toml` / `uv.lock`
  untouched (SAR-022 preserved). No host tools installed: the rehearsal
  script's required host surface (docker, curl, python3) was already
  present, and this round added no new requirement.
- Environment artifact (not a code defect): the coding wrapper's process
  environment carries `OAP_ROLE=CODING`, which one OAP-harness test
  (`test_ba38_39_tmux_config.py::test_ba39_strategic_same_prerequisites`)
  refuses by design — it fails locally inside a coding invocation but passes
  on CI (the runner has no such variable; job 103847064105 success) and in
  the local harness suite with the variable unset (152 passed, two
  consecutive runs). Separately, `tests/oap/test_roundtrip_canary.py`
  (pre-existing, untouched by this round; same known flake family the 017-a
  report recorded as a CI BrokenPipeError on attempt 1) failed once during a
  local full-suite run and passed in every isolated run and in CI at the
  head. Neither artifact is evidence against this round's changes.

## D0 decisions (routine in-scope mechanics, C-07)

- Scan placement at the order's literal anchor: immediately before
  `compose up -d db` (after the pre-existing build/runtime-user/asset
  checks). The refusal therefore performs no `up`/build beyond what the base
  flow already did before that point, per the order's own wording.
- Port occupancy detection via a python3 socket bind on `127.0.0.1:<port>`
  (python3 is already a hard requirement of the script; no new host tool).
- Port-occupant classification via each owned container's
  `NetworkSettings.Ports` JSON (`docker inspect`), not the human-facing
  `PORTS` column, for an exact HostPort match.
- `--status` / `--cleanup-owned` branch before the env/secrets/port
  refusal checks: a SIGKILLed run can leave `deploy/env.production` behind,
  and the recovery modes must then still work (they neither create nor
  overwrite those files). The pre-existing refusal behaviors are unchanged
  on the full and `--config-only` paths (diff + regression tests).
- Fake-harness port-precheck determinism via per-`ps`-call state phases
  (startup scan sees no residue; the port precheck sees the occupant) so the
  precheck — which in a real full run is shadowed by the earlier startup
  scan whenever the same residue holds the port — is exercised at its own
  boundary without test-time synchronization.

## Limits and uncertainty

- The fake-docker tests prove the harness boundary (invocation shapes,
  scoping, refusal messages, log-based no-up/no-down/no-kill guarantees);
  the real-daemon smoke above additionally exercised `--status`,
  `--cleanup-owned`, and `--config-only` against the actual Docker 29.1.3 /
  Compose 2.40.3 daemon. A full real rehearsal run (build + containers +
  smoke checks end to end) was not executed locally in this round; the CI
  container job covers the build/runtime-user/asset checks and the
  `--config-only` path at the head, and the full-mode happy path is
  unchanged code (diff-verified).
- Ownership detection relies on the Compose project label, which Compose
  writes for containers it created; a resource that lost its label (e.g.
  manually re-labeled) would not be classified as owned. This matches the
  order's ownership rule exactly.
- As with the base script, rehearsal safety presupposes the operator keeps
  `SLAIF_REHEARSAL_PROJECT` values under the documented prefix (usage text
  now says so explicitly); a non-prefixed project name is outside the
  ownership rule by definition and is never touched.
- Report-head CI is not observed at authoring (CP-05/CP-06); implementation
  CI is the observed record above. Coding does not claim strategic
  acceptance of this report.
