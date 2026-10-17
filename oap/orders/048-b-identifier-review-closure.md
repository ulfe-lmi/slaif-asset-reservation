<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "048-b",
  "objective": 48,
  "round": "b",
  "slug": "identifier-review-closure",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "1baffe27a66609944f4d7b8e5c12dc69dfaa00b9",
  "issue_number": 99,
  "branch": "codex/99-oap-048-a-authorization-foundation",
  "pr_mode": "AMEND",
  "pr_number": 100,
  "previous_round": "048-a",
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
    "oap/reports/048-b-identifier-review-closure.md"
  ],
  "forbidden_resources": [
    "Reservation scheduling/service/policy/exclusion/lifecycle/audit/idempotency/authentication/proxy/network/deployment behavior changes",
    "Existing merged migration bytes; inventory/bootstrap data; dependencies/lockfile; protected Administration boundary changes",
    "OAP helper/constitution/workflow/framework changes; full architecture/PLAN or historical reports/orders/coverage/bootstrap rewriting; CRITICAL mutation",
    "Real credentials/data/host/DNS/TLS/firewall/private exports/lab/execution; foreign resource cleanup; auth-home copying",
    "Other objective/PRs, merging or auto-merge, further delegation"
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Human2026-10-17 authorization request\u00a77/\u00a710/\u00a711; explicit OAP/CODING selection and execution-tightening preference",
      "section_or_evidence": "Opaque string, multiple unassigned users, admin-only edit, upgrade preservation and meaningful negatives; one collected corrective round, no optional expansion."
    },
    {
      "marker": "A",
      "source": "ARCHITECTURE A16/SAR048/052/053; immutable048-a acceptance2/3/4/5/6/7",
      "section_or_evidence": "Exact populated identifier preservation, unsetNULL, no blank-unique collisions, complete denial/rollback/upgrade evidence and honest operator docs."
    },
    {
      "marker": "E",
      "source": "STRATEGIC complete frozen048-a review at fdb004125e262cee8c6efd6a01e8f8b05d395454, implementation6b548eb465eb9fc679546c6c7c57c264a2f13432; PR100",
      "section_or_evidence": "Report/helper verifiedliteralparent/report-only/orderhash/realremote; all17pathsordered. Root reviewed full code/migrations/tests/docs and1440/390PNGs. Implementationall5CI PASS; reportheadCIpending at review, no acceptance invented."
    },
    {
      "marker": "I",
      "source": "Independent ownedPostgreSQL probes048-independent-probes.log; test_review_048.py",
      "section_or_evidence": "2FAIL/1PASS in1.91s at byte-identical frozen source: Adminstrips spaces; secondcreate_user external_identifier empty raisesValidationError; injectedpost-writecommandfailure rollsback. New permanent negative testsmissing; tupleassertcouldprintverifier; guide falselycallsissue99 PR99."
    },
    {
      "marker": "C",
      "source": "CRITICAL.md; fullyselectedhumanA16 and scope-reviewed rootfindings",
      "section_or_evidence": "Routine implementation/test/doc corrections D0; no new product/risk judgment, noCRITICAL or realDB operation. NONE."
    }
  ],
  "decision_class": "D0",
  "target_gate": "Authorization foundation for continued development only; complete selected authorization milestone requires later enforcement/read-only interfaces/qualification/fresh independent ICA; no deployment",
  "expected_report_path": "oap/reports/048-b-identifier-review-closure.md",
  "tests": [
    "focused account/foundation/upgrade/admin-guidance server tests and existing private3counterexamples becomePASS; add permanent empty/whitespace/negativePOST/missingselector/rollback/repeatedmigrate safety coverage",
    "focused realChromium at1440/390, actuallyview max2selectedprivacy-safe screenshots, preserveidentifierleadingzeroes and full-stringlength128",
    "Ruff/mypy/check/makemigrationsdryrun/docslinks;160stdlibOAPharness withroleenvunset; normalfullCI at finalimplementation and exactnewreporthead",
    "NO localfullpytest, NO operational/rehearsal/HTTPS/Gunicorn/restore detours, syntheticGit orhostpackageinstallation; allunchangedregressionsarecoveredbynormalCI"
  ]
}
-->

#048-b — single collected identifier review closure

Same objective48, issue99, SAMEbranch codex/99-oap-048-a-authorization-foundation, SAMEPR100 (AMEND); originalmainbase1baffe27a66609944f4d7b8e5c12dc69dfaa00b9. Startfromfrozen reportheadfdb004125e262cee8c6efd6a01e8f8b05d395454, implementation6b548eb465eb9fc679546c6c7c57c264a2f13432. New FRESH coding context for this corrective round.048-a order/report remain byte-identical. Source hashes bind the pre-b frozen source (projection contains the048-a temporal update); this is not a request to alter fullARCH/PLAN/law. All048-a acceptance and non-goals remain in force, subject only to the concrete corrections below. Sourcehelper/report identity verified PASS. Do not repeat alreadycompleted work or invent a new issue/PR.

## Compact ordered read set
Standard C04 readset, thisorder, relevant048-a acceptance/result sections (not wholehistory); only changed User model/admin field, newaccounts0005 migrationhelp, accounts authorizationhelper doc if needed, existing newtests/foundation/upgrade/browser and docs/authorization.md/inventory. No fullARCH/PLAN/roadmap load. Private local-testing.md remains useful but NO LOCAL FULL SUITE. Root diagnostic source/probes at ~/codex-supervision/slaif-asset-reservation/workorders/group-authorization-runtime-20261017/test_review_048.py and bounded048-independent-probes.log (synthetic data only); read only this small diagnostic, not raw transcripts/realenv. Existing ownedroot~/codex-work/slaif-auth-048-922064 has Python3.13/PG17/browser tools and artifacts; do not recreate valuable environments or inspect/touch foreign containers.

## Required corrections (complete collected review; no optional refinements)
1. Fix actual opaque-value mutation: the current generated Admin CharField strips surrounding whitespace. Rootget_form field.clean(' 00042-Ext ') returns'00042-Ext', violating048-a acceptance2's explicit no-normalization rule. Preserve every character of a populated identifier, including spaces/case/leadingzeroes, through authorized Admin create/update and model/manager paths; retain128character limit measured on the whole value. Set appropriate form field behavior without replacing allUserAdmin fields/weakeningvalidation. Exactly emptystring is UNASSIGNED, not a populated identifier: normalize it toNULL consistently on supported manager/model create/update paths. Root twoUser.objects.create_user(...external_identifier='') calls currently failuniqueness on the second instead of leavingbothunset. Pin this behavior permanently for empty/None/default through create_user and ordinary save/update paths; no blank-unique collisions. Do NOTstrip/casefold/parse populatedstrings or rewrite existing nonempty identifiers; no data backfill. Existing accounts/groups/UUID/email/password/token/domain data remains preserved. This is a value-handling correction, not a new identity or membership system.
2. Correct visible product meaning in Userfieldhelp, the SAME new/unmergedaccounts0005 migration's fieldhelp and inventory: "not aLinuxUID" is categorically wrong for the explicitly approved external UID usecase. Say it may represent an external account identifier (including aLinuxUID) but is opaque, not validated as aUID, not a credential or grant of machine access, and not a replacement for appidentity. Keep meaningful nearby associated help. For unmerged new migration headers do not invent generator provenance/version: use a plain authored-purpose comment or an actuallyverified generated header; do not rewrite any older merged migration. No additional schema migration/newcolumns are needed for normalization/help corrections.
3. Complete the already-required negative evidence, preserving all existing assertions: add direct forged POST denials for a nonstaff user and staff without accounts.change_user, with a VALID same-payload authorized positive control and unchanged storedidentifier; pin missing --user refusal with zero writes; add a post-real-write fault injection test proving grant_management_access rolls back earlier grants/retains oldgrants/groups/flags if a subsequent grant fails. Rootindependentrollbackprobe alreadyPASS; no new commandbehavior or concurrency/locking design requested. In the populated-upgrade test, create the subsequent unprivileged users THEN run normalmigrate again and assert they stillreceiveNOgrants/groups, while originaluserbaseline and legacyrows remain unchanged. Existing test currently re-runsmigrate only BEFORE newusers are created. Snapshot token/password preservation safely: the current tupleassert includes tok.verifier and would print it on a regression. Compare via safe boolean/digest and safe failuremessage, never raw secret/verifier values. Do not dilute SQLuniqueness, actualPGmigration, privilege-denial or idempotence tests. No new general test/permission framework.
4. Repair newoperatorguide's false PR99 reference (99is the issue; actualPR100). Keep normaldocs product/task-oriented: remove order/PR delivery chronology from the guide's first-screen narrative, use a concise Available now vs Planned/enforcement-not-yet-active status and preserve the exact permission matrix/currentStaffbehavior. Do not rewrite README/INSTALL or unrelateddocs. Make the explicit migration/setup procedure executable in the currentlysupported Dockerworkflow by referencing INSTALL and using its existing retained SAR_COMPOSE_PROJECT convention/productionCompose path and python manage.py commands (manage.py itself is nonexecutable100644). Existing installations MUSTkeep their same projectname/volume identity; no deployment or command execution against realservices. Do not duplicate TLS/installsecurity procedure or pretend latergates/read-all routes/scopes areimplemented. No changes to actual Compose/runtime/config.
5. Preserve048-a immutable report; the new b report supersedes any unverified claims cleanly rather than rewriting it. In particular tests/test_form_guidance.py was NOTchanged in actuala diff despite beinglisted in a report; actualGitdiff is authoritative. The claimed real5-daypilot cause of localrehearsal failures is UNPROVEN: named testcases near600/716/747use fake_docker syntheticrows; the proved boundary was source-copy Gitmetadata. Do not turn that speculation into a productfinding or inspectforeign resources. Report extra localattempts honestly as nonqualifying environment evidence; do not repeat them. No source/testhelper/framework fixes for those unrelated failures.
6. Run ONLY focused account/foundation/upgrade/form-guidance tests and newadminChromium flow at1440/390 against the existingowned isolatedenvironment, with OAP_ROLEunset. Sync finaleditedsourcecopy and verify testedbytes match thisbranch. The three small rootprobes should nowallPASS; add equivalent durable regressions instead of relyingonprivateprobes only. Actuallyview at most2privacy-safe selected screenshots in thisfreshcontext, preserve UIlabel/help/nooverflow/noDjango/passwordsecrecy. RunRuff/mypy/check/makemigrations--check--dryrun, changedlinks/gitdiffcheck and160test stdlibOApharness. NO localfullpytest or operational_hardening/rehearsal/HTTPS/Gunicorn/restore sweep, no Caddy/pg_dump install, no syntheticGit to support unrelatedtests. The normal FULLCI is the required fullsuite. Run it at finalimplementationhead; repeat only after actual relevantchange/failure; preserve required newreport-head checks. Wait outside model with existingwatchhelpers; do not poll repeatedly or reread unchanged history. Aim for concreteedit/diagnostic within15minutes of compact readset; no speculative future feature planning.

## Scope guards / strongest reason not to change
Only the concrete field/form/help/test/doc defects above; no management/booking enforcement or asset-group/read-all API/token work, no dependency/proxy/network/engine/constraints/policy changes. Permission definitions/helper semantics, one-timebaseline migration logic and commandwrite logic are preserved unless an in-scope failingtest demonstrates a real additional defect; do not add optional locking/multi-database/generalframework work. Strongest objection: normalization could change a populated externalmapping; mitigate by converting ONLY exactempty toNULL, preserving all populatedstrings and128limit and proving roundtrip/uniqueness/clear/reuse. No CRITICAL mutation, no realDB/data/exposure/D2 operations, noforeigncleanup, no authcopy, no selfmerge or delegation.

## Recovery/publication
Samebranch/PR100; do not reset/stash/clean/forcepush. Include newexactorder/pointerbytes, preserveoriginala bytes and sourcehistory. Commit/push implementation and updateexistingPR throughstructuredbody/file (not unsafe interpolation; ghpr edit may bebroken, structuredRESTworks). Use Closes #99 as before; no newPR. Capture actual full finalimplementationSHA afterobservedCI. Write immutable oap/reports/048-b-identifier-review-closure.md with literal Implementation head SHA: <actualfullID> and Report publication commit: SELF; finalcommit ONLYthatreport, firstparentimplementation. SeparateobservedimplementationCIfrom NOTYETOBSERVEDreportheadCI; no future claim. Push/verifyremoteactualPR/head/orderhash/report-only/parent, signal responseFIFOexactOK, thennomoremuta­tion. ResponseFIFO ~/codex-supervision/slaif-asset-reservation/response.fifo. Strategy independently reviews thisnewhead beforeanymerge.

## Deferred human adjudication
- Decision: NONE
