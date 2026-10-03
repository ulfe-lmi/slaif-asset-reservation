<!-- OAP-META
{
 "kind": "report",
 "id": "029-c",
 "order_path": "oap/orders/029-c-command-safety.md",
 "order_sha256": "d3836be1ed8354a041d4b37a4959cda9a12b377f9f8ba643f0900dca5146d4c0",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 57,
 "pr_number": 58,
 "branch": "codex/57-oap-029-a-product-documentation",
 "implementation_head": "0fc0022474a8115071807f6178df71d769aba9a3",
 "base_sha": "f406c612f52f64a50f0a145b27a7f580838c7287",
 "result": "PARTIAL",
 "observed_implementation_ci": {
  "observed_head": "0fc0022474a8115071807f6178df71d769aba9a3",
  "runs": [
   {"run_id": 37132797140, "workflow": "ci.yml", "event": "pull_request", "jobs": {"quality": "success", "test": "success", "security": "failure", "container": "success"}, "failure_boundary": "security: uv run pip-audit exit 1 -> urllib3 2.7.0 (locked) PYSEC-2026-4175/4176/4177, fix 2.8.0; pre-existing dev-only chain (requests/pip-audit/pytest-playwright); lockfile is a forbidden resource of this order"},
   {"run_id": 37132797139, "workflow": "oap.yml", "event": "pull_request", "jobs": {"oap-harness": "success"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 029-c report — Final operator-command safety corrections

Order digest: `d3836be1ed8354a041d4b37a4959cda9a12b377f9f8ba643f0900dca5146d4c0`
(committed `oap/orders/029-c-command-safety.md`, state FINAL,
base `f406c612f52f64a50f0a145b27a7f580838c7287`, issue #57, PR mode AMEND
on the existing PR #58 / branch
`codex/57-oap-029-a-product-documentation`, DHA NONE). Active pointer
`oap/active` = `029-c` + LF (6 bytes `3032 392d 630a`), committed with the
implementation head. Verified at start: local and remote branch both at
the exact 029-b report head
`f3594c7ca01ad22cc8d8406aec2d3b31c55a99b2`; base `f406c61...` present and
ancestor; remote main at the base SHA; PR #58 open, head
`f3594c7...`, `Closes #57` in body, not a draft, no auto-merge request;
order source hashes verified against the working tree
(`ARCHITECTURE.md` `8483a070...`, `PLAN.md` `d03eb297...` — both match the
order metadata); governance revision `14fc20b1...` present. The exact
029-c order bytes and the `029-c` pointer were already present in the
working tree (strategy-owned) and are committed verbatim.

Implementation head SHA: 0fc0022474a8115071807f6178df71d769aba9a3

Report publication commit: SELF

## Identity and result

- Repo/issue/branch/PR: `ulfe-lmi/slaif-asset-reservation` / #57 /
  `codex/57-oap-029-a-product-documentation` / PR #58 (AMEND round c,
  final round of this objective; `Closes #57`).
- **Result: PARTIAL.** All ordered corrections are complete and verified
  as ordered; the diff since b is exactly the two allowed docs plus the
  c order/pointer bytes. The single deviation from a COMPLETE report is
  the required `security` CI check at the exact implementation head,
  which fails for the same pre-existing, unchanged reason as in 029-a/029-b
  (locked dev-only `urllib3 2.7.0` vs published advisories, fix 2.8.0),
  which this order forbids fixing and explicitly routes to strategy / a
  pending human scope decision.

## Acceptance evidence

1. **Exact unified patch applied; no editorial rewrite** — PASSED.
   The order's exact unified diff (extracted verbatim from the committed
   order file; 4605 bytes, SHA-256
   `ae11fbd8aad8dee944ddcc42ed3bf1e38e155f6de0a32ca18dc77b2a5329ea38`)
   was applied with `git apply` after a `--check` pass. Post-apply,
   `git apply --reverse --check` of the same patch succeeds, proving the
   worktree equals base + exact patch bytes. Changes: INSTALL.md
   prerequisite line (Git, curl, Bash); section 5 step 13 (quoted
   `read`-prompt hostname + quoted `${SAR_SERVICE_HOST}` curl); step 16
   (quoted `${SAR_SERVICE_HOST}` in the status-only 401 probe); section 8
   restore block as a single fail-closed AND-chain ending in
   `start app` only after `stop`, `cp`, `pg_restore`, and
   `operational_check` all succeed (with the date-substitution and
   fail-closed comments); section 9 rollback block (quoted
   `read`-prompt image tag + hostname, `docker image inspect` existence
   guard, quoted tag, AND-chain through `up -d app`, readiness probe,
   final `operational_check`). docs/README.md: the two specialist index
   labels corrected (`CRITICAL.md` — the deferred human adjudication
   register; `audit/` — independent closure-audit protocol). No unrelated
   paragraph was touched; no other file in the patch.
2. **Bash syntax + bounded temporary shell harness + substitution** —
   PASSED. `bash -n` on all four changed command blocks (extracted
   byte-exact from the patched INSTALL.md): PASSED x4. TEMPORARY harness
   (owned scratch files under /tmp, no repository files): synthetic
   `docker`/`curl` shell functions recording every call, with injected
   failure points; 9 scenarios executed:
   - Restore block: success -> exact call order `stop`, `cp`,
     `exec pg_restore`, `run operational_check`, `start` with `start`
     only last; injected `cp` failure -> chain stops after `cp` (no
     `pg_restore`, no `operational_check`, no `start`); injected
     `pg_restore` failure -> stops after `exec`; injected
     `operational_check` failure -> stops after `run` (no `start`).
     In every failure scenario `start app` is never called.
   - Rollback block: success -> exact call order `image inspect`,
     `tag`, `up -d app`, readiness `curl`, `run operational_check`;
     injected failures at `image inspect` / `tag` / `up -d app` /
     readiness `curl` each stop the chain immediately after the failing
     call.
   18/18 assertions passed. This proves shell control flow only — no new
   restore claim, and no real DB/restore/secret/host access. Quoted
   `${SAR_SERVICE_HOST}` / `${SAR_PREVIOUS_IMAGE}` substitution verified
   in a scratch shell with 6 cases including glob characters and spaces
   (stays one literal argument; no globbing; no public HTTPS probe, no
   real image retag). 6/6 passed.
3. **Exact diff scope; evidence reuse under byte identity** — PASSED.
   `git diff --name-only f3594c7...(029-b head) 0fc0022...` lists exactly
   `INSTALL.md`, `docs/README.md`, `oap/orders/029-c-command-safety.md`,
   `oap/active` — the two allowed docs plus the c orchestration bytes.
   Product, lockfile, config, migrations, tests, canonical sources
   (PLAN/ARCHITECTURE/CRITICAL), all a/b order and report bytes, and all
   other docs are byte-identical (zero diff outside the four files).
   Prior 029-a real-PG17 quickstart/rehearsal evidence is reused for
   unchanged behavior under that byte identity; no unchanged expensive
   local suite was rerun. Cheap checks on the changed docs: link/anchor
   check PASSED (20 + 43 relative links, all targets and anchors
   resolve; link targets and headings unchanged since b); ledger sweep
   of all added lines found no credential-like content (no
   password/secret/token/Bearer/Authorization/cookie/key patterns, no
   long hex/base64 blobs); `git diff --check` clean. No repository
   tests or source edits.
4. **PR #58 amendment, CI observation, truthful report, signal** —
   IN PROGRESS at authoring (this publication completes it). PR #58 body
   amended via `gh api` REST with a JSON payload file (the known
   deprecated Projects (classic) GraphQL field made `gh pr edit`
   unavailable, as anticipated by the order); no credential in any
   command-line argument. Body now carries the concise final
   scope/verification, the observed implementation-head CI, and the
   unresolved security blocker (final advisory-feed wording per the
   order). All five actual implementation-head checks observed to
   completion (below). This report is the truthful PARTIAL; the response
   FIFO is signaled exactly `OK` (4f4b) only after verified remote
   publication of this report, then EXIT.

## Verification and negative paths

- `bash -n` on the four changed blocks: PASSED (syntax only).
- Temporary shell harness, synthetic `docker`/`curl` functions, 9
  scenarios / 18 assertions (failure injection at copy, pg_restore,
  operational-check, image-inspect, tag, up, readiness curl; success
  order checks): PASSED. Negative paths: every injected failure leaves
  the application NOT started / the chain NOT continued; the success
  path calls `start app` only as the final step.
- Scratch-shell substitution: 6/6 PASSED (glob `exa*ple.com` literal;
  `my host` single argument; quoted `/me/` probe; image tag with space
  single argument to `image inspect` and `tag`; readiness URL verbatim).
  No public HTTPS probe, no real image retag.
- Link/anchor check (two changed docs): PASSED; link targets and
  headings byte-unchanged vs the 029-b head.
- Ledger sweep (added lines only): CLEAN. `git diff --check`: CLEAN.
- Worktree == base + exact order patch (reverse-apply check): PASSED.
- Diff since b: exactly the two docs + order/pointer bytes: PASSED.
- Real PostgreSQL restore, real deployment, real TLS/DNS exposure, real
  secret/host access: NOT RUN (forbidden by the order; harness is
  shell-control-flow evidence only, and per TC-02 mocks prove only the
  harness boundary, not a real restore).

## CI observed before authoring

At implementation head `0fc0022474a8115071807f6178df71d769aba9a3`
(all runs completed before authoring; job conclusions from the
structured CI data):

- Run 37132797140 (workflow `ci.yml`, event pull_request, head 0fc0022):
  quality success, test success (full suite incl. browser at this
  head), container success, **security failure** — `uv run pip-audit`
  exits 1: "Found 3 known vulnerabilities in 1 package" —
  `urllib3 2.7.0` (locked, dev-only chain via
  requests/pip-audit/pytest-playwright) with PYSEC-2026-4177,
  PYSEC-2026-4176, PYSEC-2026-4175, fix 2.8.0. Same pre-existing
  boundary as 029-a/029-b; this order forbids the lockfile change and
  routes the disposition to a separate pending human scope decision.
- Run 37132797139 (workflow `oap.yml`, event pull_request, head
  0fc0022): oap-harness success.

Report-head CI: NOT YET OBSERVED AT AUTHORING (the report-only commit's
checks are reported by strategy; none are claimed here).

## Evidence interpretation correction (report/PR only)

Per the order: the two advisory feeds disagree on publication dates —
the repository security advisory page for GHSA-vxq7-64xx-v4gw displays
Sep 15, while the independently retrieved global GitHub advisory API
gives published_at Sep 30 for all three advisories (vxq7 14:46:18Z,
gh4c 15:00:38Z, 8988 14:46:04Z), i.e. postdating the old Sep 21 green
run. Neither 029-a's nor 029-b's blanket publication-date inference
stands without identifying the source/feed. This report therefore states
only the current observed `pip-audit` failure versus the historical
green CI, with no unproved explanation of the historical data. Old
reports remain immutable.

## Privacy and boundaries

No secrets, tokens, peppers, verifiers, cookies, CSRF values,
Authorization material, private exports, or personal data in this
report, the PR, or any changed file. All verification used owned
disposable scratch files under /tmp (block extractions, harness,
scenario driver, PR body drafts) and mock shell commands; the scratch
directory is owned by this round and contains no repository copies. No
production/lab/Neumann/SmartScheduling/DNS/TLS/firewall/public-exposure
boundary crossed. No destructive cleanup, no reset/clean/stash/
force-push. No new dependencies; no tools installed beyond the locked
environment. No operational CLAUDE.md/Claude launcher.

## DHA outcome and unresolved gates

- Decision: NONE (as declared in the order). No CRITICAL entry
  appended, no gate cleared, no adjudication performed.
- Unresolved gate for strategy: the pre-existing `pip-audit`/`security`
  CI failure (locked urllib3 2.7.0, dev-only chain, 3 advisories, fix
  2.8.0). Resolution requires a dependency/lockfile decision under a
  separate order / human scope disposition; the pending question about
  a separate minimal urllib3 security PR is noted and is NOT an
  authorization. This round neither fixed nor waived it.

## Limitations

- Strongest unresolved limitation: the `security` CI job cannot pass at
  this head without a forbidden lockfile change, so the PR cannot be
  strategy-accepted under an all-green-CI policy until that boundary is
  handled separately.
- The shell-harness evidence proves the control flow of the documented
  command blocks only (TC-02: it proves the harness boundary, not a
  real restore); no real restore drill is claimed.
- All ordered documentation corrections are complete and verified; no
  runtime behavior changed in any byte.
- No merge, release, or self-certification is claimed or implied.
