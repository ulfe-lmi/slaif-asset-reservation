<!-- OAP-META
{
  "id": "037-b",
  "round": "b",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "c4703beacf9c887d7ccfb59c89af4f389bdb57ed",
  "issue_number": 73,
  "branch": "codex/73-oap-037-a-form-guidance",
  "pr_mode": "AMEND",
  "previous_round": "037-a",
  "pr_number": 74,
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
    "oap/orders/037-b-guidance-accuracy-closure.md",
    "oap/reports/037-b-guidance-accuracy-closure.md"
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

# 037-b — Guidance accuracy and required browser coverage

H: human requirement5 and mandatory Playwright acceptance; human requires CODING.
A: A-15/SAR-044; preserve all 037-a requirements and product boundaries.
E: frozen PR74 report1998ad1f09971cd5804cb50966a6ccf01c265fd2,
implementationcc8dbbbd6c2d9f5784198670ea78e5247eb09caf; actual report-only
verification3PASS and all5 current-headchecks SUCCESS (CI37267040040,
OAP37267040031). STRATEGIC read the source diff and ACTUALLY viewed all26
hash-matched images. Coding's own session confirms29actualview_imagecalls,
26distinctfiles. That evidence is valid; no repeated visual-tool diagnosis.
I: final fresh all47-row independent audit remains mandatory. C: D0/DHA_NONE.

One purpose: close the demonstrated inaccurate/missing form guidance and
required browser evidence. Same branch/issue73/PR74, originalbasec4703beacf9c887d7ccfb59c89af4f389bdb57ed.
Do not rewrite immutable037-a order/report or restart its work.

## Acceptance
1. Correct DST occurrence help in BOTH member reservation and staff blackout
   forms, inventory and docs. `interpret_local_wall_time` REJECTS ambiguous
   times with omitted fold; Automatic has NO ambiguous-time default. First/
   second choose the two occurrences only when a clock time repeats; a
   nonexistent spring-forward time is always rejected. Preserve parser,
   choice wirevalues and validation. Test actual invalid ambiguous Automatic
   POST retains help; explicit occurrences and nonexistent-time negatives.
2. Correct asset/admin help against actual source: only MACHINE can parent
   children; machine itself has no parent. Asset.timezone is metadata, while
   member availability uses the account's timezone, not asset.timezone.
   Asset.slug is a displayed/searchable stable label; current detail/API routes
   use UUIDs, so do not falsely say changing slug breaks those URLs. Policy
   names are NOT unique (only active target constraints exist), so remove the
   invented name uniqueness rule. Review remaining changed help for the same
   source contradictions; correct only demonstrated inaccurate guidance.
3. Admin user help must not promise member self-service password change:
   `/profile/` has only display_name/timezone, no member password-change route.
   Explain administrator-set passwords/current real paths. Individual/group
   permissions control per-model administration; management entry follows
   active human staff status, not arbitrary permission selections. Superuser
   does not bypass the active-human/staff admission gate. Keep concise exact
   effects; no authorization changes.
4. Complete actual inherited admin inventory/rendered guidance, not AST/base
   fields only. `last_login` and `date_joined` ARE editable, both currently
   have empty help, contrary to the inventory's read-only claim. Explain their
   meanings/units and correction impact without making them read-only.
   `AdminPasswordChangeForm.__init__` dynamically adds `usable_password` for
   users with a usable password; the screenshot exposes generic Single
   Sign-On/LDAP wording despite no such configured authentication. Customize
   nearby help for this HIGH-IMPACT enabled/disabled choice: disabling removes
   the current password and prevents password login; no alternate human-login
   backend is supplied. Preserve the built-in warning, validators/hashing/
   conditional field/action/permissions; add actual GET/invalid-POST and
   enable/disable behavior tests. No new password feature.
5. Fix presentation helper `human_duration`: 1441 currently renders '1 day',
   1501 '1 day, 1 hour', 2890 '2 days'; all lose the remaining minute(s).
   Preserve remainder minutes for every nonzero remainder, including days.
   Cover actual policy detail with non-round minutes and helper boundaries;
   no stored-unit/evaluator changes. Fresh initialized default has minimum1,
   not30. Use actual initializer for default-policy presentation evidence or
   identify30-minute guidance fixture as custom, never the fresh default.
6. Close required037-a acceptance6 browser coverage: current admin login/user
   add/change/password/group/asset add/change browser cases ONLY use1440,
   with no390 admin assertions/captures. Cover both1440/390, actually visible
   nearby help and actual control relationships. The current nearby helper
   returns true if no container exists and only checks count/text, not visible
   or associated controls; make it substantive. Shared server assertions must
   bind each help target to its own control, not any aria on the page.
   Actual captured long forms should include below-fold new guidance and
   actions (full-page or selected scroll captures), safe synthetic fixtures,
   no credential/verifier/token/CSRF/cookie/HAR/trace screenshots.
   Coding actually view_image all new/changed representative images, record
   paths/hashes; STRATEGIC reviews final images. Do not begin full038 theme.
7. Reconcile inventory/docs with these fixes. Legacy assets/templates is NOT
   routed by current config.urls; classify unreachable legacy controls instead
   of inventing current field coverage or adding routes. Legacy read-only
   field help constants in AssetAdminForm are skipped because those fields
   are excluded; do not claim rendered field-help when absent (readonly
   context may be explained safely). docs/api-contract currently claims scope
   effect lines on token-created/list, where templates only show labels;
   state the actual distinction. Keep guides task-oriented. No unrelated
   historical rewrites. Check changed docs relative links.
8. Focused tests in owned DISPOSABLE SOURCE only, then full standard suite
   via all5 exact final implementation-head CI; required report-head CI stays.
   Do not repeat unchanged local fullsuite. Preserve prior negative assertions,
   role/CSRF/owner/token/privacy/protectedmodel guards. Short honest report
   names literal implementationhead/SELF, actual tests/failures/unrun evidence;
   initial037-a development had browser selector failures before repair, so
   supersede its overbroad 'No test failures at either head' interpretation
   with precise final-head versus development-attempt results (do not amend it).
   Immutable report-only commit, actualverify/push, Closes #73; coding never
   merges. No new CI machinery or runtime/schema/dependency/product behavior.

## Scope, negative paths and recovery
Same bounded presentation paths/forbidden resources as037-a. Preserve all
validators/clean/service_values/permissions/password admission/hash behavior,
reservation policy/exclusivity/audit/token/wire/DB constraints. No canonical
law/architecture/projection/runtime/dependency/schema edits. No extra feature.
Any genuine out-of-scope defect is reported for separate strategic decision.
Private diagnostic `workorders/037-guidance-diagnostic.json` records real
owned-clone reproduction atcc8dbbb (no DB connection): lost remainder,
ambiguous Automatic rejection, GPU-parent rejection, editable date fields.
Source/screenshot evidence above is sufficient to edit promptly, not re-plan.

Every pytest/management command runs an OWNED DISPOSABLE SOURCE clone with
explicit own PG17 URLs/PYTHONPATH/settings, childOAP_ROLE cleared. Existing
ownedDB receipt workorders/033b-owned-test-db.json: validate exact containerID/
nonce; parse private environment into childdict, never source/eval/print.
Never valuable-source product tests/foreignPG16:5432/unknowncleanup/reset/
clean/stash/forcepush/authcopy/realInternet/DNS/TLS/firewall/secrets/lab/data.
Use focused experiments, wait CI through existing helpers outside model.

Strongest reason not to merge: helpful-looking guidance contradicts behavior,
misleads operators about authentication, or claims absent field/mobile coverage.
Resolve these source-demonstrated contradictions and rendered evidence; no
new deployment authority or broader UI-polish objective is needed.

## Deferred human adjudication
- Decision: NONE
