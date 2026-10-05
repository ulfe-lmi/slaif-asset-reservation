<!-- OAP-META
{
  "kind": "report",
  "id": "039-a",
  "order_path": "oap/orders/039-a-slaif-design.md",
  "order_sha256": "837528350dd05fbb7e56cb9c0f0ce1d73c5e53be54c09c2bc7698aa44056372f",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 77,
  "pr_number": 78,
  "branch": "codex/77-oap-039-a-slaif-design",
  "implementation_head": "01159efce5d91302e99a99a21509c440d0989048",
  "base_sha": "c55b57a3f0093fb31ea17ee4158c8c1051c8fc2d",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "01159efce5d91302e99a99a21509c440d0989048",
    "runs": [
      {
        "run_id": 37344926250,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "test": "success",
          "security": "success",
          "container": "success"
        }
      },
      {
        "run_id": 37344926002,
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

# SLAIF design and responsive qualification

Implementation head SHA: 01159efce5d91302e99a99a21509c440d0989048
Report publication commit: SELF

Result: COMPLETE for the bounded design objective; development only.
Execution: ROOT directly implemented and reviewed under the human instruction to
stop the coding clients and complete the task. No coding client was restarted.
This is not independent ICA or authorization for deployment.

## Result and acceptance evidence

- Shared SLAIF palette, local Roboto body/Roboto Condensed headings, spacious
  hierarchy, cards, forms, table regions, action hierarchy, footer and public
  landing composition. Current slaif.si/doc.slaif.si/edu.slaif.si/trainings were
  captured through real Chromium and visually inspected on 2026-10-05. Fonts
  are unmodified Google Fonts files pinned to the documented revision with
  original SIL OFL copyright/license notices packaged locally. No runtime font
  or logo hotlink; no unrelated HTML/framework copied.
- Responsive member/staff navigation uses a local script, visible Menu control,
  Enter/Escape behavior, focus restoration and one current page/location per
  navigation. Links remain available without script initialization. Public
  Login and Administration stay visible. Branded page titles and administration
  styling preserve native model permissions, protected records and form behavior.
- Native semantic tables use contained horizontal scrolling. Default and custom
  controls have readable contrast and visible focus. Long administration forms
  now constrain widths and stack field layouts before space becomes cramped;
  panels no longer conceal overflowing help. Dangerous actions are distinct.
  Operator stylesheet remains after all packaged/native responsive styles.
- New real-browser fixture matrix: 33 surfaces across anonymous/member/staff/
  administration, default and institutional themes, 1440/1024/768/390 widths,
  plus six open-navigation captures. Meaningful synthetic assets, reservations,
  policy, blackout, audit and nonsecret token rows are seeded. Checks cover
  anonymous/owner privacy, Administration navigation, heading/product identity,
  decoded images/fonts, existing help IDs, actual text contrast, focus controls,
  page overflow and help clipping. Native hidden/disabled controls are correctly
  distinguished; composite controls may transfer focus to an inner input.
- Final local matrix: `pytest --browser chromium tests/browser/test_slaif_design.py
  --no-cov -q --output test-results`: 8 passed in 95.71s, producing 270 PNGs.
  This capture source matches 0ea11bd4bd45db4dc301ffba7257a0803e5d69ae.
  The final implementation differs only by merging a duplicate navigation class
  attribute into `management-nav subnav`; neither stylesheet references subnav.
  Focused real-browser default390 after that correction: 1 passed in 13.51s.
  Full CI at the final literal implementation head reran all eight cases.
- ROOT actually viewed representative screenshots covering every surface, all
  four viewport classes and both themes: default1440/default1024 sets and
  custom768/custom390 sets, with final current-location navigation samples
  rechecked. Contact sheets preserve actual captured pixels; selected long
  administration forms were additionally inspected at top/middle/bottom.
  This is not a claim that 270 originals were individually opened. Artifacts
  are retained privately; screenshot manifest SHA-256:
  `4055cfee39c60b926308c87aaf832adafae8522bd562a08475b4e62b1b51d8b9`.
  Captures exclude password values/verifiers, token plaintext, cookies, CSRF
  values, traces and private data; the one-time token response is not visited.
- Documentation: visual system/tokens/font provenance in docs/ux/visual-design.md,
  branding reference and task-oriented TESTING guide. Five changed-document local
  links resolve. Ruff/format/type checks and diff whitespace checks passed.

## Iterations and negative evidence

Initial focused runs exposed required fixture timestamp, absent admin-login H1
and member-to-staff login transition errors; these were fixed before acceptance.
Visual/contrast review then corrected stacked public mobile navigation, custom
footer/Menu/Logout contrast, cramped token columns, chosen-permission headings,
clipped administration help/pickers, generic hover contrast and custom Delete/
Close controls. A geometry assertion was added after visible clipping passed the
original page-width assertion; no content is hidden to make tests pass.

Capture focus initially displaced sticky sidebars/table position; snapshots now
reset document/table scroll after focus checks. Batched native focus checks first
misclassified CSS-hidden sort links and composite widgets; focused failures led
to correct visibility/composite handling, preserving focus coverage. No backend
code was changed below those presentation/test boundaries.

Initial implementation CI 37341122152 and superseded implementation CI37344159904
were cancelled as obsolete after necessary corrections; neither is acceptance
for the final head. Intermediate passes and failures do not substitute final CI.

## Exact-head verification and limits

At 01159efce5d91302e99a99a21509c440d0989048:
CI37344926250 quality/test/security/container SUCCESS; OAP37344926002
 oap-harness SUCCESS. Full test job: **964 passed, 1 warning, 643.09s**.
Security includes pip-audit; container job builds/validates production shape.
Report-head checks were not yet observable when these immutable report bytes
were authored and remain mandatory before merge.

Scope is templates/static presentation, licensed local fonts, related browser
expectations/fixtures and documentation plus ordered orchestration files.
Application Python/domain/services/validators/permissions/admission/schema/
migrations/dependencies/runtime Docker/Compose/proxy/security/inventory bytes
are unchanged from the base. Current architecture/projection/law are unchanged.
All product tests used owned disposable source and PostgreSQL with explicit
settings/URLs, cleared role environment and exact resource cleanup. No valuable
configuration, foreign service, real data, DNS/TLS/firewall or public deployment
was touched.

Strongest reason against merge: styling can conceal controls or make a green
layout check misleading. Real screenshot iterations, clipping/contrast/focus
checks, preserved authority bytes and final full CI address the demonstrated
risks. Optional broader refinements are not new acceptance requirements.

The selected milestone still needs combined deployment/documentation qualification
and fresh isolated independent audit against all applicable canonical requirements
at an exact merged revision. No release or real Internet exposure is authorized.

DHA operation: NONE.
