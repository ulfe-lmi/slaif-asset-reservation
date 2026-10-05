# Operator branding (optional, same image, no rebuild)

**Status:** implemented optional appearance mechanism (038-a, SAR-045).
Off by default; when enabled, overrides are read-only, operator-owned and
validated on use.

## What it changes

The packaged SLAIF identity remains the default on every browser surface.
When enabled, an operator directory may supply, per slot, at most one file
that replaces the corresponding default:

| Slot             | File names (one per slot)                     | Formats            | Max size  | Where it appears                                                                  |
|------------------|-----------------------------------------------|--------------------|-----------|-----------------------------------------------------------------------------------|
| `style.css`      | `style.css`                                   | CSS (strict UTF-8) | 256 KiB   | Loaded AFTER the built-in styles on public, member, staff and admin surfaces and the standalone error pages |
| `logo`           | `logo.svg` / `logo.png` / `logo.jpg` / `logo.webp` | inert image      | 256 KiB   | Site header (wide viewports), standalone error pages, administration header |
| `logo-compact`   | `logo-compact.svg` / `.png` / `.jpg` / `.webp` | inert image        | 256 KiB   | Site header and administration header on narrow viewports (≤ 480 px)              |
| `favicon`        | `favicon.svg` / `.png` / `.jpg` / `.webp`      | inert image        | 256 KiB   | Browser tab identity on all browser surfaces                                      |
| `hero`           | `hero.svg` / `.png` / `.jpg` / `.webp`         | inert image        | 256 KiB   | The public landing hero image                                                     |

Slots are fixed: there is no request-selected file name, no directory
listing and no way to address a path. Unknown files in the directory are
ignored. Two files for the same slot are ambiguous: that slot falls back
(closed failure), the other slots are unaffected.

The product title remains **SLAIF Asset Reservation** on all surfaces;
branding changes imagery and presentation only.

## Enabling it

The application reads the `SLAIF_BRANDING_DIR` environment variable
(default: unset = disabled). The shipped overlay adds it together with a
bounded read-only mount of the same `app` service — no rebuild, no new
service, network, port, database, proxy, privilege or runtime change:

```bash
install -d -m 755 deploy/branding
# add at most one file per slot (see the table above)

# production-shaped deployment (canonical):
docker compose -f compose.production.example.yaml \
    -f compose.branding.example.yaml up -d

# local evaluation:
docker compose -f compose.yaml -f compose.branding.example.yaml up -d
```

The overlay sets `SLAIF_BRANDING_DIR=/branding` and mounts
`./deploy/branding:/branding:ro`. The application runs as UID:GID
10001:10001 on a read-only rootfs; it cannot write to the mounted
directory, and the host directory is never replaced or created by the
application.

## Refresh and cache semantics

- **Server side:** each request re-stats the directory and the slot file;
  a change (content, size or mtime) is picked up on the next request.
  Editing or replacing a file therefore takes effect on the next page
  load; no container restart, no rebuild, no re-deploy is required (and
  restarting the same image is harmless).
- **Browser side:** `/branding/*` responses carry `Cache-Control:
  no-cache`, so the browser revalidates on every navigation; a plain page
  reload shows updated assets without a hard refresh.
- **Static defaults:** packaged assets (including the fallback logo) are
  served by the normal static pipeline and cache as usual.

## Fallback and failure behavior

- **Disabled, missing directory, empty directory, absent slot file, or
  invalid file:** that slot uses the packaged default — the override
  stylesheet link is simply not emitted, and image slots fall back to the
  packaged logo. One invalid asset never breaks login, administration,
  error pages or any other slot.
- **`/branding/*` endpoints are total:** they return the override bytes
  when the slot is currently valid and the packaged fallback otherwise
  (empty stylesheet for `style.css`, the packaged logo for image slots).
  They never return 404 or 500 for a slot, so a page that referenced an
  override at render time never shows a broken subresource even if the
  file disappears before the subresource request.
- Rejections are silent: no file path or content is logged or rendered in
  errors.

## Security boundaries

Overrides are **trusted operator inputs only** — they are never member
uploads and never derived from private data. The mechanism enforces:

- **Directory:** must be a real directory (a symlinked directory is
  refused). Only single-level, fixed slot file names are ever opened.
- **File access:** each candidate is `lstat`-checked (regular file, not a
  symlink, within the size cap), opened with `O_NOFOLLOW`, and re-checked
  with `fstat` on the open descriptor before a bounded read — a swap to a
  symlink, directory or special file (including FIFOs) between check and
  open is refused. A directory or FIFO named like a slot file is never
  opened.
- **Image formats:** PNG, JPEG and WebP are magic-byte verified; SVG must
  be a well-formed, **static, inert** document: only an allowlist of
  geometry/paint/text elements and attributes (plus `data-*`), the SVG
  namespace only, no DOCTYPE or comments, no scripts, no event handlers,
  no `<image>`, `<use>`, `<a>`, `<style>`, filters or animation, no
  `xlink:href`, no remote or `data:` references, and `url()` limited to
  local `#fragment` gradient/clip references. HTML, active SVG and
  unknown MIME content are rejected.
- **CSS:** strict UTF-8; `@import`, any `url(...)` resource, `data:` URIs
  and other active content (`javascript:`, `expression(`, `behavior:`,
  `<script`) are rejected.
- **Responses:** correct `Content-Type` per slot plus the global
  `X-Content-Type-Options: nosniff`; no server-side template or code
  execution is involved in serving an override.
- Existing routes, authentication, CSRF, owner scoping, audit, token and
  one-time-secret behavior are unchanged; the branding slots add no
  access rights and no state.

## Limits and troubleshooting

- Max 256 KiB per file; five slots (≤ 1.25 MiB total) per deployment.
- If a slot silently keeps its default, the file was rejected: check the
  name (exact slot + allowed extension), that only one file uses that
  slot, the format (the SVG rules above are strict), the size, and that
  it is a regular file (not a symlink or special file). No rejection
  detail is intentionally logged.
- The favicon should be square and small (16–64 px) for predictable tab
  rendering; the logo should be legible at ~32 px header height; the hero
  is rendered at 7.5 rem width with its own aspect ratio.

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
