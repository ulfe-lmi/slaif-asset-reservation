<!-- OAP-META
{
  "id": "039-a",
  "round": "a",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "c55b57a3f0093fb31ea17ee4158c8c1051c8fc2d",
  "issue_number": 77,
  "branch": "codex/77-oap-039-a-slaif-design",
  "pr_mode": "CREATE_OR_RESUME",
  "previous_round": null,
  "pr_number": null,
  "allowed_paths": [
    "src/slaif_reservation/web/static/web/ (design tokens, local assets/licensed fonts, bounded navigation only)",
    "src/slaif_reservation/web/templates/web/ (presentation only; privacy/CSRF/token history unchanged)",
    "src/slaif_reservation/web/templates/admin/ (presentation/identity only; protected editing unchanged)",
    "src/slaif_reservation/management_ui/templates/management_ui/ (presentation only)",
    "src/slaif_reservation/config/admin_site.py (display names/identity only, no admission changes)",
    "src/slaif_reservation/accounts/admin.py (labels/presentation only)",
    "src/slaif_reservation/assets/admin.py (labels/presentation only)",
    "src/slaif_reservation/web/forms.py (labels/help only if needed)",
    "src/slaif_reservation/management_ui/forms.py (labels/help only if needed)",
    "src/slaif_reservation/web/templatetags/presentation.py (optional display-only helper)",
    "tests/browser/test_slaif_design.py",
    "tests/browser/ (necessary semantic selector/layout expectations only)",
    "tests/test_product_entry.py (title/presentation expectations only)",
    "tests/test_form_guidance.py (label/presentation expectations only)",
    "tests/test_web_human_mvp.py (title/presentation expectations only)",
    "tests/test_management_ui.py (presentation expectations only)",
    "tests/fixtures/branding/ (accessible custom fixture styling only)",
    "docs/branding.md (design tokens/local asset provenance only)",
    "docs/ux/visual-design.md",
    "TESTING.md (task-oriented qualification)",
    "oap/active",
    "oap/orders/039-a-slaif-design.md",
    "oap/reports/039-a-slaif-design.md"
  ],
  "forbidden_resources": [
    "Domain/services/validators/permissions/admission/crypto/scopes/wire/API/idempotency/audit/exclusion behavior changes",
    "Models/schema/migrations/dependency constraints/lockfile/inventory/runtime/Docker/Compose/proxy/security changes",
    "Unrelated product features/OAP machinery/canonical law/architecture/projection/history rewrites",
    "Real deployment/public exposure/DNS/TLS/firewall/production data/secrets/privatelegacy/lab/Neumann resources",
    "Valuable-source product tests/unknowncleanup/reset/clean/stash/forcepush/auth copying"
  ],
  "requirements": [
    "SAR-005",
    "SAR-008",
    "SAR-014",
    "SAR-015",
    "SAR-020",
    "SAR-042",
    "SAR-043",
    "SAR-044",
    "SAR-045",
    "SAR-046"
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

# 039-a — SLAIF design and responsive qualification

H: human requirement7, visualqualitybar, Playwright acceptance; latest explicit
human asks coding clients shut down and ROOT complete the work itself.
A: A-15/SAR-046 and preserved042–045/browser/domain/security guarantees.
E: mergedPR76/issue75closed, mainc55b57a3f0093fb31ea17ee4158c8c1051c8fc2d.
Impl5026a10b7afc584ad1218e3ed7d5b1aa036b93a7/report63a6c377225af030af428b910a6b5a977a8e9735
all5exactchecksSUCCESS (impl37329478745/746;report37331232282/293),956fullpasses.
ROOT actually reviewed31default/customPNGimages; branding mechanism accepted.
LIVE20261005 Playwright reference captures reviewed for slaif.si/doc.slaif.si/
edu.slaif.si/trainings:cream251251249, darkteal224846, lime+blue,palebluehero,
Roboto body/RobotoCondensed headings. I: freshfull47-rowICA remainsmandatory.
C: D0/DHA_NONE. One purpose: coherent SLAIF application presentation.

## Acceptance
1. Build a coherent local self-contained SLAIF visual system from CURRENT
   references (actualscreenshots already observed, refresh if changed): colors,
   typography/headinghierarchy/spacing/pagewidth/nav/cards/buttons/forms/tables/
   status/footer/landing composition. CSS custom properties support accepted
   operator overrides. Do not copy unrelated site HTML/product assumptions or
   hotlink criticalassets. Local official/permissivelylicensed assets only with
   provenance and bundled license where needed; no license/rights invention.
2. Product landing explains purpose and obviousLogin/Administration. Clear
   member versus staff navigation, sensible narrow-screen design, consistent
   branded browser titles, clear primary/secondary/danger actions. Full admin
   experience shares palette/type/spacing/branding while native behavior/model
   permissions/read-only boundaries remain. No visibleDjango/frameworkbranding.
   Resolve only demonstrated presentation defects (e.g. clipped selectedvalue,
   inconsistent admin headings) and necessary existing criteria, no backendfixes.
3. Accessible readable contrast/focus/keyboard/labels/associatedhelp, responsive
   forms/tables, no horizontalPAGEoverflow at1440/1024/768/390. Tables may use
   clearly usable contained horizontal scrolling with semantics retained.
   Preserve all fieldvalidation/CSRF/owner/token/secrecy/history/audit/policy/
   exclusivity/protectedmodel guarantees. Do not hide meaningful controls/text
   to make tests pass. Custom CSS remains AFTER defaults, sameimage mechanism
   and invalidassetfallback unchanged.
4. Real Playwright with meaningfulsynthetic users/assets/policies/blackouts/
   owner+otherreservations/audit/tokens(nonsecretrows) covers:
   anonymous landing/userlogin/adminlogin; memberdashboard/assetlist/detail/
   availability/reserve/reservationlist+detail/profile/tokenlist+create;
   managementdashboard/policylist+detail+form/blackoutlist+detail+form/
   reservationmanagement/auditlist+detail/exportcontrols; adminindex/userlist+
   change/assetlist+change/relevantadminsurfaces. Allfourwidths1440/1024/768/390
   and DEFAULT+CUSTOMinstitutionaltheme. Functionalnav/role/privacy/CSRF/help/
   labels/actions/keyboard/nooverflow/noframework semantic assertions, not200only.
   Never screenshot plaintexttoken/password/verifier/cookie/CSRF/rawHTML/HAR/
   trace/private data. No brittlepixelCI snapshots unlessenvironmentstable.
5. ROOT actuallyopens/views representative screenshots acrossEVERYsurface,
   viewportclass andtheme, records artifacts/hashes/findings and iterates poor
   hierarchy/spacing/clipping/contrast/mobile composition beforefinalhead.
   No image/dimension/CSS-only inference or firstversion acceptance because
   tests pass. Coding clients staySHUTDOWN (human override supersedes earlier
   CLI-batch instructions); nativeROOTview_image available. Report actual
   visualmethods/provenance; milestoneindependentICA remainsseparate.
6. Professional task-oriented design/token/provenance docs andTESTING newmatrix
   guide; no workledger in productdocs. ChangedMarkdown links valid. Focused
   tests duringedits; fullstandardall5 at finalliteralimplementationhead and
   mandatoryreportheadCI, no unchangedlocalfullrepeat. CorrectactualPR Closes77.
   Immutableorder/report, literalhead/SELF, report-only firstparent/push/verify,
   no same-round mutation afterreport. ROOT owns conditionaldevelopmentmerge.

## Scope, resources and objection
Presentation only. No productfeature/security/domain/DB/runtime changes.
Every productpytest/management operation runs OWNED DISPOSABLE SOURCE with
explicitownedURLs/settings/PYTHONPATH/minenv/childROLEcleared. OwnPG17receipt
033b-owned-test-db.json exactID/nonce first, envparsedasdata never source/eval/
print; uniquedatabase andexactcleanup. No unknownDocker/tmux/process/resources,
valuableenv/privateexports/secret/auth/history copies. Requiredreadsetloaded;
concrete edit/diagnostic promptly. WaitCIoutside model withhelpers.

Strongest reason AGAINST change: attractive presentation can conceal controls,
reduce accessibility or accidentally weaken protected/secretflows. Preserve
businesscodebytes, exercise actualauth/forms andboth themes/four widths,
inspect real screenshots and requirefullcurrentchecks. No deploymentauthority.

## Deferred human adjudication
- Decision: NONE
