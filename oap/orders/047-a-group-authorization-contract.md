<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "047-a",
  "objective": 47,
  "round": "a",
  "slug": "group-authorization-contract",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "dad6e29d4f8e4fd941843b230474d35dafb69d1a",
  "issue_number": 97,
  "branch": "codex/97-oap-047-a-group-authorization-contract",
  "pr_mode": "CREATE_OR_RESUME",
  "pr_number": null,
  "previous_round": null,
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "2d300121b37b62eeeb0676764d5d82739adf006a13e70d35ff62b84c59f7eb43",
    "PLAN.md": "d30d89981907dd2af475b7a5f27aa0715defed3a78c6431b76e7e05204ef833f",
    "ARCHITECTURE-for-agents.md": "a0a31be7b4efbf9f61c76488888b081cc0db296ff75c8eaae74b712b72ac32a6",
    "oap/coding-instructions/AGENTS.md": "1611e9700de5b311deeb45460162464f7f24462e74790dddfcec2bb016b30394"
  },
  "requirements": [
    "SAR-001",
    "SAR-010",
    "SAR-012",
    "SAR-013",
    "SAR-016",
    "SAR-017",
    "SAR-018",
    "SAR-019",
    "SAR-021",
    "SAR-036",
    "SAR-037",
    "SAR-038"
  ],
  "allowed_paths": [
    "ARCHITECTURE.md",
    "PLAN.md",
    "ARCHITECTURE-for-agents.md",
    "docs/authorization.md",
    "docs/governance/GROUP-AUTHORIZATION-PROJECTION-REVIEW.md",
    "oap/active",
    "oap/orders/047-a-group-authorization-contract.md",
    "oap/reports/047-a-group-authorization-contract.md"
  ],
  "forbidden_resources": [
    "Application/source/model/migration/test/runtime/dependency/inventory changes",
    "Immutable historical orders/reports/audits/bootstrap records and CRITICAL changes",
    "Real service/private data/host/DNS/TLS/firewall/secrets; broad cleanup; credentials copying",
    "Other objectives/branches, merging, auto-merge or task delegation"
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Current human request2026-10-17 sections1\u201311 and workflow clarification",
      "section_or_evidence": "Group-based capabilities, exact-asset booking, separate cross-user read bearer and external identifier; Concentrated OAP; use the coding agent."
    },
    {
      "marker": "A",
      "source": "ARCHITECTURE A12/A14; strategic S05/S12/S20/S23",
      "section_or_evidence": "Explicit human-authorized product evolution before compact projection; stable IDs and full architecture; fresh independent closure required."
    },
    {
      "marker": "E",
      "source": "Live GitHub/Git reconciliation2026-10-17",
      "section_or_evidence": "main dad6e29 clean, no open PRs, main CI successful;046-a acceptedquiescent. Existing A07/SAR013 staff gate and A08/SAR036 deferrals conflict with newly selected target."
    },
    {
      "marker": "I",
      "source": "Source inspection management_ui/auth.py,reservations/services.py,api/reservation_views.py,accounts/models.py,assets/models.py",
      "section_or_evidence": "Staff blanket authority, owner-only bearer, no external identifier or asset-group eligibility; new human scope needs bounded contract first."
    },
    {
      "marker": "C",
      "source": "CRITICAL.md and explicit human-selected scope",
      "section_or_evidence": "No registered entries; no unresolved human product choice admitted. Documentation-only D0; no deployment or runtime change."
    }
  ],
  "decision_class": "D0",
  "target_gate": "Selected M-GROUP-AUTHORIZATION contract only; not implementation/milestone/release/deployment acceptance",
  "expected_report_path": "oap/reports/047-a-group-authorization-contract.md",
  "tests": [
    "python3 -m unittest discover -s tests/oap -p test_*.py -v",
    "changed Markdown paths/anchors, canonical/projection source hash and full-to-compact semantic coverage; measure routine coding read set",
    "git diff --check; prove only allowed documentation/order/pointer/report paths changed",
    "normal full five CI jobs at final implementation head and report-head checks at exact frozen head; no unrelated bespoke qualification"
  ]
}
-->

#047-a — selected group authorization contract

## Goal and scope
Record the human-selected M-GROUP-AUTHORIZATION contract before implementation. One documentation purpose, no application/runtime changes. Issue97, exact starting main dad6e29d4f8e4fd941843b230474d35dafb69d1a, no openPR;046-a completed, not replayed. Create/resume only the metadata branch/PR. Private sequence is orientation only; this order is the sole executable scope.

## Ordered read set
Standard compact C04 set, then ARCHITECTURE.md A01/A04–A09/A12–A15 and affected stable rows010/012/013/014/016/017/019/021/036/037/038; PLAN P03/P04/P06; docs/audit/ICA-PROTOCOL.md; docs/governance/INTERNET-UX-PROJECTION-REVIEW.md structure only. Inspect management_ui/auth.py and api/reservation_views.py bounded authorization definitions only to distinguish current source from target. Do not load whole roadmap/history, private transcripts, future drafts or other source trees. If a source/hash mismatch is real, stop affected writes and ask strategy rather than adjusting expected values.

## Acceptance
1. Append the exact strategy-authored A16 payload below to full ARCHITECTURE.md, and the six exact SAR048–053 requirement rows below within A14 before A15. Add a concise top note identifying A16 as the current2026-10-17 selected target and pointing to its controlled evolution table. Preserve old IDs, invariants and historical baseline/audit prose. Do not silently repurpose old requirements or advertise unimplemented access.
2. Add PLAN P08: human provenance, selected target, no infrastructure authorization, prerequisite plus five purposes (048permissions/externalID/upgrade;049booking;050management;051bearer;052qualification/freshindependentICA), existing milestone history preserved; group/asset restriction deferral superseded only by A16. Mark those purposes as scoped future work, not completed. Other deferrals remain.
3. Recompose the compact executor projection after full source is authored: include all A16 executor obligations directly (eligibility, every capability boundary/partial visibility, scope+current grants, minimal owner data, explicit upgrades, no execution/deployment), revise conflicting old staff/group-deferral clauses with explicit A16 applicability, retain old invariants and named SAR mappings. Update source digest only after semantic reconciliation. Do not make full architecture/A16 an indirect routine mandatory read. Add concise docs/governance/GROUP-AUTHORIZATION-PROJECTION-REVIEW.md tracing all A16 facets/human sections1–11 to full and compact clauses, with honest context byte/token estimates, exact sources/hashes, accepted-vs-candidate changes and limitations; semantic review is not ICA.
4. Add docs/authorization.md as a clearly labelled SELECTED TARGET / NOT IMPLEMENTED BY THIS CONTRACT guide: permission matrix, Admin/staff distinction, baseline and explicit legacy-staff upgrade intent, exact-asset semantics, future owner-only vs separate read-all bearer contract and external enforcer boundary. Do not publish operator commands/endpoints as existing before implementation. Concise useful prose, no product history ledger.
5. Meaningful review covers all human sections1–11, privacy/upgrade negative boundaries, no invention of projects/hierarchies/execution or broadened owner-only surfaces. All application/test/migration/deployment/dependency/bootstrap files are byte-identical to base. No CRITICAL change.
6. Run the complete stdlib OAP harness, changed Markdown link/anchor checks and git diff --check; standard quality/test/security/container/oap-harness must pass at frozen implementation head. During editing use focused checks; no repeated expensive full suite without a relevant change/failure. Report-head CI is observed by strategy after the immutable report. Do not run unrelated bespoke qualification. Four product CI jobs remain intact.

## Negative paths and strongest objection
The strongest reason against this slice is confusing future authorization meaning with current functionality or weakening existing privacy by an ambiguous amendment. Label selected/unimplemented target, map explicit exceptions and preserve owner-only routes, active-human, CSRF, audit, exclusion, abuse, protected admin and infrastructure boundaries. Validate no runtime paths changed. Metadata/source hashes bind the pre-edit accepted source, not candidate identity.

## Recovery and publication
Reconcile actual branch/base/PR, preserve the clean unused maintenance/group-authorization branch and all historical work. Only strategy owns this immutable order/pointer. Apply only allowed paths, never amend an old migration/order/report, never merge or delegate. Code/artifacts can use owned temporary tools; current repository .venv/python is an obsolete symlink, so do not alter it merely for docs checks. Full normal product CI supplies exact-head product regression. If tool setup is needed use owned local directories and never valuable .env/deploy paths. Include `Closes #97` in PR body. PR creation precedes report. Capture literal full implementation head after observed CI; commit ONLY immutable matching report with first parent=that head, Report publication commit:SELF. Push/verify remote PR/head/report-only identity, send exact responseFIFO OK and stop. Do not mutate after report publication or claim its future CI. D0; no product milestone acceptance.

## Deferred human adjudication
- Decision: NONE

## Exact strategy-authored architecture payload
Append the following UTF-8 paragraph block as A16 (not a new governance authority):

```markdown
## A-16. Selected group authorization extension (2026-10-17)

The human selected M-GROUP-AUTHORIZATION: extend existing Django groups and individual permissions across member, management and Administration surfaces; explicit exact-asset booking eligibility; separately authorized cross-user read-only browser/bearer access; one optional external user identifier. This section defines selected target behavior, not an implementation or qualification claim. The prior Internet/UX evidence remains historical; this changed authorization target needs fresh exact-revision independent closure.

**Controlled evolution of prior requirements.** SAR-001–SAR-047 retain their stable IDs and preservation obligations. For this new target, SAR-008 additionally requires booking capability and exact-asset eligibility; SAR-010 replaces implicit staff lifecycle authority with the relevant explicit capability while preserving owner lifecycle rights; SAR-012 preserves owner-only member and existing bearer routes and permits only the separately named cross-user read surface; SAR-013 replaces blanket staff management admission with explicit capabilities. SAR-014/016/017 add only the explicit read-all scope and separate compatible read interface; existing tokens/endpoints never widen. SAR-019 availability privacy, SAR-018 idempotency and SAR-021 bounded audit remain unchanged. SAR-036's deferral of existing-group/resource restriction and delegated management capabilities is superseded only by this section; projects, organizational trees, delegated group ownership, general policy languages, management/mutation bearer APIs and all execution/infrastructure exclusions remain deferred. Historical A-04/A-07/A-08/A-09/A-15 staff-only/group-deferred statements are baseline context where this selected amendment explicitly differs.

**One additive grant system.** Reuse Django Group, user group membership and individual user permissions; do not introduce parallel membership, hardcoded operator group names or explicit deny rules. Grants combine across all groups and individual assignments. Use documented custom application permissions, distinct from Administration model View permissions. The following selected codenames live in the reservations namespace; Django permission records may be attached to the existing Reservation content type, without a new authority model:

| Application permission | Meaning |
|---|---|
| reservations.book_assets | Create new reservations, additionally subject to exact-asset eligibility and existing policy/domain checks. |
| reservations.view_all_reservations | Explicit cross-user reservation listing/detail in the separate All reservations browser/read-only API surfaces. |
| reservations.cancel_others_reservations | Existing audited cancellation of another owner's reservation; no implied read-all or release permission. |
| reservations.release_others_reservations | Existing audited release of another owner's reservation; no implied read-all or cancellation permission. |
| reservations.view_booking_policies | Inspect policy information through management. |
| reservations.manage_booking_policies | Create/update/deactivate policies through existing audited services; includes that module's read interface. |
| reservations.view_maintenance_blackouts | Inspect blackouts and their relevant details. |
| reservations.manage_maintenance_blackouts | Create/deactivate blackouts through existing audited services; includes that module's read interface. |
| reservations.view_audit_history | Existing bounded filtered audit browser. |
| reservations.export_audit_history | Existing filtered bounded CSV export; does not implicitly grant unrelated audit/reservation UI access. |

All application access requires current active non-service-account human eligibility. Staff is admission to /admin/ only, with existing model permissions; staff or unrelated Administration permissions confer no application management or booking bypass. Trusted active human superusers retain Django's application-permission semantics and all protected-record/domain restrictions. They still meet explicit asset group eligibility when creating bookings; Administration can deliberately configure access, not bypass it through a reservation adapter. Enforcement is server-side at direct GET/POST endpoints and relevant shared services; buttons/navigation reflect the same checks. Partial-capability users receive a useful management landing without unauthorized counts, data, links or actions. Mutation capability without read-all must not incidentally disclose another owner's record through redirects, overlap previews, errors or audit. Protected Administration records stay read-only/service-backed.

**Booking eligibility.** Assets are explicitly unrestricted or group-restricted. A restricted asset requires membership in at least one of its allowed existing groups; restricted with no allowed groups fails closed. Check only the asset being booked, never implicit parent inheritance. All existing assets migrate unrestricted. Browser and bearer creation share the authoritative authorization check around the existing reservation service; token creation also requires its action scope and owner's current capability/membership. Keep active/reservable/exclusive checks, UTC/DST, policies/counters, PostgreSQL exclusion/locking and atomic audit unchanged. Assets remain browsable and show whether the member is eligible; do not disclose sensitive account/group metadata. Access changes never rewrite existing bookings. Owners may still list/inspect/cancel/release their accepted reservations after losing booking capability or asset group membership, subject to existing lifecycle/cutoff rules.

**Separate cross-user read surfaces.** An explicit All reservations browser view requires view_all_reservations and supports existing validated asset, status/lifecycle, time filters and pagination. Owner pages remain private. Authorized viewers inspect owner, asset, original times, effective end, status and lifecycle, with mutation controls only for the corresponding capability. Read-only viewers cannot cancel/release/edit by forged requests. Policy/blackout/audit capabilities do not imply read-all; overlap previews without read-all show only the safe confirmation information needed for the blackout operation.

Add reservations:read_all as an explicit token scope. New cross-user list/detail routes require BOTH that scope AND the owner's current view_all_reservations permission. Existing reservations:read remains owner-only even for staff/superusers. Existing token scope records never change automatically. Issuance refuses authority-exceeding read-all and create scopes; use rechecks current owner permissions/membership, expiry/revocation/activity/service-account rules and existing shared abuse controls. Group/permission removal takes effect on subsequent requests with the same token; no process-global grant cache. No cross-user bearer mutation surface. Reuse validated bounded filtering/pagination but use a minimal explicit cross-user representation: reservation/asset UUID and safe asset identity, owner UUID plus external_identifier (null when unset), aware original start/end, effective_end, status/lifecycle, release/cancellation timestamps and unambiguous blocking/effective interval semantics. Exclude owner email/display/profile/admin flags, passwords/verifiers/token secrets, private locators, unrelated metadata and private purpose/cancellation/blackout free text. Existing owner representations remain compatible.

**External identifier.** Add optional external_identifier to the existing User, opaque case-sensitive string of at most128characters. Preserve numeric strings and leading zeroes. Populated values are unique; unset is NULL and multiple users may be unset. Existing accounts remain unset; no inference or backfill. Only authorized account administrators edit it in existing Administration. Member profile and bearer input cannot modify it. It is neither a credential nor Linux UID validation, and does not replace UUID/email/password/token identity. The external enforcer owns account mapping, enforcement, polling, caches/refresh and outages. No SSH/PAM, account synchronization, workload/container execution, GPU allocation or automatic machine login grants enter this application. Reservation entitlement is not login authority. Cancelled reservations do not block; confirmed/released consumed intervals preserve [start,effective_end) and aware timestamps.

**Deliberate upgrade.** Inventory every current management route/action and map its grant. Introduce explicit migrations and setup docs preserving users/groups/reservations/policies/audits/tokens and old individual permissions. A one-time baseline booking-permission assignment to existing non-service-account users preserves their former booking access; document its exact scope and test it against a populated pre-upgrade database. Newly created accounts receive no automatic application grants or privileged-group membership; explain the required booking grant in account administration. Current staff management access is NOT silently retained through is_staff: provide a dry-run-first explicit idempotent setup command/procedure for an operator to grant chosen current staff the management capability set. Never infer read-all from old Administration View permissions. Real deployed DB changes remain operator-owned, with backup/rollback guidance; test migrations only on owned synthetic databases. Example operator groups may be Administrators, Lab members, Students and Reservation readers, but their names are never authorization constants.

**Evidence.** Test direct endpoint and service denial, nonstaff partial grants, additive multi-group and individual grants, staff/no-grant and superuser boundaries, viewer mutation denial, browser/API asset parity, removal while tokens stay valid, missing scopes, owner-only tokens for privileged owners, inactive/service accounts, retained owner lifecycle access, opaque/unique/unset identifiers, minimal-response canaries, unchanged conflicts/lifecycle/audit/idempotency. Use focused tests per implementation purpose and full normal exact-head checks, meaningful Chromium flows/screenshots for new controls, upgrade tests, generated OpenAPI and docs links. Final independent audit starts with this human scope, full current architecture and exact merged revision, maps all applicable stable requirements and records limits; it is not strategic self-certification or real deployment authorization.
```

## Exact new stable requirement rows
Insert these six rows before A15 without deleting any existing row:

```markdown
### SAR-048 — Additive application capabilities

A-16 one grant system and explicit management capabilities; direct/group union; staff/Admin separation; protected records and active-human/superuser constraints.

Source: human authorization extension2026-10-17 sections1–11; A-16.

Inspect: accounts authorization/models/admin, assets eligibility, shared reservation services and browser/API/management adapters as applicable. Evidence: focused positive/negative capability, privacy and migration tests; exact-head CI and fresh independent closure.
Initial independent-closure classification: **UNPROVEN** (new selected target).

### SAR-049 — Exact-asset booking eligibility

A-16 booking capability, unrestricted/group-restricted exact asset, shared browser/bearer enforcement, no inheritance or historical reservation rewriting.

Source: human authorization extension2026-10-17 sections1–11; A-16.

Inspect: accounts authorization/models/admin, assets eligibility, shared reservation services and browser/API/management adapters as applicable. Evidence: focused positive/negative capability, privacy and migration tests; exact-head CI and fresh independent closure.
Initial independent-closure classification: **UNPROVEN** (new selected target).

### SAR-050 — Explicit cross-user browser visibility

A-16 All reservations separation, validated filters/pagination, granular mutation controls and denial, owner/privacy and partial-management boundaries.

Source: human authorization extension2026-10-17 sections1–11; A-16.

Inspect: accounts authorization/models/admin, assets eligibility, shared reservation services and browser/API/management adapters as applicable. Evidence: focused positive/negative capability, privacy and migration tests; exact-head CI and fresh independent closure.
Initial independent-closure classification: **UNPROVEN** (new selected target).

### SAR-051 — Explicit read-all bearer authority

A-16 read-all scope AND current owner permission; authority-bounded issuance, live revocation of grants, existing owner-only contract, read-only minimal lifecycle data.

Source: human authorization extension2026-10-17 sections1–11; A-16.

Inspect: accounts authorization/models/admin, assets eligibility, shared reservation services and browser/API/management adapters as applicable. Evidence: focused positive/negative capability, privacy and migration tests; exact-head CI and fresh independent closure.
Initial independent-closure classification: **UNPROVEN** (new selected target).

### SAR-052 — Opaque external user identifier

A-16 optional128character opaque unique populated identifier, multipleNULL, no inference, admin-only edit, minimum authorized cross-user API disclosure.

Source: human authorization extension2026-10-17 sections1–11; A-16.

Inspect: accounts authorization/models/admin, assets eligibility, shared reservation services and browser/API/management adapters as applicable. Evidence: focused positive/negative capability, privacy and migration tests; exact-head CI and fresh independent closure.
Initial independent-closure classification: **UNPROVEN** (new selected target).

### SAR-053 — Authorization upgrade and qualification

A-16 deliberate baseline booking preservation, explicit legacy-staff setup, no future autogrants; full route map, negative matrix, current architecture freshness and independent closure.

Source: human authorization extension2026-10-17 sections1–11; A-16.

Inspect: accounts authorization/models/admin, assets eligibility, shared reservation services and browser/API/management adapters as applicable. Evidence: focused positive/negative capability, privacy and migration tests; exact-head CI and fresh independent closure.
Initial independent-closure classification: **UNPROVEN** (new selected target).

```
