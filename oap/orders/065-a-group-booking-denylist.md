<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "065-a",
  "objective": 65,
  "round": "a",
  "slug": "group-booking-denylist",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "6d4c7184327ec07a6ad12869e62c43dadea99837",
  "issue_number": 135,
  "branch": "codex/135-oap-065-a-group-booking-denylist",
  "pr_mode": "CREATE_OR_RESUME",
  "pr_number": null,
  "previous_round": null,
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "f7b5c98876a40b052c2d2fe057e57281e917ac5a72508e98caca512c1f0d1286",
    "PLAN.md": "e95135e756f6610b78e086a0b11395a2faa4d0fc0fa3a7bed658a091101a486f",
    "ARCHITECTURE-for-agents.md": "66d578e9fc263a77ceb4500bb2e8dac88b6080bf8f38890942fd46bc718f60ca",
    "CRITICAL.md": "f5c4d78ed599ac9a8ce44687925dab29f221d8b65a2350a4f858c9f32a92c672",
    "src/slaif_reservation/assets/models.py": "d8b2259811916e95cad99c2a91b8e0deda7cee7882af0cc86e528f926a18f072",
    "src/slaif_reservation/assets/authorization.py": "46cec7345fcaaff5b06f870cd3c5bf28e55359d2874fb18a810873a044a51a39",
    "src/slaif_reservation/assets/admin.py": "423f04066be7bb99653cd1fd6ff0440e26f137d20a46dd107e3610b6bc81514d",
    "src/slaif_reservation/reservations/services.py": "f35381e94abe08747c0498142c467fcc7d98e754c6f52353fc7f9cdc901015f1",
    "src/slaif_reservation/api/reservation_views.py": "ae3d3d5c6ba3386bec723f6b24cd3b09aca35291dfd33c1a1ba86d19af30a33e",
    "src/slaif_reservation/web/selectors.py": "9a2af3c4c4f7d44d06c1ee80fc7798cc36ab0ecea4c921f4e724643fa4fccfbb",
    "src/slaif_reservation/web/views.py": "adfdfa6a3c2e8772cbcfb72150595e425a5f5ad33b5b43221f84fd19874ccd79",
    "tests/test_booking_authorization.py": "4c6b2fb3f60ede42d237dd81be7a2bd080896711be37efba989df6b6bf0278d7",
    "docs/authorization.md": "cba3ef323d6f964d3e142060bb5a5b465c16aa4bf71eefba3131835b4563a5dd"
  },
  "requirements": [
    "SAR-001",
    "SAR-007",
    "SAR-008",
    "SAR-009",
    "SAR-011",
    "SAR-012",
    "SAR-017",
    "SAR-018",
    "SAR-019",
    "SAR-032",
    "SAR-036",
    "SAR-037",
    "SAR-044",
    "SAR-048",
    "SAR-049",
    "SAR-053",
    "SAR-057"
  ],
  "allowed_paths": [
    "PLAN.md",
    "ARCHITECTURE.md",
    "ARCHITECTURE-for-agents.md",
    "src/slaif_reservation/assets/models.py",
    "src/slaif_reservation/assets/migrations/0004_asset_excluded_booking_groups.py",
    "src/slaif_reservation/assets/authorization.py",
    "src/slaif_reservation/assets/admin.py",
    "src/slaif_reservation/web/selectors.py",
    "src/slaif_reservation/web/views.py",
    "src/slaif_reservation/web/templates/web/asset_list.html",
    "src/slaif_reservation/web/templates/web/asset_detail.html",
    "src/slaif_reservation/api/reservation_views.py",
    "tests/test_booking_authorization.py",
    "tests/test_assets_models.py",
    "tests/test_assets_admin.py",
    "tests/test_bootstrap_assets.py",
    "tests/test_migrations.py",
    "tests/test_form_guidance.py",
    "tests/test_api_v1_reservations.py",
    "tests/test_authorization_upgrade.py",
    "tests/browser/test_booking_authorization_browser.py",
    "tests/browser/test_form_guidance_browser.py",
    "README.md",
    "INSTALL.md",
    "docs/authorization.md",
    "docs/human-ui.md",
    "docs/api-contract.md",
    "docs/security-model.md",
    "docs/deployment.md",
    "docs/ux/form-guidance-inventory.md",
    "oap/active",
    "oap/orders/065-a-group-booking-denylist.md",
    "oap/reports/065-a-group-booking-denylist.md"
  ],
  "forbidden_resources": [
    "No mass-email implementation, account/SMTP/token/authentication/permission model or reservation schema change, no reservation exclusion/locking/lifecycle/policy/idempotency rewrite, no dependency/lock/Docker/Compose/proxy/CI/OAP helper or historical order/report/audit edit. The existing shared predicate must remain the single new-booking eligibility authority; only the minimum API/web adapter change needed for truthful responses is allowed.",
    "No real user/group/asset data, production DB/migration, private SmartScheduling export, real SMTP/recipient/credential, lab job, host/DNS/TLS/firewall/public exposure/deployment, foreign worktree/PR resource mutation or CODING merge/automerge."
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Human 2026-11-19/20 selected GitHub issue #135 for implementation after PR113 merge; issue #135 author described exact-asset group booking denylist and deny-over-allow behavior; human directed CODING via OAP and development merge after CI",
      "section_or_evidence": "All issue #135 acceptance criteria are selected: optional excluded groups, independent of booking_restricted, deny wins on dual membership, exact asset only, browser/API/service parity, privacy-safe UI, old reservations preserved, old assets default no exclusions."
    },
    {
      "marker": "A",
      "source": "Current ARCHITECTURE.md A-16/SAR-049 and stable SAR001..056; current PLAN P08/P09; human issue #135 selected amendment",
      "section_or_evidence": "A-16 grants are additive and originally excluded explicit deny rules; this human-selected amendment is ONE narrow asset-level exclusion that supersedes only that prohibition, not a general deny policy. Append A-18 and SAR-057 while preserving prior IDs and one reservation authority; update compact executor projection/source digest semantically. No real deployment."
    },
    {
      "marker": "E",
      "source": "Live main 6d4c7184327ec07a6ad12869e62c43dadea99837 after merged PR113, open issue135, current assets/models.py/authorization.py/admin.py, shared reservation service, browser selectors and API preflight; old branch CI security repaired by current lock",
      "section_or_evidence": "Asset currently has booking_restricted and allowed_booking_groups, no exclusions; user_can_book_asset and batch_asset_booking_states drive service/API/UI; create_reservation row-locks principal+asset then checks shared predicate; API rechecks before idempotency cache; member list/detail show privacy-safe state. Existing migration0003 grants default unrestricted. PR113 final head 3a90fbd0032c7e4a3c6e4f2cb69cc74734d3604b passed quality/test/security/container CI run44642086867, and merged main6d4c718 has the identical complete Git tree (46977169fe416f2f116f50f0571aa11f4f6ac3f0). Post-merge main CI run44644445398 was still in progress at order finalization; do not claim its result until terminal and require terminal exact-head evidence at the next merge gate."
    },
    {
      "marker": "I",
      "source": "Existing auth.Group M2M and shared asset eligibility predicate, Django migrations/Admin, current browser/API/legacy-import tests",
      "section_or_evidence": "Add blank M2M excluded_booking_groups with no data backfill; enforce current membership deny before allowed-group pass on exact asset, even when unrestricted, while global Book and policy/domain checks remain. Prefetch exclusions in list to avoid N+1; add distinct privacy-safe excluded state/help. Admin field independently configurable with clear deny precedence. Preserve existing reservations/owner lifecycle. Tests on real owned PostgreSQL/Chromium."
    },
    {
      "marker": "C",
      "source": "Attributable human selection resolves deny precedence and narrow scope; CRITICAL register empty",
      "section_or_evidence": "D0/DHA NONE: no unresolved human choice about whether to add deny, inheritance or precedence. Strongest objection is accidental denial for multi-group members and operational surprise; default empty exclusions, visible admin guidance/member eligibility, exact negative tests and explicit operator opt-in mitigate. No D2 action."
    }
  ],
  "decision_class": "D0",
  "target_gate": "One reviewed development PR delivering issue135 exact-asset denylist with migration/default-empty compatibility, browser/API/service/Admin parity, privacy-safe UI and five exact-head CI; mass-email remains separate selected objective and final independent ICA follows both; no real deployment",
  "expected_report_path": "oap/reports/065-a-group-booking-denylist.md",
  "tests": [
    "Fresh/migrated Asset.excluded_booking_groups is empty for existing assets; applying migration preserves existing allowlists, permissions, reservations and lifecycle; no data rewrite. Admin can set zero or more existing groups independently of booking_restricted, with useful help on precedence, exact-asset scope and no other access grant; server-side validation/CSRF/model permissions unchanged.",
    "Owned real PostgreSQL shared predicate + create_reservation: unrestricted asset with excluded group denies, non-excluded Book user succeeds; restricted allowed+excluded membership denies (deny precedence), allowed-only succeeds; restricted-empty still fails; missing global Book/inactive/service/staff/superuser boundaries preserved; multiple groups/direct permissions combine as before except narrow exclusion; exact asset only, no parent inheritance. Group membership or exclusions added/removed take effect for NEW bookings on next request; existing reservations not deleted/rewritten, owner cancel/release still allowed after loss.",
    "Browser and bearer API direct create/forged POST and cached idempotent replay recheck current exclusion before a prior success is reused; preserve existing owner-only API contract, stable 403 code/privacy and PostgreSQL exclusion/audit coupling. Asset list You can book and detail Booking access show a distinct truthful non-bookable state without group names/IDs or other metadata; asset remains visible; no N+1 query regression with prefetch. Test bootstrap reapply and legacy future-import plan use current shared eligibility or explicitly report any unresolved discrepancy.",
    "Focused unit/integration/concurrency/upgrade and Chromium desktop/mobile default/custom theme where relevant; inspect privacy-safe screenshots <=2 at a time, no horizontal overflow/framework branding. Current docs/architecture/projection semantics and links; ruff/format/mypy/check/makemigrations/OpenAPI unchanged endpoint shape; normal five exact-head CI at implementation/report heads. No real assets/user data/deployment. CODING opens PR with Closes #135, report-only child/SELF, remote verification/FIFO OK; never merges."
  ]
}
-->

# 065-a — exact-asset group booking denylist

## Goal and authority

Implement all selected behavior of GitHub issue #135 on exact main `6d4c7184327ec07a6ad12869e62c43dadea99837` after PR113 merged and local main was fast-forwarded. This is one authorization-purpose PR, issue135/branch in metadata. The human explicitly selected a narrow asset-level denylist and DENY-over-allow precedence, amending A-16's original additive-only assumption only for this one asset booking gate. Do not ask the human to reselect it. The separately selected Administration mass-email feature is NOT part of this PR; strategy will issue its next bounded OAP objective after this merge.

## Numbered acceptance and negative paths

1. **Model, upgrade, Admin.** Add optional `Asset.excluded_booking_groups` using EXISTING `auth.Group`, blank/default-empty for all existing assets, no data backfill or other Asset/reservation schema change. Its setting works on unrestricted and restricted assets independently of `booking_restricted`. Admin field is editable by existing authorized asset administrators, with nearby help that exclusion wins, only the booked asset is checked, and no group name is a code constant. Existing allowlist and asset records remain byte/row-preserved on upgrade. Update current architecture A-14 with stable SAR-057 and A-18 selected amendment, PLAN selected scope and compact executor projection/source identity without erasing SAR-049 or A-16 history; no general explicit-deny language/policy engine.
2. **One authoritative predicate.** An eligible new booking needs current active human + `reservations.book_assets`, must NOT belong to ANY excluded group on the exact asset, and if `booking_restricted` is true must also belong to at least one allowed group. Deny wins if membership is both allowed and excluded; excluded group denies even when the asset is otherwise unrestricted. Staff/superuser/unrelated Admin permission never bypasses membership exclusion; no parent-child inheritance. `user_can_book_asset` and `batch_asset_booking_states` must agree, with current membership evaluated on each request and both M2M sets prefetched on lists. Shared `create_reservation()` remains the final row-locked authority; the bearer preflight continues rechecking before idempotent cache replay. Preserve policy/duration/lead/horizon/counters/blackouts/overlap/audit/owner lifecycle invariants.
3. **Member/API truth and privacy.** Keep assets visible. List `You can book` and detail `Booking access`/reserve action show a distinct excluded-but-not-bookable state; explain it without exposing excluded group names/IDs or other members. Direct browser and API POST cannot bypass; preserve existing non-disclosing 403 booking_not_authorized representation and owner-only API routes. Exclusion does not delete/rewrite prior bookings, and owners can still cancel/release accepted reservations after losing booking eligibility. No new cross-user or bearer mutation scope.
4. **Evidence/docs.** Run focused tests per metadata, including migration/default-empty, unrestricted/restricted overlap, multi-group additions/removals, no inheritance, direct service/browser/API and idempotent replay, UI privacy, existing reservation lifecycle, bootstrap/legacy preservation, Admin guidance and relevant regression suites. Update only now-false current README/INSTALL/authorization/human-ui/API/security/deployment/form-inventory prose. Keep normal product docs task-oriented, no work-order ledger. Show source-specific negative paths, real owned PG and Chromium desktop/mobile screenshots viewed in batches <=2, and normal five exact-head CI. CODING commits implementation/order/pointer, opens/amends one PR with `Closes #135`, then immutable report-only child with literal implementation head/SELF, verifies remote PR/parent/path/head and signals FIFO OK. CODING never merges.

## Strongest objection and recovery

The narrow exclusion may surprise a member who also belongs to an allowed group. Operator opt-in is explicit and default-empty, the Admin field explains precedence, member UI states the access result without leaking group identity, and negative tests cover dual membership. Existing reservations stay historical and lifecycle rights stay owner-scoped. This is D0, Decision NONE; no real data/import/job/host/deployment. Fresh CODING through sourced `~/codex-supervision/slaif-asset-reservation/codex.sh` from checkout, `codex --yolo --profile early-beta` in right tmux pane. Preserve foreign worktrees/resources and the historical order/report set; no reset/clean/force.

## Deferred human adjudication
- Decision: NONE
