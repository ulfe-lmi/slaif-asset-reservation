<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "050-b",
  "objective": 50,
  "round": "b",
  "slug": "operator-authorization-guide",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "b873f4cf1071bded044ba456625b0ced355407a8",
  "issue_number": 103,
  "branch": "codex/103-oap-050-a-management-authority",
  "pr_mode": "AMEND",
  "pr_number": 104,
  "previous_round": "050-a",
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "4566e797b709b71f13b2929572a2d1145d15a5a7ab8b41db50ebfdab962628cd",
    "PLAN.md": "2c856ae47ec985b953a8d26edbe2c07fd343833a41bc45aefcd304a7e67c1432",
    "ARCHITECTURE-for-agents.md": "41c32e0b0d6427a173dfe0b722446ae8ee311f3880929db65ed0245309b3a59e",
    "src/slaif_reservation/accounts/authorization.py": "ef603110106cfc3c735e9992a3bfe0dd30c83035668ae928d927d42c4d4f3bd0",
    "src/slaif_reservation/reservations/management/commands/grant_management_access.py": "12a4b6f3f97722fc6a3ed874ffb53e288ffd618e1434f3dca4508095f9561749",
    "docs/authorization.md": "4983d59009a93d9a0473173e7a75c6a6e2bfefb72898d77f4a04feee249b9590",
    "INSTALL.md": "072598e021abdb8723d33a1550425db92de97c3d52b5ffaaeba2ff3536ea6268",
    "docs/security-model.md": "c482bf04b6b4c57f57d7f9904aced2f91a6a936ccfc0968df4b0d33e16199a8c"
  },
  "requirements": [
    "SAR-013",
    "SAR-019",
    "SAR-021",
    "SAR-048",
    "SAR-049",
    "SAR-050",
    "SAR-053"
  ],
  "allowed_paths": [
    "docs/authorization.md",
    "INSTALL.md",
    "docs/security-model.md",
    "oap/active",
    "oap/orders/050-b-operator-authorization-guide.md",
    "oap/reports/050-b-operator-authorization-guide.md"
  ],
  "forbidden_resources": [
    "ALL application/static/template/test/model/migration/runtime/dependency/Compose/proxy/source or behavior changes; no new group/permission/setup command or automatic grants.",
    "ARCHITECTURE/PLAN/projection/law/helper/OAPmachinery/CRITICAL/history/immutable050-a orolderorders/reports; docs/README needsno gratuitousedit.",
    "Realaccounts/groupassignments/DB/data/secrets/hosts/exposure/DNS/TLS/firewall, foreignresource/process inspection or cleanup, merge/automerge/delegation."
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Human authorization extension sections2-3,10-11; explicit Concentrated OAP/coding selection",
      "section_or_evidence": "Existing groups/individual grants across member/management/Admin; intentional existingStaff upgrade; no automatic future enrolment; document permission matrix,migrationprocedure,example group setup."
    },
    {
      "marker": "A",
      "source": "ARCHITECTURE.md A-16 / SAR048-050,053 and immutable050-a acceptance6",
      "section_or_evidence": "Staff onlyAdminadmission; appcaps add; modulemanage includesmodule read; no modelView-to-readAll inference; explicitchosenStaff upgrade and actualgroup examples before returning service."
    },
    {
      "marker": "E",
      "source": "PR104 implementation95d29b82ca1ff3581f3b0647fbf335b58db2b019/report88dc75a0fdf874e0aec758af1752d2da7b42de71",
      "section_or_evidence": "Realremote reportverifierPASS. All5implementationCI passed1207tests/160OAP. Rootwhole44-file code/test review found no required runtime correction; root5PGprobesPASS and fresh2ChromiumtestsPASS9.59s, exact-head screenshots actually inspected. Requiredreport-headCI being observed separately, no pending success assumed."
    },
    {
      "marker": "I",
      "source": "STRATEGIC frozen050-a fullreview / source search / comment https://github.com/ulfe-lmi/slaif-asset-reservation/pull/104#issuecomment-6244453995",
      "section_or_evidence": "Guide has NO examplegroup setup or nonstaffassignment walkthrough despite reportclaim; INSTALL upgrade goes migrate->restart without selectedStaff grant note; securityreference still Staff-visibleblackoutreasons. Correct only missing required operator guidance/evidence facts."
    },
    {
      "marker": "C",
      "source": "050-a acceptance6 and collectedDOC1-DOC3 findings on sameissue103/PR104",
      "section_or_evidence": "ONE documentation-only corrective purpose; all runtime/tests/permissions/schema/engine/proxy bytes mustremainunchanged. Old private branding/nav scope concerns explicitlysuperseded, no code/path expansion required."
    }
  ],
  "decision_class": "D0",
  "target_gate": "M-GROUP-AUTHORIZATION management/browser slice only; bearer read_all/issuance and fresh independent closure follow; no release/deployment",
  "expected_report_path": "oap/reports/050-b-operator-authorization-guide.md",
  "tests": [
    "Cross-check exactcodenames/labels/flags againstcurrentaccounts.authorization/Reservation.Meta/grant_management_access --help orsource; examples/direct+group union/StaffmodelAdmin separation/assetACL semantics matchactualcode. No realaccount/configmutation.",
    "ChangedMarkdown relative links+anchors and newlylinked existingguide targets; every Compose command retains -p \"$SAR_COMPOSE_PROJECT\", actualfilenames/flags. Walk upgrade order/migration/dryrun/apply/verify/restart without executing realDB writes.",
    "Prove app/static/templates/tests/models/migrations/config/deps/deploy/source trees BYTEIDENTICAL to95d29b82ca1ff3581f3b0647fbf335b58db2b019; gitdiffscope/whitespaceclean; reuse exactexistingruntime/PG/Chromium evidence, no newlocal fullsuites/browser/screens/rehearsal/Gunicorn/restore tests.",
    "NormalFULLrequiredCI at finalimplementation and exactreporthead; preservequality/test/security/container/OAPjobs. No checkwaiver; no rerunlocaltypes/appchecks absentcodechange; waitoutside model withexistingghrunwatch helpers."
  ]
}
-->

# 050-b — complete the operator authorization setup guide

## Goal / scope

ONE documentation/evidence-completeness correction on SAME issue103, branchcodex/103-oap-050-a-management-authority andPR104. Base main remainsb873f4cf1071bded044ba456625b0ced355407a8. Start from exact050-a report88dc75a0fdf874e0aec758af1752d2da7b42de71, parent95d29b82ca1ff3581f3b0647fbf335b58db2b019. Code review passed; selectedoperator guidance in acceptance6 is absent. No further runtime or test implementation is ordered.

## Compact reads

Normal CODING law/projection/communication/SECURITY-CORE/TESTING-CORE, this order, then ONLY the relevant guide/INSTALL upgrade/security paragraphs and existingpermissionconstant/command/Meta excerpts needed for factual accuracy. Do not ingest previousfullreports/source/testhistory or private strategic handoffs. SHA256bindings are PRE-ROUND FILECONTENT hashes, not Gitobject IDs. Fresh coding context, no images needed.

## Numbered acceptance / documentation

1. **Concrete group setup.** Add a concise operator-executable procedure using EXISTING Administration Groups/User permissions: create/select group, choose the appropriate APPLICATION permissions distinct from model View, assign current users via their group membership; individual assignments remain supported and unchanged. Nonstaff can receive selectedmanagement/read rights; Staff is required onlyforAdministration plusexistingmodelpermissions. Grants union acrossallgroups andindividualpermissions; removingonegroup doesnotremoveanothergrant. No automaticfutureuserenrolment, flags/groups/modelpermissions never inferred from group names.
2. **Illustrative role table and effects.** Include the human's examples (namesillustrative, neverapplicationconstants): Administrators (fullmember/management and intentionallyconfiguredAdministrationStaff+modelauthority), Lab members (book_assets+view_all_reservations, noextraoperations unlessgranted), Students (book_assets and ownlifecycle), Reservation readers (view_all_reservations withoutBookassets orothersmutations). Use exactexistingcodenames fromthematrix, notinventedpermissions. Explain explicitassetallowed-group membership inadditiontoglobalBookassets, unrestrictedfallback/noimplicitparentinheritance, no Staff/superuser asseteligibilitybypass, and existingownerlifecycle afterbookingeligibilityloss. A groupnameitself grantsnothing. Existing tokens stayowner-only; bearerreadAll/scopeissuance remainsplanned, notannouncedimplemented. No projects/denypolicies/directory/machineaccess promises.
3. **Upgrade sequence discoverable in INSTALL.** Add a SHORT current-authorization compatibility note/link between migration and apprestart in INSTALL's existingupgradepath. State that oldStaffstatus alone no longerprovidesmanagement, so operators mustINTENTIONALLY choose retainedmanagementgrants before returningservicetousers. In the authorizationguide, order the existingbackup->migrations->choosecurrentactivehumanStaffUUIDs->defaultdryrun->explicit--apply->verifyselectedgrants->restart/accesscheck steps. Use existinggrant_management_access (allnine management/readAll permissions, Bookassetsseparate) onlywhenoperatorchooses topreservealllegacyStaffmanagement authority; partial/nonstaff grantsuseexistingAdmin groups/individuals, notnewflags/expandedcommand. Explainwhere STAFF_UUID comesfrom (existingAdministrationuserchangeURLUUID), defaultdryrun meansNO --apply (do NOTinvent--dry-run), repeat--user selection ifneeded, no massStaffgrant or autoenrolment. compose run --rm doesnotrequirethelongrunningappservice alreadyrunning; commands canusecurrentapplicationimage beforepublicservice restart. Preserve retainedComposeprojectname/volumeidentity, actualfilenames/secrets/topology/backup and allmigration/defaultpolicyinstructions.
4. **Precise security reference.** Replace the now-ambiguous Staff-visibleblackoutreason wording with actual authorizedblackout-detail readers/managers (includingnonstaff appcap users), preserving protectedAdminmodel rules and ordinarymember/APIavailabilityprivacy. No accesschange. Do not broaden auditCSVdata or500/7daybounds.
5. **Scope/evidence honesty.** Leave immutable050-a untouched; newreport supersedes inaccurateclaims: docs/README.md wasNOTchanged andneedsnoedit; actual050-a changed7productdocs,15adaptedexistingtests+2newtests,total17,10managementtemplates+2webtemplates. EarlierretainedAllPNGpredatednavfix; strategyregenerated2focusedtests at95d29b8 (2PASS9.59s) and actuallyviewedcurrentAll1440/partial390artifacts underprivate050-frozen-browser, so visualfreshness isresolved; doNOTrecapture/rerunbrowser. Root5independentPGprobesPASS3.68s. Extra69browserlocalrunpassed but abortedfullserver wasNOTqualification; sourcecopyhasnoGitMETADATA andpgtoolsabsent locally, doNOTclaimGit/Dockerexecutablesabsent withoutactualproof. ProductproofcomesfromexactrecordedCI/source/runtimeevidence, notreportprose.
6. **Verification and concise report.** Check changedlinks/anchors, exactcommand/flag/codename/role correctness, scopeandgitdiffcheck. Verify ALL runtime/static/template/test/model/migration/config/deploy/dependency source bytes unchangedfrom95d29b8 (excludingonlythreedocs/order/pointer/report). Reuse validatedruntime/PG/concurrency/Chromium/visualevidence bybyteidentity; NOlocalfull/focusedapp/browser/OAPharness/operational/restore/Gunicorn/HTTPS/rehearsal reruns justbecauseMarkdownchanged. NormalFULLCI automatically runsatfinalimplementation and exactreporthead: observeallrequired5jobs, no waiver/skip. Use existingghrunwatch outside model, no newpollingframework. Fixonlyactualin-scopedocfailures; otherwisetruthfulPARTIAL. Reportshort (aim<=120lines) with acceptance1-6, exactpaths/results/byteidentity/CI/limits; no giantdevelopmentchronology.

## Negative paths / strongest objection

Poor examples might imply automaticprivilegedmembership, that modelViewgrantsreadAll, or that anAdministratorbypassesassetgroups. Explicitlyexcludeallthree and keepoperatoropt-in/actualcurrentpermissionmeaning. ChosenStaffcommand intentionallygrantsfulllegacyMngrights onlywhenoperatorselectsit, noteveryStaff/futurenewaccount. Allowner/API/booking/securityboundaries remainunchanged. D0routinefactualdocumentation, no CRITICALentry/newhumanriskdecision.

## Publication / recovery

PreserveWIP/branches; samePR104, Closes #103 retained. Commit/push ONLYallowedthreedocs+exactneworder/active, observenormalfullimplementationCI, captureliteralimplementationHEAD. Finalimmutablematchingreport-onlycommitfirstparent=implementation, Report publication commit: SELF; reportheadCI NOTYETOBSERVED atauthoring. Push/verifyactualremote/PR/head/order/report-only/parent, exactresponseFIFO OK thenEXIT. No subsequentmutation, merge/automerge/neworder/delegation. No realDB/account/group/host/secret/exposure operations. Nextscope051bearer and freshindependentclosure remainseparate.

## Deferred human adjudication
- Decision: NONE
