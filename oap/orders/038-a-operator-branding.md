<!-- OAP-META
{
  "id": "038-a",
  "round": "a",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "1afacf2448b40f3724a387ef536e4b73d6673a92",
  "issue_number": 75,
  "branch": "codex/75-oap-038-a-operator-branding",
  "pr_mode": "CREATE_OR_RESUME",
  "previous_round": null,
  "pr_number": null,
  "allowed_paths": [
    "src/slaif_reservation/web/branding.py (new bounded read-only appearance mechanism)",
    "src/slaif_reservation/web/templatetags/branding.py (new presentation helper if needed)",
    "src/slaif_reservation/config/settings/base.py (optional branding configuration only)",
    "src/slaif_reservation/config/urls.py (bounded appearance asset route only if needed)",
    "src/slaif_reservation/web/templates/web/ (branding slots and CSS ordering only)",
    "src/slaif_reservation/web/templates/admin/base_site.html (branding slots and CSS ordering only)",
    "src/slaif_reservation/web/static/web/site.css (branding image slot sizing only, no full redesign)",
    "src/slaif_reservation/web/static/web/admin-identity.css (branding sizing only)",
    "compose.branding.example.yaml (new optional read-only mount overlay; existing base topology unchanged)",
    "tests/test_branding.py",
    "tests/browser/test_branding_browser.py",
    "tests/fixtures/branding/ (safe synthetic images/CSS only)",
    "docs/branding.md",
    "INSTALL.md (optional branding procedure/pointer only)",
    "docs/README.md (branding navigation only)",
    "TESTING.md (task-oriented focused qualification only)",
    "oap/active",
    "oap/orders/038-a-operator-branding.md",
    "oap/reports/038-a-operator-branding.md"
  ],
  "forbidden_resources": [
    "models/schema/migrations/dependencies/inventory/domain/policy evaluator/source parsers/validators/service_values changes",
    "permission/admission/CSRF/token crypto/scopes/wire/API/idempotency/audit/exclusion weakening",
    "full theme/operator appearance overrides/extra product features/OAP machinery/canonical law/history rewrites",
    "real deployment/data/secrets/DNS/TLS/firewall/privatehost/lab/legacy resources",
    "valuable-source pytest/management qualification; unknown cleanup/reset/clean/stash/forcepush/auth copies"
  ],
  "requirements": [
    "SAR-014",
    "SAR-015",
    "SAR-020",
    "SAR-026",
    "SAR-033",
    "SAR-039",
    "SAR-042",
    "SAR-043",
    "SAR-045"
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

# 038-a — Operator branding without rebuilding the application

H: human6/theming acceptance example; human requires CODING for all future
implementation. A: A-15/SAR-045 and preserved security/privacy/deployment laws.
E: currentmain1afacf2448b40f3724a387ef536e4b73d6673a92, mergedPR74/issue73
closedcompleted; final37impl8aa66f66d820c33c5a9fe8200a18242592006d19/report
c8aa410027f8923cf91e403e395556a5a0bf9a13 actualverify3PASS/all5 implCI
37300284317/OAP37300284357 and reportCI37301536493/OAP37301536547SUCCESS.
Root actually reviewed12changedfinalscreens/23byteidenticalreviewedprior.
No openPRs, cleanmain before strategicpointerquiescence. I: final fresh
all47-row independentaudit remainsmandatory. C: D0/DHA_NONE.

One implementation purpose: safe operator-controlled CSS/logo/favicon/images
without source fork or application image rebuild. Refinement of prior
combinedtheme draft: full SLAIFdesign/4width allsurfacevisualqualification
is the following separate039objective; combinedfinalqualification+freshICA
040. Allhuman8requirements retained. This is not the full default redesign.

## Acceptance
1. Default image alone stays completely self-contained and functional.
   Add ONE simple bounded optional mechanism for read-only operator branding:
   CSS overrides, primary logo, secondary/compact logo where useful, practical
   favicon/browser identity and selected branding image (e.g. public hero).
   No source/template edit or application-image rebuild to use it. Operators
   may restart/reload the container using the SAME image; document exact
   refresh/cache semantics. Independent safe fallback for missing/invalid
   items; one invalid asset must not break login, admin, errors or other
   valid overrides. Keep product title SLAIF Asset Reservation.
2. Minimal operator-owned directory/configuration and OPTIONAL Compose mount
   example, not plugin/theme/template framework. Existing canonical files
   are compose.yaml (local evaluation) and
   compose.production.example.yaml (service). Current productionapp10001:10001,
   read_only rootfs, loopbackport, PG17private, 3workers*8threads preserved.
   Use compose.branding.example.yaml optionaloverlay (same service app):
   bounded read-only appearance-directory mount and narrowly named config;
   no host-wide mount, privileged mode, additional network/public port/DB/
   proxy service, Dockerfile/base Compose runtime change. Validate rendered
   overlay with BOTH supported basefiles using ownedsynthetic configuration.
   Do not include realenv/secrets or override existing Docker projects.
3. Define and enforce allowed assets/MIME/content/path/symlink/size/failure
   boundaries. Prefer fixed known slots/local inert image formats (packaged
   officialdefaultSVG can stay). No arbitrary request-selected file reads,
   traversal/encoded traversal/directory listings, symlink files or symlink
   directories, special files/unbounded reads, HTML/JS or activeSVG disguised
   as images/CSS, externalcriticalassets or remoteJavaScript mechanism.
   No server-side template/code execution. Overrides are trusted OPERATOR
   inputs, never member uploads or private-data-derived content. Correct
   response MIME/nosniff; defaultfallback/404/other chosen safe behavior is
   explicit and tested. No sensitive path/content in logs/errors. Use
   descriptor-safe reads if pathname races could escape the directory; real
   negative tests for whichever read/validation boundary is implemented.
4. CSS loads AFTER built-in styles, including admin's defaults, on public/
   member/staff/admin and relevant standalone browser errors. Primary/
   compact/favicon/image slots work consistently in current browser shell,
   admin and public landing; selected image actually visible (not unused
   config). Error rendering remains DB/session-free. Preserve original
   routes/authentication/CSRF/owner/audit/token/no-store/private/no-referrer/
   history/HTML+JSON/API/error behavior; don't weaken them for customization.
5. Actual unit/HTTP negative cases: disabled/missing/empty directory, absent
   asset, unreadable/malformed/wrongMIME/oversize input, path/symlink escape,
   specialfile/race/refusal where relevant, unsupportedHTML/JS/activeSVG,
   safe caching/refresh and per-slot fallback. Test real response bytes and
   exposed paths, not merely presence of settings/tags. No private fixture
   data/secret content in assertion failures/artifacts. Preserve existing
   productionsettings failclosed negative suite.
6. Real Playwright default + at least ONE meaningful institutional override
   fixture (different primary+compactlogo/favicon/image+CSS) at1440/390 for
   landing/memberlogin/adminlogin/memberdashboard+form/staffpage/adminindex.
   Assert actual successful assetrequests/selectedimagery/computedCSS/order,
   customCSSafterdefaults, safe invalid-overridefallback, labels/actions/
   keyboard/nooverflow/role/CSRF/privacy/noDjango visibletext. Actual Docker
   qualification on ownedtrackedSOURCEsnapshot: run SAMEbuiltimage default
   and with optionalread-onlybrandingmount; app remainsUID10001/read_only,
   cannotwrite mountedfiles, validassets/CSS servedandfallbackworks; validate
   productionoverlay topology and health. No valuable checkout/unknown
   teardown/real Internethost. This is NOT exhaustive039visual qualification.
7. Coding actually views/iterates every representative new/changed default/
   custom screenshot. The provider has a16image context ceiling: <=8PNG
   initialinputs per FRESH read-only CODING CLIcontext, prose-only tomain;
   qualified Codex0.160 sameqwen-neumann profile, ownedsource cwd,
   `codex --profile qwen-neumann exec --sandbox read-only --image <paths> --
   '<Read-only inspection, no tools or mutations>'`. No accumulated>16
   view_image maincontext and no model/profile/auth/configchanges. Actual
   images/method/hashes recorded privately, root independentlyviews. No
   pixel-perfectCI snapshots or dimension-only attractiveness claims.
8. docs/branding.md becomes concise operatorcontract: exactslots/config/RO
   mount procedure/sameimage/no-rebuild/cache/fallback/trust/size/MIMElimits.
   Preserve packagedofficiallogo source/provenance; INSTALL/docsindex clear
   optionalpointer, task-orientedTESTINGsuite; changedlink checks. No README
   historyledger/fullservice-productionclaim. Focused tests duringedits;
   fullstandard5checks at final literalimplementationhead, requiredreport
   headCI. Don't repeat unchanged localfull. Closes #75 inactualPR. Short
   report with criteria/actualcommands/heads/results/failures/limits and
   screenshot paths; report-only firstparent/SELF/push/actualverify; no further
   roundmutationafterreportpublication; codingnevermerges.

## Scope, negative guarantees, recovery
Only this optionalappearance mechanism and its real evidence/docs. No broad
SLAIFCSSdesign/font/framework/animation/newfeature, models/migrations/domain/
validators/policy/services/admission/abusecontrols/crypto/scopes/wire/audit/
constraints/dependencies/inventory/backupbehavior/canonicallaw/architecture/
projection/workflows/harness/immutablehistory changes. Genuine out-of-scope
finding is reported separately, not smuggled. No realdeployment/DNS/TLS/
firewall/secrets/privateprod/privatelegacy/lab/Neumann resources.

EVERY pytest/management qualification runs an OWNED DISPOSABLE SOURCE with
explicit ownURLs/settings/PYTHONPATH and childOAP_ROLE cleared. OwnedPG17
receipt workorders/033b-owned-test-db.json exactID/nonce check; privateenv
childdictnever source/eval/print, uniquetestDB. Docker tracked-onlysnapshot
AFTERcommit with ownernonce/IDs/ports and exactownedcleanup. No foreignPG16:
5432, valuableenv, unknownvolume down-v/prune/reset/clean/stash/forcepush/
authcopies. Launcher consumesnotification; no model-basedidlepoll. Required
readsetonce, concreteedit/diagnosticwithin15minutes. Waitcoding/CIoutside
model with helpers. Optionalrefinements separatelyrecorded.

Strongest reason AGAINST change: convenient customization becomes arbitrary
file exposure/code injection or invalidassets break authenticated/errors UI.
Mitigate one small inertallowlist/readonlyboundary/boundedsafe reads+fallback
and actual HTTP/browser/containernegativeevidence; no exposurepermission.

## Deferred human adjudication
- Decision: NONE
