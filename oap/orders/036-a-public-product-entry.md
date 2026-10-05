<!-- OAP-META
{
  "id": "036-a",
  "round": "a",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "e87497a1169bf4745489f699c28377bfbd2df717",
  "issue_number": 71,
  "branch": "codex/71-oap-036-a-public-product-entry",
  "pr_mode": "CREATE_OR_RESUME",
  "previous_round": null,
  "pr_number": null,
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
    "oap/reports/036-a-public-product-entry.md"
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

# 036-a — Public product entry and browser identity

H: human requirements3/4/public landing/Administration CTA/no visible framework
branding and current explicit instruction to use CODING. A: A-15/SAR-042/043,
preserved auth/privacy/CSRF/secrecy/permissions/domain. E: acceptedPR70 merged
e87497a1169bf4745489f699c28377bfbd2df717; finalimplf0497500fc889b5a223a5e5375f4ca2f9f633d8b/report43d574e56416dd9f26f55e6214592ff725584a7b all5exact-head checks SUCCESS/full805passed416.63s; root owned review107pass45.36s. I: fresh all47 ICA after milestone implementation. C: D0/DHA_NONE.

One purpose: public entry and structural product identity. Full form help and
complete SLAIF theme/operator overrides follow separately; do not implement them.

## Acceptance
1. Anonymous `/` returns a polished public landing: SLAIF Asset Reservation
   identity, concise shared-lab reservation purpose, obvious Login and exact
   Administration action entering `/admin/` login, locally packaged branding.
   No asset/user/reservation/audit/token identities, counts or private details.
   Seed private synthetic canaries and prove no disclosure in rendered output.
2. Sensible authenticated navigation: ordinary active human reaches Dashboard,
   staff Management, permitted administrators Administration. Keep named routes
   stable or deliberately update all selected callers/tests. No redirect loops.
   Preserve inactive/service-account rejection/termination on member routes;
   administration login must also reject service accounts (same human boundary),
   while normal active staff permissions remain exactly intact. Anonymous nav
   shows public actions, not the member workflow menu.
3. Proper custom AdminSite/configuration with product site_header/site_title/
   index_title/login/header/logo/breadcrumb identity. Keep autodiscovery/model
   registrations, permission checks and protected/read-only mutation boundaries.
   Do not hide branding with CSS or replace admin with weaker editing paths.
   Administration CTA is visible without guessing URL.
4. No browser-visible Django/default framework branding in title/body/header/
   breadcrumb/footer/accessible labels on landing, login, member/staff/admin
   and relevant error surfaces. Technical imports/classnames/docs may say Django.
   Existing DRF Browsable API currently renders Django REST framework in
   title/navbar: customize its renderer/template structurally, retaining the
   currently supported JSON/HTML renderers, controls, actions, auth and permissions.
   Never disable HTML to evade this requirement or enable new anonymous API/docs.
5. Generic branded400/403/404/500 browser errors, CSRF failure and existing
   login429/503; production traceback/reason/private query text never shown.
   Error rendering remains safe when DB is unavailable (no error-handler auth/
   model lookup dependency). Preserve API problem JSON/status/header/correlation
   contracts and privacy. No intentional change to health or abuse decisions.
6. Remove stale Work Order0006/API-not-enabled prose from three token templates,
   replacing with current scoped bearer API guidance. Preserve one-time token
   secrecy/no-store/private/no-referrer/history scrubbing, form validation,
   scope semantics/expiry/revocation; humanised scope choices belong037.
7. Modest coherent entry/admin identity layout using existing server rendering
   and CSS, clear CTA hierarchy, responsive around1440/390, keyboard/focus and
   readable labels/no unintended horizontal page overflow. Full visual system
   and override mechanism remain038. Official stable logo can be packaged from
   https://www.slaif.si/assets/slaif-logo.svg after inspection (no script/remote
   references); document source without inventing rights/funding claims. No
   hotlinked runtime-critical assets or new frontend/dependency framework.
8. Real app Playwright routes/role matrix: anonymous landing/Login/Administration
   action and login; member Dashboard; staff Management; admin index; inactive/
   service-account denials; actual Browsable API existing HTML and JSON controls;
   visible title/inner_text/labels exclude framework branding; no private leak,
   CSRF and role/protected-model negatives. Preserve original meaningful tests;
   adjust only changed entry/stale-text assertions, not owner/token boundaries.
   Capture privacy-safe screenshots at1440 and390 for landing/member login/admin
   login/admin index/member Dashboard; coding ACTUALLY views them and iterates
   poor hierarchy/spacing/overflow before final head. Save private artifact paths
   in report so STRATEGIC can ACTUALLY view all classes at review. No screenshots
   of one-time secrets/password verifiers, raw HTML/HAR/cookies/traces/private
   real data. Synthetic fixtures only. Do not declare visual quality from200s.
9. Short route/identity docs; changed Markdown links and image paths checked.
   No product-readiness claim, OAP ledger reintroduced or canonical governance
   rewrite. Focused tests while editing; full five standard exact implementation
   head CI (quality/test/security/container/oap-harness), and required report-head
   CI. Use full CI for the final frozen full suite, not repeated broad local runs
   without new failures. Short immutable report exacthead/SELF/actualresults/
   failures/limits/screenshots; PR closes issue71; coding NEVER merges.

## Execution resources and safety
Use ONLY OWNED DISPOSABLE SOURCE COPIES for EVERY product pytest/management
qualification command, including focused operational neighbor tests. Prior035
local neighbor commands ran from valuable working checkout despite isolation
instruction; STRATEGIC reran107 safely in owned source+DB. Do not repeat that
boundary failure. No `uv pytest` from REPO_ROOT and no operational/rehearsal
execution there. Lint/types/git publication may run in valuable checkout.

Existing owned PG17 receipt (validate exactID/nonce label BEFORE use):
/home/ubuntu/codex-supervision/slaif-asset-reservation/workorders/033b-owned-test-db.json
Read private environment_file using Python dict; never source/eval/print
credentials or copy auth/ignored.env. Clone tracked source into unique tmp
checkout; for uncommitted focused work copy only explicit in-scope files to
owned clone (never rawwhole checkout); for Docker tracked-snapshot scripts
commit implementation before qualification so new tracked files are present.
Clear OAP_ROLE from product-test child env; explicitly set ownPYTHONPATH and
settings/DB URL. /usr/lib/postgresql/17/bin, Chromium, Caddy2.11.6 and locked
repo .venv are installed. Different concurrent runs need unique owned database
names, project/nonce/private ports. Never foreignPG16:5432 or daemonprune/blanket
volume deletion. Existing rehearsal helpers have verified ownership/snapshot/
loopback guards; retain them. Capture private logs, output only redacted summaries.

Required readset once; concrete edit/small diagnostic within15min. Wait for
CI outside the model with existing helpers. No repeated unchanged full suites,
whole strategy books, old objectives or hypothetical extra acceptance. Stay
inside published scope; optional refinements separate. Fresh CODING context
per round, no model/profile/auth change or runtime machinery expansion.

## Strongest reason against the change
A public entry/administration link can accidentally disclose private state or
alter admission/protected mutations. Render a data-free public branch, preserve
server-side permission checks and require real role/CSRF/owner/error/renderer
negative evidence. Visual identity conveys product identity, never deployment
qualification or real exposure authorization.

## Deferred human adjudication
- Decision: NONE
