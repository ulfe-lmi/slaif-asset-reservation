<!-- OAP-META
{
 "id": "025-a",
 "round": "a",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "base_sha": "e94d95e985412f9fc2fa27508be6ae36d606c4ce",
 "issue_number": 49,
 "branch": "codex/49-oap-025-a-deployment-qualification",
 "pr_mode": "CREATE_OR_RESUME",
 "previous_round": null,
 "allowed_paths": [
  "README.md (line-12 objective count only)",
  "PLAN.md (two line-level fixes only)",
  "SECURITY.md (line-5 project-status sentence only)",
  "ARCHITECTURE.md (two line-level token fixes only: A-03 DRF constraint, SAR-022 DRF token)",
  "INSTALL.md (section 2 prerequisites only)",
  "compose.yaml (postgres image line only)",
  "compose.production.example.yaml (postgres image line only)",
  "docs/roadmap.md (line 190 count + 'Next roadmap item' block only)",
  "docs/human-ui.md (line-3 status token only)",
  "docs/api-contract.md (line-3 status token only)",
  "docs/audit/ICA-PROTOCOL.md (line-27 requirement-source reference only)",
  ".github/workflows/ci.yml (test-service postgres image line + workflow_dispatch trigger + new deployment-rehearsal job only)",
  "oap/orders/025-a-deployment-qualification.md",
  "oap/active",
  "oap/reports/025-a-deployment-qualification.md"
 ],
 "forbidden_resources": [
  "any src/ change (no product behavior change of any kind)",
  "any change under tests/ (no new or modified tests)",
  "pyproject.toml, uv.lock, or any dependency change",
  "Dockerfile (already digest-pinned; must stay byte-identical)",
  "data/, migrations, or any product byte",
  "any other .github/ change",
  "any other oap/ file (no OAP expansion: no new canary, protocol, transport, role, or governance document)",
  "any other docs/ file — in particular the historical snapshots: docs/bootstrap/**, docs/work-orders/**, docs/decisions/**, docs/discovery-brief.md, STATUS.md (HISTORICAL label), docs/project-handoff.md (HISTORICAL label) — these stay byte-identical",
  "any change to ARCHITECTURE.md beyond the two ordered token fixes (no SAR rewording, no structure change, no new content)",
  "deployment of any kind (the disposable synthetic rehearsal is the established exception; no real DNS/TLS/certificates/hosts)",
  "real secrets in Git, the diff, prompts, or logs (rehearsal creates synthetic git-ignored values only and removes them itself)",
  "Kubernetes, Swarm, Helm, Terraform, Ansible, Celery, Redis, or any new deployment platform",
  "ICA activity or milestone-completion claims",
  "any mutating GitHub operation except pushing this branch, opening this objective's PR, and triggering this objective's opt-in workflow_dispatch run on the PR branch",
  "merging or auto-merging any PR (merge is strategy's delegated act after exact-head review)",
  "credentials, auth files, sessions, tokens, auth homes"
 ]
}
-->

# 025-a — Deployment qualification: document-truth, image reproducibility, opt-in full-rehearsal CI

## Goal

Prepare the repository for the first controlled internal-alpha Docker deployment
gate by fixing exactly the deployment-relevant truth and reproducibility gaps
that skeptical inspection of main e94d95e found: (1) current-state documents
that still describe the pre-024-a world or a dependency reality the lockfile no
longer holds; (2) a broken requirement-source reference that would misdirect
the Independent Closure Audit; (3) the missing supported-host-architecture
statement in the canonical INSTALL.md; (4) the only remaining floating base
image (PostgreSQL) in the deployment and CI definitions; and (5) no way to
prove the FULL production-shaped rehearsal on a clean checkout/runner at gate
time without slowing every PR. No product changes, no new tests, no OAP
expansion, no real deployment in this PR.

## Durable provenance and requirements

- H: in-session human principal instruction 2026-09-17 (deployment-qualification
  and closure task for the first controlled internal-alpha Docker deployment;
  explicitly NOT an authorization to deploy, create/rotate real secrets,
  configure DNS/TLS, expose a host, or touch production/private data).
  Verbatim drivers: Section A — "Determine the actual supported architecture.
  The Python base was previously pinned to a linux/amd64 digest; reconcile
  that with INSTALL prerequisites and the intended deployment target";
  Section A — "determine whether the full rehearsal belongs in CI, a
  conditional deployment CI job, or remains intentionally manual; justify the
  choice from evidence"; Section B — "inspect container supply-chain/
  reproducibility choices: Python digest, PostgreSQL tag, uv image, dependency
  audit ... identify material drift risks"; Section E — "correct current-state
  drift, especially post-024 wording, but do not rewrite historical snapshots
  merely to make them look current".
- A: S-05 (canonical current documents must state current truth), S-06
  (bounded routine engineering, no planning loops), S-12 (proof-sized objective
  with H/A/E/I/C), S-15 (report boundary; truthful evidence), S-16/S-17
  (exact-head review; delegated development merge), S-19 (synthetic rehearsal
  evidence only; name exact commands and results), S-22 (development acceptance
  stays separate from deployment; no production-ready language), S-23 (ICA
  inputs must point at the real requirement source).
- E: strategy-verified at live main e94d95e985412f9fc2fa27508be6ae36d606c4ce
  (2026-09-17; coding re-verifies every line against the base before editing —
  verify, do not assume; if a cited line differs, STOP and report BLOCKED with
  the discrepancy):
  - Remote truth: GitHub main = e94d95e985412f9fc2fa27508be6ae36d606c4ce; zero
    open PRs; latest item number 48 (issue/PR), so issue #49 is next; OAP state
    INACTIVE, pointer ABSENT; worktree clean on main.
  - CI truth: run 34880911343 at merge commit e92ac9925408eabfdddb3a06f59969837
    087aed1: jobs quality/container/security/test all success, head_sha
    verified; test job 104099683014 log contains
    "======================= 611 passed in 126.58s (0:02:06) =
    ==============". Run 34881077026/34881077088 at e94d95e: success (the
    quiescent commit touches only oap/active, so path-filtered CI ran the
    oap-harness job only; the product bytes at e94d95e are identical to those
    at e92ac99).
  - Stale current-state claims (all observed at base, with line numbers):
    README.md:12 "OAP objectives 015-a through 023-a"; docs/roadmap.md:190
    "objectives 015-a through 023-a have been implemented on `main`";
    docs/roadmap.md:207-211 "Current human selection: the canonical
    installation/deployment documentation cleanup (objective 024-a, current),
    then the first real internal-alpha deployment ..."; PLAN.md:56
    "Django5.2/DRF3.16"; PLAN.md:60 "SAR requirement index are in
    ARCHITECTURE.md and specifications/REQUIREMENTS.json.";
    docs/audit/ICA-PROTOCOL.md:27 "Materialize templates/request drafts and a
    complete initial matrix from specifications/REQUIREMENTS.json.";
    docs/human-ui.md:3 "internal pre-alpha human MVP"; docs/api-contract.md:3
    "pre-alpha implementation contract"; SECURITY.md:5 "pre-alpha/bootstrap
    stage"; ARCHITECTURE.md:66 "DRF `>=3.16,<3.17`" (while pyproject.toml:10
    actually declares "djangorestframework>=3.16,<3.18"); ARCHITECTURE.md:526
    (SAR-022 body) "DRF3.16" (while uv.lock resolves djangorestframework
    3.17.2 / django 5.2.17 — changed by the human-accepted security-remediation
    round 016-a).
  - The directory `specifications/` does not exist at base; PLAN.md:60 and
    docs/audit/ICA-PROTOCOL.md:27 reference a file that was never created
    (the canonical requirement source is the ARCHITECTURE.md SAR index,
    SAR-001 through SAR-038, ARCHITECTURE.md lines ~335-690).
  - Historical documents containing old wording that MUST stay byte-identical
    (verified as historical, not live status): docs/discovery-brief.md
    (dated 2026-06-19 accepted bootstrap baseline), docs/work-orders/0001-
    application-scaffold.md, docs/decisions/0001-django-modular-monolith.md,
    STATUS.md (HISTORICAL label), docs/project-handoff.md (HISTORICAL label),
    docs/bootstrap/1/inputs/PLAN.md (archived input snapshot; its digest is
    asserted by tests/oap/test_ba01_inputs.py against tests/oap/
    fixture_digests.py INPUT_DIGESTS — do not touch).
  - Deployment-layer observations at base: Dockerfile line 3 is
    `FROM python:3.13-slim@sha256:cc9dffa47c8294ba9bb795a8dfaeb7b76f2b30acad
    e2c52a461a2999d127eb00` (linux/amd64 digest; keep byte-identical);
    Dockerfile line 17 copies uv 0.11.23 (version-pinned, keep);
    compose.yaml:3 `image: postgres:17` (FLOATING);
    compose.production.example.yaml:3 `image: postgres:17` (FLOATING);
    .github/workflows/ci.yml:29 test service `image: postgres:17` (FLOATING).
    INSTALL.md section 2 (lines 31-48) lists prerequisites WITHOUT any
    supported-architecture statement, and its outbound-connectivity bullet
    says "pull `python:3.13-slim` (pinned by digest in the `Dockerfile`) and
    `postgres:17`". .github/workflows/ci.yml `on:` has only pull_request +
    push(main); jobs quality/test/security/container; the container job runs
    `docker compose config`, rehearsal --config-only, production-compose
    render assertion, docker build, runtime-user and static/bootstrap checks;
    NO full rehearsal is run in CI. deploy/rehearse_internal_alpha_
    deployment.sh: non-interactive (no TTY needed), self-cleaning on success,
    modes (no flag)=full / --config-only / --status / --cleanup-owned, env
    overrides SLAIF_REHEARSAL_PORT (default 18080) / SLAIF_REHEARSAL_PROJECT /
    SLAIF_REHEARSAL_IMAGE, refuses to start if deploy/env.production or
    deploy/secrets/postgres_password exist, refuses to start while
    rehearsal-owned residue exists.
  - Strategy executed the FULL rehearsal (no flag) against exactly these
    bytes at e94d95e on 2026-09-17: rehearsal=ok, exit 0, post-run --status
    clean, synthetic files removed. This round re-runs it at the
    implementation head (criteria 6).
  - Coding environment: Docker Engine + Compose v2 available (as in prior
    rounds); if the full rehearsal cannot run locally, report BLOCKED with the
    exact failing step (no --config-only substitution).
- I: documentation-only plus image-tag pins plus one opt-in CI job. No product
  behavior changes. The postgres digest pin freezes the PostgreSQL minor
  version for deployment and CI (risk: the pinned digest must be one the full
  rehearsal passes — mitigated by the mandatory local full rehearsal before
  push and by the mandatory workflow_dispatch run on the PR branch). The two
  ARCHITECTURE.md token fixes change the ARCHITECTURE.md SHA-256; the
  post-merge digest is an input to the next round's ICA request (026-a) —
  record the new digest in the report. No test asserts the live
  ARCHITECTURE.md digest (fixture_digests.py asserts archived snapshot bytes
  only), so the harness is unaffected; the report must still show the full
  suite green.
- C: S-19 (synthetic evidence only; exact commands and results), S-21 (no
  secrets in artifacts), S-22 (no production-ready/deployed language; this PR
  is development acceptance of qualification inputs, not deployment),
  SAR-022 (stack documentation must match observed pyproject.toml/uv.lock),
  SAR-024 (topology/exposure documentation truthful), SAR-031 (rehearsal
  resource ownership intact), SAR-032 (evidence before readiness; CI at exact
  head), SAR-037 (canonical documents state current truth), SAR-038 (ICA
  materialization must reference the real requirement source).

## Current reconciled state and prerequisites

- Base main (local and remote): e94d95e985412f9fc2fa27508be6ae36d606c4ce
  (024-a quiescent). Worktree clean on main; oap/active absent (INACTIVE).
- Fresh round: no local/remote branch codex/49-oap-025-a-deployment-
  qualification, no PR for issue #49 (verify with git ls-remote and gh before
  creation); pr_mode CREATE_OR_RESUME resolves to CREATE. Record the
  GitHub-assigned PR number truthfully.
- If any cited E-list line differs from the live base, STOP and report BLOCKED
  with the exact discrepancy (do not guess at an alternative line).

## Ordered read set

Standard compact read set, plus (read before writing anything):
README.md (lines 1-40), PLAN.md (P-03 section), SECURITY.md (Project status
section), ARCHITECTURE.md (A-03 section lines ~62-72; SAR-022 lines ~524-532;
SAR index header lines ~330-340 — do not read the whole index this round),
INSTALL.md (section 2, lines ~31-48), compose.yaml, compose.production.
example.yaml, .github/workflows/ci.yml (in full), docs/roadmap.md (lines
~185-215), docs/human-ui.md (header), docs/api-contract.md (header), docs/
audit/ICA-PROTOCOL.md (lines ~20-35), deploy/rehearse_internal_alpha_
deployment.sh (usage header + mode dispatch), pyproject.toml (dependency
listings), uv.lock (django/djangorestframework entries only),
tests/oap/fixture_digests.py (to confirm which digests are asserted and that
live ARCHITECTURE.md is NOT among them).

## Scope and allowed paths

1. README.md — line 12 only: "015-a through 023-a" -> "015-a through 024-a".
   No other README change.
2. docs/roadmap.md — two changes only: (a) line 190: "015-a through 023-a" ->
   "015-a through 024-a"; (b) the "Next roadmap item" block (lines 207-211):
   replace "Current human selection: the canonical installation/deployment
   documentation cleanup (objective 024-a, current), then the first real
   internal-alpha deployment, human-authorized and performed per `INSTALL.md`."
   with text stating that 024-a is complete and the current human selection
   (2026-09-17) is deployment qualification for the first controlled
   internal-alpha Docker deployment (objective 025-a and the independent
   closure audit that follows), then the first real internal-alpha deployment,
   human-authorized and performed per `INSTALL.md`. Keep "The slice after that
   remains human-selected." Keep "Status: human-selected." No other roadmap
   change; do not restructure.
3. PLAN.md — two line-level fixes only: (a) line 56: "Django5.2/DRF3.16" ->
   "Django5.2/DRF3.17"; (b) line 60: "are in ARCHITECTURE.md and
   specifications/REQUIREMENTS.json." -> "are in ARCHITECTURE.md (SAR index,
   SAR-001 through SAR-038)."
4. SECURITY.md — line 5 only: "The project is in pre-alpha/bootstrap stage and
   is not approved for production use." -> "The project is in internal-alpha
   stage and is not approved for production use."
5. docs/human-ui.md — line 3 only: "internal pre-alpha human MVP" ->
   "internal-alpha human MVP".
6. docs/api-contract.md — line 3 only: "pre-alpha implementation contract" ->
   "internal-alpha implementation contract".
7. docs/audit/ICA-PROTOCOL.md — line 27 only: "Materialize templates/request
   drafts and a complete initial matrix from specifications/REQUIREMENTS.json."
   -> "Materialize templates/request drafts and a complete initial matrix from
   the ARCHITECTURE.md SAR requirement index (SAR-001 through SAR-038)."
8. ARCHITECTURE.md — exactly two token fixes, nothing else: (a) line 66 (A-03):
   "`>=3.16,<3.17`" -> "`>=3.16,<3.18`" (matches pyproject.toml:10
   `djangorestframework>=3.16,<3.18`); (b) line 526 (SAR-022 body): "DRF3.16"
   -> "DRF3.17" (matches uv.lock djangorestframework 3.17.2, resolved by the
   human-accepted 016-a security-remediation round). No rewording, no new
   content, no structural change. The report records the SHA-256 of
   ARCHITECTURE.md after the change.
9. INSTALL.md — section 2 (Prerequisites) only. Add one bullet stating the
   supported host architecture: Linux, x86_64 (amd64) only; the application
   runtime image is built from `python:3.13-slim` pinned to a linux/amd64
   digest in the Dockerfile and the PostgreSQL service image is pinned to a
   linux/amd64 digest in the Compose files; other architectures (for example
   arm64) are not supported or verified for the documented deployment path.
   Update the existing outbound-connectivity bullet so it no longer implies
   `postgres:17` is pulled as a floating tag (state that the PostgreSQL image
   is pinned by digest in the Compose files). No other INSTALL.md change.
10. compose.yaml — line 3 only: `image: postgres:17` -> `image:
    postgres:17@sha256:<digest>`. 11. compose.production.example.yaml — line 3
    only: same pin. The digest in BOTH files is the same single
    linux/amd64 digest resolved at implementation time (see criterion 4).
12. .github/workflows/ci.yml — three changes only:
    (a) test service line 29: `image: postgres:17` -> same digest pin;
    (b) add to `on:` a `workflow_dispatch` trigger with one boolean input
    `run_full_rehearsal` (default true, description: run the full
    production-shaped deployment rehearsal — opt-in, used at deployment-gate
    time);
    (c) add ONE new job `deployment-rehearsal` (name: deployment-rehearsal)
    with `if: github.event == 'workflow_dispatch' && inputs.run_full_rehearsal`,
    `runs-on: ubuntu-24.04`, steps: `actions/checkout@v4` then
    `deploy/rehearse_internal_alpha_deployment.sh` (no flags). The job must
    not run on pull_request or push events. The existing four jobs stay
    byte-identical except the test-service image pin.
    Rationale to record in the report (per human Section A): the full
    rehearsal is NOT added to every PR (it costs minutes and adds no product-
    PR signal beyond the existing image build + suite); it is intentionally
    NOT left purely manual (a clean-checkout, amd64-runner proof at gate time
    removes dependence on one local machine's history); an opt-in
    workflow_dispatch job provides gate-time freshness evidence with zero
    ordinary-loop cost.

## Non-goals

- No product features, no behavior change, no test additions/modifications.
- No OIDC, email, notifications, execution gateway, project/group
  authorization, monitoring stack, image registry, release platform,
  Kubernetes/Swarm/Helm/Terraform/Ansible/Celery/Redis.
- No OAP expansion (no new canary/protocol/transport/role/governance doc);
  no ICA activity; no milestone-completion claims.
- No real deployment, no real secrets, no DNS/TLS, no public exposure.
- No editing of historical snapshots or of any file outside allowed_paths.
- No merge, auto-merge, approval, or settings change.

## Numbered acceptance criteria

1. The report records a documentation-drift table: for each of the 11
   ordered fixes (Scope 1-8), file, base line number, exact old text, exact
   new text — and confirms no current-state document changed beyond those.
   Historical files (the E-list) are byte-identical (prove by diff).
2. ARCHITECTURE.md contains exactly the two ordered token fixes; the report
   records the post-change SHA-256 of ARCHITECTURE.md.
3. INSTALL.md changed only in section 2: the supported-architecture bullet
   present, the outbound-connectivity bullet consistent with digest pinning;
   no other INSTALL.md byte changed.
4. Postgres digest pinning: the report records the exact resolution command
   (`docker buildx imagetools inspect postgres:17` or `docker manifest
   inspect postgres:17`), the linux/amd64 digest chosen, and the PostgreSQL
   minor version that tag resolves to; compose.yaml,
   compose.production.example.yaml and the ci.yml test service all carry the
   SAME digest; `docker compose config` passes for both compose files
   (production-shaped rendered with synthetic values).
5. ci.yml: workflow_dispatch + deployment-rehearsal job exactly as specified
   (event+input gated; full rehearsal, no flags); `bash -n`/YAML-parse of the
   workflow is clean; the four pre-existing jobs unchanged apart from the
   service image pin (prove by diff).
6. Local evidence at the implementation head, commands + literal results in
   the report: FULL rehearsal (deploy/rehearse_internal_alpha_deployment.sh,
   no flag) exits 0 with rehearsal=ok and self-cleans (post-run --status shows
   no rehearsal-owned projects; deploy/env.production and deploy/secrets
   absent afterwards); full pytest suite green (611 at this revision),
   oap-harness green (154); ruff check + ruff format --check; mypy;
   makemigrations --check --dry-run; manage.py check; operational_check;
   spectacular validation; pip-audit passes.
7. CI at the exact implementation head: the four standard jobs all green with
   head_sha verified from the GitHub API. Then trigger exactly ONE
   workflow_dispatch run on the PR branch (`gh workflow run ci.yml -f
   run_full_rehearsal=true --ref <branch>`) and record its completion with
   head_sha verified — this is the end-to-end proof of the new job.
8. The implementation diff touches exactly the 12 allowed product/config files
   plus the round bytes (oap/orders/025-a-deployment-qualification.md,
   oap/active, and the report). No src/, tests/, dependency, Dockerfile,
   migration, or OAP-machinery change.
9. PR description contains: why each change group is needed (deployment
   qualification), the drift table, the digest-resolution evidence, the
   workflow_dispatch run evidence, the exact verification results, and the
   remaining blockers before a real internal-alpha deployment (truthful
   language: CI-green candidate; real deployment not yet evidenced;
   deployment remains human-authorized).
10. DHA outcome: NONE.

## Deferred human adjudication

- Decision: NONE
