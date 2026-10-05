# Branding

**Status:** packaged identity defaults for the human browser surfaces.

## Packaged logo

- File: `src/slaif_reservation/web/static/web/brand/slaif-logo.svg`
- Source: <https://www.slaif.si/assets/slaif-logo.svg>
- Fetched: 2026-10-05
- SHA-256: `3f810f1ef7fb327daf938a5302fe432e88be6a9df3d29c1b53da063cbd4d9b29`
- Inspection: the SVG source was inspected before packaging; it contains no
  scripts, external or remote references, or embedded raster payloads — only
  vector identity-mark geometry.

The file is served as a local static asset (WhiteNoise in production); no
browser surface hotlinks the logo at runtime. This repository asserts no
rights, license, or funding claims for the mark; its use is limited to
identifying the SLAIF Asset Reservation product.

## Browser identity rules

- Browser-visible surfaces (public landing, login, member and staff areas,
  administration, Browsable API, generic and rate-limit error pages) show the
  SLAIF Asset Reservation identity and never framework branding. Technical
  imports, class names, and dependency metadata may still name the framework.
- The administration site is a product `AdminSite` (site title, header, index
  title, login form, logo, footer, breadcrumbs) configured through
  `AdminConfig`; model registrations, permission checks, CSRF, and
  protected/read-only editing boundaries are unchanged.
- Operator appearance overrides (full theme mechanism, alternate images)
  remain deferred work; this file documents the packaged defaults only.
