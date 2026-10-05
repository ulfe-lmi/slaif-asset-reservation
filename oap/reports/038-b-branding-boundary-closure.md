<!-- OAP-META
{
  "kind": "report",
  "id": "038-b",
  "order_path": "oap/orders/038-b-branding-boundary-closure.md",
  "order_sha256": "72ddfa0d89739c568f11adc6c8b3bfbab4340135bb98af20b69dc2a69253774a",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 75,
  "pr_number": 76,
  "branch": "codex/75-oap-038-a-operator-branding",
  "implementation_head": "5026a10b7afc584ad1218e3ed7d5b1aa036b93a7",
  "base_sha": "1afacf2448b40f3724a387ef536e4b73d6673a92",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "5026a10b7afc584ad1218e3ed7d5b1aa036b93a7",
    "runs": [
      {
        "run_id": 37329478745,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "test": "success",
          "security": "success",
          "container": "success"
        }
      },
      {
        "run_id": 37329478746,
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

# 038-b — Branding boundary closure

Implementation head SHA: 5026a10b7afc584ad1218e3ed7d5b1aa036b93a7
Report publication commit: SELF

Result: COMPLETE for the eight ordered criteria, development only.

Execution provenance: the configured CLI failed on malformed tool-call JSON.
A fresh native CODING context qualified read-only and began two source files;
the human then explicitly instructed: "please shut it down and do this task
yourself". ROOT stopped the coding clients, preserved those edits, and completed
implementation, verification and screenshot review directly. This is not an
independent audit. The selected milestone still requires fresh independent ICA.
The immutable order and 038-a report were not changed.

## Acceptance and evidence

1. Filesystem reads walk no-follow directory descriptors, then open fixed files
   relative to the verified directory with O_NOFOLLOW/O_NONBLOCK. Regular-file
   size and identity are checked before and after bounded reads; expected I/O
   failures safely select defaults. Real directory/ancestor/FIFO replacement
   regressions, including an owned finite-time child, cover the reproduced
   escapes/blocking. Error/login pages stay functional after read failure.
2. Removed the operator-asset cache. Same-size/same-mtime replacement and
   valid-to-invalid changes revalidate on the next request. Packaged immutable
   fallback bytes alone remain cached; public responses require revalidation.
3. Conservative CSS validation refuses escapes, imports, resource functions and
   malformed comments without quadratic comment scanning. Browser sensitivity
   tests prove escaped import and image-set cause requests in an intercepted
   negative control, then cause none through the fixed service. SVG validation
   checks namespaces and bounded iterative depth/node/attribute/reference rules,
   refusing remote paint, processing instructions and active content.
4. Raster overrides are deliberately narrowed to non-interlaced eight-bit
   RGB/RGBA PNG: complete chunk framing/CRCs, bounded dimensions/pixels, bounded
   zlib stream and scanline checks. SVG remains supported under its inert subset.
   JPEG/WebP, ancillary PNG chunks and other PNG modes fall back. Magic-only,
   truncated/trailing PNG and deep/malformed SVG regressions pass; actual
   browser image decoding and favicon/logo fallback are asserted.
5. Docker qualification uses a minimal explicit environment/local Unix daemon,
   nonce labels, creation receipts and exact object identities. It refuses name
   collisions/adoption and deletes only recorded owned objects, including partial
   creations. Early build failure invokes no unowned deletion. A separately owned
   disposable sentinel survives primary cleanup. The same built production image
   runs default and branded: UID10001, read-only filesystem/mount, private PG17,
   loopback app publication, health/readiness and both-base overlay rendering.
6. Browser cases now cover reservation forms at1440/390 in both themes, populated
   owner/staff dashboards, actual decoded imagery and independent malformed-slot
   fallback. Custom fixture buttons use dark text on gold. Existing actions,
   help, keyboard access, overflow and privacy assertions remain.
7. Operator docs describe actual uncached refresh, descriptor reads, supported
   format bounds and public-asset trust. They distinguish production read-only
   root filesystem from the read-only branding mount in both examples. Packaged
   official-logo provenance is retained. Changed Markdown links: zero broken.
8. All product checks ran in owned disposable SOURCE copies, explicit settings/
   PYTHONPATH/unique owned PG17 databases, minimal child environments, OAP_ROLE
   cleared; private synthetic env parsed as data, never sourced/evaluated/printed.
   No real deployment/data/secrets/DNS/TLS/firewall/lab/Neumann work. Standard
   full checks passed at the exact implementation head; report-head checks were
   not observed at authoring. PR76 retains Closes #75; no coding client merged.

## Verification

- `pytest tests/test_branding.py -k 'not docker_production' --no-cov -q`:
  65 passed, 1 deselected, 3.51s, owned source at final application bytes.
- `pytest --browser chromium tests/browser/test_branding_browser.py --no-cov -q`:
  16 passed, 15.29s, 31 privacy-safe captures. ROOT actually opened all31 using
  view_image; manifest/hashes and PNGs are private under
  workorders/038b-root-screenshots. No pixel-only inference or CI snapshots.
- Production-overlay Docker case: 1 passed,121.04s at exact7ba6ec5cfce239e79eefb2e2530905f5882bb482.
  Later commits alter only the test's partial-resource capture/import environment;
  application bytes remain identical. Final exact-head CI reran the Docker case.
- FIFO child focused test after explicit import-path fix:1 passed,0.81s.
- ruff check/format, mypy (134 source files), git diff --check: clean.
- Final CI37329478745:956 passed,1 intentional pre-existing warning,529.19s;
  quality/security/container success. OAP37329478746:success. All five exact-head
  checks observed. Local full suite was not unnecessarily repeated.

## Failures, supersessions and limits

Initial mobile browser assertions used an exact label omitting its colon:
2 failed/14 passed; corrected semantic selector, then16 passed. CI at0eded5a
failed only the FIFO child import setup:1 failed/955 passed. Explicit source
PYTHONPATH/settings fixed it, followed by the final956-pass full CI run.

This report supersedes 038-a's incorrect claims of directory-race protection,
complete content/fallback boundaries and390 reservation-form coverage. Its
31-image final set includes the missing mobile forms and malformed fallback;
038-a's image-count wording is not reused. Historical evidence is preserved.

The full SLAIF design, four-width all-surface default/custom qualification,
combined Internet-shaped qualification and fresh independent audit remain
subsequent selected work. No production maturity or real exposure is claimed.
Decision: NONE; no CRITICAL entries or domain/schema/dependency/base-topology
changes. Independent ICA must assess this changed runtime meaning.
