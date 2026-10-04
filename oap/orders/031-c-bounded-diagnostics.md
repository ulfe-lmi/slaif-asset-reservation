<!-- OAP-META
{
  "id": "031-c",
  "round": "c",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "696b87965920817f1a6b36589562a4af68e75497",
  "issue_number": 61,
  "branch": "codex/61-oap-031-a-gunicorn-idle-connections",
  "pr_mode": "AMEND",
  "previous_round": "031-b",
  "pr_number": 62,
  "allowed_paths": [
    "tests/test_gunicorn_responsiveness.py (bounded failure diagnostics/startup cleanup only)",
    "oap/orders/031-c-bounded-diagnostics.md",
    "oap/active",
    "oap/reports/031-c-bounded-diagnostics.md"
  ],
  "forbidden_resources": [
    "all other application/domain/auth/policy/UI/dependency/migration/inventory/workflow/canonical governance edits",
    "foreign/user dirty or ignored files, existing deployment files, live services or their images/containers/volumes",
    "actual public exposure, host LAN/DNS/TLS/firewall changes, real secrets/private/production data/lab/Neumann probes",
    "merge or auto-merge, force-push/rebase/reset/clean/stash, authentication copying"
  ],
  "requirements": [
    "SAR-022",
    "SAR-024",
    "SAR-025",
    "SAR-031",
    "SAR-032",
    "SAR-033",
    "SAR-035",
    "SAR-038"
  ],
  "decision_class": "D0",
  "target_gate": "M-INTERNET-UX-PILOT development; real exposure remains human D2",
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "8483a070026f382bb9b698e9346f3cb33f7dea44f8190b231431585986ebb17d",
    "PLAN.md": "d03eb29713cfbdb7e227413618396e6bb2a7a08749225979c3055dacfd461d06"
  }
}
-->

# 031-c — Bound failure diagnostics before cleanup

Goal: final fixture correction on same issue61/PR62, before merge. H humanrequirement8 real durable regression/owned cleanup; A SAR031/032 and 031-b criterion1 bounded startup failure cleanup; E at exact implementation fe29e5640fd35945f3a9a835377aecbf617eb6a6, strategic owned actualGunicorn process with1worker/2threads became ready, log_tail called onliveprocess in owneddaemonthread did NOT return within500ms; stopping ownedprocess reaped0orphans andreaderterminated. Earlier systemPython attempt failed readiness because that interpreter lacks required applicationenvironment, thenownedprocess cleanup0; successfulreproduction usedrepo.venv/bin/python. No existingservice/DB touched. Fault: assert wait_ready messages evaluate blocking stdout.read BEFORE assertion raises/finally executes. Report464d54d36ad6f55eb942e50c292bb196c82ed674 verified against actual remote PR62, report-only firstparent fe29e5640fd35945f3a9a835377aecbf617eb6a6. Allfive implementation checks success at fe29e56; report checks may still be running, and this independently reproduced source fault warrants correction irrespective of those checks. D0/DHA NONE.

Scope tests/test_gunicorn_responsiveness.py diagnostic/readiness cleanup only plus ownorder/active/report; allruntime/app/docs/deps/migrations/workflows/othergovernance unchanged, both priororders/reports immutable. No reset/clean/stash/foreignresources/public exposure/private data/merge.

Numberedacceptance:
1. Make log diagnostics finite even while Gunicorn isalive. Small safechoice: if proc.poll isNone, return bounded explanatory marker without reading until EOF; stoppedprocess logs can be read after bounded teardown. Or ownedfile/boundednonblockingread withproof. No unbounded pipe.read on a potentiallyaliveprocess. Retain useful stoppedstartup-failure logs and finite graceful/forced/session reaping.
2. Add meaningful failure regression that simulates readiness failure WHILE REAL ownedGunicorn remainsalive (short/forced readiness-result is fixture injection, worker behavior remainsreal), causes actual same message/assert/finally path, and proves prompt return +0children. Verify live diagnostics itself completes promptly, safe afterstop, every thread/socket/child cleaned even when assertionsfail. Use boundedthread coordination to prove oldbehavior sensitivity without hangingtest or leavingdaemonbehind. Old fixture negativecontrol may be checked in disposablecopy; neverrewriteoldreports. This is fixture-safety test, not substitute for real sixsocket oldsync negatives or positives; all existing seven cases retained; report actual count.
3. Focused Gunicorn suite locally plus lint/format/type/diff; standardfiveCI on exactimplementationhead SUCCESS thennormalimmutable report-only sequence literalfullSHA firstparent/SELF, unknown reportCI atauthoring, pushremoteverify/notifyexit. Existing fullCI guards domainPG/browser/restore/threadrace. No new docsnecessary.

Strongestreasonnotmerge: a finite-readiness loop is not finite if building its failure message blocks before cleanup. Realalive-process failure regression closes this last observed gap; preserve productionpool fix and previous sensitivity controls. Do not expand into testframeworkrefactor, routineboundedfixture repaironly. Publicationnormal samePR, newcorrection c previousb; no autonomous merge.

## Deferred human adjudication
- Decision: NONE
