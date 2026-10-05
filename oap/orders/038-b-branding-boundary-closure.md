<!-- OAP-META
{
  "id": "038-b",
  "round": "b",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "1afacf2448b40f3724a387ef536e4b73d6673a92",
  "issue_number": 75,
  "branch": "codex/75-oap-038-a-operator-branding",
  "pr_mode": "AMEND",
  "previous_round": "038-a",
  "pr_number": 76,
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
    "src/slaif_reservation/web/static/web/branding-fallback.js (optional narrow image-fallback helper only if chosen)",
    "src/slaif_reservation/web/branding_png.py (optional bounded inert image validation helper only if chosen)",
    "oap/orders/038-b-branding-boundary-closure.md",
    "oap/reports/038-b-branding-boundary-closure.md"
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

# 038-b — Close demonstrated branding boundary and evidence defects

H: human6/security/mandatorybrowser qualification. A: A-15/SAR-045 and
original038-a acceptance1/3/5/6/7/8, preservedprivacy/runtime/domainlaws.
E: actualPR76 report e3ec4eb12b3b75c9984df6d3dc538a7a580d0511 firstparent
beaf1ed7defe0c14c4a4abf5e4b29486b99b87b8; verify3PASS, all5implementationCI
37310388293/OAP37310388528 SUCCESS (full931passed500.39s), all5reportCI
37312481340/OAP37312481369 SUCCESS. STRATEGIC reviewed the full scoped diff
and ACTUALLY all28final hash-matchedPNGimages. Currentmainoriginalbase
1afacf2448b40f3724a387ef536e4b73d6673a92, sameissue75/branch/PR76 AMEND.
I: finalfreshall47ICA remains. C: D0/DHA_NONE.

One purpose: make the selected optionalbranding boundary actually safe and
qualified. These are source-demonstrated failures of publishedcriteria,
not optionalrefinements. Preserve immutable038-a records; no restart/replay.
Private source-owned diagnostic workorders/038-security-diagnostic.json at
beaf1ed reproduces all below without realdata/DB/privatehost/network access;
browser requests were intercepted+aborted BEFORE any externalcontact.

## Acceptance
1. Anchor filesystem access to verified directory descriptors (including
   relevant directory components), with no-follow relative file opens and
   non-blocking special-file handling. Current lstat(root) then pathopen
   O_NOFOLLOW protects only the LEAF: a real directory swapped to a symlink
   immediately before os.open serves validCSS bytes from OUTSIDE the root
   (actually reproduced). A regularslot swapped to a FIFO between lstat and
   open BLOCKS indefinitely (owned child killed after3s). No outside bytes,
   no blocked request/worker. Close all descriptors even on errors. Catch
   expected stat/open/fstat/read failures and bounded parse failures so
   single badasset leaves login/admin/standaloneerrors/otherassets intact.
   Injected EIO currently escapes OSError;1200nestedSVGg nodes currently
   escape RecursionError. Real interleaving regression tests (directory/
   ancestor/symlink/FIFO replacements; finite ownedchild timeout), not only
   staticpre-existing links or removalafterrender. HTTP/pages fallback tests
   for failed reads and bounded/deep parse; no sensitivepath/contentlogs.
2. Correct refresh/cache identity. Currentkey onlymtime+size; replacing a
   file/root while preserving those values can return stalevalidatedbytes.
   Use complete relevant inode/device/change-time/root identity and safe
   bounded reads OR remove the tinycache if simpler. Pin same-size,
   same-mtime atomic replacement and valid->invalid replacement; nextrequest
   must safely revalidate/refresh. Document the exactactual rule; don'tclaim
   arbitrary content-change detection frommtime/sizealone. No unbounded
   caching, no weakened directory/file checks on cache hits.
3. Fix actual content-gate bypasses. `_css_is_valid` accepts escaped @import
   and image-set("http://..." 1x); Chromium ACTUALLY issues both resource
   requests from acceptedCSS. `_svg_is_valid` accepts paintvalues with
   leading-space externalurl(), contrary to localfragment-only contract.
   Preserve practical operator CSS overriding (tokens/selectors/media/layout),
   use conservative bounded validation if needed, but don'tadvertise substring
   checks as resource prevention. Reject these executable resource constructs
   including escaped/normalized variants. Browser sensitivity: oldaccepted
   fixtures attempt requests (intercept+abort .invalid fixtures), fixedservice
   fallsback and issues none. SVG: enforce actualnamespace and boundeddepth/
   node/attribute/reference validation; no recursion/remote paint/data/script.
   No new dependency/parserframework/template execution/remoteJS mechanism.
4. Actual malformedimage fallback, not merely magic-prefix acceptance.
   Eight-byte PNG signature currentlypasses and is served asimage/png though
   no browser can decode it. Add meaningful boundedformat validation and/or
   a narrow deterministic browser fallback that covers malformed images for
   every advertisedformat/slot, including tabidentity. Normal PNG/SVGfixture
   assets remainusable; no badimage breaks a page/validotherassets. It is D0
   to narrow optionalunsupported image formats if this simplifies reliable
   boundedvalidation: document exactnewlimits, preserve primary/compact/
   favicon/selectedimage/coreCSS/no-rebuildmechanism and packagedofficialSVG.
   Never claim full image validity frommagic bytes. Assert actual image decode
   (naturalWidth/naturalHeight/complete or equivalent) and fallback in real
   browser, not juststatus200 or srctags. Cover truncated/invaliddata with a
   validprefix, namespaces/deepSVG, normalpositiveformats/slots.
5. Repair ownedDocker qualification safety INSIDE the existingtest only.
   `_run`/`_docker_available`/`_in_app_get` currentlyinherit ambientenvironment
   (including DOCKER_HOST/CONTEXT and product/OAPvariables); pin qualified
   LOCALUnixdaemon/minimal explicit childenvironment, clear conflicting
   contexts/auth/productenv/childOAP_ROLE. Do not copy authhomes.
   Actualfake-tool earlyBUILDFAILURE diagnostic shows finally invokes volume
   rm and image rm although NOTHING was created. Cleanup only successfully
   created, recorded ownedobjects by verifiedidentity/nonce/creation evidence;
   refuse colliding/foreignresources, never adopt or delete them. Preserve
   foreignsentinels on earlyfailure/interleavings and wholeDocker case.
   Reuse suitable existingqualified ownership primitives ratherthan invent
   another framework; allowedtest helpers only, no OAP/deploymachinerychanges.
   Exactnewhead trackedSOURCEsnapshot/sameimage default+ROmount/UIhealth/
   UID10001/prodreadonly/privateDB/loopbackproof, exactownedcleanup.
6. Close missing038-a browser evidence: bothdefault/custom reservation-form
   cases ONLYcapture/assert1440 thennavigateaway at390. Assert/capture/view
   the SAME form at390 too, with validreadable labels/associatedhelp/actions/
   keyboard/nooverflow and CSSafterdefaults. Seed meaningful owner/staff
   state for the representative dashboards ratherthan onlyzeros/emptylists;
   publiclanding remainsdata-free. Fix the demonstrated customfixture
   white-text-on-gold button contrast with fixtureCSS only (no defaultredesign);
   preserve existingmeaningful assert paths. Actualdefault/custom/error/
   malformedfallbackimages and decoding checks, no secret/token/rawHTML/HAR/
   trace captures. FullSLAIFdesign is still039, no broadappearancechanges.
7. Reconcile conciseoperatorcontract withactualsecurity/cache/format/fallback/
   directorymechanism; preserve officialpackagedlogo provenance. Clarify
   read_onlyROOTFS is production-shaped; localcompose only guarantees the
   branding mount read-only. No workorder/statusledger in normalbranding
   introduction. Update task-orientedTESTING/docs/INSTALL pointer onlywhere
   factschange, checklinks. Newreport explicitlysupersedes038-a's unsafe
   'descriptor-safe', 'allboundaries tested', resourcepreventing/invalidfallback
   and complete390form claims; don'trewriteit. Allrequiredoriginalcriteria
   remain. Optionalskip-linkoverlay/adminfullstyling stay039, notnewbackendwork.
8. EVERY producttest/management command from OWNED DISPOSABLE SOURCE, explicit
   ownedURLs/settings/PYTHONPATH/childOAP_ROLEcleared. Privateenv parsed into
   Pythonchilddict, NEVERsource/eval/print (038-a's sourced/tmp/runenvrecipe is
   NOT acceptable as proof of this rule). OwnPG17receipt exactID/nonce first;
   uniqueownDB. Focusedtests duringedits; fullstandardall5 at final literalhead
   and requiredreport-headCI. No unchangedlocalfullrepeat. Commit BEFORE new
   Dockertracked-snapshotqualification. Coding actuallyview allchangedimages
   in <=8PNGperFRESHqualifiedROCLIcontext (provider16cap); rootreviewsactual
   finalbytes. Short truthfulreport/literalhead/SELF/failures/limits/commands/
   screenshots, correctsamePRCloses75, report-onlyfirstparent/push/actualverify,
   no mutationafterreport; codingnevermerges. WaitCIoutside model, notpaidpoll.

## Scope and recovery
Same originalappearance-only paths, plus two optionalnarrowhelperpaths in
metadata if chosen. No appmodels/migrations/reservation/domain/policy/abuse/
permission/admission/crypto/scopes/wire/audit/deps/inventory/backup/runtime/
Dockerfile/baseCompose/workflow/law/projection/immutablehistory changes.
Only optionalbranding defects and its safety/evidence. No realInternet/DNS/
TLS/firewall/secrets/privateprod/privatelegacy/lab/Neumannresources.
Never valuable-source producttests/foreignPG16:5432/unknownDockercleanup/
prune/down-v/reset/clean/stash/forcepush/authcopy. Concreteedit/experiment
promptly; requiredreadset once; no hypothetical additionalacceptance.

Strongest objection: a trustedstyling feature still breaches its own file/
input/fallback boundary and unsafequalification can touch foreignresources.
These deterministic findings must be fixed and sensitivity-tested; no new
human meaning or exposure decision is needed.

## Deferred human adjudication
- Decision: NONE
