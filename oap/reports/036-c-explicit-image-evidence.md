<!-- OAP-META
{
 "kind": "report",
 "id": "036-c",
 "order_path": "oap/orders/036-c-explicit-image-evidence.md",
 "order_sha256": "081aa548d26e11fa64fae2449cddbcb9c5119a2dcee431f4700f507a06defbe3",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 71,
 "pr_number": 72,
 "branch": "codex/71-oap-036-a-public-product-entry",
 "implementation_head": "269a083dd01bb1458f2a947245a5f6a22c652cc0",
 "previous_implementation_head": "69e26338c921d96f45f3037bbc142cb4cce12643",
 "base_sha": "e87497a1169bf4745489f699c28377bfbd2df717",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "269a083dd01bb1458f2a947245a5f6a22c652cc0",
  "runs": [
   {
    "run_id": 37257312256,
    "workflow": "CI",
    "jobs": {
     "quality": "success",
     "test": "success",
     "security": "success",
     "container": "success"
    }
   },
   {
    "run_id": 37257312192,
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

# 036-c — Explicit image-input evidence

Implementation head SHA: 269a083dd01bb1458f2a947245a5f6a22c652cc0
Report publication commit: SELF

Result: COMPLETE for all four 036-c acceptance items. Evidence-only
correction round: NO product changes, NO optional visual refinements, NO new
product runs. PR #72 (issue #71), AMEND mode, same objective, same branch,
same base e87497a1169bf4745489f699c28377bfbd2df717. All 036-a/036-b
acceptance is retained; the 036-a and 036-b immutable reports are preserved
byte-identically.

## 1. Actual image inspection — this evidence begins here

Method (per order H/E): the qualified Codex 0.160 client (profile
qwen-neumann, model qwen3.8-27b, reasoning xhigh) received ALL 10 existing
private 036-b PNGs as actual initial image attachments via CLI `--image`
arguments with the `--` delimiter (not textual filenames). The standalone
read-only qualification at the same profile proved real image input
(landing: correct visual heading/background/teal CTA/three cards;
admin-login-390: header/empty fields/theme control/button). No
profile/model/auth files were changed. The coding model of this launch
actually visually inspected each of the 10 attached bitmaps in its input
context before finalizing the observations below. No other image tool was
invoked by coding this round and no unavailable tool is claimed; root has
separately actually viewed all 10 via view_image per the order. No
observation below is inferred from CSS, PNG dimensions or report prose.

Supersession: the 036-a visual claim ("all 9 look good") and the 036-b claim
("opened and inspected with the agent's image viewing tool") lacked
invocation evidence and are hereby superseded as unsupported prior coding
visual-inspection claims. Actual coding image-input evidence begins with
THIS 036-c image-input context. Both prior reports remain immutable and are
not rewritten.

## 2. Image identities (private root home; NOT copied to Git)

Root: /home/ubuntu/codex-supervision/slaif-asset-reservation/workorders/036b-screenshots/

| File | SHA-256 |
|---|---|
| landing-1440.png | 0a3167f9126467c64f35abfd6a6baf6cffe2e83037b4064653658d5deae44ce4 |
| landing-390.png | 425030f5d309ab81fe00b77529e5ffd8c4d968504431b757f43d95adfa48c8b2 |
| member-login-1440.png | bf571a9e51d9fe84534b63612ddf3ef4860c5e144675ae0085d36de9fc9d9ff1 |
| member-login-390.png | 1cc978a8fdfaf8ffa2f859e4c03cd493946b185968e6f3bb4705c1cb3e8e9215 |
| member-dashboard-1440.png | 79a101810c44be56c74367a3a4fd1ae345fbc6668ba57c05e5c84b2d35e41922 |
| member-dashboard-390.png | 34500e20fc2d6bc09087f53394b68f47d3984eaa9033058ad772248fcbba1212 |
| admin-login-1440.png | 49cdd662299e094457127684eeb79eb9a571768b012f13f9037501a6ee94081d |
| admin-login-390.png | d49395735ec8261bbedfe8ace03e1dbb2df541e20290766ad9e9fe2058f2c64c |
| admin-index-1440.png | af0575db055b76a14415e4883c7c1a1222781cfc8c7216af4574a5a2330530ce |
| admin-index-390.png | cb5e4567ed4a4c98d5179f0280724a39c09d043a4ff453af55ca6fc7677ad8e5 |

All 10 verified PNG 8-bit/color RGB, non-interlaced (1440x900 for the 1440
surfaces, 390x844 for the 390 surfaces).

## 3. Per-image observations (hierarchy / logo-CTA / nav-form / readability-overflow)

| Image | Observation |
|---|---|
| landing-1440.png | White header: brand + "Log in" text link (keyboard focus ring visible) + outlined "Administration" button. Centered hero: SLAIF color logo, large "SLAIF Asset Reservation" H1, two-line gray support copy, CTA pair (solid teal "Log in" primary + outlined "Administration"), then three white feature cards (Find the asset / Check availability / Keep track). Clear top-down hierarchy; strong CTA contrast; no private data; no overflow. |
| landing-390.png | Header actions wrap to a second line under the brand; heading wraps to two lines; support copy four lines; CTAs stack vertically near full width; "Find the asset" card fully visible, remaining cards below the fold. No horizontal overflow; readable; tap targets retained. |
| member-login-1440.png | Left-aligned "Log in" H1 with "Use the account created by an administrator. Self-registration is not available."; labeled Email/Password fields with full-width inputs; solid teal submit. Clear hierarchy; visible associated labels; no framework branding; no overflow. |
| member-login-390.png | Header wraps (brand line, then Log in / Administration line); form stacks full width; note wraps to two lines; submit below the fields. No overflow; readable. |
| member-dashboard-1440.png | Two-tier header: brand + nav (Dashboard, Assets, My reservations, API tokens, Profile) + solid Logout; "Times shown in Europe/Ljubljana." bar below. H1 Dashboard; Active reservation "Entry GPU" 2026-10-05 03:32 - 04:32; Next upcoming reservations bullet "Entry GPU, 2026-10-05 05:02"; Browse assets / View all my reservations links. Clear hierarchy and navigation; local-time display with zone banner; synthetic data only (no purpose/free text); no overflow. |
| member-dashboard-390.png | Nav wraps to two lines with Logout; time banner under the header; all sections stack; bullet text wraps. No overflow; readable. |
| admin-login-1440.png | Centered administration card: steel-blue header with SLAIF logo on a white chip + "SLAIF Asset Reservation administration" + theme toggle; labeled Email/Password fields; centered "Log in" button; "SLAIF Asset Reservation" footer link. No Django administration branding; usable form; no overflow. |
| admin-login-390.png | Same card at content width; header title wraps to two lines; fields full width; submit button renders "LOG IN" (uppercase) vs "Log in" at 1440 on the same page — minor label-casing inconsistency (reported, NOT implemented this round). No overflow; readable. |
| admin-index-1440.png | Full-width steel-blue header: logo chip + "SLAIF Asset Reservation administration"; small-caps "WELCOME, ENTRY-STAFF@EXAMPLE.COM." + VIEW SITE / CHANGE PASSWORD / LOG OUT + theme toggle (signed-in operator's own synthetic identity, not third-party data). H1 "Administration"; grouped nav ACCOUNTS / ASSETS / AUDIT / AUTHENTICATION AND AUTHORIZATION / RESERVATIONS with per-row View/Add/Change actions; "Recent actions -> My actions -> None available" panel; footer identity line. No "Django site administration" text; no overflow. |
| admin-index-390.png | Header title and welcome line wrap to two lines; nav groups stack full width with identical actions; capture ends inside the RESERVATIONS group (Recent actions panel below the fold at this viewport). No overflow; readable. |

Cross-surface: no framework/Django branding on any of the five surfaces;
synthetic fixtures only (Entry GPU, entry-staff@example.com, 2026-10-05
times); no token, password, verifier, CSRF, cookie, raw HTML, trace or
private data in any capture.

## 4. Scope and byte identity

- Measured `git diff --name-only 69e26338c921d96f45f3037bbc142cb4cce12643
  269a083dd01bb1458f2a947245a5f6a22c652cc0`: exactly oap/active,
  oap/orders/036-c-explicit-image-evidence.md and
  oap/reports/036-b-admission-visual-closure.md. Zero product/source/
  runtime/test byte differences; source and normal docs are byte-identical
  to the 036-b implementation head; a/b reports are committed and clean in
  the working tree.
- The committed order bytes match the strategy-published order
  byte-for-byte (SHA-256 081aa548d26e11fa64fae2449cddbcb9c5119a2dcee431f4700f507a06defbe3).
- Under that measured complete source/runtime/test identity, 036-b product
  evidence is REUSED without rerun (focused 17+63+5+12 passed; full suite
  835 passed, 1 warning in 452.72 s at 69e2633; the 10 privacy-safe
  screenshots were produced at that head). No unchanged broad local runs
  this round (evidence-only order).

## 5. CI at exact implementation head 269a083 (observed before authoring)

- CI run 37257312256: quality success, test success (835 passed, 1 warning
  in 460.38 s), security success, container success. oap run 37257312192:
  oap-harness success. No missing/skipped/cancelled check among the five
  exact-head checks.
- Report-head CI: NOT YET OBSERVED AT AUTHORING; its outcome goes to the
  private execution receipt, never to this immutable report.

## Failures, uncertainties, limits

- One minor visual inconsistency observed and REPORTED, not implemented:
  the administration login submit button reads "Log in" at 1440 but "LOG IN"
  (uppercase) at 390 on the same page. Deferred to strategy / the 038
  visual scope.
- Model-level visual inspection of the attached bitmaps; no pixel
  measurement tooling used; the independent root view_image review of all 10
  is the separate check. This is not the 038 full visual system, not ICA,
  and not a release or visual-acceptance claim.
- Decision: NONE stands; no DHA candidates. No credentials, verifiers,
  peppers, cookies, CSRF values, tokens or private data appear in this
  report or any captured artifact.
