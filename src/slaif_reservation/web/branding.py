"""Bounded, read-only operator appearance overrides (SAR-045).

Optional by default: when ``settings.BRANDING_DIR`` is unset, or a slot file
is missing or invalid, the packaged defaults stand and the page is
unchanged. One invalid asset can never break another slot or any page:
every slot is discovered and validated independently, fail closed.

Security boundary
-----------------
* Only fixed slot names under the configured directory are ever read; there
  is no request-selected file name, so traversal cannot reach a path.
* The directory itself must be a real (non-symlink) directory. Every slot
  file is checked with ``lstat`` (regular file, not a symlink, within the
  size cap) and opened with ``O_NOFOLLOW``, then ``fstat``-checked on the
  open descriptor, so a swap to a symlink or special file between check and
  open is refused.
* Image slots accept only local inert formats (static SVG with a strict
  element/attribute allowlist, PNG, JPEG, WebP) with magic-byte
  verification; HTML, scripts, remote references, active SVG, data URIs and
  unknown MIME content are rejected.
* The CSS slot must be strict UTF-8 and must not contain imports, ``url()``
  resources, data URIs or other active content.
* Responses carry the correct MIME type with the global
  ``X-Content-Type-Options: nosniff`` header and ``Cache-Control: no-cache``
  so the browser revalidates on every load (see docs/branding.md for the
  exact refresh semantics).
* Overrides are trusted operator inputs only; they are never member
  uploads, never derived from private data, and no sensitive path or
  content is logged or rendered in errors.

The ``/branding/`` endpoints are total: they serve the override bytes when
the slot is currently valid and the packaged fallback otherwise (empty
stylesheet for the CSS slot, the packaged logo for image slots), so a page
never references a broken subresource even if a file disappears between
render and request.
"""

from __future__ import annotations

import os
import re
import stat
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.http import HttpRequest, HttpResponse

STYLE_CSS = "style.css"
IMAGE_SLOTS = ("logo", "logo-compact", "favicon", "hero")
IMAGE_EXTENSIONS = (".svg", ".png", ".jpg", ".jpeg", ".webp")

MAX_CSS_BYTES = 256 * 1024
MAX_IMAGE_BYTES = 256 * 1024

_CONTENT_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}

SLOT_URLS = {
    STYLE_CSS: "/branding/style.css",
    "logo": "/branding/logo",
    "logo-compact": "/branding/logo-compact",
    "favicon": "/branding/favicon",
    "hero": "/branding/hero",
}

DEFAULT_BRAND_STATIC = "web/brand/slaif-logo.svg"
_DEFAULT_BRAND_FILE = (
    Path(__file__).resolve().parent / "static" / "web" / "brand" / "slaif-logo.svg"
)

# --- content validation -----------------------------------------------------

_CSS_ACTIVE_MARKERS = (
    "@import",
    "url(",
    "data:",
    "javascript:",
    "vbscript:",
    "expression(",
    "behavior:",
    "-moz-binding",
    "<script",
)


def _css_is_valid(data: bytes) -> bool:
    """Strict UTF-8, no imports/resource loads/data URIs or active content."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    lowered = text.lower()
    return all(marker not in lowered for marker in _CSS_ACTIVE_MARKERS)


_SVG_NS = "http://www.w3.org/2000/svg"
_SVG_ALLOWED_TAGS = frozenset(
    {
        "svg",
        "g",
        "rect",
        "circle",
        "ellipse",
        "line",
        "polyline",
        "polygon",
        "path",
        "text",
        "tspan",
        "title",
        "desc",
        "defs",
        "linearGradient",
        "radialGradient",
        "stop",
        "clipPath",
        "mask",
        "pattern",
    }
)
_SVG_ALLOWED_ATTRS = frozenset(
    {
        "id",
        "class",
        "xmlns",
        "x",
        "y",
        "cx",
        "cy",
        "r",
        "rx",
        "ry",
        "width",
        "height",
        "x1",
        "y1",
        "x2",
        "y2",
        "points",
        "d",
        "transform",
        "fill",
        "fill-opacity",
        "fill-rule",
        "stroke",
        "stroke-width",
        "stroke-opacity",
        "stroke-linecap",
        "stroke-linejoin",
        "stroke-dasharray",
        "stroke-dashoffset",
        "opacity",
        "viewBox",
        "gradientUnits",
        "gradientTransform",
        "offset",
        "stop-color",
        "stop-opacity",
        "maskUnits",
        "maskContentUnits",
        "patternUnits",
        "patternContentUnits",
        "text-anchor",
        "font-family",
        "font-size",
        "font-weight",
        "letter-spacing",
        "display",
    }
)
_SVG_URL_FRAGMENT_RE = re.compile(r"^url\(\s*#[^)\s#]*\s*\)$", re.IGNORECASE)
# Raw substrings that only occur in markup (a literal '<' cannot appear in
# well-formed text content), checked before parsing as a fast rejection.
_SVG_RAW_REJECT_MARKERS = (
    "<script",
    "<iframe",
    "<object",
    "<embed",
    "<image",
    "<use",
    "<style",
    "<foreignobject",
    "<animate",
    "<set",
    "<a ",
    "<a>",
    "<!doctype",
    "<!--",
    "<![",
    "xlink:href",
    "javascript:",
    "data:",
    "@import",
)


def _svg_is_valid(data: bytes) -> bool:
    """Inert static SVG: strict element/attribute allowlist, no remote refs."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    lowered = text.lower()
    if any(marker in lowered for marker in _SVG_RAW_REJECT_MARKERS):
        return False
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return False
    if _local_name(root.tag) != "svg":
        return False
    return _svg_node_is_inert(root)


def _local_name(tag: object) -> str:
    """Local (namespace-free) name, case preserved: SVG names are camelCase."""
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1]


def _svg_node_is_inert(node: ET.Element) -> bool:
    if _local_name(node.tag) not in _SVG_ALLOWED_TAGS:
        return False
    for raw_name, value in node.attrib.items():
        name = _local_name(raw_name)
        if not (name in _SVG_ALLOWED_ATTRS or name.startswith("data-")):
            return False
        lowered_value = value.lower()
        if "javascript:" in lowered_value:
            return False
        if name == "xmlns" and value != _SVG_NS:
            return False
        if lowered_value.startswith("url("):
            if not _SVG_URL_FRAGMENT_RE.match(value):
                return False
    return all(_svg_node_is_inert(child) for child in node)


def _raster_is_valid(data: bytes, extension: str) -> bool:
    if extension == ".png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if extension in (".jpg", ".jpeg"):
        return data.startswith(b"\xff\xd8")
    if extension == ".webp":
        return data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    return False


def _image_is_valid(data: bytes, extension: str) -> bool:
    if extension == ".svg":
        return _svg_is_valid(data)
    return _raster_is_valid(data, extension)


# --- bounded reads ----------------------------------------------------------


def _root_is_real_dir(root: Path) -> bool:
    try:
        st = os.lstat(root)
    except OSError:
        return False
    return stat.S_ISDIR(st.st_mode)


def _read_bounded(root: Path, name: str, cap: int) -> bytes | None:
    """Descriptor-safe bounded read; None on any check failure."""
    full = root / name
    try:
        st = os.lstat(full)
    except OSError:
        return None
    if not stat.S_ISREG(st.st_mode) or st.st_size > cap:
        return None
    try:
        fd = os.open(full, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError:
        return None
    try:
        fst = os.fstat(fd)
        if not stat.S_ISREG(fst.st_mode) or fst.st_size > cap:
            return None
        data = os.read(fd, cap + 1)
    finally:
        os.close(fd)
    if len(data) > cap:
        return None
    return data


# --- resolution -------------------------------------------------------------


@dataclass(frozen=True)
class ResolvedAsset:
    slot: str
    file_name: str
    content_type: str
    data: bytes


def _configured_root() -> Path | None:
    raw = getattr(settings, "BRANDING_DIR", None)
    if not isinstance(raw, str):
        return None
    raw = raw.strip()
    return Path(raw) if raw else None


def _slot_file_name(root: Path, slot: str) -> str | None:
    """Exactly one candidate file for the slot; ambiguous or absent -> None."""
    if slot == STYLE_CSS:
        try:
            st = os.lstat(root / STYLE_CSS)
        except OSError:
            return None
        return STYLE_CSS if stat.S_ISREG(st.st_mode) else None

    prefix = slot + "."
    candidates: list[str] = []
    try:
        entries = os.scandir(root)
    except OSError:
        return None
    with entries:
        for entry in entries:
            name = entry.name
            if not name.startswith(prefix):
                continue
            extension = "." + name[len(prefix) :]
            if extension not in IMAGE_EXTENSIONS:
                continue
            try:
                if not entry.is_file(follow_symlinks=False):
                    continue
            except OSError:
                continue
            candidates.append(name)
    return candidates[0] if len(candidates) == 1 else None


def _validate_slot_data(slot: str, file_name: str, data: bytes) -> str | None:
    """Return the response content type, or None when the content is invalid."""
    if slot == STYLE_CSS:
        return _CONTENT_TYPES[".css"] if _css_is_valid(data) else None
    extension = "." + file_name.rsplit(".", 1)[-1]
    return _CONTENT_TYPES.get(extension) if _image_is_valid(data, extension) else None


# (root, slot) -> (file name, mtime_ns, size, resolved-or-None). Re-stat on
# every call: a file change (mtime/size) revalidates immediately, so edits
# are picked up on the next request without a restart.
_cache: dict[tuple[str, str], tuple[str, int, int, ResolvedAsset | None]] = {}


def resolve_slot(slot: str) -> ResolvedAsset | None:
    if slot not in SLOT_URLS:
        return None
    root = _configured_root()
    if root is None or not _root_is_real_dir(root):
        return None
    key = (str(root), slot)
    file_name = _slot_file_name(root, slot)
    if file_name is None:
        _cache.pop(key, None)
        return None
    cap = MAX_CSS_BYTES if slot == STYLE_CSS else MAX_IMAGE_BYTES
    try:
        st = os.lstat(root / file_name)
    except OSError:
        return None
    cached = _cache.get(key)
    if (
        cached is not None
        and cached[0] == file_name
        and cached[1] == st.st_mtime_ns
        and cached[2] == st.st_size
    ):
        return cached[3]
    data = _read_bounded(root, file_name, cap)
    resolved: ResolvedAsset | None = None
    if data is not None:
        content_type = _validate_slot_data(slot, file_name, data)
        if content_type is not None:
            resolved = ResolvedAsset(
                slot=slot,
                file_name=file_name,
                content_type=content_type,
                data=data,
            )
    if len(_cache) > 32:
        _cache.clear()
    _cache[key] = (file_name, st.st_mtime_ns, st.st_size, resolved)
    return resolved


def asset_url(slot: str) -> str:
    return SLOT_URLS[slot]


def _default_brand_bytes() -> bytes:
    return _DEFAULT_BRAND_FILE.read_bytes()


_default_bytes = lru_cache(maxsize=1)(_default_brand_bytes)


def _response(data: bytes, content_type: str) -> HttpResponse:
    response = HttpResponse(data, content_type=content_type)
    response["Cache-Control"] = "no-cache"
    return response


def _serve_slot(_request: HttpRequest, slot: str) -> HttpResponse:
    resolved = resolve_slot(slot)
    if resolved is not None:
        return _response(resolved.data, resolved.content_type)
    if slot == STYLE_CSS:
        # The packaged default is "no override stylesheet": an empty,
        # revalidated stylesheet keeps the page byte-identical and the
        # browser console clean if a file vanished after render.
        return _response(b"", _CONTENT_TYPES[".css"])
    return _response(_default_bytes(), "image/svg+xml")


def branding_style_view(request: HttpRequest) -> HttpResponse:
    return _serve_slot(request, STYLE_CSS)


def branding_image_view(slot: str) -> Callable[[HttpRequest], HttpResponse]:
    def view(request: HttpRequest) -> HttpResponse:
        return _serve_slot(request, slot)

    return view
