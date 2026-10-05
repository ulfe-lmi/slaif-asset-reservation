<!-- OAP-META
{
  "id": "037-a",
  "round": "a",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "c4703beacf9c887d7ccfb59c89af4f389bdb57ed",
  "issue_number": 73,
  "branch": "codex/73-oap-037-a-form-guidance",
  "pr_mode": "CREATE_OR_RESUME",
  "previous_round": null,
  "pr_number": null,
  "allowed_paths": [
    "src/slaif_reservation/web/forms.py (labels/help/widgets only)",
    "src/slaif_reservation/management_ui/forms.py (labels/help/widgets only)",
    "src/slaif_reservation/accounts/forms.py (administration presentation only)",
    "src/slaif_reservation/accounts/admin.py (form/help/password-status presentation only)",
    "src/slaif_reservation/assets/admin.py (form/help presentation only)",
    "src/slaif_reservation/reservations/admin.py (read-only guidance only)",
    "src/slaif_reservation/audit/admin.py (read-only guidance only)",
    "src/slaif_reservation/config/admin_site.py (group/admin form guidance only; admission unchanged)",
    "src/slaif_reservation/web/templatetags/form_guidance.py",
    "src/slaif_reservation/web/templates/web/ (field/help/action/policy/scopes presentation only; token secrecy/history and root behavior unchanged)",
    "src/slaif_reservation/management_ui/templates/management_ui/ (field/help/action/policy presentation only)",
    "src/slaif_reservation/assets/templates/assets/ (raw filter help only)",
    "src/slaif_reservation/web/templates/admin/ (field/help/readonly/password-status presentation only)",
    "src/slaif_reservation/web/static/web/site.css (help/field spacing only)",
    "src/slaif_reservation/web/static/web/admin-identity.css (help spacing only)",
    "tests/test_form_guidance.py",
    "tests/browser/test_form_guidance_browser.py",
    "tests/test_web_human_mvp.py (label/help expectations only)",
    "tests/browser/test_human_mvp_browser.py (human scope-label expectations only)",
    "tests/test_management_ui.py (label/help expectations only)",
    "tests/test_assets_admin.py (help/password/status expectations only)",
    "tests/browser/test_product_entry_browser.py (label expectations only if needed)",
    "docs/ux/form-guidance-inventory.md",
    "docs/human-ui.md (field/policy/scope guidance only)",
    "docs/api-contract.md (display labels vs unchanged wire values only)",
    "TESTING.md (task-oriented new suite guidance only)",
    "oap/active",
    "oap/orders/037-a-form-guidance.md",
    "oap/reports/037-a-form-guidance.md"
  ],
  "forbidden_resources": [
    "models/schema/migrations/dependencies/inventory/domain/policy evaluator/source parsers/validators/service_values changes",
    "permission/admission/CSRF/token crypto/scopes/wire/API/idempotency/audit/exclusion weakening",
    "full theme/operator appearance overrides/extra product features/OAP machinery/canonical law/history rewrites",
    "real deployment/data/secrets/DNS/TLS/firewall/privatehost/lab/legacy resources",
    "valuable-source pytest/management qualification; unknown cleanup/reset/clean/stash/forcepush/auth copies"
  ],
  "requirements": [
    "SAR-005",
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
    "SAR-020",
    "SAR-021",
    "SAR-042",
    "SAR-043",
    "SAR-044"
  ],
  "decision_class": "D0",
  "target_gate": "M-INTERNET-UX-PILOT development; real exposure stays human D2",
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "f8a8df265d4dd452969d4bee874045c8f8a8261f9c87c96ba4c049a7dddf320d",
    "PLAN.md": "b19219e2d727af5a9554e011ba45a786f1bb61f25c001011fc18006cae665d08"
  }
}
-->

# 037-a — Understandable forms and choices

H: human requirement5, administration experience and default-policy UX;
latest human requires CODING. A: A-15/SAR-044 and preserved005/008-017/020/021.
E: PR72 accepted and mergedc4703beacf9c887d7ccfb59c89af4f389bdb57ed;
finalreport77d09551547b1b9cccdc6f08db43069cd0df68c0 all5checksSUCCESS;
source835pass, root actually viewed10 images, coding actualimage inputs/tool
records established. I: fresh full47-row ICA remains final. C: D0/DHA_NONE.
One purpose: every non-obvious field/choice explains its meaning and effect.
No full theme or operator overrides this round.

## Acceptance
1. Complete field/control inventory before guidance edits, then coverage map
   in docs/ux/form-guidance-inventory.md. Enumerate ACTUAL runtime bound forms,
   inherited/model-generated admin add/change/password/group fields, dynamic
   renamed fields and raw template filters/actions. The earlier39declared-field
   AST baseline is incomplete, not coverage proof. For every editable control,
   record meaningful label/help and rendered association, or explicit reason
   its purpose is self-evident (no filler "Enter name"). Protected/read-only
   admin models require contextual explanation and the supported mutation path.
2. Member surfaces: login(email/admin-created account, no self-registration),
   profile(display name and REQUIRED IANA timezone, no blank fallback),
   reservation start/end/purpose and DST start/end occurrence(only relevant to
   ambiguous local clock times), cancel/release, token name/lifetime/scopes,
   raw asset search/kind/parent/tag/reservable filters and availability controls.
   Actually render nearby help with labels and matchinghelp IDs/aria-describedby
   or accessible fieldset relationship. Cover errors and group-checkbox choices.
3. Staff: every policy field, blackout field/confirmation, cancellation/release,
   policy/blackout deactivation, raw policy asset filter, reservation filter
   asset/q/status/lifecycle/from/to, audit action/target/actor/source/correlation/
   timestamp filters and export-related controls. Explain actual selector
   semantics from source. Policy units/horizon means how far future START is
   allowed; duration elapsed minutes/max2880=48h2d; lead/cutoff effects; global
   fallbackvs exact/parent priorities; optional purpose; upcoming/account limits
   across assets/tokens. Existing overlap cap8 REJECTS when>=8 existing records
   intersect proposed interval (not a simultaneous occupancy sweep). Show
   default policy in understandable units, including2days(2880minutes),7days,
   zero lead/cutoff and50/8 limits; do not change stored units or evaluator.
   Blackout exact-asset behavior, overlapconfirmation and existing reservations
   not automatically canceled must be clear; high-impact choices get warnings.
4. Administration: all User add/change/password-change/groups/userpermissions/
   active/staff/superuser/service-account choices, Group permissions, AssetTag,
   Asset parent/slug/name/kind/booking mode/description/location/timezone/state/
   verification/capabilities/tags/internal locator fields and relevant readonly
   views/search/filter choices. Explain administrative permissions vs broad
   reservable-asset policy (groups are NOT project/membership authorization).
   Flags’actual effects must be precise; no implied notifications/OIDC/reset.
   Protected policies/reservations/blackouts/audit/tokens remain read-only, with
   clear service-backed routes. Never expose password/verifier fragments:
   replace inherited password-hash summary with safe password status and the
   real permitted password-change action, preserving validation/hashing and
   account/model permissions. No model/schema changes just to add help text.
5. Human-readable token scope labels AND useful explanations replace machine-
   string-only UI choices/displays while exact stored/wire values stay intact.
   assets:read is RESERVED and does NOT grant bearer inventory discovery;
   availability:read and reservation read/create/cancel/release explain their
   separate effects. No auto-added scopes/new rights/lifetime rules; preserve
   one-time plaintext, no-store/private/no-referrer/history scrubbing. No Django
   or work-order text in user-visible guidance; meaningful ordinary language.
6. Real rendered tests cover the actual inventory, not tests merely checking
   help constants. Verify visible meaningful help/labels/association on GET and
   invalid POST across member/management/admin/raw filters; unchanged negative
   timezone/DST/duration/policy validation, staff/SA/nonstaff/owner/CSRF/scopes/
   protected admin and token secret behavior. Playwright representative seeded
   forms and long labels at1440/390: reservation, token creation, profile,
   policy, blackout, audit/reservation filters, admin user add/change/password/
   groups and asset add/change; no horizontal page overflow, keyboard access,
   nearbyhelp. Preserve original assertions; adjust label selectors semantically
   only. No screenshots of one-time tokens or password/verifiers/CSRF/cookies/
   rawHTML/HAR/traces/real data. Use safe fixtures and shared coverage checks.
7. Coding actually opens/views all representative screenshots with view_image
   and iterates poor guidance/spacing before finalhead; record artifactpaths
   and actualmethod. Important correction: Codex formattedstdout omits image
   events! Actual session JSONL response_item function_call shows14view_image
   calls in036a and16in036b; priorSTRATEGICabsence inference was incorrect,
   clarified onmergedPR72. Tool is ALREADY available at originalprofile; no
   settings/model/auth changes needed. Currentreadonly client qualification
   actually calledview_image and sawmemberlogin390. Never countCSS/dimensions
   as visual inspection; root will open the finalimages too. No unsupported
   COMPLETE claims. No forced pixel-perfect CI snapshots.
8. Short task-oriented docs/links/coverage artifact, no executionledger/private
   fixture port/receipt paths in normaldeveloper/operator guides. Focused tests
   duringedits; commit before tracked-snapshot Docker qualification; finalfull
   suite via all5exactheadCI plus mandatoryreport-headCI. Do not repeat an
   unchanged local fullsuite. Report short literalimplementationhead/SELF/
   actualcommands/counts/failures/limitations/inventory and screenshot paths;
   PRforissue73 with Closes #73; coding NEVER merges.

## Scope and resources
Presentation only: labels/help/widgets/shared safe field templates/formatting/
admin form classes. Preserve all parsers/clean validators/service values,
account/model permissions, admission guards, policy/domain/audit/DB behavior,
asset inventory/schema/migrations/dependencies/crypto/wire contracts. No new
role/project auth, notifications or unrelated bug/refactor/theming. Any genuine
out-of-scope defect is reported for separate strategic decision, not smuggled.

EVERY product pytest/management qualification uses ownedDISPOSABLE SOURCE
copies, including focused operational neighbors. Never uvpytest fromvaluable
REPO_ROOT. Existing ownedPG17 receipt:
/home/ubuntu/codex-supervision/slaif-asset-reservation/workorders/033b-owned-test-db.json
ValidateexactcontainerID/nonce beforeconnection; parseprivateenvironment_file
intoPythonchildenv, not source/eval/print. Unique owned DBname/run; clear child
OAP_ROLE; ownPYTHONPATH/settings URLs. Installedroot.venv/PG17client/Chromium/
Caddy2.11.6 available. Sourceclone trackedfiles plus ONLYorderednew/changed
files for uncommitted focus; no ignored.env/auth/history copies. Owner nonce/
ports/cleanupIDs; neverforeignPG16:5432/blanketdown-v/prune/reset/clean/stash.
Captureprivatelogs/redacted summaries only; no source/fixture secrets printed.

Requiredreadset once; concreteedit/diagnostic within15minutes. Waitcoding/CI
outside model with existinghelpers. No fullstrategicbook/old objective rereads
or hypothetical extra acceptance. Optional refinements separately recorded.

Strongest reason against change: help/labels can silently misdescribe behavior,
lose accessible associations or weaken inherited admin/password/permission
rules. Cross-check actualdomain/selector/validator semantics, preserve business
code byte identity, test actual rendered forms and meaningful negatives, and
review real screenshots; no production/exposure implication.

## Deferred human adjudication
- Decision: NONE
