"""Bounded, read-only operator appearance overrides (SAR-045).

Optional by default: when ``settings.BRANDING_DIR`` is unset, or a slot file
is missing or invalid, the packaged defaults stand and the page is
unchanged. One invalid asset can never break another slot or any page:
every slot is discovered and validated independently, fail closed.

Security boundary
-----------------
Fixed slots are read relative to verified no-follow directory descriptors,
including each ancestor. Special files cannot block reads. Every resolution
reads and validates bounded bytes anew; operator assets are never cached.
CSS conservatively rejects escaped/resource-loading syntax. SVG has bounded,
namespace-aware inert validation; raster overrides support bounded RGB/RGBA
PNG only. Expected file/parse failures silently select packaged defaults.

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

from slaif_reservation.web.branding_png import png_is_valid

STYLE_CSS = "style.css"
IMAGE_SLOTS = ("logo", "logo-compact", "favicon", "hero")
IMAGE_EXTENSIONS = (".svg", ".png")

MAX_CSS_BYTES = 256 * 1024
MAX_IMAGE_BYTES = 256 * 1024

_CONTENT_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
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
    "@charset",
    "url(",
    "image-set(",
    "image(",
    "src(",
    "data:",
    "javascript:",
    "vbscript:",
    "expression(",
    "behavior:",
    "-moz-binding",
    "<",
)


def _css_is_valid(data: bytes) -> bool:
    """Conservative CSS subset: no escapes, resource functions or imports.

    Remove complete comments then whitespace for token sensitivity. Rejecting
    escapes rather than decoding them also covers escaped keywords/strings,
    line continuations and alternate browser escape normalization.
    """
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    if "\\" in text or any(ord(char) < 32 and char not in "\t\r\n" for char in text):
        return False
    parts: list[str] = []
    cursor = 0
    while True:
        opening = text.find("/*", cursor)
        if opening == -1:
            parts.append(text[cursor:])
            break
        parts.append(text[cursor:opening])
        closing = text.find("*/", opening + 2)
        if closing == -1:
            return False
        cursor = closing + 2
    text = "".join(parts)
    if "*/" in text:
        return False
    normalized = re.sub(r"\s+", "", text).lower()
    return all(marker not in normalized for marker in _CSS_ACTIVE_MARKERS)


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


MAX_SVG_DEPTH = 32
MAX_SVG_NODES = 2048
MAX_SVG_ATTRIBUTES = 64


def _svg_is_valid(data: bytes) -> bool:
    """Bounded inert SVG in the actual SVG namespace; no recursive walk."""
    try:
        text = data.decode("utf-8")
        if any(marker in text.lower() for marker in _SVG_RAW_REJECT_MARKERS):
            return False
        declaration_free = re.sub(r"^\s*<\?xml\s+[^?]*\?>", "", text, count=1)
        if "<?" in declaration_free:
            return False
        root = ET.fromstring(text)
    except (UnicodeDecodeError, ET.ParseError, ValueError, RecursionError):
        return False
    if root.tag != f"{{{_SVG_NS}}}svg":
        return False
    stack = [(root, 1)]
    count = 0
    while stack:
        node, depth = stack.pop()
        count += 1
        if depth > MAX_SVG_DEPTH or count > MAX_SVG_NODES:
            return False
        if node.tag not in {f"{{{_SVG_NS}}}{tag}" for tag in _SVG_ALLOWED_TAGS}:
            return False
        if len(node.attrib) > MAX_SVG_ATTRIBUTES:
            return False
        for name, value in node.attrib.items():
            if not (name in _SVG_ALLOWED_ATTRS or name.startswith("data-")):
                return False
            if "{" in name or len(value) > 8192:
                return False
            normalized = value.strip().lower()
            if any(marker in normalized for marker in ("\\", "data:", "javascript:", "@import")):
                return False
            if "url" in normalized and not _SVG_URL_FRAGMENT_RE.fullmatch(normalized):
                return False
        stack.extend((child, depth + 1) for child in node)
    return True


def _image_is_valid(data: bytes, extension: str) -> bool:
    if extension == ".svg":
        return _svg_is_valid(data)
    return extension == ".png" and png_is_valid(data)


# --- bounded reads ----------------------------------------------------------


def _open_root(root: Path) -> int | None:
    """Walk each directory component from /, refusing symlinks atomically."""
    descriptor: int | None = None
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
    try:
        absolute = Path(os.path.abspath(root))
        descriptor = os.open("/", flags)
        for component in absolute.parts[1:]:
            child = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
            os.close(descriptor)
            return None
        return descriptor
    except (OSError, ValueError):
        if descriptor is not None:
            os.close(descriptor)
        return None


def _read_bounded(root_fd: int, name: str, cap: int) -> bytes | None:
    """No path re-resolution, no blocking FIFO opens, no unbounded reads."""
    descriptor: int | None = None
    try:
        descriptor = os.open(
            name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
            dir_fd=root_fd,
        )
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > cap:
            return None
        chunks = bytearray()
        while len(chunks) <= cap:
            chunk = os.read(descriptor, cap + 1 - len(chunks))
            if not chunk:
                break
            chunks.extend(chunk)
        after = os.fstat(descriptor)
        if len(chunks) > cap or _stat_identity(before) != _stat_identity(after):
            return None
        return bytes(chunks)
    except OSError:
        return None
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _stat_identity(status: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        status.st_dev,
        status.st_ino,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


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


def _slot_file_name(root_fd: int, slot: str) -> str | None:
    """Bounded fixed-name discovery relative to the anchored directory."""
    names = [STYLE_CSS] if slot == STYLE_CSS else [slot + ext for ext in IMAGE_EXTENSIONS]
    candidates = []
    for name in names:
        try:
            status = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
        except OSError:
            continue
        if stat.S_ISREG(status.st_mode):
            candidates.append(name)
    return candidates[0] if len(candidates) == 1 else None


def _validate_slot_data(slot: str, file_name: str, data: bytes) -> str | None:
    """Return the response content type, or None when the content is invalid."""
    if slot == STYLE_CSS:
        return _CONTENT_TYPES[".css"] if _css_is_valid(data) else None
    extension = "." + file_name.rsplit(".", 1)[-1]
    return _CONTENT_TYPES.get(extension) if _image_is_valid(data, extension) else None


def resolve_slot(slot: str) -> ResolvedAsset | None:
    if slot not in SLOT_URLS:
        return None
    root = _configured_root()
    if root is None:
        return None
    root_fd = _open_root(root)
    if root_fd is None:
        return None
    try:
        file_name = _slot_file_name(root_fd, slot)
        if file_name is None:
            return None
        cap = MAX_CSS_BYTES if slot == STYLE_CSS else MAX_IMAGE_BYTES
        data = _read_bounded(root_fd, file_name, cap)
        if data is None:
            return None
        content_type = _validate_slot_data(slot, file_name, data)
        if content_type is None:
            return None
        return ResolvedAsset(slot, file_name, content_type, data)
    finally:
        os.close(root_fd)


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
