"""038-a — bounded read-only operator branding qualification (SAR-045).

Covers the acceptance boundary of the optional appearance mechanism:
disabled/missing/empty directories, real response bytes and MIME, content,
size, format, path/symlink/special-file and ambiguity negatives, per-slot
fallback independence, safe refresh semantics, preserved page/auth behavior
and the owned-production-overlay Docker qualification (same built image,
default and with the read-only branding mount).

All product-test runs use an owned disposable source copy, an owned
PostgreSQL 17 project and cleared OAP_ROLE (see TESTING.md); this file is
executed from such a copy.
"""

from __future__ import annotations

import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import uuid
import zlib
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from django.test import Client, override_settings

from slaif_reservation.web import branding

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "branding"
CUSTOM = FIXTURES / "custom"
DEFAULT_LOGO_BYTES = (
    REPO_ROOT / "src" / "slaif_reservation" / "web" / "static" / "web" / "brand" / "slaif-logo.svg"
).read_bytes()

VALID_CSS = b":root {\n  --background: #10233f;\n}\n"
VALID_PNG = (CUSTOM / "logo.png").read_bytes()
VALID_SVG = (CUSTOM / "hero.svg").read_bytes()


def _png(width: int, height: int, rgba: tuple[int, int, int, int]) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    raw = b"".join(b"\x00" + bytes(rgba) * width for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


# --- disabled / missing / empty ------------------------------------------------


@pytest.mark.django_db
def test_disabled_defaults_and_total_endpoints(client: Client) -> None:
    with override_settings(BRANDING_DIR=None):
        html = client.get("/").content.decode()
        assert "/branding/" not in html
        assert "/static/web/brand/slaif-logo.svg" in html or "/static/" in html
        # The branding endpoints are total: fallback bytes, never a 404.
        css = client.get("/branding/style.css")
        assert css.status_code == 200
        assert css.content == b""
        logo = client.get("/branding/logo")
        assert logo.status_code == 200
        assert logo["Content-Type"] == "image/svg+xml"
        assert logo.content == DEFAULT_LOGO_BYTES
        assert client.get("/branding/favicon").content == DEFAULT_LOGO_BYTES
        assert client.get("/branding/hero").content == DEFAULT_LOGO_BYTES
        assert client.get("/branding/logo-compact").content == DEFAULT_LOGO_BYTES


@pytest.mark.django_db
def test_missing_and_empty_directories_fall_back(client: Client) -> None:
    with override_settings(BRANDING_DIR="/nonexistent-sar038a-branding"):
        assert client.get("/").status_code == 200
        assert "/branding/style.css" not in client.get("/").content.decode()
    empty = Path(tempfile.mkdtemp(prefix="sar038a-empty-"))
    try:
        with override_settings(BRANDING_DIR=str(empty)):
            html = client.get("/").content.decode()
            assert "/branding/style.css" not in html
            assert "/branding/hero" not in html
    finally:
        empty.rmdir()


@pytest.mark.django_db
def test_no_request_selected_file_routes(client: Client) -> None:
    with override_settings(BRANDING_DIR=str(CUSTOM)):
        for path in ("/branding/", "/branding/other", "/branding/logo/extra"):
            assert client.get(path).status_code == 404
        # Traversal-style requests never reach the mechanism: the router
        # normalizes them away from the fixed slot routes.
        assert client.get("/branding/../config/settings/base.py").status_code == 404


# --- valid overrides: real bytes and page references ---------------------------


@pytest.mark.django_db
def test_style_css_served_with_exact_contract(client: Client) -> None:
    with override_settings(BRANDING_DIR=str(CUSTOM)):
        response = client.get("/branding/style.css")
        assert response.status_code == 200
        assert response.content == (CUSTOM / "style.css").read_bytes()
        assert response["Content-Type"] == "text/css; charset=utf-8"
        assert response["Cache-Control"] == "no-cache"
        assert response["X-Content-Type-Options"] == "nosniff"


@pytest.mark.django_db
def test_image_slots_served_with_mime_and_exact_bytes(client: Client) -> None:
    with override_settings(BRANDING_DIR=str(CUSTOM)):
        logo = client.get("/branding/logo")
        assert logo.status_code == 200
        assert logo["Content-Type"] == "image/png"
        assert logo.content == (CUSTOM / "logo.png").read_bytes()
        hero = client.get("/branding/hero")
        assert hero["Content-Type"] == "image/svg+xml"
        assert hero.content == (CUSTOM / "hero.svg").read_bytes()
        favicon = client.get("/branding/favicon")
        assert favicon["Content-Type"] == "image/png"
        assert favicon.content == (CUSTOM / "favicon.png").read_bytes()
        compact = client.get("/branding/logo-compact")
        assert compact["Content-Type"] == "image/png"


@pytest.mark.django_db
def test_pages_reference_overrides_and_css_order(client: Client) -> None:
    with override_settings(BRANDING_DIR=str(CUSTOM)):
        html = client.get("/").content.decode()
        for marker in (
            "/branding/hero",
            "/branding/logo",
            "/branding/logo-compact",
            "/branding/favicon",
            "/branding/style.css",
        ):
            assert marker in html
        # The override stylesheet loads AFTER the built-in styles.
        assert html.index("/branding/style.css") > html.index("/static/web/site.css")
        # The product title is unchanged.
        assert "<title>SLAIF Asset Reservation</title>" in html

        error = client.get("/does-not-exist")
        assert error.status_code == 404
        error_html = error.content.decode()
        assert "/branding/favicon" in error_html
        assert "/branding/style.css" in error_html
        assert "/branding/logo" in error_html

        admin_login = client.get("/admin/login/").content.decode()
        assert "/branding/favicon" in admin_login
        assert "/branding/logo" in admin_login
        assert "/branding/style.css" in admin_login
        # In the admin, the override loads after the admin identity sheet.
        assert admin_login.index("/branding/style.css") > admin_login.index(
            "/static/web/admin-identity.css"
        )


@pytest.mark.django_db
def test_staff_admin_index_receives_override(client: Client, django_user_model) -> None:
    django_user_model.objects.create_user(
        email="brand-admin@example.com",
        password="not-a-secret",
        timezone="Europe/Ljubljana",
        is_staff=True,
        is_superuser=True,
    )
    with override_settings(BRANDING_DIR=str(CUSTOM)):
        assert client.login(email="brand-admin@example.com", password="not-a-secret")
        html = client.get("/admin/").content.decode()
        assert "/branding/style.css" in html
        assert "/branding/favicon" in html
        assert "/branding/logo" in html


# --- content / format negatives -------------------------------------------------

INVALID_CSS = [
    ("not-utf8", b"\xff\xfe\x00<style>a{}</style>"),
    ("remote-url", b"a { background: url(http://evil.example/x.png) }"),
    ("protocol-relative", b"a { background: url(//evil.example/x.png) }"),
    ("data-uri", b"a { background: url(data:text/plain;base64,AAA) }"),
    ("at-import", b'@import "https://evil.example/x.css"; a {}'),
    ("javascript", b"a { background: javascript:alert(1) }"),
    ("script-tag", b"<script>alert(1)</script>"),
    ("behavior", b"a { behavior: url(x.htc) }"),
    ("oversize", b"a{color:#000}\n" * 86000),  # > 256 KiB
]


@pytest.mark.django_db
@pytest.mark.parametrize("name,data", INVALID_CSS, ids=[item[0] for item in INVALID_CSS])
def test_invalid_css_falls_back_without_breaking_slots(client: Client, name, data) -> None:
    root = Path(tempfile.mkdtemp(prefix=f"sar038a-css-{name}-"))
    try:
        (root / "style.css").write_bytes(data)
        shutil.copy(CUSTOM / "logo.png", root / "logo.png")
        with override_settings(BRANDING_DIR=str(root)):
            response = client.get("/branding/style.css")
            assert response.status_code == 200
            assert response.content == b""
            html = client.get("/").content.decode()
            assert "/branding/style.css" not in html
            # The other slot keeps working independently.
            assert "/branding/logo" in html
            assert client.get("/branding/logo").content == (root / "logo.png").read_bytes()
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.django_db
def test_css_at_exact_cap_is_valid(client: Client) -> None:
    root = Path(tempfile.mkdtemp(prefix="sar038a-css-cap-"))
    try:
        css = ("a{color:#000}\n" * 16383).encode()
        assert len(css) <= branding.MAX_CSS_BYTES
        (root / "style.css").write_bytes(css)
        with override_settings(BRANDING_DIR=str(root)):
            response = client.get("/branding/style.css")
            assert response.content == css
    finally:
        shutil.rmtree(root, ignore_errors=True)


INVALID_IMAGES = [
    ("html-disguised", "logo.png", b"<html><script>alert(1)</script></html>"),
    ("jpeg-magic-in-png", "logo.png", b"\xff\xd8\xff\xe0" + b"\x00" * 32),
    ("png-magic-in-jpg", "logo.jpg", b"\x89PNG\r\n\x1a\n" + b"\x00" * 32),
    ("bad-webp", "logo.webp", b"RIFF\x00\x00\x00\x00XXXX"),
    ("empty", "logo.png", b""),
    (
        "oversize-png",
        "logo.png",
        _png(1, 1, (1, 2, 3, 4)) + b"\x00" * (branding.MAX_IMAGE_BYTES + 1),
    ),
]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "name,file_name,data", INVALID_IMAGES, ids=[item[0] for item in INVALID_IMAGES]
)
def test_invalid_image_falls_back_to_packaged_default(
    client: Client, name: str, file_name: str, data: bytes
) -> None:
    root = Path(tempfile.mkdtemp(prefix=f"sar038a-img-{name}-"))
    try:
        (root / file_name).write_bytes(data)
        (root / "favicon.png").write_bytes(VALID_PNG)
        with override_settings(BRANDING_DIR=str(root)):
            # Page references the packaged default for the broken slot only.
            html = client.get("/").content.decode()
            assert "/branding/logo" not in html
            assert "/branding/favicon" in html
            # The endpoint stays total: packaged default bytes, never a 404.
            logo = client.get("/branding/logo")
            assert logo.status_code == 200
            assert logo.content == DEFAULT_LOGO_BYTES
            assert client.get("/branding/favicon").content == VALID_PNG
            # Login and error surfaces remain fully functional.
            assert client.get("/login/").status_code == 200
            assert client.get("/does-not-exist").status_code == 404
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _svg(body: str) -> bytes:
    return (
        '<?xml version="1.0"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">{body}</svg>'
    ).encode()


INVALID_SVGS = [
    ("script", _svg("<script>alert(1)</script>")),
    (
        "foreignobject",
        _svg("<foreignObject><body><img src=x onerror=alert(1)></body></foreignObject>"),
    ),
    ("iframe", _svg('<iframe src="https://evil.example"></iframe>')),
    ("object", _svg("<object data='x'></object>")),
    ("embed", _svg('<embed src="x.svg">')),
    ("image", _svg('<image href="https://evil.example/x.png">')),
    ("use", _svg('<use href="https://evil.example/s.svg#x">')),
    ("anchor-javascript", _svg('<a href="javascript:alert(1)"><rect width="1" height="1"/></a>')),
    ("onload-attr", _svg('<rect width="1" height="1" onload="alert(1)"/>')),
    ("xlink-href", _svg('<image xlink:href="x.png" xmlns:xlink="http://www.w3.org/1999/xlink"/>')),
    ("data-uri-fill", _svg('<rect width="1" height="1" fill="data:image/png;base64,AAA"/>')),
    ("remote-style", _svg("<style>@import 'https://evil.example/x.css';</style>")),
    ("doctype", _svg("")),  # replaced below with a DOCTYPE variant
]
INVALID_SVGS[-1] = (
    "doctype",
    b'<?xml version="1.0"?>\n<!DOCTYPE svg>\n<svg xmlns="http://www.w3.org/2000/svg"></svg>',
)


@pytest.mark.django_db
@pytest.mark.parametrize("name,data", INVALID_SVGS, ids=[item[0] for item in INVALID_SVGS])
def test_invalid_svg_rejected(client: Client, name, data) -> None:
    root = Path(tempfile.mkdtemp(prefix=f"sar038a-svg-{name}-"))
    try:
        (root / "logo.svg").write_bytes(data)
        with override_settings(BRANDING_DIR=str(root)):
            assert branding.resolve_slot("logo") is None
            logo = client.get("/branding/logo")
            assert logo.content == DEFAULT_LOGO_BYTES
            html = client.get("/").content.decode()
            assert "/branding/logo" not in html
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.django_db
def test_inert_svg_with_local_gradient_is_accepted(client: Client) -> None:
    root = Path(tempfile.mkdtemp(prefix="sar038a-svg-ok-"))
    try:
        data = _svg(
            '<defs><linearGradient id="g">'
            '<stop offset="0" stop-color="#ffffff"/>'
            '<stop offset="1" stop-color="#216869"/>'
            "</linearGradient></defs>"
            '<rect width="10" height="10" fill="url(#g)"/>'
            '<text x="1" y="5" font-size="2" data-variant="a">S</text>'
        )
        (root / "logo.svg").write_bytes(data)
        with override_settings(BRANDING_DIR=str(root)):
            resolved = branding.resolve_slot("logo")
            assert resolved is not None
            assert resolved.content_type == "image/svg+xml"
            assert client.get("/branding/logo").content == data
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.django_db
def test_ambiguous_slot_and_unknown_entries(client: Client) -> None:
    root = Path(tempfile.mkdtemp(prefix="sar038a-ambiguous-"))
    try:
        (root / "logo.png").write_bytes(VALID_PNG)
        (root / "logo.svg").write_bytes(VALID_SVG)
        (root / "evil.html").write_bytes(b"<html>never read</html>")
        (root / "notes").mkdir()
        (root / "notes/readme.txt").write_bytes(b"never read")
        (root / "logo.txt").write_bytes(b"not an allowed extension")
        with override_settings(BRANDING_DIR=str(root)):
            # Two candidates for one slot fail closed; unknown entries are
            # never opened.
            assert branding.resolve_slot("logo") is None
            assert client.get("/branding/logo").content == DEFAULT_LOGO_BYTES
        (root / "logo.svg").unlink()
        with override_settings(BRANDING_DIR=str(root)):
            assert client.get("/branding/logo").content == VALID_PNG
    finally:
        shutil.rmtree(root, ignore_errors=True)


# --- path / symlink / special-file boundary -------------------------------------


@pytest.mark.django_db
def test_symlink_file_and_directory_rejected(client: Client) -> None:
    root = Path(tempfile.mkdtemp(prefix="sar038a-symlink-"))
    try:
        (root / "logo.png").write_bytes(VALID_PNG)
        (root / "style.css").write_bytes(VALID_CSS)
        with override_settings(BRANDING_DIR=str(root)):
            assert branding.resolve_slot("logo") is not None
        # Swap the slot file for a symlink pointing outside the directory.
        (root / "logo.png").unlink()
        (root / "outside.png").write_bytes(VALID_PNG)
        os.symlink(root / "outside.png", root / "logo.png")
        with override_settings(BRANDING_DIR=str(root)):
            assert branding.resolve_slot("logo") is None
            assert client.get("/branding/logo").content == DEFAULT_LOGO_BYTES
            # The other slot is unaffected.
            assert client.get("/branding/style.css").content == VALID_CSS
        # A symlinked root directory is refused wholesale.
        link_root = root / "link-root"
        os.symlink(root, link_root)
        with override_settings(BRANDING_DIR=str(link_root)):
            assert branding.resolve_slot("logo") is None
            assert branding.resolve_slot("style.css") is None
        # A directory named like a slot file is not readable as a file.
        (root / "outside.png").unlink()
        os.unlink(root / "logo.png")
        os.unlink(link_root)
        (root / "logo.png").mkdir()
        with override_settings(BRANDING_DIR=str(root)):
            assert branding.resolve_slot("logo") is None
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.django_db
def test_fifo_slot_file_rejected_without_open(client: Client) -> None:
    root = Path(tempfile.mkdtemp(prefix="sar038a-fifo-"))
    try:
        os.mkfifo(root / "logo.png")
        with override_settings(BRANDING_DIR=str(root)):
            started = time.monotonic()
            assert branding.resolve_slot("logo") is None
            # The lstat check refuses before any open, so this cannot block.
            assert time.monotonic() - started < 5
            assert client.get("/branding/logo").content == DEFAULT_LOGO_BYTES
    finally:
        shutil.rmtree(root, ignore_errors=True)


# --- refresh semantics -----------------------------------------------------------


@pytest.mark.django_db
def test_file_change_picked_up_on_next_request(client: Client) -> None:
    root = Path(tempfile.mkdtemp(prefix="sar038a-refresh-"))
    try:
        v1 = b":root { --background: #000000; }\n"
        v2 = b":root { --background: #111111; }\n"
        (root / "style.css").write_bytes(v1)
        with override_settings(BRANDING_DIR=str(root)):
            assert client.get("/branding/style.css").content == v1
            (root / "style.css").write_bytes(v2)
            future = time.time() + 2
            os.utime(root / "style.css", (future, future))
            assert client.get("/branding/style.css").content == v2
            # A valid file replaced by an invalid one also revalidates.
            (root / "style.css").write_bytes(b"@import 'x';")
            os.utime(root / "style.css", (future + 1, future + 1))
            assert client.get("/branding/style.css").content == b""
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.django_db
def test_removed_file_after_render_serves_safe_fallback(client: Client) -> None:
    root = Path(tempfile.mkdtemp(prefix="sar038a-race-"))
    try:
        (root / "style.css").write_bytes(VALID_CSS)
        (root / "logo.png").write_bytes(VALID_PNG)
        with override_settings(BRANDING_DIR=str(root)):
            html = client.get("/").content.decode()
            assert "/branding/style.css" in html
            assert "/branding/logo" in html
            # The files disappear between render and subresource requests.
            (root / "style.css").unlink()
            (root / "logo.png").unlink()
            assert client.get("/branding/style.css").content == b""
            assert client.get("/branding/logo").content == DEFAULT_LOGO_BYTES
            # The page itself still renders.
            assert client.get("/").status_code == 200
            assert client.get("/login/").status_code == 200
    finally:
        shutil.rmtree(root, ignore_errors=True)


# --- preserved behavior -----------------------------------------------------------


@pytest.mark.django_db
def test_auth_and_error_behavior_unchanged(client: Client) -> None:
    with override_settings(BRANDING_DIR=str(CUSTOM)):
        login_html = client.get("/login/").content.decode()
        assert 'name="csrfmiddlewaretoken"' in login_html
        assert client.get("/").headers.get("X-Frame-Options") == "DENY"
        # CSRF failure (enforcing client) still renders the branded error page.
        enforcing = Client(enforce_csrf_checks=True)
        response = enforcing.post("/logout/")
        assert response.status_code == 403
        assert "/branding/favicon" in response.content.decode()


@pytest.mark.parametrize(
    "data",
    [
        rb'@\69mport "https://branding-probe.invalid/x.css";',
        b'body { background: image-set("https://branding-probe.invalid/x.png" 1x) }',
        b'body { background: -webkit-image-set("https://branding-probe.invalid/x.png" 1x) }',
        b'@im/**/port "https://branding-probe.invalid/x.css";',
    ],
)
def test_normalized_css_resource_constructs_refused(data: bytes) -> None:
    assert not branding._css_is_valid(data)


@pytest.mark.parametrize(
    "data",
    [
        b"<svg><rect/></svg>",
        b'<?xml-stylesheet type="text/css" href="https://branding-probe.invalid/x.css"?>'
        + VALID_SVG,
        _svg('<rect fill=" url(https://branding-probe.invalid/x.svg#paint)"/>'),
        _svg('<rect fill="url(https://branding-probe.invalid/x.svg#paint)"/>'),
        _svg("<g>" * 1200 + "</g>" * 1200),
    ],
)
def test_svg_namespace_resources_and_depth_refused(data: bytes) -> None:
    assert not branding._svg_is_valid(data)


@pytest.mark.parametrize("data", [b"\x89PNG\r\n\x1a\n", VALID_PNG[:-1], VALID_PNG + b"garbage"])
def test_truncated_or_trailing_png_refused(data: bytes) -> None:
    assert not branding._image_is_valid(data, ".png")


def test_root_directory_swap_cannot_read_outside(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "branding"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    original = b"body { color: blue; }"
    (root / "style.css").write_bytes(original)
    (outside / "style.css").write_bytes(b"body { color: red; }")
    real_open = os.open
    swapped = False

    def swap(path, flags, *args, **kwargs):
        nonlocal swapped
        if Path(path).name == "style.css" and not swapped:
            swapped = True
            root.rename(tmp_path / "original")
            root.symlink_to(outside, target_is_directory=True)
        return real_open(path, flags, *args, **kwargs)

    with override_settings(BRANDING_DIR=str(root)), monkeypatch.context() as patch:
        patch.setattr(branding.os, "open", swap)
        result = branding.resolve_slot("style.css")
        assert swapped
        assert result is None or result.data == original


def test_ancestor_symlink_refused(tmp_path: Path) -> None:
    actual = tmp_path / "actual"
    (actual / "branding").mkdir(parents=True)
    (actual / "branding" / "style.css").write_bytes(VALID_CSS)
    link = tmp_path / "link"
    link.symlink_to(actual, target_is_directory=True)
    with override_settings(BRANDING_DIR=str(link / "branding")):
        assert branding.resolve_slot("style.css") is None


def test_regular_file_swapped_to_fifo_is_nonblocking(tmp_path: Path, monkeypatch) -> None:
    slot = tmp_path / "style.css"
    slot.write_bytes(VALID_CSS)
    real_open = os.open

    def swap(path, flags, *args, **kwargs):
        if Path(path).name == "style.css":
            slot.unlink()
            os.mkfifo(slot)
            assert flags & os.O_NONBLOCK, "special-file opens must not block"
        return real_open(path, flags, *args, **kwargs)

    with override_settings(BRANDING_DIR=str(tmp_path)), monkeypatch.context() as patch:
        patch.setattr(branding.os, "open", swap)
        assert branding.resolve_slot("style.css") is None


def test_fifo_swap_finishes_in_real_bounded_child(tmp_path: Path) -> None:
    (tmp_path / "style.css").write_bytes(VALID_CSS)
    code = """import os,sys,pathlib,django
from unittest.mock import patch
django.setup()
from django.test import override_settings
from slaif_reservation.web import branding
root=pathlib.Path(sys.argv[1]); slot=root/'style.css'; original=os.open
def swap(path,flags,*args,**kwargs):
    if pathlib.Path(path).name=='style.css':
        slot.unlink(); os.mkfifo(slot)
    return original(path,flags,*args,**kwargs)
with override_settings(BRANDING_DIR=str(root)),patch.object(branding.os,'open',swap):
    assert branding.resolve_slot('style.css') is None
"""
    environment = {
        key: os.environ[key]
        for key in (
            "PATH",
            "PYTHONPATH",
            "DJANGO_SETTINGS_MODULE",
            "DATABASE_URL",
            "TEST_DATABASE_URL",
        )
        if key in os.environ
    }
    environment["PYTHONPATH"] = str(REPO_ROOT / "src")
    environment["DJANGO_SETTINGS_MODULE"] = "slaif_reservation.config.settings.test"
    try:
        result = subprocess.run(
            [sys.executable, "-c", code, str(tmp_path)],
            env=environment,
            capture_output=True,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        pytest.fail("FIFO replacement blocked the owned child")
    assert result.returncode == 0, "bounded FIFO refusal failed"


@pytest.mark.django_db
def test_read_error_does_not_break_login_or_errors(
    client: Client, tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / "style.css").write_bytes(VALID_CSS)

    def failed_read(*args):
        raise OSError("synthetic read failure")

    with override_settings(BRANDING_DIR=str(tmp_path)), monkeypatch.context() as patch:
        patch.setattr(branding.os, "read", failed_read)
        assert client.get("/branding/style.css").content == b""
        assert client.get("/login/").status_code == 200
        assert client.get("/missing-page/").status_code == 404


def test_same_size_and_mtime_replacement_revalidates(tmp_path: Path) -> None:
    slot = tmp_path / "style.css"
    first = b"body { color: blue; }"
    second = b"body { color: pink; }"
    assert len(first) == len(second)
    slot.write_bytes(first)
    stamp = slot.stat().st_mtime_ns
    with override_settings(BRANDING_DIR=str(tmp_path)):
        assert branding.resolve_slot("style.css").data == first
        replacement = tmp_path / "replacement"
        replacement.write_bytes(second)
        os.utime(replacement, ns=(stamp, stamp))
        replacement.replace(slot)
        assert branding.resolve_slot("style.css").data == second
        slot.write_bytes(b'@import "x";')
        os.utime(slot, ns=(stamp, stamp))
        assert branding.resolve_slot("style.css") is None


# --- owned production-overlay Docker qualification -------------------------------


OWNER_LABEL = "slaif.qualification.owner"


def _docker_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    environment = {key: os.environ[key] for key in ("PATH", "TMPDIR") if key in os.environ}
    environment["DOCKER_HOST"] = "unix:///var/run/docker.sock"
    if extra:
        assert set(extra) <= {"SLAIF_APP_HOST_PORT"}
        environment.update(extra)
    return environment


class _OwnedDocker:
    """Identity receipts for this test only; never cleanup by project selector."""

    def __init__(self, nonce: str) -> None:
        self.nonce = nonce
        self.started = datetime.now(UTC).replace(microsecond=0)
        self.objects: dict[tuple[str, str], tuple[str, str]] = {}

    def inspect(self, kind: str, reference: str) -> dict | None:
        command = (
            ["docker", "inspect", reference]
            if kind == "container"
            else ["docker", kind, "inspect", reference]
        )
        result = _run(command, timeout=30)
        if result.returncode:
            return None
        try:
            return json.loads(result.stdout)[0]
        except (ValueError, IndexError):
            return None

    def absent(self, kind: str, reference: str) -> None:
        assert self.inspect(kind, reference) is None, "qualification name already exists"

    def remember(self, kind: str, reference: str) -> None:
        metadata = self.inspect(kind, reference)
        if metadata is None:
            return
        labels = metadata.get("Labels") or metadata.get("Config", {}).get("Labels") or {}
        if labels.get(OWNER_LABEL) != self.nonce:
            raise AssertionError("qualification refused an unowned object")
        created = metadata.get("CreatedAt") or metadata.get("Created")
        if not created or datetime.fromisoformat(created.replace("Z", "+00:00")) < self.started:
            raise AssertionError("qualification refused an old object")
        identity = metadata.get("Id") or metadata.get("ID") or metadata.get("Name")
        assert identity
        self.objects[(kind, identity)] = (self.nonce, created)

    def cleanup(self) -> None:
        for kind in ("container", "network", "volume", "image"):
            for (object_kind, identity), (nonce, created) in list(self.objects.items()):
                if object_kind != kind:
                    continue
                metadata = self.inspect(kind, identity)
                if metadata is None:
                    continue
                labels = metadata.get("Labels") or metadata.get("Config", {}).get("Labels") or {}
                if (
                    labels.get(OWNER_LABEL) != nonce
                    or (metadata.get("CreatedAt") or metadata.get("Created")) != created
                ):
                    raise AssertionError("cleanup refused a changed ownership receipt")
                command = (
                    ["docker", "rm", "-f", identity]
                    if kind == "container"
                    else ["docker", kind, "rm", identity]
                )
                assert _run(command, timeout=120).returncode == 0, "owned cleanup failed"


def _run(
    cmd: list[str], *, env: dict[str, str] | None = None, timeout: int = 600
) -> subprocess.CompletedProcess:
    full_env = _docker_env(env)
    return subprocess.run(cmd, capture_output=True, text=True, env=full_env, timeout=timeout)


def _docker_available() -> bool:
    if shutil.which("docker") is None or shutil.which("git") is None:
        return False
    result = subprocess.run(
        ["docker", "version", "--format", "{{.Server.Version}}"],
        capture_output=True,
        text=True,
        timeout=30,
        env=_docker_env(),
    )
    return result.returncode == 0


def _wait_healthy(container: str, timeout_s: int = 240) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        result = _run(
            [
                "docker",
                "inspect",
                "--format",
                "{{.State.Health.Status}}",
                container,
            ],
            timeout=30,
        )
        if result.stdout.strip() == "healthy":
            return
        if result.stdout.strip() == "unhealthy":
            raise AssertionError(f"container {container} became unhealthy")
        time.sleep(2)
    raise AssertionError(f"container {container} not healthy within {timeout_s}s")


def _in_app_get(
    container: str, path: str, headers: dict[str, str] | None = None
) -> tuple[int, bytes]:
    code = (
        "import urllib.request as u, json, sys\n"
        "req = u.Request(sys.argv[1], headers=json.loads(sys.argv[2]))\n"
        "try:\n"
        "    r = u.urlopen(req, timeout=10)\n"
        "    print(r.status, flush=True)\n"
        "    sys.stdout.buffer.write(r.read())\n"
        "except u.HTTPError as e:\n"
        "    print(e.code, flush=True)\n"
        "    sys.stdout.buffer.write(e.read())\n"
    )
    result = subprocess.run(
        [
            "docker",
            "exec",
            container,
            "python",
            "-c",
            code,
            f"http://127.0.0.1:8000{path}",
            json.dumps(headers or {"X-Forwarded-Proto": "https"}),
        ],
        capture_output=True,
        timeout=60,
        env=_docker_env(),
    )
    if result.returncode != 0:
        raise AssertionError(
            f"in-app GET {path} failed: {result.stderr.decode(errors='replace')[:400]}"
        )
    status = int(result.stdout.split(b"\n", 1)[0])
    return status, result.stdout.split(b"\n", 1)[1]


def test_docker_production_overlay_qualification() -> None:
    """Same built image, production topology: default, then read-only branding.

    Owned and disposable: tracked-file snapshot build, uniquely named
    project, kernel-assigned loopback port, synthetic configuration, exact
    owned cleanup. Skips honestly only when docker/git prerequisites are
    absent.
    """
    if not _docker_available():
        pytest.skip("docker or git prerequisites missing")

    nonce = uuid.uuid4().hex
    tag = f"slaif038a-{nonce}:test"
    project = f"slaif038a{nonce}"
    root = Path(tempfile.mkdtemp(prefix=f"slaif038a-{nonce}-"))
    snapshot = root / "snapshot"
    snapshot.mkdir()
    compose_base: list[str] | None = None
    owned = _OwnedDocker(nonce)
    sentinel_owner = _OwnedDocker(nonce + "-sentinel")
    sentinel = f"{project}_foreign"
    volume = f"{project}_postgres-data"
    network = f"{project}_default"
    try:
        for kind, name in (
            ("image", tag),
            ("volume", volume),
            ("network", network),
            ("container", f"{project}-app-1"),
            ("container", f"{project}-db-1"),
            ("container", f"{project}-migrate"),
        ):
            owned.absent(kind, name)
        # 1. Tracked-file snapshot (exactly the tracked content at HEAD).
        archive = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "archive", "HEAD"],
            capture_output=True,
            timeout=120,
        )
        assert archive.returncode == 0, archive.stderr.decode(errors="replace")[:400]
        extracted = subprocess.run(
            ["tar", "-x", "-C", str(snapshot)],
            input=archive.stdout,
            capture_output=True,
            timeout=120,
        )
        assert extracted.returncode == 0, extracted.stderr.decode(errors="replace")[:400]
        tracked = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "ls-files"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        tracked_files = [line for line in tracked.stdout.splitlines() if line]
        assert len(tracked_files) > 0
        on_disk = [
            str(path.relative_to(snapshot)) for path in snapshot.rglob("*") if path.is_file()
        ]
        assert sorted(on_disk) == sorted(tracked_files), "snapshot must be tracked-only"

        # 2. Build the image once; both runs share it (no rebuild).
        build = _run(
            ["docker", "build", "--label", f"{OWNER_LABEL}={nonce}", "--tag", tag, str(snapshot)],
            timeout=1800,
        )
        owned.remember("image", tag)
        assert build.returncode == 0, "owned image build failed"
        inspect = _run(["docker", "image", "inspect", tag, "--format", "{{.Config.User}}"])
        assert inspect.stdout.strip() == "10001:10001"
        # A separately owned disposable sentinel must never be adopted or
        # deleted by this qualification's primary owner.
        sentinel_owner.absent("volume", sentinel)
        created = _run(
            ["docker", "volume", "create", "--label", f"{OWNER_LABEL}={nonce}-sentinel", sentinel]
        )
        assert created.returncode == 0, "sentinel creation failed"
        sentinel_owner.remember("volume", sentinel)
        with pytest.raises(AssertionError, match="unowned object"):
            owned.remember("volume", sentinel)

        # 3. Rendered overlay topology against BOTH supported base files.
        for base in ("compose.yaml", "compose.production.example.yaml"):
            rendered = _run(
                [
                    "docker",
                    "compose",
                    "-f",
                    str(snapshot / base),
                    "-f",
                    str(snapshot / "compose.branding.example.yaml"),
                    "config",
                    "--format",
                    "json",
                ]
            )
            assert rendered.returncode == 0, rendered.stderr[-2000:]
            config = json.loads(rendered.stdout)
            services = config["services"]
            base_rendered = _run(
                ["docker", "compose", "-f", str(snapshot / base), "config", "--format", "json"]
            )
            base_config = json.loads(base_rendered.stdout)
            assert set(services) == set(base_config["services"]), "overlay adds no services"
            app = services["app"]
            environment = app.get("environment") or {}
            if isinstance(environment, list):
                environment = {
                    item.split("=", 1)[0]: item.split("=", 1)[1]
                    for item in environment
                    if "=" in item
                }
            assert environment.get("SLAIF_BRANDING_DIR") == "/branding"
            branding_volumes = [
                v
                for v in app.get("volumes", [])
                if isinstance(v, dict) and v.get("target") == "/branding"
            ]
            assert len(branding_volumes) == 1
            assert branding_volumes[0].get("type") == "bind"
            assert branding_volumes[0].get("read_only") is True
            assert str(branding_volumes[0].get("source", "")).endswith("deploy/branding")
            ports = app.get("ports", [])
            assert any(
                port.get("host_ip") == "127.0.0.1" and port.get("target") == 8000 for port in ports
            )

        prod_rendered = _run(
            [
                "docker",
                "compose",
                "-f",
                str(snapshot / "compose.production.example.yaml"),
                "-f",
                str(snapshot / "compose.branding.example.yaml"),
                "config",
                "--format",
                "json",
            ]
        )
        prod_config = json.loads(prod_rendered.stdout)["services"]["app"]
        assert prod_config.get("user") == "10001:10001"
        assert prod_config.get("read_only") is True

        # 4. Owned synthetic production configuration (never the repo's):
        #    the production compose is copied, and only the image reference
        #    is pointed at the tag built from the tracked snapshot.
        secret = uuid.uuid4().hex * 2
        pepper = uuid.uuid4().hex * 2
        db_password = uuid.uuid4().hex
        prod_yaml = root / "prod.yaml"
        prod_text = (snapshot / "compose.production.example.yaml").read_text(encoding="utf-8")
        assert "slaif-asset-reservation:internal-alpha" in prod_text
        document = yaml.safe_load(prod_text)
        document["services"]["app"]["image"] = tag
        for service in ("app", "db"):
            document["services"][service]["labels"] = {OWNER_LABEL: nonce}
        document["volumes"]["postgres-data"] = {"external": True, "name": volume}
        document["networks"] = {"default": {"external": True, "name": network}}
        prod_yaml.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
        for kind, name in (("volume", volume), ("network", network)):
            result = _run(["docker", kind, "create", "--label", f"{OWNER_LABEL}={nonce}", name])
            assert result.returncode == 0, "owned resource creation failed"
            owned.remember(kind, name)
        deploy = root / "deploy"
        (deploy / "secrets").mkdir(parents=True, exist_ok=True)
        env_file = deploy / "env.production"
        env_file.write_text(
            "\n".join(
                [
                    "DJANGO_SETTINGS_MODULE=slaif_reservation.config.settings.production",
                    f"SLAIF_DJANGO_SECRET_KEY={secret}",
                    "SLAIF_DEBUG=false",
                    "SLAIF_ALLOWED_HOSTS=127.0.0.1",
                    "SLAIF_CSRF_TRUSTED_ORIGINS=https://127.0.0.1",
                    f"SLAIF_API_TOKEN_PEPPER={pepper}",
                    f"DATABASE_URL=postgres://slaif:{db_password}@db:5432/slaif_reservation?connect_timeout=5",
                    "SLAIF_TRUSTED_PROXY_PEERS=127.0.0.1,::1",
                    "SLAIF_ENABLE_API_DOCS=false",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        env_file.chmod(0o600)
        (deploy / "secrets" / "postgres_password").write_text(db_password, encoding="utf-8")

        branding_dir = deploy / "branding"
        branding_dir.mkdir()
        for name in ("logo.png", "logo-compact.png", "favicon.png", "hero.svg", "style.css"):
            shutil.copy(CUSTOM / name, branding_dir / name)

        compose_base = [
            "docker",
            "compose",
            "-p",
            project,
            "-f",
            str(prod_yaml),
        ]
        compose_brand = compose_base + [
            "-f",
            str(snapshot / "compose.branding.example.yaml"),
        ]
        compose_env = {"SLAIF_APP_HOST_PORT": "0"}

        # 5. Default run first: the same built image without the overlay.
        up = _run(compose_base + ["up", "-d", "db"], env=compose_env, timeout=300)
        for name in (f"{project}-app-1", f"{project}-db-1"):
            owned.remember("container", name)
        assert up.returncode == 0, "owned application start failed"
        _wait_healthy(f"{project}-db-1")
        migrate = _run(
            [
                "docker",
                "run",
                "--rm",
                "--name",
                f"{project}-migrate",
                "--label",
                f"{OWNER_LABEL}={nonce}",
                "--network",
                f"{project}_default",
                "--env-file",
                str(env_file),
                tag,
                "python",
                "manage.py",
                "migrate",
                "--noinput",
            ],
            timeout=600,
        )
        assert migrate.returncode == 0, (migrate.stdout + migrate.stderr)[-2000:]
        up = _run(compose_base + ["up", "-d"], env=compose_env, timeout=300)
        for name in (f"{project}-app-1", f"{project}-db-1"):
            owned.remember("container", name)
        assert up.returncode == 0, "owned application start failed"
        _wait_healthy(f"{project}-app-1")

        app_container = f"{project}-app-1"
        state = _run(
            [
                "docker",
                "inspect",
                "--format",
                "{{.Config.User}}|{{.HostConfig.ReadonlyRootfs}}",
                app_container,
            ]
        )
        assert state.stdout.strip() == "10001:10001|true"

        status, body = _in_app_get(app_container, "/")
        assert status == 200
        default_html = body.decode()
        assert "/branding/hero" not in default_html
        # Production serves the packaged logo under its manifest name.
        assert "/static/web/brand/slaif-logo." in default_html
        status, css_body = _in_app_get(app_container, "/branding/style.css")
        assert status == 200 and css_body == b""
        status, logo_body = _in_app_get(app_container, "/branding/logo")
        assert status == 200 and logo_body == DEFAULT_LOGO_BYTES
        status, _ = _in_app_get(app_container, "/health/live")
        assert status == 200
        status, _ = _in_app_get(app_container, "/health/ready")
        assert status == 200

        # 6. Branding run: same project and image, overlay added.
        up = _run(compose_brand + ["up", "-d"], env=compose_env, timeout=300)
        for name in (f"{project}-app-1", f"{project}-db-1"):
            owned.remember("container", name)
        assert up.returncode == 0, "owned application start failed"
        _wait_healthy(app_container)

        status, body = _in_app_get(app_container, "/")
        assert status == 200
        branded_html = body.decode()
        for marker in (
            "/branding/hero",
            "/branding/logo",
            "/branding/favicon",
            "/branding/style.css",
        ):
            assert marker in branded_html
        status, css_body = _in_app_get(app_container, "/branding/style.css")
        assert status == 200
        assert css_body == (branding_dir / "style.css").read_bytes()
        status, logo_body = _in_app_get(app_container, "/branding/logo")
        assert status == 200
        assert logo_body == (branding_dir / "logo.png").read_bytes()
        status, favicon_body = _in_app_get(app_container, "/branding/favicon")
        assert favicon_body == (branding_dir / "favicon.png").read_bytes()
        status, _ = _in_app_get(app_container, "/login/")
        assert status == 200
        status, _ = _in_app_get(app_container, "/health/ready")
        assert status == 200

        # 7. The app cannot write to the mounted (read-only) directory.
        for attempt in (
            "echo x >> /branding/style.css",
            "echo x > /branding/evil.txt",
            "rm /branding/logo.png",
        ):
            refused = _run(["docker", "exec", app_container, "sh", "-c", attempt], timeout=30)
            assert refused.returncode != 0
        assert (branding_dir / "logo.png").exists()
        assert not (branding_dir / "evil.txt").exists()

        # 8. Fallback inside the container: one invalid asset does not break
        #    the page or the other slots.
        (branding_dir / "logo-compact.png").write_bytes(b"<html>invalid</html>")
        status, body = _in_app_get(app_container, "/login/")
        assert status == 200
        fallback_html = body.decode()
        assert "/branding/logo" in fallback_html
        assert "/branding/style.css" in fallback_html
        assert "/static/web/brand/slaif-logo." in fallback_html
        status, compact_body = _in_app_get(app_container, "/branding/logo-compact")
        assert status == 200 and compact_body == DEFAULT_LOGO_BYTES
    finally:
        # Record partial creations too; never adopt foreign objects or delete
        # names for which this run has no verified creation receipt.
        try:
            for kind, name in (
                ("image", tag),
                ("volume", volume),
                ("network", network),
                ("container", f"{project}-app-1"),
                ("container", f"{project}-db-1"),
                ("container", f"{project}-migrate"),
            ):
                if owned.inspect(kind, name) is not None:
                    owned.remember(kind, name)
        finally:
            try:
                owned.cleanup()
                if sentinel_owner.objects:
                    metadata = sentinel_owner.inspect("volume", sentinel)
                    assert metadata is not None, "foreign sentinel was removed"
                    assert metadata["Labels"][OWNER_LABEL] == nonce + "-sentinel"
            finally:
                sentinel_owner.cleanup()
                shutil.rmtree(root, ignore_errors=True)


def test_docker_children_ignore_foreign_configuration(monkeypatch) -> None:
    for key in (
        "DOCKER_HOST",
        "DOCKER_CONTEXT",
        "DOCKER_CERT_PATH",
        "DOCKER_CONFIG",
        "DATABASE_URL",
        "OAP_ROLE",
    ):
        monkeypatch.setenv(key, "foreign-synthetic-fixture")
    environment = _docker_env()
    assert environment["DOCKER_HOST"] == "unix:///var/run/docker.sock"
    assert set(environment) <= {"PATH", "TMPDIR", "DOCKER_HOST"}


def test_cleanup_never_deletes_uncreated_resources(monkeypatch) -> None:
    calls = []

    def refused(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 1, "", "synthetic refusal")

    monkeypatch.setattr(__import__(__name__, fromlist=["_run"]), "_run", refused)
    owned = _OwnedDocker("synthetic-owner")
    owned.cleanup()
    assert calls == []


def test_cleanup_refuses_changed_ownership(monkeypatch) -> None:
    owned = _OwnedDocker("synthetic-owner")
    owned.objects[("volume", "synthetic-volume")] = ("synthetic-owner", "2026-10-05T00:00:00Z")
    monkeypatch.setattr(
        owned,
        "inspect",
        lambda *args: {
            "Name": "synthetic-volume",
            "Labels": {OWNER_LABEL: "foreign"},
            "CreatedAt": "2026-10-05T00:00:00Z",
        },
    )
    with pytest.raises(AssertionError, match="changed ownership"):
        owned.cleanup()


def test_early_build_failure_never_deletes_names(monkeypatch) -> None:
    calls = []

    def failed(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 1, "", "synthetic refusal")

    module = __import__(__name__, fromlist=["_run"])
    monkeypatch.setattr(module, "_docker_available", lambda: True)
    monkeypatch.setattr(module, "_run", failed)
    with pytest.raises(AssertionError, match="build failed"):
        test_docker_production_overlay_qualification()
    assert not any(
        command[1:3] in (["volume", "rm"], ["image", "rm"], ["rm", "-f"]) for command in calls
    )
