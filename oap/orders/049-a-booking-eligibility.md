<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "049-a",
  "objective": 49,
  "round": "a",
  "slug": "booking-eligibility",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "12947e9b368445eeb4a48416421626224b49f4dc",
  "issue_number": 101,
  "branch": "codex/101-oap-049-a-booking-eligibility",
  "pr_mode": "CREATE_OR_RESUME",
  "pr_number": null,
  "previous_round": null,
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "4566e797b709b71f13b2929572a2d1145d15a5a7ab8b41db50ebfdab962628cd",
    "PLAN.md": "2c856ae47ec985b953a8d26edbe2c07fd343833a41bc45aefcd304a7e67c1432",
    "ARCHITECTURE-for-agents.md": "41c32e0b0d6427a173dfe0b722446ae8ee311f3880929db65ed0245309b3a59e",
    "src/slaif_reservation/accounts/authorization.py": "d1b0879fbda947c7c9a75aa153a88a272a3481d33ea74a9d8ef25bbc39daaf6b"
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
    "SAR-014",
    "SAR-015",
    "SAR-017",
    "SAR-018",
    "SAR-019",
    "SAR-020",
    "SAR-028",
    "SAR-029",
    "SAR-030",
    "SAR-032",
    "SAR-043",
    "SAR-044",
    "SAR-048",
    "SAR-049",
    "SAR-053"
  ],
  "allowed_paths": [
    "src/slaif_reservation/assets/models.py",
    "src/slaif_reservation/assets/admin.py",
    "src/slaif_reservation/assets/authorization.py",
    "src/slaif_reservation/assets/migrations/0003_booking_access.py",
    "src/slaif_reservation/accounts/admin.py",
    "src/slaif_reservation/reservations/services.py",
    "src/slaif_reservation/reservations/exceptions.py",
    "src/slaif_reservation/api/reservation_views.py",
    "src/slaif_reservation/web/views.py",
    "src/slaif_reservation/web/selectors.py",
    "src/slaif_reservation/web/templates/web/asset_list.html",
    "src/slaif_reservation/web/templates/web/asset_detail.html",
    "src/slaif_reservation/legacy_import/planner.py",
    "src/slaif_reservation/legacy_import/importer.py",
    "tests/test_booking_authorization.py",
    "tests/test_booking_access_upgrade.py",
    "tests/browser/test_booking_authorization_browser.py",
    "tests/test_assets_admin.py",
    "tests/test_assets_models.py",
    "README.md",
    "INSTALL.md",
    "docs/authorization.md",
    "docs/human-ui.md",
    "docs/api-contract.md",
    "docs/ux/form-guidance-inventory.md",
    "oap/active",
    "oap/orders/049-a-booking-eligibility.md",
    "oap/reports/049-a-booking-eligibility.md",
    "tests/test_form_guidance.py",
    "tests/test_pilot_readiness_check.py",
    "tests/test_operational_hardening.py",
    "tests/test_abuse_controls.py",
    "tests/test_management_ui.py",
    "tests/test_pilot_path.py",
    "tests/test_bootstrap_assets.py",
    "tests/test_api_v1_reservations.py",
    "tests/test_import_lock_order.py",
    "tests/test_legacy_import_concurrency.py",
    "tests/test_restore_drill.py",
    "tests/test_default_policy.py",
    "tests/test_authorization_foundation.py",
    "tests/test_api_tokens.py",
    "tests/test_reservations_concurrency.py",
    "tests/test_web_human_mvp.py",
    "tests/test_reservations_services.py",
    "tests/test_reservation_shortcuts.py",
    "tests/browser/test_reservation_shortcuts_browser.py",
    "tests/browser/test_product_entry_browser.py",
    "tests/browser/test_form_guidance_browser.py",
    "tests/browser/test_pilot_path_browser.py",
    "tests/browser/test_slaif_design.py",
    "tests/browser/test_human_mvp_browser.py",
    "tests/browser/test_branding_browser.py"
  ],
  "forbidden_resources": [
    "Reservation model/time/exclusion/schema or existing merged migrations; policy math/counters/horizon/lead/cutoff/blackout semantics; audit/idempotency core storage/hash/replay implementation changes",
    "Management capability switch, All reservations views, read_all scope/issuance change/newAPI/userdirectory, UIDbehavior changes, project/membership hierarchy/denies/parentaccessinheritance or external execution",
    "Dependency/lockfile/Dockerfile/Compose/proxy/securitysettings/deploymentsemantics/bootstrapinventory/schema/parser changes; OAP helper/framework or historical law/reports/orders/CRITICAL mutation",
    "Globaltestautogrants/autousepermissionreceivers/UserManagerdefaultgrants or weakened existing assertions; actualownershiphelper/image-clockfixtures/OAPtests changes",
    "RealDB/data/exports/hosts/secrets/DNS/TLS/firewall/exposure; foreignresources/authcopy; selfmerge/automerge/delegation"
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Human2026-10-17authorizationrequest\u00a72/\u00a74/\u00a79/\u00a710/\u00a711 and explicitOAP/CODING selection",
      "section_or_evidence": "Bookcapability plus exactassetgroupeligibility; samebrowser/bearer authority, noStaffbypass, allassetvisibility, oldOwner lifecycle; no engines redesign."
    },
    {
      "marker": "A",
      "source": "ARCHITECTURE A16/SAR048/049/053; preserved SAR001/005\u2013020/028\u2013030",
      "section_or_evidence": "AdditiveexistingDjangogroups/individualperms; restrictedemptyfailclosed; no parenteligibilityinheritance; oldassetsunrestricted; policy/exclusion/audit/idempotency/ownerprivacy andhistoricalimportexception preserved."
    },
    {
      "marker": "E",
      "source": "048-c/PR100merged12947e9 after allthreefrozenroundreviews/exact5impl+reportCI PASS, mainpushCIpending; issue99closed",
      "section_or_evidence": "Helper has_reservation_permission(user,barecodename), BOOKING_BASELINE_PERMISSION=book_assets ready; UseroptionalUID complete; MetaTenpermissions existing; no booking enforcement or assetACL yet."
    },
    {
      "marker": "I",
      "source": "Currentcreate_reservation/_lock_principal; webassets/reserve; APIidempotency; bootstrapandlegacyfutureimport inspection",
      "section_or_evidence": "Insertcheckonlycreation, notgenericprincipal lock/lifecycle. APIpreflight beforecache plus insideauthoritativelock. Bootstrap existingmatchesreused unchanged; futurelegacyapplyseparatepathneedscommonguard, retaincompletedpast exception. Manyoldpositivefixturesneedexplicitbookgrant, notglobaltestprivilege defaults."
    },
    {
      "marker": "C",
      "source": "CRITICAL and human/A16 explicitselectedmeaning",
      "section_or_evidence": "No unresolvednew product/risk choice. RoutineD0 authorizationimplementation with ownedtests; no realinfra/data/identity action. NONE."
    }
  ],
  "decision_class": "D0",
  "target_gate": "M-GROUP-AUTHORIZATION bookingeligibilityslice only; management/read_all/qualification/independentclosure follow; no release/deployment",
  "expected_report_path": "oap/reports/049-a-booking-eligibility.md",
  "tests": [
    "new realPG service/browser/bearer/group-union/currentgrants/directPOST/emptyrestricted/parentnoninheritance/StaffandSuperuser objecteligibility cases",
    "ownerlist/detail/cancel/release afterglobalbook/allowedGroup loss; APIauthorizationbeforeidempotentreplay plus restoredgrant originalreplay, unchanged conflict/audit/counter/blackout/DST/CSRF/expiry rules",
    "populatedoldAssetsmigrateunrestricted preservingrecords; normalbootstrap reapplypreserves configuredACL; futurelegacyplan/applystaleauthrefusal, historicalcompletedexceptionpreserved",
    "focused affectedexistingpositivebookingfixture suites; no autouseglobalgrants; realPG concurrency; relevantChromium1440/390 default/custom assertions and max2selectedscreenshotsactuallyviewed",
    "Ruff/mypy/check/makemigrationsdryrun/OpenAPI--validate--fail-on-warn/docslinks;160OAPtests cleanroleenv; normalfullCI at finalimplementation and exactreporthead; no localfull/operational/HTTPS/restore/Gunicorn/wholevisualdetours"
  ]
}
-->

#049-a — one authoritative booking capability and exact-asset group eligibility

## Goal / current state
One implementation purpose: enforce new-reservation authorization under selectedA16, across member/browser/bearer and sharedcreation authority, with explicit per-asset group eligibility. Issue101, exact base12947e9b368445eeb4a48416421626224b49f4dc (merged048/PR100, issue99closed). All048latestimplementation/report fivechecksPASS; mergedmainpushCI maystillrun and is notassumedPASS. Old048/047 are complete, not replayed. Fresh coding context; branch inmetadata CREATE_OR_RESUME, actualPRnumber retrievedonlyaftercreation.

## Compact reads
C04 standard projection/law/protocol/security/testing and thisorder; then only accounts/authorization.py; Asset/model/admin and bootstrap apply/existing-recordmatch excerpts; reservations/services.py principal/assetlocks/create/owner-lifecycle authorization; exceptions; web asset list/detail/reserve + selectors/templates; APIReservationListCreateAPIView and _DOMAIN_STATUS/helpers; readonlyapi/idempotency.py execute/replay authorization boundaries; legacy_import planner/apply future-policy branch. Existing newpermission/UID behavior is final: do notreimplement048 or load itswholehistory. Read relevant positivebookingfixture definitions by rg/boundedexcerpts, not everytestfile/sourcebook. Read docs/authorization currentstatus and only relatedREADME/INSTALL/human/API/group-form sections. No fullARCH/PLAN/history or futureorders. Existing owned resource notes under ~/codex-supervision/slaif-asset-reservation/workorders/group-authorization-runtime-20261017/local-testing.md; heed no-local-full restriction over earlierdetour history.

## Numbered acceptance
1. Add Asset.booking_restricted (Boolean, defaultFalse) and Asset.allowed_booking_groups (optionalM2M to EXISTING auth.Group; no new membership table/system). One NEW forwardassets0003_booking_access migration only; all existing assets become unrestricted, allowedgroups empty, with existingasset identities/metadata/parent/state and all other product rows preserved. Never alter mergedmigrations or reservationDBmodel/exclusion constraints. Unrestricted ignores leftoverallowedgroup selections; otherwiseeligible activehumans with book_assets maybook. Restricted requiresmembership in ATLEASTONE allowedgroup; restricted+emptygroup list failsclosed, including afterlastallowedgroup deletion. Check onlythe booked asset, neverparent-to-child access inheritance. AllfiveAssetkinds follow identicaleligibility. No explicitdeny rules or group-name constants; grants combine across allgroups and individualperms, and globalbookgrant maycome fromonegroup whileassetmembership comesfromanother.
2. Implement a small shared assets/authorization.py eligibility check using existing has_reservation_permission(user,BOOKING_BASELINE_PERMISSION) and actualgroupmembership. Permissionhelper usesbarecodenames and active authenticated nonservice human semantics; trustedactive superusers keep globalhas_perm semantics BUTstillmustbelongtoone allowedgroup onrestrictedassets. Staff or unrelatedAdministration modelpermissions NEVERbypassglobalbookingcapability or asseteligibility. Sharethe predicate inservice/browser/API; no duplicated policy engine. Enforce it in create_reservation AFTERfreshprincipal+assetlocks in the existingatomic transaction, before any reservation/auditwrite. Keep all current policy/time/counter/blackout/overlap/exclusion/audit rules and exactnamedconstraint handling unchanged. Do NOTput the bookingcheck in generic _lock_principal, cancel/release, profile/token reads or other sharedprincipal entry: owners mustretainoldlist/inspect/cancel/releaseafterlosingglobalbookcap/membership, evenifasset/policydeactivated, underexistingactive-account/lifecycle/cutoff rules. No ORMcreation bypass, no implicitprivileged-system-staff.
3. Browser GET/POST reservation creation denies unauthorizedactivehumans on directrequests, notonlyhiddenbuttons. Assetsremainbrowsable underexistingactive/memberprivacyfilters regardlessofbookingeligibility; memberlist/detail clearly show ownbookingaccess and offerReserve onlywhenapp+asseteligibility and existingreservable/exclusiveflags permit. Explanations useful, no privategroups/names/other-user metadata. The existing Reservable filter remains an ASSETFLAG filter; its currenttext "Onlyassets youcanbook" becomeswrong: correctthe guidance ratherthan silentlyfilteringineligibleassets out. Grouping/nonreservable resources mustnotlookbookable. Do notalteravailability privacy/semantics, quick1/2/4h/custom/defaulttimes/DST/profilezone/minmax/CSRF rules. Avoid unnecessaryper-row querygrowth by using currentprefetch/query facilities; no new policy framework.
4. BearerPOST /api/v1/reservations additionally requiresowner's CURRENTbook_assets and exactasseteligibility, alongsidecurrentreservations:create scope. Do NOTbroaden existingowner-onlyGET/detail/cancel/release or addread_allscopes/routes. Authorizationrechecked on EVERYcreationrequest BEFOREreturningcachedidempotentcreationresponse, analogous to existingscope/owneractivitychecks, and AGAINinside theauthoritativerow-locked creationservice foractualnewwrites. A revokedbook/groupgrant yields403onacachedcreatePOST whileoriginalacceptedbooking/cachedrecordremainunchanged; restoregrant thenoriginalsamekeyreplaystillreturnsoriginalstatus/body/correlation. Do notmodifyapi/idempotency.py's hashing/storage/ownership/retention/action/replaylogic orturnunknown-asset404sintoanewunrecordedcontract: preserveexistingcallback404idempotencybehavior, e.g.preflighttheauthpredicateonlywhenassetexists (globalbookcheckstillapplies) andkeepexistingmissingassetcallback. Add stable booking_not_authorized problemcode403 with safehumanUI/machinedocs, no raw group/account/UID/SQLdetails. Existing mutationinput/outputfields and scope/authn/abuse/expiry/revocation/clientIP/proxy rules preserved; read-only availability/owner access do notrequirebookauthority. Requests needcurrenteligibility; no asset-boundedtoken scopes or tokenissuingchange yet (that is051).
5. Existing Administration configures theexactasset fields with accessiblelabels/help: unrestricted vsrestricted, emptyrestricted deniesall, anyallowedgroup suffices, no parentinheritance, stillneedglobalBookassets, no machine/login rights and no existing-reservation rewrite. Keepstaffadmission/per-modelasset permissions and protectedrecords. Reuse existinggeneric admin-form-guidance.js viaAssetAdminmedia IF needed forgenerateddual-select ARIAbinding; theJS alreadygenericallyhandlesselectors and mustnotbe rewritten. New-userAdminhelp/group/individualpermission guidance MUSTnowexplainrequiredBookassets assignmentafteraccountcreation (directorviaGroups), additivegrants andassetGroupchecks. Do notautoenrolnewusers, autoassignBookperms orchangeUserManager/defaults; keepUIDvaluehandlingfinal. ManagementstilluseslegacyStaffuntil050: keep thosehelpclaims CURRENT, do notannouncefuturegatesasactive.
6. Close the relatedexistingcreationadapterboundary withoutredesign: syntheticlegacy import's ordinary FUTUREcreation (and staleplanapply) reuses theSAMEcurrentbookingauthpredicate; futureconfirmedrecords cannotbe used tobypassgroup/capability eligibility. Preserve thedocumentedcompleted-past historicalimportexception and existingpolicy/time/statusclassifications, sourceidempotency, audittransaction/locks/parser. Aplanmadebeforeaccessremoval isadvisory:applyrecheckslockedfreshprincipal/asset and createsNOreservation/successaudit whennolongerauthorized. Useexisting safeclassification machinery; no privateexports/contact/realcutover or newformats. Bootstrap importexistingmatchingrecords alreadyreusesexistingAssetwithoutwrites: DO NOTmodifygenericbootstrapformat/parser/data; pin a focusedtestthat repeatedapplypreserves configuredbooking_restricted/groups. Newassetsdefaultunrestricted; upgradesmustnotimportDemo.
7. Meaningfulpositive/negative tests with realownedPG/authenticatedHTTP: no-relevant-grants(activeordinaryANDstaff/unrelatedAdminperms), nonstaffbookgrant, direct+multiple-group union, restrictedempty/lastgroupdeleted, sameassettypeacrossfivekinds, parentrestricted-childunrestricted andopposite, superuserrestrictednonmembershipdenied/membershipallowed. Browser/API/directservice parity; forgePOSTs despitehiddenactions; validtokenlosesgrant/membership/assetaccess anddenialapplieswithoutreplacement, scope-missingstilldenied; inactive/servicesuperusersdenied. Owners retainownread/cancel/releaseafterbook/grp loss usingappropriateownedtoken scopes; no implicitcross-owner access. Confirm existingconflict/exclusion/concurrency, policycounter, blackout/auditrollback, idempotency andDST/currentform behavior stillauthoritative with eligibleprincipals. Provepopulatedoldassetsmigrateunrestricted withrecordpreservation. Do notgrantpermissionsgloballyinautousefixtures/signals, monkeypatchUserManager orweakenassertions tokeepoldsuitesgreen. NecessaryexistingPOSITIVEbookingfixturesmustexplicitlygrantbook_assets throughrealPermission records; preserveexistingnegativeprivilegecases and add newviewer/noGrantcases. Existingtestfilesallowed onlyforthoseprovenfixture adaptations/assertions directlyaffectedbynewbookingguard; no actualownership/helper/harness/clock/productionenvironment testchanges.
8. FocusedChromium at1440and390: eligible vsineligibleassetsbothvisible, disabled/absentreserveactionandclearreason, eligiblebookworks, directPOSTdenied, newAdminselectorhelpbound/keyboardreachable/nooverflow/noDjango. Defaultandcustomtheme functionalassertions; actuallyview MAXTWOselected privacy-safe screenshots inthisfreshcontext (no accumulated16-image bundle). ReuseexistingSLAIFstyling/helpers, no redesign/CSSframework. Run new+relevantold server/API/service/concurrency/legacyapply/boundedbrowser suites locally, NOT fulllocalpytest or unchangedoperational/HTTPS/restore/Gunicorn/wholevisualqualification. AlltestprocessesOAP_ROLEunset. NormalFULLCI isrequired atfinalimplementation and exactfrozenreporthead. Preserve currentfixtureclockfix and allactualresourceguards. Fix onlyactualin-scopefailures, runfocusedchecksafteredits, fullCIrepeatonlyafterrelevantchange/failure; waitoutside model withwatchhelpers.
9. UpdateONLYproved-currentproductdocs: docs/authorization bookinggate/assetconfig/newuser/upgradestatus andexamplegroups (operatornames,notconstants); docs/human-ui eligibility; docs/api-contract currentcreate403/auth-before-replay invariant; newAdminfieldsinventory. Remove now-falseREADME/INSTALL "no group/resourceauthorization, everyactivehuman maybook" wording, replaceconciseactualglobalbook+assetgroupbehavior andproject/org stilldeferred; linkguide withoutwork-orderledger. ExistingmanagementStaffandread_allplannedremaintruthfuluntiltheirpurposes, no advertisefuturefunctionality. INSTALLnewordinaryaccountsetuprequiresdeliberatebookgrant asappropriate; allComposecommandskeepretainedprojectname. No command/runtimetopology/security/proxy/image/dependency/bootstrapchanges, nofullinstallrewrite. OpenAPIgeneratedvalidation --fail-on-warn, lint/format/types/check/makemigrationsdryrun/docslinks/diffcheck and160stdlibOApharness. Do notupdatefullARCH/PLAN/hashlaw merelyforstatus; targetclausesremainnormative, exactreport/evidenceprovidescurrentproof.

## Owned resources / execution
Explicitly REUSE the knownOWNED isolatedenvironment ~/codex-work/slaif-auth-048-922064 (0700), its ownedsourcecopy/lockedPython3.13.14venv, Chromium/Ubuntu24override and scopedextractedlibs, and PG17container exactCID7680db038ecebff114a19a929c6b2e3800d7274b23254a41707c2873d7c4067d named slaif-auth-048-922064/loopbackport22708 withprivate0600credentialfiles andcreationreceipt. This is same-goalownedresource reuse, not adoptionofa foreignproject. VerifyexactCID/name/receiptbeforeuse/cleanup, neverprintcredentials. Sync ONLYGitlistednonignoredbranchfilesintoownedcopybeforetests; keeptoolchain dirs, ignoreold.git-junk (no syntheticGit needed). Sequentialpytestonly/no sharedtestDBconcurrentprocesses; no valuable .env/deploypaths. Do notcontact/inspectforeigncontainersorrealservices. Source-copylacksGitmetadata bydesign: operationalfixturesbelonginnormalCI, no detours. No hostpackageinstallation/newmodel/provider fallback. Aimforconcreteedit/diagnosticwithin15minaftercompactreadset; no repeatedunchangedinstructionreads orhypotheticalfutureproblems. Strategyownsotherobjectives; no subagents/delegation. Source-beforeCodex alreadyhandledbywrapper.

## Non-goals / strongest objection
Only NEWbookingauthorization. No managementswitch/read-allbrowserorAPI/scopes, userdirectory, account-IDchanges, org/projects/denies/groupownership, machine/PAM/SSH/jobs/gateway/inference allocation, loginrights, monitoring, rate/proxy/deploymentchanges, dependencies, schema/constraint/lifecycle/policy redesign. Do notalterthegenericprincipal lockorownerlifecycle torequirebookingaccess. Strongestobjection: a UI-onlyorcached/bypassablecheckcouldleakbookauthorityorstrandowners; mitigatewithcommonpredicate,row-lockedauthoritativecreate, pre-replayauthorization, futureimportrevalidation, eligibilityvisibilityand retainedownerlifecycle/exclusion/auditproof. Allchosenmeaningalreadyhuman/A16; routineD0, no newCRITICALorrealD2 action.

## Publication / recovery
Preserve clean048branch andunusedmaintenancebranch; switchtonewexactbranchfromorigin/mainbaseabove, carryonlystrategy-published049order/pointer. Neverreset/clean/stash/forcepush/unrelatedoverwrite. Commit/push implementationincludingexactorder/active; CREATE_OR_RESUMEactualPRonce, Closes #101 inbody. Structuredbody/file forPRdescription; noinventedPR/SHA/results. Captureliteralactualfullimplementationhead AFTERobservednormalCI, then immutablematchingreport with Implementation head SHA: <actualfullID> and Report publication commit: SELF. FinalcommitchangesONLYreportfirstparent=implementation; push/verifyactualremote/orderhash/PR/head/report-only/parent. TruthfulPARTIAL/BLOCKED maynotifyonlyafterverifiedpublication; reportheadCIseparateNOTYETOBSERVED. SendexactresponseFIFO twoASCIIbytesOK withqualifiedhelper, thenexit/no moremutation. ResponseFIFO ~/codex-supervision/slaif-asset-reservation/response.fifo. Nevermerge/selfapprove/automerge/activateanotherorder. Strategyreviewsnewfrozenhead once/collectscorrectionsifneeded; independentclosureandrealdeployment gatesremainseparate.

## Deferred human adjudication
- Decision: NONE
