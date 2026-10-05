<!-- OAP-META
{
  "id": "037-c",
  "round": "c",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "c4703beacf9c887d7ccfb59c89af4f389bdb57ed",
  "issue_number": 73,
  "branch": "codex/73-oap-037-a-form-guidance",
  "pr_mode": "AMEND",
  "previous_round": "037-b",
  "pr_number": 74,
  "allowed_paths": [
    "src/slaif_reservation/accounts/admin.py (guidance/widget/media presentation only)",
    "src/slaif_reservation/web/templates/admin/ (guidance association only, stock validation/submit/script behavior preserved)",
    "src/slaif_reservation/web/static/web/admin-form-guidance.js (new narrow local association helper only if needed)",
    "tests/test_form_guidance.py",
    "tests/browser/test_form_guidance_browser.py",
    "docs/ux/form-guidance-inventory.md",
    "docs/human-ui.md (guidance facts only)",
    "TESTING.md (remove superseded association exceptions)",
    "oap/active",
    "oap/orders/037-c-admin-guidance-closure.md",
    "oap/reports/037-c-admin-guidance-closure.md"
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

# 037-c — Final administration guidance closure

H: human5, required nearby accessible guidance. A: A-15/SAR-044;
preserve all037-a/b criteria/negative product laws. E: PR74 frozenb report
 dbb24c77b6a9dd2b6d12dd25e291531fe40d7931, impl
6bd5e1960ae4702e9996e0fd383548d218d2b744; actualverify3PASS/all5impl
(CI37292761571/OAP37292761690) and report(CI37293875468/OAP37293875510)
SUCCESS. ROOT viewed all22changedfinal images, hashesPASS;13others identical
revieweda (coding re-viewed identicaladminlogin, report's12reuse distinction).
I: freshfinalall47ICA remains. C: D0/DHA_NONE. SAMEbranch/issue73/PR74,
originalbasec4703beacf9c887d7ccfb59c89af4f389bdb57ed, AMEND.

One purpose: finish truthful, accessible administration guidance. Remaining
findings below are published037-b criteria3/6/7, not optional visual polish.
Do not repeat completed37a/bimplementation or rewrite immutable records.

## Acceptance
1. Correct remaining permission help. `_USER_FIELD_HELP.user_permissions`
   still says 'per-model administration and management access only';
   GroupAdmin.permissions says '(administration and management access)'.
   management_ui/auth.py authorizes management solely by active authenticated
   human staff status; no selected model permission is consulted there.
   Say model permissions govern per-model administration; management access
   comes from active human staff status. Clarify is_staff's extra model-
   permission requirement applies to ADMINISTRATION operations only. No
   permission/guard/feature changes. Pin rendered wording plus real staff
   without individual/group permissions can access management, while admin
   model operations retain model permission enforcement and protected models.
2. Correct new inventory contradiction: only legacy assets/views.py HTML
   views/templates are currently unrouted. Staff assets/api.py endpoints
   ARE routed: config.urls includes api.urls, which expands
   *asset_api_urls.urlpatterns; /api/v1/assets/ and UUIDdetail are live
   staff-session endpoints. Keep the existing bearer assets:read reserved
   limitation. Test real resolver or HTTP+current source correspondence;
   do NOT add/remove routes. Supersede reportb's erroneous blanket
   unreachable-REST claim in new report, preserve immutableb.
3. Required accessible associations must not be waived as 'impossible':
   b intentionally leaves usable_password RadioSelect and JS-created
   groups/user_permissions/permissions from/to lists with visible help but
   no association. Supply normal accessible group/legend/help relationships
   or matching stable helpIDs+aria-describedby for the ACTUAL rendered
   controls AFTER admin widgets initialize, including both radio choices
   and both sides of each permission/group selector. Minimal presentation
   templates/widgets/local script; no broad JS library or monkeypatch of
   framework source. Preserve all existing warning/validators/actions/
   fieldnames/media/keyboard behavior, password enable-disable and safe
   password status. Replace the unbound bypass assertions with substantive
   actual browser associations at1440/390; GET and invalidPOST keep help;
   every describedby target exists. Update inventory/TESTING assertions
   without misclaiming DOM coverage. No broader theme/branding override.
4. Focus only changed guidance/association tests+necessary neighbors in
   OWNED DISPOSABLE SOURCE/ownPG17, explicitURLs/settings/PYTHONPATH,
   childOAP_ROLE cleared; no valuable checkout/foreignPG16:5432/unknowncleanup.
   Final full suite through all5 exact implementationheadCI, requiredreport
   headCI; don't rerun unchanged localfull. Capture/view changed userchange,
   group and password pages at1440/390 after actual widget initialization;
   assert linkedhelp/keyboard/nooverflow. <=8PNGinputs per FRESH read-only
   CODING visual CLIcontext (qualifiedsameprofile0.160), concise prose only
   tomaincontext, never >16accumulatedimages. Reuse unchanged artifacts ONLY
   by byteidentity. Root actually reviews finalcaptures. Shortliteralhead/
   SELF report, exactcommands/results/failures/limits and supersessions;
   correctsamePRbodyCloses#73, report-only firstparent/push/actualverify,
   responseASCII OK ONLYafterremotepublication; codingnevermerges.

## Boundaries and recovery
Preserve models/migrations/domain/validators/services/admission/crypto/
scopes/wire/audit/idempotency/constraints/deps/runtime/architecture/PLAN/
projection/historicalordersreports/inventorybytes. No realInternet/DNS/TLS/
firewall/secrets/lab/privateprod/legacydata. Only presentation accuracy and
required existingaccessible associations. Oldb client finishedrc0 and all
WIPcommitted/published; sameobjective suffixc, notclient recovery replay.
Use actual boundedreadset once; edit/diagnose promptly. Wait CI outside model.
OwnedPG17 receipt workorders/033b-owned-test-db.json validateexactID/nonce;
parseprivateenvchilddict never source/eval/print. UniqueownDB/testsource.

Strongest objection: declaring guidance complete while inaccurate permission
help, active-route misclassification or inaccessible dynamic controls remain.
Repair these exact source/DOMfindings; no new product or D2decision.

## Deferred human adjudication
- Decision: NONE
