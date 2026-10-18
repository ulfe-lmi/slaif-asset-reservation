<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "050-a",
  "objective": 50,
  "round": "a",
  "slug": "granular-management-authority",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "b873f4cf1071bded044ba456625b0ced355407a8",
  "issue_number": 103,
  "branch": "codex/103-oap-050-a-management-authority",
  "pr_mode": "CREATE_OR_RESUME",
  "pr_number": null,
  "previous_round": null,
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "4566e797b709b71f13b2929572a2d1145d15a5a7ab8b41db50ebfdab962628cd",
    "PLAN.md": "2c856ae47ec985b953a8d26edbe2c07fd343833a41bc45aefcd304a7e67c1432",
    "ARCHITECTURE-for-agents.md": "41c32e0b0d6427a173dfe0b722446ae8ee311f3880929db65ed0245309b3a59e",
    "src/slaif_reservation/accounts/authorization.py": "d1b0879fbda947c7c9a75aa153a88a272a3481d33ea74a9d8ef25bbc39daaf6b",
    "src/slaif_reservation/management_ui/auth.py": "3127bd69ce496297656e476ac73037e3dea31688d3329c7aabc4777a52162df4",
    "src/slaif_reservation/management_ui/views.py": "818f6371bdb2151fc41bdf8106840ccfcb7d16b40b44916d5b7efb3838b40253",
    "src/slaif_reservation/reservations/services.py": "fcba30664d6f44cee7caf5fd2b9130fa820f6aeca257da56fcc1016592065368"
  },
  "requirements": [
    "SAR-001",
    "SAR-005",
    "SAR-006",
    "SAR-007",
    "SAR-008",
    "SAR-009",
    "SAR-010",
    "SAR-011",
    "SAR-012",
    "SAR-013",
    "SAR-014",
    "SAR-015",
    "SAR-016",
    "SAR-017",
    "SAR-018",
    "SAR-019",
    "SAR-020",
    "SAR-021",
    "SAR-033",
    "SAR-043",
    "SAR-044",
    "SAR-048",
    "SAR-049",
    "SAR-050",
    "SAR-053"
  ],
  "allowed_paths": [
    "src/slaif_reservation/accounts/authorization.py",
    "src/slaif_reservation/accounts/admin.py",
    "src/slaif_reservation/reservations/services.py",
    "src/slaif_reservation/management_ui/auth.py",
    "src/slaif_reservation/management_ui/views.py",
    "src/slaif_reservation/management_ui/selectors.py",
    "src/slaif_reservation/management_ui/forms.py",
    "src/slaif_reservation/web/templatetags/application_access.py",
    "src/slaif_reservation/web/templates/web/base.html",
    "src/slaif_reservation/web/templates/admin/change_form.html",
    "src/slaif_reservation/management_ui/templates/management_ui/dashboard.html",
    "src/slaif_reservation/management_ui/templates/management_ui/_nav.html",
    "src/slaif_reservation/management_ui/templates/management_ui/policy_list.html",
    "src/slaif_reservation/management_ui/templates/management_ui/policy_detail.html",
    "src/slaif_reservation/management_ui/templates/management_ui/policy_form.html",
    "src/slaif_reservation/management_ui/templates/management_ui/blackout_list.html",
    "src/slaif_reservation/management_ui/templates/management_ui/blackout_detail.html",
    "src/slaif_reservation/management_ui/templates/management_ui/blackout_form.html",
    "src/slaif_reservation/management_ui/templates/management_ui/reservation_list.html",
    "src/slaif_reservation/management_ui/templates/management_ui/reservation_detail.html",
    "src/slaif_reservation/management_ui/templates/management_ui/audit_list.html",
    "src/slaif_reservation/management_ui/templates/management_ui/audit_detail.html",
    "tests/test_management_authorization.py",
    "tests/browser/test_management_authorization_browser.py",
    "tests/test_management_ui.py",
    "tests/test_reservations_services.py",
    "tests/test_reservations_concurrency.py",
    "tests/test_default_policy.py",
    "tests/test_legacy_import.py",
    "tests/test_legacy_import_concurrency.py",
    "tests/test_import_lock_order.py",
    "tests/test_api_v1_reservations.py",
    "tests/test_form_guidance.py",
    "tests/test_reservation_shortcuts.py",
    "tests/test_pilot_path.py",
    "tests/test_restore_drill.py",
    "tests/test_product_entry.py",
    "tests/test_authorization_foundation.py",
    "tests/browser/test_form_guidance_browser.py",
    "tests/browser/test_product_entry_browser.py",
    "tests/browser/test_reservation_shortcuts_browser.py",
    "tests/browser/test_pilot_path_browser.py",
    "tests/browser/test_slaif_design.py",
    "README.md",
    "INSTALL.md",
    "docs/authorization.md",
    "docs/human-ui.md",
    "docs/security-model.md",
    "docs/runbooks/management-blackouts.md",
    "docs/ux/form-guidance-inventory.md",
    "docs/README.md",
    "oap/active",
    "oap/orders/050-a-granular-management-authority.md",
    "oap/reports/050-a-granular-management-authority.md"
  ],
  "forbidden_resources": [
    "Reservation or Asset/User models/migrations/exclusion/schema; booking eligibility/predicate; policy/time/counter/lead/cutoff/lifecycle math or audit/idempotency storage semantics. No new capability records, token scopes/issuance/API contracts/routes or directory API.",
    "Staff admission and per-model Administration rules; protected read-only/service-backed model boundaries. No hardcoded group names, automatic staff grants/enrolment, parallel memberships, deny rules, projects or policy DSL.",
    "Docker/Compose/proxy/runtime/settings/dependencies/bootstrap/legacy importer/restore implementation/clock/image ownership/OAP machinery or oldorders/reports/ARCHITECTURE/PLAN/projection/CRITICAL. No whole visual redesign or newCSSframework.",
    "Existing test files only necessary legitimate positive actor grants and now-false UI/help assertions; no assertion weakening/global autouse grants/UserManager defaults/model mocks. No real user/data/DB/host/secret/exposure/DNS/TLS/firewall/resources, foreign process/container cleanup, merge/automerge/delegation."
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Human group-authorization request sections2-3,5,9-11 and explicit Concentrated OAP/coding clarification",
      "section_or_evidence": "Selected independent app capabilities across existing groups/individual permissions; Staff onlyAdmin admission, readonlyAllreservations, partial-accessUI/server checks, activehuman constraints and deliberate staff upgrade."
    },
    {
      "marker": "A",
      "source": "ARCHITECTURE.md A-16 and SAR-048/SAR-050/SAR-053; SAR-010/012/013/019/020/021 preservation as amended",
      "section_or_evidence": "Exact ten chosen codenames exist. Managepolicy/blackout includesmodule read; readAll distinct frommodelView; mutateothers doesnot implyreadAll; exportdoesnotgrantotherUI; no hidden disclosure by overlap/redirect/count. Existing reservation service remainsauthority."
    },
    {
      "marker": "E",
      "source": "MergedPR102 atb873f4cf1071bded044ba456625b0ced355407a8, issue101closed; prior048/PR100 foundation",
      "section_or_evidence": "049-a/b reviewed, corrected and merged expectedhead after required5impl/reportchecksPASS1185tests. Bookassets/assetACL and externalidentifier implemented. CoremanagementstillStaff. MainpushCI maystillrun and mustnotbe assumedPASS. Source tree base equals acceptedPRreport tree."
    },
    {
      "marker": "I",
      "source": "Live source inspection management_ui/urls.py(17routes), auth.py, views.py, forms/selectors/templates and reservations/services.py; test-callsite AST inventory",
      "section_or_evidence": "All17managementviews useblanketmanagement_required; dashboard leaksallcounts; StaffORowner lifecycle helper; policy/blackout sharedStaffactor; fullowner overlap rows and mutation redirects; unconditionally rendered actions/export. Existing reservation filters/Paginator50 present but reservation template hasno pagination links."
    },
    {
      "marker": "C",
      "source": "Accepted047contract/PLANP08 purpose050 and livebase reconciliation",
      "section_or_evidence": "One purpose: capability-based management authority plus existing separate cross-user browser. ExistingownerAPI remainsunchanged; bearerread_all issuance/representation is051. No migration/settings/runtime/framework scope. OldpositiveStafffixtures needexplicitreal grants, negativecasespreserved."
    }
  ],
  "decision_class": "D0",
  "target_gate": "M-GROUP-AUTHORIZATION management/browser slice only; bearer read_all/issuance and fresh independent closure follow; no release/deployment",
  "expected_report_path": "oap/reports/050-a-granular-management-authority.md",
  "tests": [
    "Complete17route/action permission inventory and realPermission-record endpoint matrix: nonstaffselectedcapabilities, staff/modelViewwithnogrant denied, combinedgroups+direct, allpartialread/manage/export/mutationonly cases, inactive/service/superusers.",
    "Shared audited service guards for policy/blackout/cross-usercancel/release; removal afterGET and current locked-principal recheck; retainedownercancel/release afterbook/group loss; existingconflict/cutoff/blackout/auditrollback/PG concurrency preserved.",
    "Allreservations filters(asset/status/lifecycle/awarefrom/to/search) and actualpagination50 with preservedquery, original/effectiveend/releasedhistory, ownerroute/API isolation includingstaff/superuser tokenread/mutate owneronly.",
    "No unauthorized modulecounts/buttons/links/recordDOM/redirect leakage; blackoutmanage/view withoutreadAll onlysafeoverlapcount+confirmation; exportonlyusablefilteredform no auditbrowser access, existing500row/7day/safeCSV bounds.",
    "Focused realChromium1440/390 partialroles+validCSRF forgedPOST/default/customtheme/accessiblenav/help/noDjango/nooverflow; max2retainedselectedscreenshots actuallyviewed.",
    "Focusednew+affectedold tests, realPG concurrency asaffected; normal lint/types/check/migrationsdryrun/OpenAPI/docslinks/diffcheck;160OAPwithroleunset; fullnormalCI oncefinalimplementation+exactreporthead. No localfull/unrelatedrehearsal/HTTPS/Gunicorn/restorewholequalification."
  ]
}
-->

# 050-a — granular management authority and a separate All reservations browser

## Goal / scope

Replace blanketStaff management authority with the nine existing explicit application permissions and expose the existing management reservation browser as the separate All reservations view. This is ONE purpose across server services/routes and their UI controls, SAME selectedA16 target. Baseb873f4cf1071bded044ba456625b0ced355407a8; issue103. 049/PR102 is acceptedmerged/issue101closed; never replay it. Reconcile livefacts first, preserve oldbranches/untracked/foreignwork and create/resume the exact new branch. MainpushCI maystillrun, not assumedgreen; acceptedPRtreebyteidentity and priorrequiredchecks known.

## Compact reads

Normal CODING router/law/projection/communication + SECURITY-CORE/TESTING-CORE, then this order and only relevant management/service/template/test excerpts. All needed product decisions and route mapping are below. Do NOT load fullstrategicARCH/PLAN/history/oldreports. Existing ten codenames are in accounts/authorization.py, modelMeta and docs/authorization. source_hashes are SHA256 of pre-round FILE BYTES (compute hash of git show BASE:path), NOT Git object IDs; strategy verified them at publication. No rewriting unchanged targetarchitecture orlaw.

## Numbered acceptance / negative paths

1. **One additive capability system and exact route inventory.** Use existing accounts.has_reservation_permission with current active authenticated NON-service human eligibility and real groups/individual grants; no group-name constants, denies or second memberships. Normal superuser has_perm semantics retained, Administration stillStaff+per-model and protectedrecords remainread-only. management_ui.is_management_user now means any of the nine MANAGEMENT_PERMISSIONS, NOTStaff; book_assets alone gives no management access. Shared small permission/access helper and optional allowed application_access template tag may derive booleans; no permission DSL/contextprocessor/settings changes. Inventory ALL17currentroutes and operation guards in docs/authorization with the matrix below. For read capabilities checked before fetching protected records, direct GET/POST cannot be authorized by a hidden button. Anonymousloginredirect; authenticatedwithoutcap403; inactive/service and their superuser variants denied. Staff or modelViewpermissions alone do not count.

| Existing /manage/ route | Required application permission(s), reservations namespace |
|---|---|
| / | Any of the nine MANAGEMENT_PERMISSIONS, active human |
| policies/ and policies/<uuid>/ | view_booking_policies OR manage_booking_policies |
| policies/new/, policies/<uuid>/edit/ (GET+POST), policies/<uuid>/deactivate/ (POST) | manage_booking_policies |
| blackouts/ and blackouts/<uuid>/ | view_maintenance_blackouts OR manage_maintenance_blackouts |
| blackouts/new/ (GET+POST), blackouts/<uuid>/deactivate/ (POST) | manage_maintenance_blackouts |
| reservations/ and reservations/<uuid>/ | view_all_reservations ONLY (model view_reservation is not sufficient) |
| reservations/<uuid>/cancel/ (POST) | cancel_others_reservations; no implicit requirement/grant of readAll/release |
| reservations/<uuid>/release/ (POST) | release_others_reservations; no implicit requirement/grant of readAll/cancel |
| audit/ and audit/<uuid>/ | view_audit_history ONLY |
| audit/export.csv | export_audit_history ONLY; retain existing filtered/bounded behavior |

2. **Shared mutation authority, not adapter-only checks.** Replace _lock_staff_actor with a small current active-human capability guard for the relevant calls: create/update/deactivate_policy require manage_booking_policies; create/deactivate_blackout require manage_maintenance_blackouts. Read from the fresh row-locked actor, preserving transaction/lock order/full_clean/protectedwrite/auditcoupling and existingdenialcodes where practical. cancel_reservation permits active human OWNER or cancel_others_reservations; release analogously OWNER or release_others_reservations. Remove implicitStaff ORowner but keep owner lifecycle completely independent of Bookassets/assetgroups, current cutoff/status/time/effectiveinterval rules, activeaccount eligibility and audit semantics. Service-account ownership/superuser never bypasses human eligibility. Do not change generic reservation lock order, bookinggate, counter/exclusion/time/policymath orapi/idempotency internals. No source-based ADMIN or internal-source backdoor. Bare readAll is NEVER a mutation grant; managepolicy and manageblackout do not imply one another.
3. **Useful partial-access UI with no incidental disclosure.** Base nav separates Management capability links from Staff-only Administration, and offers obvious All reservations to authorized readers separately from My reservations. Reuse existingSLAIF layout/mobilemenu, no redesign. Dashboard/_nav only show authorized modules/actions and counts; do not fetch/pass unauthorized counts. A mutation-only user without readAll may submit an authorized existing action by known UUID, but must not acquire list/detail viaGET or be redirected to a private detail aftersuccess/failure: redirect safely to permittedmanagementlanding, with genericmessages/no owner/free-text/recorddata. Explain its partial access sensibly; no need to build a UUID-mutation UI. Policy/blackout view-only has no editor/deactivate buttons; readAll-only has no otherscancel/release forms/warnings. A user with only export_audit_history must have a usable way to set EXISTING AuditFilterForm filters and download CSV (small form on managementdashboard is sufficient), without granting audit browser/detail/history or unbounded data/counts. Auditreader-only sees no export and directexport403. Modulemanage includes its own read interface as explicitlyselected; no other inferred rights.
4. **All reservations browser, existing route reuse.** /manage/reservations/ anddetail become labelled All reservations/Reservation details (keep URLs/names, separatefromordinaryownerpages). Require view_all_reservations, including forStaff. Reuse existing validated asset/status/lifecycle/search/awarefrom-to filters and Paginator50; add visible previous/next/page navigation that PRESERVES all filters (template currently hasno links). Prove >50matchingrecords pagination, invalidfilter empty/error behavior and no arbitrary unbounded output. Show owner(existingbrowserdisplayidentity), asset, originalstart/end, effectiveend, currentstatus and derive_lifecycle with existing half-open release/cancelhistory meaning. Preserve the current authorized management browser representation/relatedpurpose text rather than inventing a directory or adding unrelatedaccount/privateasset fields. No email/profile/physical-locator/secrets expansion. API representation is a SEPARATE minimal contract in051, not this browser change. Controls only corresponding managementcap; owners still manage their own acceptedbookings through unchanged ownerworkflow. Explicitread-only viewer cannot change others even through valid forgedPOST; owner/member/API selectors remainowner-only even when principal hasallmanagementcaps.
5. **Blackout preview privacy.** Existingblackoutcreate/detail expose affected ownername/UUID/list. A viewer/manager with blackouts permission but WITHOUTreadAll must receive only safe overlapcount/confirmation information, never affected rowobjects/UUIDs/names/emails/purpose/free-text or private links in HTML/hiddenfields/redirects. Keep existing need to confirm nonzero overlap, released-prefix blocking, creation/deactivationaudit and no automaticreservationrewrite. WithreadAll, existingfullaffectedlist/links mayrender. No bypass by manually confirming false or forgedrows. Testboth create-unconfirmed, confirmedcreate anddetailread paths withprivacycanaries. Auditreader/export authority remains separate, with existing500max/default7day/safeCSVcolumns/filters and none of token/credential/header/request/privatepayload/physicallocator/purpose/cancellationreason in export.
6. **Deliberate upgrade and current help/docs.** No new migrations/permissions/defaultgrants. Existinggrant_management_access (048) already provides dryrun-first/idempotent explicitselection of activehumanStaff, noautoenrolment. Document how operators intentionally preserve chosen currentStaff management authority around upgrade before returning servicetousers, and how nonstaff get selectedindividual/group grants. Update currentAdminhelp for Staff=Administrationadmissiononly, group/individualapplicationgrants nowactive, superuser/human boundaries. Preserve allAdminmodelpermission/protectedmutation/password/UID logic. Existing adminprotected-record guidance may clarify applicationpermissions needed and not link unavailablemodule. Update only now-falseREADME/INSTALL/human/security/authorization/blackout-runbook/forminventory/docindex text, with concrete17route matrix and exampleoperatorgroups; no ledger/chronology/newADR. BearerreadAll/scopeissuance remainsplanned, ownerAPI unchanged. Retain currentBookassets/ACL/newuser instructions, existingComposeprojectnames/secret/proxy/database/deploymentboundaries. Accountsarenotauto-added toprivilegedgroups.
7. **Meaningful positive+negative evidence.** New tests/test_management_authorization.py with realPermission rows and ownedPG/HTTP/service calls: nonstaffeachcap, no relevantcap, staff+unrelatedAdminViewnomgmt, superuser/noStaffappsemantics, inactive/service(includingsuperuser), combinedmultiplegroups+individualunion and removals while same sessionvalid. MapALL17routes/GET+POSTactions; validpayloads/CSRF where appropriate, no hidden-action bypass, view-only readonlymutationdenials, wrongmutationcapdenials (cancelvsrelease, policyvsblackout), mutator-onlysuccess-withoutreadAll and safe redirects/no unauthorizedDOM. Explicit tests for sharedlockedservice guards afterrevocation, auditrollback/conflict/cutoff/blackout/exclusion invariants and retainedowner lifecycle afterbook/eligibilityloss. Existingownerbearerread/mutations remainowner-only even forsuperuser/Staff/allcaps; no newtoken/routing work. Reuse affected concurrency/importlock/restore/policytests to preserve locks/backup behavior.
8. **Existing positive fixtures, narrow adaptations.** Inventory real management mutation calls beforeediting. The allowed oldtest list includes all discovered service-callers plushelp/navfixtures to avoid049's omittedlegacyfixture problem. Give only legitimate oldmanagementactors explicit real needed apppermissions (dedicatedfullmanagerfixtures may intentionally grant allnine; Staff flag by itself is not a test grant). Preserve no-grantordinary/Staff/service/inactive negativecases and modelViewdistinction. Existing assertions that hardcode oldStaff/help/navtext may be updated to actualcurrent semantics; do not weaken behavior assertions or auto-grantglobally/inconftest/UserManager/signals. Keep 049rootfixes, sourceclock/resourceownership guards and historicalno-grantimportexception intact. Do not modify files merely because allowed.
9. **Focused Chromium evidence.** tests/browser/test_management_authorization_browser.py: readAll-onlynonstaff navigation/list/filter/page/detail and NOcancel/release/editcontrols; validCSRF forgedothersPOST403/nochange; nonstaffsinglemodulemanager actionablepages butothermodules/Admin403; blackoutmanagerwithoutreadAll safeoverlapconfirmation; auditreader-noexport and export-onlyfiltereddownload/nohistoryUI. Defaultandcustomtheme checks at1440/390, visiblelabels/help/mobilemenu/focusability/no pageoverflow/no user-visibleDjango. Use synthetic meaningfulrecords only; capture/retain/view atMOSTTWOselected images in this freshcontext (read-onlyAllreservations1440 and partialmanagement390 sufficient). No16+image accumulation, wholevisualredesign, pixel CI snapshots or unrelatedqualification.
10. **Verification and report.** Focused new+affected old server/browser suites and realPGconcurrency duringedits, then Ruff/format/mypy/check/makemigrationsdryrun(nochanges)/OpenAPI--validate--fail-on-warn/changedlinks+anchors/diffcheck;160OAPstdlib withOAP_ROLEunset. Full normalCI oncefinalimplementation and requiredexactreporthead, repeatonlyafterrelevantchange/failure. Record failures/skips/notrun honestly. No localfull/unmodifiedoperational/rehearsal/HTTPS/Gunicorn/restore-whole/wholevisual detour; normalCI coversunchanged qualification. Format actualcanonicaleditedfiles beforecopy-sync toowned tests (049-b neededaCIrepairwhenonlyownedcopyformatted). Waitoutside modelwithwatchhelpers. No codechangesafterreportpublication; collectnecessarycorrections intoonenextsuffix if needed.

## Non-goals / strongest objection

A broad decorator could accidentally giveeverymanager reservationread/export/cancel powers, leakrecords through overlapcounts/redirects, or retain hiddenStaff bypass in services. Rejectthat implementation: keep capabilities independent, protectreadqueries beforefetching, row-locked mutations recheck, partialUIprivacymatrix and realnegativecases proveit. ExistingStafflosingimplicitmanagement is DELIBERATE humanselection, mitigatedbyexplicitupgradecommand/docs, not an excuse to auto-grant. No tokenread_all, externalenforcer, directory, projects, schema, scheduler/PAM/SSH or unrelatedUI/architecture/governance work. D0/DHA NONE.

## Owned resources / execution

Reuse qualifiedowned ~/codex-work/slaif-auth-048-922064 (private0700 sourcecopy/locked3.13,Chromium/Ubuntu24override) and PostgreSQL17 exactCID7680db038ecebff114a19a929c6b2e3800d7274b23254a41707c2873d7c4067d/name slaif-auth-048-922064/loopback22708 afterverifyingreceipt. Synthetic0600credentialfiles neverprint. Sync ONLYGitlistedauthorizedsource/testfiles intoownedcopy, runDBsuites sequentially/no foreigncleanup. SourcecopyhasnoGitbydesign, do not manufactureGit orrunoperational/rehearsalpaths there. No hostpackages/newprovider fallback. Source-supervisioncodex.sh fromdevcwd beforeCodex/--yolo/righttmuxpane handledbywrapper. Fresh050context; no subagents. Concreteedit/smallestdiagnosticwithin15min aftercompactreadset, no speculativefuturedesign/repeatedunchangedinstructions.

## Publication / reporting / recovery

Create/resume actualPR on exactbranch andissue103; retrieveactualnumber, preserveCloses #103. Commit/push implementationincludingexactorder/active, observecurrentimplementationCI honestly, recordliteralfullimplementationHEAD. Immutable matchingreport-only commit:firstparent=implementation, Report publication commit: SELF; reportacceptance1-10, actualpathscope/tests/negativeevidence/limits/screens andDHA. Describe FINALwholeimplementation toreviewer, not abandonedapproaches orcorrectionchronology. ReportheadCI NOTYETOBSERVED atauthoring; push/verifyactualremote/PR/head/order/reportonly/parent, thenexactresponseFIFO OK andEXIT. PARTIALifblocked, nevermanufacturegreen/outscopefix. Nevermerge/automerge/activateanotherorder. Lostnotification afterpublishedreport meansreview, notrerun. Sameobjective/branch/PRonrecovery. IndependentmilestoneICA andrealdeployment remainseparate.

## Deferred human adjudication
- Decision: NONE
