<!-- OAP-META
{
  "id": "036-b",
  "round": "b",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "e87497a1169bf4745489f699c28377bfbd2df717",
  "issue_number": 71,
  "branch": "codex/71-oap-036-a-public-product-entry",
  "pr_mode": "AMEND",
  "previous_round": "036-a",
  "pr_number": 72,
  "allowed_paths": [
    "src/slaif_reservation/web/urls.py",
    "src/slaif_reservation/web/views.py (entry dispatch/navigation only)",
    "src/slaif_reservation/web/templates/web/base.html",
    "src/slaif_reservation/web/templates/web/landing.html",
    "src/slaif_reservation/web/templates/web/login.html (identity only)",
    "src/slaif_reservation/web/templates/web/token_list.html (stale claim only)",
    "src/slaif_reservation/web/templates/web/token_create.html (stale claim only)",
    "src/slaif_reservation/web/templates/web/token_created.html (stale claim only; preserve secrecy/history/header logic)",
    "src/slaif_reservation/web/static/web/site.css (entry/identity only)",
    "src/slaif_reservation/web/static/web/brand/slaif-logo.svg (verified official packaged asset only)",
    "src/slaif_reservation/web/static/web/admin-identity.css",
    "src/slaif_reservation/web/templates/admin/ (structural identity/login/header only)",
    "src/slaif_reservation/web/templates/web/browsable_api.html",
    "src/slaif_reservation/web/templates/web/error.html",
    "src/slaif_reservation/config/admin_site.py",
    "src/slaif_reservation/config/apps.py (AdminConfig only)",
    "src/slaif_reservation/config/urls.py (entry/error wiring only)",
    "src/slaif_reservation/config/views.py (generic browser error handlers only)",
    "src/slaif_reservation/config/abuse.py (HTML429/503 identity/template only; counter behavior unchanged)",
    "src/slaif_reservation/config/settings/base.py (AdminConfig/template/renderer/error wiring only)",
    "src/slaif_reservation/api/renderers.py (existing Browsable API identity only)",
    "src/slaif_reservation/api/urls.py (display name only if necessary)",
    "src/slaif_reservation/accounts/admin.py (identity integration only; permissions/protection unchanged)",
    "tests/test_product_entry.py",
    "tests/browser/test_product_entry_browser.py",
    "tests/test_web_human_mvp.py (selected root/identity assertions only)",
    "tests/browser/test_human_mvp_browser.py (selected root/stale-token assertions only)",
    "tests/test_assets_admin.py (customsite/serviceaccount admission only)",
    "tests/test_api_schema.py (browser identity/HTML compatibility only)",
    "tests/test_abuse_controls.py (branded error assertions only)",
    "tests/test_abuse_http.py (root/identity fixture adaptation only)",
    "deploy/rehearse_https_boundary.sh (anonymous root/identity probes only if needed)",
    "QUICKSTART.md (entry routes only)",
    "docs/human-ui.md (public entry/identity only)",
    "docs/api-contract.md (browser identity only)",
    "docs/branding.md (packaged logo source/identity notes only)",
    "TESTING.md (new evidence only)",
    "oap/active",
    "oap/orders/036-a-public-product-entry.md",
    "oap/reports/036-a-public-product-entry.md",
    "oap/orders/036-b-admission-visual-closure.md",
    "oap/reports/036-b-admission-visual-closure.md"
  ],
  "forbidden_resources": [
    "full theme/override mechanism/all-field help/default policy/abuse counter/domain/API mutation features",
    "models/schema/migrations/dependencies/inventory/canonical governance/history/machinery changes",
    "permission/scope/privacy/CSRF/token/idempotency/protectedadmin weakening",
    "real exposure/production data/host/DNS/TLS/firewall/secrets/Neumann/legacy data",
    "valuable-checkout operational tests/foreign resource cleanup/reset/clean/stash/forcepush/auth copying"
  ],
  "requirements": [
    "SAR-011",
    "SAR-012",
    "SAR-013",
    "SAR-014",
    "SAR-015",
    "SAR-016",
    "SAR-017",
    "SAR-021",
    "SAR-025",
    "SAR-039",
    "SAR-040",
    "SAR-042",
    "SAR-043"
  ],
  "decision_class": "D0",
  "target_gate": "M-INTERNET-UX-PILOT development; final real Internet exposure remains human D2",
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "f8a8df265d4dd452969d4bee874045c8f8a8261f9c87c96ba4c049a7dddf320d",
    "PLAN.md": "b19219e2d727af5a9554e011ba45a786f1bb61f25c001011fc18006cae665d08"
  }
}
-->

# 036-b — Administration admission and visual-evidence closure

H: selected human requirements3/4 and intensive actual visual qualification;
latest human says use CODING. A: A-15/SAR-011/013/042/043 and all preserved
privacy/CSRF/role/protected-domain guarantees. E: actualPR72 implementation
0e2d45d6d62f50f2c5e930efe9fa4b5557f551ae/report e65785dcbd5e8681bcc967686e09136f010655f9 verified3PASS realremote/firstparent/report-only. Implementation all5 CI SUCCESS/full828passed469.04s; reportCI37251188908/OAP37251188780SUCCESS. STRATEGIC reviewed frozen diff and actually viewed all9 supplied images. C: D0/DHA_NONE. I: final fresh independent47row ICA remains later.

Same objective/branch/PR72/basee87497a1169bf4745489f699c28377bfbd2df717.
Retain all036-a acceptance. This is ONE collected required correction round:

1. Restore staff-only administration credential admission. Current custom
   form subclasses AuthenticationForm and its confirm_login_allowed checks
   only active/non-service, dropping the previous AdminAuthenticationForm
   staff guard. Actual owned Django/PG probe at literalimplementation:
   valid NON-STAFF member POST /admin/login/ returns302 and creates member
   session. Reject such credentials generically; preserve normal member-login
   access, valid staff admission, password/CSRF/shared-budget behavior and all
   model permission checks. Inherit/admin-confirm appropriately; no new rights.
2. Enforce active-human rule on EVERY admin access, not just login. Current
   SlaifAdminSite inherits has_permission(active&&staff), so existing staff
   service-account session opens /admin/ HTTP200 with admin model content.
   Root actual owned probe proves site.has_permission=True for that session.
   Override site permission to require active staff HUMAN; direct index/model
   list/change requests must deny/terminate service/inactive sessions even
   after an operator changes the account flag on a prior valid human session.
   Test real HTTP/browser flag-transition, nonstaff credential POST, valid
   staff/superuser and protected read-only model matrix. No blanket permission
   bypass, session impersonation privilege or domain mutation weakening.
   Private probe receipt: workorders/036-auth-probe.json in strategic home;
   selected boolean/status evidence only, never dump credential-bearing logs.
3. Complete the required10-image matrix:1440/390 for landing/member login/
   member Dashboard/admin login/admin index. Existing9 omit member-login390;
   Dashboards are completely empty. Seed a representative synthetic asset,
   effective policy and own reservation via existing domain services so actual
   populated Dashboard layout/navigation/timezone/privacy are exercised.
   Keep no one-time token/password-verifier/cookie/CSRF/rawHTML/HAR/traces or
   real private data in artifacts. Retain empty-state behavior tests too.
4. Scoped administration identity readability: actual screenshots show a tiny
   low-contrast official logo on default blue header/yellow title, unlike the
   public entry. Make logo/wordmark legible and modest header identity coherent
   with entry, and use a concise Administration heading (avoid repeated long
   "site administration" copy). Only identity/header/footer/logo CSS/templates,
   not full037form-help or038design/theme/override work. Preserve controls,
   focus/contrast/layout and permissions; check1440/390 screenshots afterwards.
5. Coding MUST actually open/view the PNG screenshots using an image-capable
   viewing tool, not merely inspect CSS, dimensions or text. Available runtime
   evidence around a's claim "Now viewing...all9lookgood" consists of CSS/source
   inspections; no image-view invocation established. Preserve immutable a
   report. New report accurately records image-view method/artifact paths and
   supersedes unsupported visual-complete claims; do not claim all criteria
   passed when the matrix or actual viewing is missing. If an image tool is
   absent/unsupported, identify the exact capability boundary with the smallest
   attempted diagnostic and report it; no invented visual evidence/waiver.
   STRATEGIC will actually view the final10 images again at frozen review.
6. Keep TESTING.md task-oriented. Replace newly appended "036-a...(evidence)"
   execution ledger/private port34421/receipt033-b/precommit counts with short
   reproducible public-entry/browser-identity test guidance and appropriate
   disposable-source warning. Round chronology/results belong in immutable
   OAP reports already retained. No need to rewrite other historical records.
7. Focused repaired auth/role/browser/visual cases first; final implementation
   full required CI/five checks plus normal report-head CI. Do not repeat an
   unchanged broad local suite. Short honest immutable report exacthead/SELF,
   actual negatives/images/failures/skips/limits and real remote verification.
   Previous report-head checks preserved (allSUCCESS), never cancelled/waived.

Strongest objection: branding must not substitute for an admission boundary;
old sessions and nonstaff valid credentials exposed precisely that weakness.
Prove both negative paths at real HTTP/browser boundaries, preserve staff
positive cases, role/CSRF/budgets, and explicit image evidence. No new feature,
source schema/dependency/inventory/canonical law/machinery or deployment/D2.
Every product test/management/qualification MUST run only owned SOURCE copies
and explicit owned PG17, including focused operational neighbors. Clear child
OAP_ROLE; private env dictionary only, no ignored/auth copies or secret output.
Root actual images/missing coverage and probe are evidence, not human release.

## Deferred human adjudication
- Decision: NONE
