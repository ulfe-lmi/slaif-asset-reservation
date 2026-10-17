<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "048-c",
  "objective": 48,
  "round": "c",
  "slug": "deterministic-verification-clock",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "1baffe27a66609944f4d7b8e5c12dc69dfaa00b9",
  "issue_number": 99,
  "branch": "codex/99-oap-048-a-authorization-foundation",
  "pr_mode": "AMEND",
  "pr_number": 100,
  "previous_round": "048-b",
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "4566e797b709b71f13b2929572a2d1145d15a5a7ab8b41db50ebfdab962628cd",
    "PLAN.md": "2c856ae47ec985b953a8d26edbe2c07fd343833a41bc45aefcd304a7e67c1432",
    "ARCHITECTURE-for-agents.md": "41c32e0b0d6427a173dfe0b722446ae8ee311f3880929db65ed0245309b3a59e",
    "oap/coding-instructions/AGENTS.md": "1611e9700de5b311deeb45460162464f7f24462e74790dddfcec2bb016b30394"
  },
  "requirements": [
    "SAR-001",
    "SAR-007",
    "SAR-009",
    "SAR-011",
    "SAR-012",
    "SAR-014",
    "SAR-015",
    "SAR-018",
    "SAR-021",
    "SAR-026",
    "SAR-027",
    "SAR-032",
    "SAR-034",
    "SAR-035",
    "SAR-037",
    "SAR-038",
    "SAR-048",
    "SAR-052",
    "SAR-053"
  ],
  "allowed_paths": [
    "src/slaif_reservation/accounts/models.py",
    "src/slaif_reservation/accounts/admin.py",
    "src/slaif_reservation/accounts/authorization.py",
    "src/slaif_reservation/accounts/migrations/0005_user_external_identifier.py",
    "src/slaif_reservation/reservations/models.py",
    "src/slaif_reservation/reservations/migrations/0003_reservation_application_permissions.py",
    "src/slaif_reservation/reservations/management/commands/grant_management_access.py",
    "tests/test_authorization_foundation.py",
    "tests/test_authorization_upgrade.py",
    "tests/test_accounts.py",
    "tests/test_form_guidance.py",
    "tests/browser/test_authorization_admin_browser.py",
    "docs/authorization.md",
    "docs/ux/form-guidance-inventory.md",
    "ARCHITECTURE-for-agents.md",
    "oap/active",
    "oap/orders/048-a-authorization-foundation.md",
    "oap/reports/048-a-authorization-foundation.md",
    "oap/reports/048-a-authorization-foundation.md",
    "oap/orders/048-b-identifier-review-closure.md",
    "oap/reports/048-b-identifier-review-closure.md",
    "oap/orders/048-c-deterministic-verification-clock.md",
    "oap/reports/048-c-deterministic-verification-clock.md",
    "tests/test_qualification_image_ownership.py"
  ],
  "forbidden_resources": [
    "All application/account/authorization/schema/migration/asset/engine/API/UI/proxy/deployment/dependency changes: current048-b implementation is semantically accepted pending CI verification only",
    "tests/test_branding.py and actual _OwnedDocker ownership checks, actualDocker build/cleanup behavior, CI workflow changes, OAP helper/constitution/framework expansion",
    "Existing assertion weakening, sleeps/probabilistic repeated retries, stale/symlink/ownership/ID/race/cache-negative removal",
    "Immutable048-a/b orders/reports or historical audit evidence; realhost/time/DNS/TLS/firewall/secrets/data; foreign resource inspection/adoption/deletion",
    "Any new PR/issue, merge/auto-merge, delegation or unrequested feature"
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Human authorization request2026-10-17\u00a711 and approved OAP execution/verification scope",
      "section_or_evidence": "Meaningful full CI mandatory; smallest bounded fixes to demonstrated failures, no unrelated refactor or qualificationframework."
    },
    {
      "marker": "A",
      "source": "ARCHITECTURE SAR007/009/031/032/037/048/052/053;048-a/b acceptance and source preservation",
      "section_or_evidence": "Actualnegativeevidence, exact-head checks and owned-resource guard integrity; no relaxed ownership proofs or application changes."
    },
    {
      "marker": "E",
      "source": "Frozen048-b59380287b1e12ad89af2e76d86cf51a14bccc21a/implementationf6eca5b1f91dfa57640fe04aa1e31a27c93ec2cd/PR100",
      "section_or_evidence": "RootcompletecorrectivereviewPASSsemantic/source/visual; independent3probesPASS1.84s and assertionprivacycanaryabsent. CI39062814291attempt1and2each1114PASS1FAIL in unchangedmock cached-proof test, mtime36microseconds and350microseconds behindwallclock. No sourcefeaturefailed."
    },
    {
      "marker": "I",
      "source": "tests/test_qualification_image_ownership.py::simulated_build and tests/test_branding.py::_OwnedDocker.build_image lines679\u2013703",
      "section_or_evidence": "Fakebuild zero-latency Path.write_text usesFSmtime; actualhelpercomparesmtime>=time.time sampledjustbefore. Two uncoordinated clocks createfalse stale-output failure; guard is appropriate forrealconstruction and mustnotchange. Controlfakeclock/timestamps to make fakeinputs honor freshness contract."
    },
    {
      "marker": "C",
      "source": "CRITICAL and existingdevelopmentauthority",
      "section_or_evidence": "Routine narrow testfixture defect blocking selectedCI, D0; no new product/risk decision or control waiver. NONE."
    }
  ],
  "decision_class": "D0",
  "target_gate": "Authorization foundation for continued development only; complete selected authorization milestone requires later enforcement/read-only interfaces/qualification/fresh independent ICA; no deployment",
  "expected_report_path": "oap/reports/048-c-deterministic-verification-clock.md",
  "tests": [
    "Only fast simulated-image-ownership cases, including deterministic clock-skew/zero-latency regression that fails oldfixture and passes fixedfixture; explicit stale/symlink/ID/nonce/cache/foreign-tag failure protections retainassertions",
    "No localrealDockerwarm-cache/rehearsal/fullpytest; unchangedrealwarm-cache and fullproduct tests runnormally inCI",
    "Ruff/gitdiffcheck,160OAPstdlibtests (env-uOAP_ROLE), normalfullCI at actualfinalimplementation and frozennewreporthead; no blind retries or weakening; reportall earlierfailedattempts honestly"
  ]
}
-->

#048-c — deterministic fake construction timestamp for required CI

One small VERIFICATION-ONLY purpose on SAMEobjective48/issue99/branch codex/99-oap-048-a-authorization-foundation/PR100(AMEND). Originalmainbase1baffe27a66609944f4d7b8e5c12dc69dfaa00b9; startfrom literalfrozenb report59380287b1e12ad89af2e76d86cf51a14bccc21a, implementationf6eca5b1f91dfa57640fe04aa1e31a27c93ec2cd. Root full b review is complete: all actualfield/help/privilege/upgrade/secret-handling corrections satisfy publishedcriteria; independentoriginal3counterexamples nowPASS1.84s; controlled negativeassertionprivacyprobe emitsNORAWverifier; corrected1440/390PNGsbothvisuallyreviewed. Do not revisit/rewrite/extend application code. bReportPARTIAL is a truthful snapshot of the CI failure and staysimmutable.

## Demonstrated blocking boundary (not an authorization defect)
CI39062814291 failed-job-only retry at EXACTsamef6eca5b head alsofailed: attempt1and2 each1114passed/1failed in test_cached_created_requires_actual_construction_proof. SourceHelper tests/test_branding.py:702 correctlyrequires metadata.st_mtime>=started. Fake simulated_build in tests/test_qualification_image_ownership.py writes an IIDfile immediately with Path.write_text and inherits the filesystem's timestamp, while the helper reads Python wallclock just before. Actualfailures:1792266034.944909<1792266034.9449453 (36microseconds), then1792266708.6291215<1792266708.6294715 (350microseconds). A newfakeoutput is misclassifiedstale because these clocks/resolutions are uncoordinated. Real Dockerconstruction normallytakeslonger and its guard remains unchanged; no realimagequalification defect was found. Stop retrying untilgreen. This narrowlyaddedfixture repair is necessary for the mandated verification, not permission for broadtest/helper cleanup.

## Compact read set
C04 standard compact reads, thisorder, only tests/test_qualification_image_ownership.py simulated_build and its mockedpositive/negative cases; readonly tests/test_branding.py _OwnedDocker.build_image/cleanup as context; relevantCI failure receipt048-b-ci-retry.json in ~/codex-supervision/slaif-asset-reservation/workorders/group-authorization-runtime-20261017/ ifneeded (no rawlogs). No fullARCH/PLAN/oldreports/history. CurrentapplicationCIsourceevidence is alreadyindexed in b report; preserve it. Fresh coding context; no imagesneeded.

## Acceptance
1. Change ONLY the fake construction fixture in tests/test_qualification_image_ownership.py and a small deterministic regression in that SAME file, plus neworder/pointer/report. Make a successfulsimulatedbuild produce a deliberatelyfresh fakeIIDfile timestamp using a controlled clock/timestamp consistent with the helper's sampledstart, instead of relying on zero-latency realFSmtime matching realwallclock. An acceptable pattern is a scoped fakeclock in the importedbranding module for simulated_build and explicitfresh outputmetadata from that logicalclock; preserve actual time for the separate realDocker warm-cache test. Another equallysmall deterministicfixture-only solution is permitted if it preserves all protections. Do not alter host/systemclock, use sleeps/tolerances/probabilityloops, relaxactualassertions or modifyactual_OwnedDocker helper/ownership code. Do not catch/skip/assertaway thefailure.
2. Keep and explicitlyprove the stale-outputfault stillREFUSED (stale timestamp deliberatelyolderthancontrolledstart); preserve symlink/malformed/ID/nonce/owner/created/named-image/foreign-tag-race/no-unproven-cleanup assertions. Prove oldfixture cannot satisfy the positivefakeconstruction contract under an intentionallyskewed/coarse logicalclock, then fixedfixture can. Use deterministicfakeinputs, no flakyexpectationthatprobabilitywill reproduce. The unchangedrealwarm-cache test remains in normalfullCI with all assertionsintact; no realDockerlocal qualification is needed here. No testsdisabled/marks/skips/removal or newframework.
3. Actualapplication/runtime/authorization/userfield/migration/Group/permission/engine/proxy/dependency/inventory/docs/code are byte-identical to b. Only allowedtestfixture/regression change; readonlybranding helper strictlybyte-identical. No userdata, credentials, private host, foreigncontainers or realdata access. Earliera/b orders/reports byte-identical. Full b criteria remain satisfied and ARE NOT scope to reimplement. Do not edit accounts orfixoptionalfeatures.
4. Locallyrun ONLY mockedcases in thisfile (deselect existingreal_warm_cache test) and the160purestdlibOAPtests withOAP_ROLEunset; Ruff/gitdiffcheck. ExistingownedPython3.13environment/sourcecopy canbeused; sync theonechangedtestfile. NO localfullpytest, no operational/rehearsal/HTTPS/Gunicorn/restore/wholevisualtests, no apt/Caddy/pgdump or syntheticGit. NormalFULLCI at finalimplementationhead mustpass; requirednewreport-headchecks remain. Additionalresourcerehearsal/matrix is unnecessary. If a genuinelydifferentfailureappears, diagnose actualfirstboundary and report; no unrelated edits. Aim for concreteedit/diagnostic within15minutesaftercompactreadset.
5. Update SAMEPR100 description with a concise verification note that fakeIIDtimestamps aredeterministic and actualownershipvalidation/runtime/authsemanticsunchanged; Closes #99 retained. Create no newPR/issue and nevermerge/automerge. Run fullnormalCI at actualimplementation; thenpublish matchingreport-only commit withliteralimplementationSHA andSELF, exactfirstparent/remoteidentity checks, separate reportheadCI notyetobserved. Report earlier1114pass1fail attempts as historical evidence, no retroactivePASS; recordtestfixtureexpectednegative and focusedresult. No audit/deployment claim.

## Strongest objection and bounded choice
Changing a test to obtaingreen could mask realresourceownership defects. Mitigation: only fixmockinput timestamp determinism, keepactualhelperbyte-identical and stale/wrongidentity/symlink/race/cleanupnegativeprotections; unchangedrealDockerconstructionproof stillrunsin normalCI. No increasedownershipauthority or relaxedwindow. This is D0verificationrepair; user requested meaningfulCI, not blind retries. No new human productchoice/CRITICALentry.

## Publication/recovery
SamePR100/issue99/branch, newcorrectionc only, preserve allprevioussource/work/history; neverreset/clean/stash/forcepush or editoldreports. Includeexactneworder/pointer. AfterobservedimplementationCI captureliteralactualfullimplementation head; finalreport oap/reports/048-c-deterministic-verification-clock.md contains Implementation head SHA: <actualfullID> and Report publication commit: SELF. FinalcommitchangesONLYthatreport, firstparentimplementation; push/verifyrealremote/orderhash/parent/report-only/currentPRhead. Signal exactresponseFIFO OK bytes thenstop. ResponseFIFO ~/codex-supervision/slaif-asset-reservation/response.fifo. Waitoutside model withCLIhelpers. Strategy independentlychecks currenthead/requirements beforeconditionaldevelopmentmerge. No additionaldelegation or realdeployment.

## Deferred human adjudication
- Decision: NONE
