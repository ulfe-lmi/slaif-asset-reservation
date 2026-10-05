<!-- OAP-META
{
 "kind": "report",
 "id": "038-a",
 "order_path": "oap/orders/038-a-operator-branding.md",
 "order_sha256": "ac01f0e55bab896aed9b402f4a566fcda19e3d508aacbebeef6acff10bdf680a",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 75,
 "pr_number": 76,
 "branch": "codex/75-oap-038-a-operator-branding",
 "implementation_head": "beaf1ed7defe0c14c4a4abf5e4b29486b99b87b8",
 "base_sha": "1afacf2448b40f3724a387ef536e4b73d6673a92",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "beaf1ed7defe0c14c4a4abf5e4b29486b99b87b8",
  "runs": [
   {
    "run_id": 37310388293,
    "workflow": "CI",
    "jobs": {
     "quality": "success",
     "test": "success",
     "security": "success",
     "container": "success"
    }
   },
   {
    "run_id": 37310388528,
    "workflow": "oap",
    "jobs": {
     "oap-harness": "success"
    }
   }
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 038-a — Operator branding without rebuilding the application

Implementation head SHA: beaf1ed7defe0c14c4a4abf5e4b29486b99b87b8
Report publication commit: SELF

Result: COMPLETE for all eight 038-a acceptance items. PR #76 (issue #75),
CREATE_OR_RESUME created the PR, branch
codex/75-oap-038-a-operator-branding, base
1afacf2448b40f3724a387ef536e4b73d6673a92 (= origin/main at order start).
One optional appearance mechanism plus its real evidence/docs: 27 files vs
base (+2346/-29), every one inside the order allowed_paths; zero changes
under models/, migrations/, services, policy evaluator, parsers, validators,
admission, crypto, API/wire contracts, inventory or dependencies. The
implementation was refined by in-place amend before publication (screenshot
iterations touched three test/fixture files only, no app-facing bytes); the
final head beaf1ed7defe0c14c4a4abf5e4b29486b99b87b8 is the only head observed
by CI, and the scratch working tree used for local runs was verified
byte-identical to it (non-cache files). Coding never merged; the PR stays
open for strategic/human acceptance.

## 1. Default self-contained; one bounded optional mechanism (acceptance 1)

- Default image alone is unchanged and functional: branding is OFF unless
  the operator sets SLAIF_BRANDING_DIR; with it unset every /branding/*
  route serves the packaged fallback and all pages render exactly as before
  (default browser suite green; no template diff beyond adding slots and
  the post-default CSS link).
- ONE bounded mechanism, no source/template edit or image rebuild to use
  it: src/slaif_reservation/web/branding.py (new) implements five FIXED
  slots (style.css, logo, logo-compact, favicon, hero) read from
  SLAIF_BRANDING_DIR (env read in config/settings/base.py; setting
  BRANDING_DIR). Operators restart/reload the SAME image with the env var
  and an optional read-only mount (item 2).
- Read path is descriptor-safe: lstat (regular file only, refuses
  symlinks/special files) -> open O_RDONLY|O_NOFOLLOW -> fstat (re-check)
  -> bounded read, 256 KiB per-slot cap. Format gates: PNG/JPEG/WebP
  magic-byte validation; strict inert-SVG allowlist (tag/attribute
  whitelist; rejects script, image/use/a/style, remote refs, data: URIs,
  event handlers, url() other than local #fragment); CSS must be UTF-8 and
  rejects @import, url(), data: and active content.
- Total behavior on the five /branding/* routes: valid override bytes OR
  the packaged fallback for that slot — never 404/500. Per-slot
  independent fallback: one missing/invalid asset degrades only its own
  slot (unit + browser fallback tests). Cache/refresh semantics are
  explicit and documented: Cache-Control: no-cache on all /branding/*
  responses, correct Content-Type + X-Content-Type-Options: nosniff,
  per-slot mtime cache invalidation (docs/branding.md).
- Product title stays "SLAIF Asset Reservation" (asserted in the server
  suite on landing, login, admin and error renders).

## 2. Operator directory + optional Compose overlay (acceptance 2)

- Minimal operator-owned configuration: one directory with up to five
  known slot files (docs/branding.md contract); no plugin/theme/template
  framework.
- compose.branding.example.yaml (new): an OPTIONAL overlay on the existing
  app service only — env SLAIF_BRANDING_DIR=/branding plus
  ./deploy/branding:/branding:ro. Same image, no rebuild, no
  Dockerfile/base Compose runtime change, no new service/port/network/DB/
  proxy, no privileged mode, no host-wide mount; does not override
  existing Docker projects; no real env/secrets included.
- Rendered overlay validated with owned synthetic configuration against
  BOTH supported base files (compose.yaml and
  compose.production.example.yaml) in the Docker qualification (item 6):
  same built image default -> branded; app remains UID 10001 with
  read_only rootfs; mounted file write refused; valid assets/CSS served;
  fallback works; production topology and health asserted.

## 3. Enforced asset boundaries (acceptance 3)

- Fixed known slots only: /branding/<slot> for exactly five slot names;
  no request-selected filenames, no path components, no traversal or
  encoded traversal, no directory listings.
- Symlink files/directories and special files refused (lstat + O_NOFOLLOW
  + fstat re-check); bounded 256 KiB reads; descriptor-safe read path
  guards pathname races; no server-side template/code execution.
- No HTML/JS or active SVG disguised as images/CSS (allowlist above); no
  external critical assets or remote JavaScript mechanism (CSS url() only
  local #fragment; SVG remote/data: rejected). Packaged official default
  SVGs stay as the fallback.
- Correct response MIME and nosniff on every /branding/* response; the
  chosen safe behavior (packaged fallback, never 404/500 on the five
  routes) is explicit and tested; no sensitive path/content in logs or
  errors (failures are generic). Overrides are trusted OPERATOR inputs,
  never member uploads or private-data-derived content. Real negative
  tests exist for every implemented read/validation boundary (item 5).

## 4. CSS ordering, consistency, standalone errors (acceptance 4)

- Override CSS loads AFTER built-in styles on public/member/staff/admin
  AND after admin defaults (admin/base_site.html), including standalone
  browser error pages (web/error.html). Error rendering remains
  DB/session-free (tested).
- Slots work consistently in the current browser shell, admin and public
  landing; the selected hero image is actually rendered (successful asset
  requests + computed CSS asserted, not unused config). Compact logo
  switch at <=480px (site.css/admin-identity.css slot sizing only).
- Original routes/authentication/CSRF/owner/audit/token/no-store/
  private/no-referrer/history/HTML+JSON/API/error behavior preserved;
  unchanged negatives stay green in the full suite (CI test job at the
  exact head).

## 5. Unit/HTTP negative cases (acceptance 5)

- tests/test_branding.py (new): 44 tests — 43 non-docker unit/HTTP +
  1 Docker qualification. Coverage: disabled/missing/empty directory,
  absent asset, unreadable/malformed/wrong-MIME/oversize input, path and
  encoded-path traversal, symlink file and symlink directory escape,
  special file, race/refusal on the read path, unsupported HTML/JS and
  active-SVG variants (script, use, image, a, style, data:, remote ref,
  event handler, url() forms), safe caching/refresh (no-cache header,
  mtime invalidation), per-slot fallback, total route behavior, real
  response bytes (override vs fallback content asserted), MIME/nosniff,
  unchanged title and error behavior. No private fixture data or secret
  content in assertions. Existing production settings fail-closed
  negative suite preserved and green.
- Local run at the exact final bytes (scratch, owned PG17, child
  OAP_ROLE cleared, unique owned DB per run):
  source /tmp/sar038a-runenv.sh && cd /tmp/sar038a-scratch-966879331 &&
  uv run pytest --ds=slaif_reservation.config.settings.test
  tests/test_branding.py -k "not docker" -p no:cacheprovider --no-cov -q
  -> 43 passed. Nothing was run from the valuable repo root.

## 6. Playwright default + override; real Docker qualification (acceptance 6)

- tests/browser/test_branding_browser.py (new): 13 tests (--browser
  chromium) — default identity and one meaningful institutional override
  (different primary + compact logo, favicon, hero image and CSS) at
  1440/390 across landing, member login, admin login, member dashboard +
  form, staff page and admin index. Asserts actual successful asset
  requests (status + bytes), selected imagery and computed CSS,
  stylesheet order (custom CSS after defaults, including admin defaults),
  compact switch, safe invalid-override fallback, labels/actions/keyboard
  access/no horizontal overflow/roles/CSRF/privacy/no Django-visible
  text.
- Local run at the exact final bytes: same runenv, uv run pytest
  --ds=slaif_reservation.config.settings.test --browser chromium
  tests/browser/test_branding_browser.py -p no:cacheprovider --no-cov -q
  -> 13 passed.
- Real Docker qualification (test_docker_production_overlay_qualification):
  owned tracked SOURCE snapshot via git archive from the owned scratch,
  SAME built image run default and with the optional read-only branding
  mount; overlay topology validated against both base compose files with
  owned synthetic configuration; app stays UID 10001/read_only, cannot
  write mounted files, valid assets/CSS served, fallback works, health
  and topology asserted, exact owned cleanup. Local: 1 passed (55.99s) at
  the final fixture bytes. No valuable checkout, no real Internet host.
  (The archived commit is the scratch's pre-amend local commit whose tree
  is identical to the final head for all app-facing content; the two
  differ in three test-only files. Fixtures were read from the working
  tree, byte-identical to the final head.)

## 7. Actual screenshot viewing with iteration (acceptance 7)

- Method: 4 FRESH read-only codex CLI contexts
  (codex --profile qwen-neumann exec --sandbox read-only --image
  <paths> -- 'Read-only inspection, no tools or mutations'), owned source
  cwd (scratch), <=8 PNG initial inputs each, prose-only to main; no
  accumulated >16 view_image in main context; no model/profile/auth/
  config changes. All 30 unique PNGs were actually opened and visually
  inspected: default set (13), institutional override set (13), invalid-
  compact fallback (4, incl. re-capture). No forced pixel-perfect CI
  snapshots; no dimension-only attractiveness claims. Root will view the
  final images independently.
- Iterations (all fixture/test-only; no product-behavior change, folded
  into the final head by amend): (a) the custom fixture style.css was a
  partial theme (dark background without text tokens) and a reviewer
  flagged illegible login text; the fixture now sets a coherent token set
  (--background/--text/--muted/--border/--accent/--surface) and was
  re-reviewed; (b) the 1440 landing capture showed the focused skip link
  covering the header logo because the keyboard check ran before the
  capture; the test was re-sequenced (keyboard check after capture,
  blur() before the mobile capture) and re-reviewed clean.
- Out-of-scope findings reported to strategy, NOT fixed in 038-a:
  (1) the focused .skip-link overlays the site header at narrow widths
  (pre-existing focus style, all themes); (2) admin-area internal
  controls keep Django structural styling (e.g. blue button) — operator
  CSS loads after admin defaults and CAN retheme them if provided.
- Non-defect: in the fallback capture the valid primary slot shows the
  fixture logo at 1440 while the invalid compact slot falls back to the
  packaged logo at 390 (as designed and asserted).
- Private receipt (NOT in Git):
  /home/ubuntu/codex-supervision/slaif-asset-reservation/workorders/038a-
  screenshot-review.log (sha256 of every reviewed PNG, appended per
  batch) and 038a-screenshot-review-method.md (method + iterations).
  Final reviewed set (last recorded hash per file):

| File | SHA-256 |
|---|---|
| branding-default-landing-1440.png | 71fe9443562b2df4e53343025d2a92e47e69d4adc2208a0e6a30fa9b7f8a3e3b |
| branding-default-landing-390.png | 9e275f3d5c3473b02d1af4d916ab056ad75b8bb1ad06ee2d3d323de772e2f54c |
| branding-default-member-login-1440.png | db2de236f9d864ceb06d582a5ae549f90e406c8ca4cef16ba59fa9178bd62b1d |
| branding-default-member-login-390.png | c5c005f1fa0e1664659968ee76f005eff1984f9a9cab7c1e4e9efe4e3da5e189 |
| branding-default-admin-login-1440.png | 3a3ebdeec32f7ecd2976c332228c7c7909360ff6c98112b73bc910b82263895a |
| branding-default-admin-login-390.png | 7323a6434764b4e37a5e648476c63cab40a4ba02b3e62aa65f02c76b39e779f6 |
| branding-default-member-dashboard-1440.png | 9301d761c97cebf67ff65671f6e4a1e8b242ca8c77ca46493460e98c4c9039d9 |
| branding-default-member-dashboard-390.png | 816898146249b292bd05bec60902a1a220a32f779ac641cb2e51d4283748fbdc |
| branding-default-member-form-1440.png | 4395f5e81e92506ab8a3f5c3325fd2e6c19b3f47c6c9e79b4ac0e650da0c1372 |
| branding-default-staff-1440.png | fd29fb8e8bee7cc7b11d7b2fdcd1d336de048ea296023989e234871df4d42fa7 |
| branding-default-staff-390.png | 03a701a026846ae36d9d478f30d25e7d69b686981ea139558d27c51db248ef2f |
| branding-default-admin-index-1440.png | 6d2ccf3411c49b14bc64b2533a64c6514dfccc2a778010f99320d59f42cbccf1 |
| branding-default-admin-index-390.png | ba4cc2360b04f7b3daec8b580573ba13121d11ef918b700a954e4af89b43c259 |
| branding-custom-landing-1440.png | fd35b38e49c8cc68ac8f93422f2a5eb9f9cf9230ee0e0a1e6dc4f68c80225385 |
| branding-custom-landing-390.png | 13918d02978c26e9561c32a58baf2502521006cd281ad5b73aa41c3c9a80bd76 |
| branding-custom-member-login-1440.png | abe207d82da95e58cb6a53f62af535c4578915432d79384ba7b10e4f9e094d68 |
| branding-custom-member-login-390.png | 9ca8b9081bf11b3d336177662c0e6cfbafd745f0930640c6b250c2bdf65d1851 |
| branding-custom-admin-login-1440.png | da16739837e494f3b8a6320646c425d84cf00627d6312c156470889a0a150450 |
| branding-custom-admin-login-390.png | af6b6ccfbf59e73222c6c480abae9a0021193f79c90f96bed0613f6079bfdeda |
| branding-custom-member-dashboard-1440.png | 21172c98b4955d24a8b57289533094c81bd35b5cd3f8a1c47a229cfda1df5edb |
| branding-custom-member-dashboard-390.png | c4a0ab48fff986ffe16e95497be1d705daa01a6638225f0a6c7462b339dcae87 |
| branding-custom-member-form-1440.png | 8fd9ec869c13b1ae21457f65c48b2261934497a4c3eaa7ee721be90ee93a3058 |
| branding-custom-staff-1440.png | 8736856d0db6e5ef408f9668be4265b5e2b846078970d7c7543f7d15c713bebc |
| branding-custom-staff-390.png | b55e31c41fd54cb45b54c965b081569d6627420601497137c5f2468e416ba4c0 |
| branding-custom-admin-index-1440.png | 276bbccd09a8825ff28c071e719d4e3a9fb9a40a4740b346446b8d7090382166 |
| branding-custom-admin-index-390.png | 9df54025ac00f175d9e0cce2017b5b4a582cee33e6d7f3b9ebd93d6393aa80c1 |
| branding-fallback-compact-1440.png | abe207d82da95e58cb6a53f62af535c4578915432d79384ba7b10e4f9e094d68 |
| branding-fallback-compact-390.png | b61c2392de8e379a289dfd7d1fe1cefdaad96cb68314d04bd8e828f5225accf7 |

Synthetic fixtures only — no token, password, verifier, CSRF, cookie, raw
HTML, trace or private data in any capture.

## 8. Docs, CI and publication (acceptance 8)

- docs/branding.md is the concise operator contract: exact slots,
  SLAIF_BRANDING_DIR, read-only mount procedure, same-image/no-rebuild,
  cache/refresh semantics, per-slot fallback, trust model (operator
  input, never member upload), 256 KiB size limit, allowed MIME/inert-
  format rules, packaged official logo provenance preserved. INSTALL.md
  carries the optional pointer, docs/README.md the navigation entry,
  TESTING.md task-oriented guidance for the new suites; changed link
  checks pass. No README history ledger, no full service-production
  claim.
- Focused tests were run during edits; the full standard 5 checks ran at
  the final literal implementation head beaf1ed7defe0c14c4a4abf5e4b29486b99b87b8:
  CI run 37310388293 — quality success (20s), test success (9m44s),
  security success (17s), container success (30s); oap run
  37310388528 — oap-harness success (39s). All five checks passed at the
  exact head; no missing/skipped/cancelled check. The exact-head test job
  is the full-suite coverage for beaf1ed; the unchanged local full suite
  was NOT repeated, per the order.
- Quality gates clean at the final bytes: ruff check ., ruff format
  --check . and mypy src (strict, 133 source files) all clean.
- Report-head CI: NOT YET OBSERVED AT AUTHORING; its outcome goes to the
  private execution receipt, never to this immutable report.
- PR #76 for issue #75 (body ends Closes #75); coding never merges.

## Failures, uncertainties, limits

- No test failures at the final head. The only iterations were two
  fixture/test-only changes (custom fixture token set; browser landing
  test re-sequencing) folded into the final head by amend; CI observed
  only the final head.
- Local Docker qualification built the app snapshot from the scratch's
  committed tree (pre-amend commit d010d520887ac5ef7e319d59bd644b859f5660d7),
  which is byte-identical to the final head for all app-facing content
  (the two commits differ in three test-only files); fixture bytes came
  from the scratch working tree, verified byte-identical to the final
  head. The exact-head full-suite and container coverage is the CI
  evidence above.
- Two genuine out-of-scope findings were NOT fixed and are reported for
  strategy: focused .skip-link overlays the site header at narrow widths
  (pre-existing, all themes); admin internal controls keep Django
  structural styling (operator CSS can retheme, loads after admin
  defaults).
- This report claims no strategic acceptance, no production/exposure
  change, no DHA candidates. No credentials, verifiers, peppers, cookies,
  CSRF values, tokens or private data appear in this report or in any
  captured artifact. Decision: NONE stands.
