"""Real Gunicorn trust-boundary, parser-privacy and stall regressions (OAP 033-a).

These tests launch the real installed Gunicorn 23 with the real Django WSGI
application under the *production* settings (synthetic SLAIF_* environment,
dead database) and prove the boundary below the Django test client:

- the explicitly configured trusted-proxy peer list is the only source of
  TLS/client-identity forwarding: a trusted loopback peer's
  ``X-Forwarded-Proto`` is honored and a missing header falls back to the
  real plain-HTTP transport (301 under ``SECURE_SSL_REDIRECT``);
- an untrusted peer (a real TCP source address outside the trusted
  /32, reached over loopback) cannot forward even with a full spoofed
  header set;
- a *server-derived* ``wsgi.url_scheme`` (Gunicorn's own
  ``forwarded-allow-ips`` handling) cannot bypass the middleware trust
  list: an untrusted 127.0.0.1 peer with the shipped
  ``--forwarded-allow-ips 127.0.0.1,::1`` and ``X-Forwarded-Proto: https``
  still receives a 301, and an underscore wire variant never yields 200;
- Gunicorn's parser/access logs retain neither a malformed raw request
  line nor a request target/query: canary bytes sent at the parser and in
  the URL are absent from the captured log while the safe JSON categories
  are present;
- an oversized multipart POST with a *valid* CSRF token (small/large
  controls that reach the actual body limit, never an early 403/301
  false pass) is rejected with 400 at DATA_UPLOAD_MAX_MEMORY_SIZE before
  any view runs, and the pool stays responsive;
- stalled partial-header clients do not delay ``/health/live`` on the
  shipped production command line.

Safety properties mirror ``test_gunicorn_responsiveness.py``: every server
run is a bounded subprocess in its own session (terminated, force-killed,
reaped and orphan-audited), unique ports on owned interfaces, a dead
``DATABASE_URL`` so no product database can be contacted by mistake, and
finite log reads. Only status codes, header categories and latencies are
asserted; no response bodies or recorded CSRF material — the one-time
CSRF cookie value needed by the body-limit controls is held in
memory only and never printed, logged or asserted on.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest
from tests import test_gunicorn_responsiveness as gtr
from tests.test_gunicorn_responsiveness import (
    BIND,
    DEAD_DATABASE_URL,
    READINESS_DEADLINE_S,
    GunicornServer,
    _compose_command,
    _dockerfile_command,
    _free_port,
    _open_idle_client,
)
from tests.test_settings import (
    TEST_PRODUCTION_API_TOKEN_PEPPER,
    TEST_PRODUCTION_SECRET_KEY,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PROMPT_MS = 2000.0
SETTLE_S = 1.5
LOOPBACK_PEERS = "127.0.0.1,::1"
# A loopback source address outside the trusted 127.0.0.1/32: the
# untrusted-peer negative control binds its client socket here, keeping
# the test fully inside owned loopback resources (no LAN-facing
# listener, no probing of external or private hosts).
UNTRUSTED_LOOPBACK_PEER = "127.0.0.2"
# An explicit peer that matches no local interface: every real peer,
# including 127.0.0.1, is untrusted.
NO_LOCAL_PEERS = "198.51.100.10"
MALFORMED_CANARY = "oap033a-malformed-canary"
QUERY_CANARY = "oap033a-query-canary"
PATH_CANARY = "oap033a-path-canary"
OVERSIZED_BODY_BYTES = 3_000_000  # above Django's 2.5 MiB default body limit


class ProductionGunicornServer(GunicornServer):
    """Real gunicorn subprocess running the production settings.

    Same ownership and bounded-teardown contract as ``GunicornServer``;
    only the WSGI environment differs (production settings module plus a
    synthetic SLAIF_* environment) and the bind host may be non-loopback.
    """

    def __init__(
        self,
        args: list[str],
        label: str,
        trusted_peers: str,
        *,
        bind_host: str = BIND,
        allowed_hosts: str = "127.0.0.1",
    ) -> None:
        self._bind_host = bind_host
        self.port = _free_port()
        self.label = label
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "PYTHONPATH": str(REPO_ROOT / "src"),
            "DJANGO_SETTINGS_MODULE": "slaif_reservation.config.settings.production",
            "DATABASE_URL": DEAD_DATABASE_URL,
            "SLAIF_DJANGO_SECRET_KEY": TEST_PRODUCTION_SECRET_KEY,
            "SLAIF_ALLOWED_HOSTS": allowed_hosts,
            "SLAIF_CSRF_TRUSTED_ORIGINS": "https://127.0.0.1",
            "SLAIF_TRUSTED_PROXY_PEERS": trusted_peers,
            "SLAIF_API_TOKEN_PEPPER": TEST_PRODUCTION_API_TOKEN_PEPPER,
            "PYTHONUNBUFFERED": "1",
        }
        cmd = [
            sys.executable,
            "-m",
            "gunicorn",
            "slaif_reservation.config.wsgi:application",
            "--bind",
            f"{bind_host}:{self.port}",
            *args,
        ]
        self.proc = subprocess.Popen(
            cmd,
            cwd=REPO_ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        self._stopped = False
        self._orphans = 0

    def wait_ready(self) -> bool:
        deadline = time.monotonic() + READINESS_DEADLINE_S
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                return False
            # The same probe contract as the production Compose healthcheck:
            # a loopback request carrying X-Forwarded-Proto. 200 means the
            # trusted transport is honored; 301 means the stack is up and
            # (for an untrusted probe peer) the redirect fires. Either proves
            # a live server; anything else (5xx, refused, timeout) does not.
            status, _h, _ms, _note = _request(
                self._bind_host,
                self.port,
                "/health/live",
                headers={"X-Forwarded-Proto": "https"},
                read_timeout_s=2.0,
            )
            if status in (200, 301):
                return True
            time.sleep(0.25)
        return False

    def stop(self) -> int:
        # The parent orphan audit matches on "--bind <BIND>:<port>"; point
        # it at the actual bind host for non-loopback servers.
        original_bind = gtr.BIND
        gtr.BIND = self._bind_host
        try:
            return super().stop()
        finally:
            gtr.BIND = original_bind

    def full_log(self) -> str:
        """The entire captured log; valid only after ``stop()`` (EOF)."""
        assert self._stopped, "full_log must run after bounded teardown"
        try:
            return self.proc.stdout.read()
        except Exception:  # pragma: no cover - stream already consumed
            return ""


def _shipped_production_args(source: str = "dockerfile") -> list[str]:
    """The production command line exactly as declared by ``source``.

    ``source`` is ``"dockerfile"`` (access log off by default) or
    ``"compose"`` (the production Compose example, which pins
    ``--access-logfile -``/``--error-logfile -``). Both shared flags must
    be declared identically; the access/error logfile pins are carried
    when present.
    """
    flags = (
        _dockerfile_command()
        if source == "dockerfile"
        else _compose_command(REPO_ROOT / "compose.production.example.yaml")
    )
    for name in (
        "workers",
        "threads",
        "keep-alive",
        "timeout",
        "forwarded-allow-ips",
        "header-map",
        "logger-class",
    ):
        assert name in flags, f"{source} command is missing --{name}"
    args = [
        "--workers",
        flags["workers"],
        "--threads",
        flags["threads"],
        "--keep-alive",
        flags["keep-alive"],
        "--timeout",
        flags["timeout"],
        "--forwarded-allow-ips",
        flags["forwarded-allow-ips"],
        "--header-map",
        flags["header-map"],
        "--logger-class",
        flags["logger-class"],
    ]
    for name in ("access-logfile", "error-logfile"):
        if name in flags:
            args += [f"--{name}", flags[name]]
    return args


def _ready(server: GunicornServer) -> None:
    if not server.wait_ready():
        server.stop()
        raise AssertionError(
            f"{server.label}: gunicorn did not become ready; log tail:\n{server.log_tail()}"
        )


def _request(
    host: str,
    port: int,
    path: str,
    headers: dict[str, str] | None = None,
    read_timeout_s: float = 5.0,
    bind_addr: str | None = None,
) -> tuple[int | None, dict[str, str] | None, float, str]:
    """One raw HTTP/1.1 GET; returns (status|None, headers|None, ms, note).

    ``bind_addr`` pins the client socket's local (source) address, used by
    the untrusted-peer control to present a real TCP source outside the
    trusted peer list while staying on loopback.
    """
    started = time.monotonic()
    sock: socket.socket | None = None
    try:
        if bind_addr:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.bind((bind_addr, 0))
            sock.connect((host, port))
        else:
            sock = socket.create_connection((host, port), timeout=3.0)
        sock.settimeout(read_timeout_s)
        all_headers = {"Host": host, "Connection": "close", **(headers or {})}
        raw = f"GET {path} HTTP/1.1\r\n"
        for name, value in all_headers.items():
            raw += f"{name}: {value}\r\n"
        raw += "\r\n"
        sock.sendall(raw.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = sock.recv(8192)
            if not chunk:
                break
            buf += chunk
        if b"\r\n\r\n" not in buf:
            return (
                None,
                None,
                (time.monotonic() - started) * 1000.0,
                "incomplete",
            )
        head = buf.split(b"\r\n\r\n", 1)[0].decode("latin-1")
        lines = head.split("\r\n")
        status = int(lines[0].split(" ", 2)[1])
        resp_headers: dict[str, str] = {}
        for line in lines[1:]:
            name, _, value = line.partition(":")
            resp_headers[name.strip().lower()] = value.strip()
        return status, resp_headers, (time.monotonic() - started) * 1000.0, "ok"
    except TimeoutError:
        return (
            None,
            None,
            (time.monotonic() - started) * 1000.0,
            "read-timeout",
        )
    except OSError as exc:
        return (
            None,
            None,
            (time.monotonic() - started) * 1000.0,
            f"connect:{type(exc).__name__}",
        )
    finally:
        if sock is not None:
            sock.close()


def _raw_exchange(
    host: str, port: int, payload: bytes, read_timeout_s: float = 5.0
) -> tuple[bytes, str]:
    """Send arbitrary bytes (a hostile client may send anything) and read."""
    sock: socket.socket | None = None
    try:
        sock = socket.create_connection((host, port), timeout=3.0)
        sock.settimeout(read_timeout_s)
        sock.sendall(payload)
        chunks: list[bytes] = []
        try:
            while True:
                chunk = sock.recv(8192)
                if not chunk:
                    break
                chunks.append(chunk)
                if b"\r\n\r\n" in b"".join(chunks):
                    break
        except TimeoutError:
            return b"".join(chunks), "read-timeout"
        return b"".join(chunks), "ok"
    except OSError as exc:
        return b"", f"connect:{type(exc).__name__}"
    finally:
        if sock is not None:
            sock.close()


def _fetch_csrf_cookie(port: int) -> str:
    """GET /login/ from the trusted loopback peer; return the ``csrftoken=``
    cookie header value.

    The value is held in memory for the CSRF controls and is never
    recorded, printed or asserted on (SAR-015: one-time secret handling).
    """
    status, headers, _ms, note = _request(BIND, port, "/login/", {"X-Forwarded-Proto": "https"})
    if status != 200:
        raise AssertionError(f"login GET before CSRF controls: {status} ({note})")
    for value in (headers or {}).values():
        if value.lower().startswith("csrftoken="):
            return value.split(";", 1)[0]
    raise AssertionError("login GET did not set the CSRF cookie")


def _send_multipart_post(
    port: int, *, csrf_cookie: str, field_size: int
) -> tuple[int | None, float, str]:
    """POST a multipart body with a *valid* CSRF token to /login/.

    The X-CSRFToken header carries the same value as the cookie, so the
    CSRF check passes and the request reaches body parsing: the small
    control reaches the view, the large control hits
    DATA_UPLOAD_MAX_MEMORY_SIZE. Only the status code, latency and a note
    are returned; the CSRF material itself is never returned or logged.
    """
    boundary = "----slaif033a-oversized-boundary"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="payload"\r\n'
        "Content-Type: text/plain\r\n\r\n".encode()
        + b"x" * field_size
        + f"\r\n--{boundary}--\r\n".encode()
    )
    # A secure request without an Origin header would be rejected by the
    # CSRF referer check; the supported browser contract sends the exact
    # trusted origin, which the production settings allowlist.
    head = (
        f"POST /login/ HTTP/1.1\r\n"
        f"Host: {BIND}\r\n"
        "X-Forwarded-Proto: https\r\n"
        f"Origin: https://{BIND}\r\n"
        f"Cookie: {csrf_cookie}\r\n"
        f"X-CSRFToken: {csrf_cookie.split('=', 1)[1]}\r\n"
        f"Content-Type: multipart/form-data; boundary={boundary}\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    sock = socket.create_connection((BIND, port), timeout=3.0)
    started = time.monotonic()
    sender_error: list[str] = []

    def _send() -> None:
        try:
            sock.sendall(head.encode() + body)
        except OSError as exc:
            sender_error.append(type(exc).__name__)

    sender = threading.Thread(target=_send, name="oap-033a-multipart-send", daemon=True)
    sender.start()
    status: int | None = None
    note = "ok"
    try:
        sock.settimeout(10.0)
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = sock.recv(8192)
            if not chunk:
                note = "eof-before-response"
                break
            buf += chunk
        if b"\r\n\r\n" in buf:
            status = int(buf.split(b"\r\n", 1)[0].split(b" ", 2)[1])
        elif not sender_error:
            note = "no-response"
    except TimeoutError:
        note = "read-timeout"
    except OSError as exc:
        note = f"socket:{type(exc).__name__}"
    finally:
        sock.close()
        sender.join(timeout=5.0)
        if sender.is_alive() and not sender_error:
            note = f"send-stuck:{note}"
    return status, (time.monotonic() - started) * 1000.0, note


@pytest.fixture(scope="module", autouse=True)
def _collected_staticfiles() -> None:
    """Collect static assets once per module, mirroring the image build.

    The production staticfiles backend is a manifest storage that requires
    collected assets (the Dockerfile runs collectstatic at build time);
    anonymous page GETs like ``/login/`` render ``{% static %}`` tags.
    ``staticfiles/`` is a gitignored build artifact of this repository.
    """
    result = subprocess.run(
        [sys.executable, "manage.py", "collectstatic", "--no-input", "--clear"],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "DJANGO_SETTINGS_MODULE": "slaif_reservation.config.settings.local",
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"collectstatic failed:\n{result.stdout}\n{result.stderr}"


# ---------------------------------------------------------------------------
# Trust matrix on the real server
# ---------------------------------------------------------------------------


def test_trusted_loopback_peer_forwards_and_missing_header_falls_back_to_http() -> None:
    server = ProductionGunicornServer(_shipped_production_args(), "trusted-peer", LOOPBACK_PEERS)
    try:
        _ready(server)

        status, _h, _ms, note = _request(
            BIND, server.port, "/login/", {"X-Forwarded-Proto": "https"}
        )
        assert status == 200, (
            f"trusted peer X-Forwarded-Proto https must be honored: {status} ({note})"
        )

        status, headers, _ms, note = _request(BIND, server.port, "/login/")
        assert status == 301, (
            f"trusted peer without X-Forwarded-Proto must fall back to the "
            f"plain transport: {status} ({note})"
        )
        assert headers is not None
        assert headers.get("location", "").startswith("https://127.0.0.1")
        assert headers.get("location", "").endswith("/login/")

        # One-hop XFF: a single valid IP normalizes; forwarding still works.
        status, _h, _ms, note = _request(
            BIND,
            server.port,
            "/login/",
            {"X-Forwarded-Proto": "https", "X-Forwarded-For": "203.0.113.77"},
        )
        assert status == 200, (
            f"single-IP X-Forwarded-For from a trusted peer must not break "
            f"forwarding: {status} ({note})"
        )

        # Ambiguous XFF: identity falls back to the peer, scheme still honored.
        status, _h, _ms, note = _request(
            BIND,
            server.port,
            "/login/",
            {"X-Forwarded-Proto": "https", "X-Forwarded-For": "203.0.113.77, 203.0.113.78"},
        )
        assert status == 200, (
            f"ambiguous X-Forwarded-For must fall back to the peer, not reject: {status} ({note})"
        )

        # An invalid X-Forwarded-Proto value falls back to the plain transport.
        status, _h, _ms, note = _request(BIND, server.port, "/login/", {"X-Forwarded-Proto": "ftp"})
        assert status == 301, (
            f"invalid X-Forwarded-Proto value must fall back to http: {status} ({note})"
        )
    finally:
        server.stop()


def test_untrusted_loopback_peer_cannot_forward() -> None:
    # The server binds 127.0.0.1 and trusts exactly 127.0.0.1/32. The
    # client binds its local address to 127.0.0.2, so its genuine TCP
    # source address is a loopback peer outside the trust list: forwarding
    # must not apply. Everything stays inside owned loopback resources.
    server = ProductionGunicornServer(_shipped_production_args(), "untrusted-peer", "127.0.0.1/32")
    try:
        _ready(server)
        status, headers, _ms, note = _request(
            BIND,
            server.port,
            "/login/",
            {"X-Forwarded-Proto": "https", "X-Forwarded-For": "127.0.0.1"},
            bind_addr=UNTRUSTED_LOOPBACK_PEER,
        )
        assert status == 301, f"untrusted peer must not forward scheme or client: {status} ({note})"
        assert headers is not None
        assert headers.get("location", "").startswith("https://")

        status, _h, _ms, note = _request(
            BIND, server.port, "/login/", bind_addr=UNTRUSTED_LOOPBACK_PEER
        )
        assert status == 301, f"untrusted peer without headers: {status} ({note})"
    finally:
        server.stop()


def test_server_derived_scheme_and_underscore_variant_cannot_bypass_trust() -> None:
    # Peers: an explicit address matching no local interface, so 127.0.0.1
    # itself is untrusted. The shipped --forwarded-allow-ips still contains
    # 127.0.0.1, so Gunicorn's own layer derives wsgi.url_scheme=https from
    # X-Forwarded-Proto before the middleware runs: the middleware must
    # undo that server-derived scheme for the untrusted peer.
    server = ProductionGunicornServer(_shipped_production_args(), "scheme-bypass", NO_LOCAL_PEERS)
    try:
        _ready(server)
        status, _h, _ms, note = _request(
            BIND, server.port, "/login/", {"X-Forwarded-Proto": "https"}
        )
        assert status == 301, (
            f"server-derived https scheme bypassed the middleware trust list: {status} ({note})"
        )

        # Underscore wire variant: the shipped --header-map drop discards it
        # at the parser, and even if it survived, the untrusted-peer branch
        # strips it. It must never produce a 200.
        status, _h, _ms, note = _request(
            BIND, server.port, "/login/", {"X_Forwarded_Proto": "https"}
        )
        assert status in (301, 400), (
            f"underscore X-Forwarded-Proto variant must never forward: {status} ({note})"
        )
    finally:
        server.stop()


# ---------------------------------------------------------------------------
# Parser and access log privacy on the real server
# ---------------------------------------------------------------------------


def test_gunicorn_parser_log_omits_malformed_request_line() -> None:
    server = ProductionGunicornServer(_shipped_production_args(), "parser-privacy", LOOPBACK_PEERS)
    try:
        _ready(server)
        # A NUL byte in the method is rejected by the Gunicorn parser
        # (RFC 9110 token / method-length checks), so the canary travels in
        # the raw rejected text only.
        payload = (
            f"GET\x00{MALFORMED_CANARY} /health/live HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n"
        ).encode()
        data, note = _raw_exchange(BIND, server.port, payload)
        assert note == "ok", f"raw exchange failed: {note}"
        assert data, "no response to malformed request line"
        status_line = data.split(b"\r\n", 1)[0]
        status = int(status_line.split(b" ", 2)[1])
        assert status == 400, f"malformed request line must be 400, got {status}"
        assert MALFORMED_CANARY.encode() not in data
    finally:
        server.stop()
    log = server.full_log()
    assert MALFORMED_CANARY not in log, "raw malformed request line retained in the gunicorn log"
    assert '"category":"invalid-request"' in log, (
        "safe invalid-request category missing from the gunicorn log"
    )


def test_gunicorn_access_log_omits_request_target_and_query() -> None:
    # The production Compose example enables the access log (--access-logfile
    # -); the Dockerfile command leaves it off, which is equally safe (there
    # is nothing to leak). This exercises the enabled case with the safe
    # formatter.
    server = ProductionGunicornServer(
        _shipped_production_args("compose"), "access-privacy", LOOPBACK_PEERS
    )
    try:
        _ready(server)
        status, _h, _ms, note = _request(
            BIND,
            server.port,
            f"/login/?probe={QUERY_CANARY}",
            headers={"X-Forwarded-Proto": "https"},
        )
        assert status == 200, f"trusted login GET with query: {status} ({note})"

        # A 404 with a hostile path exercises the app, Django and gunicorn
        # log entry points at once.
        status, _h, _ms, note = _request(
            BIND,
            server.port,
            f"/no-such-page/{PATH_CANARY}/",
            headers={"X-Forwarded-Proto": "https"},
        )
        assert status == 404, f"hostile path must 404: {status} ({note})"
    finally:
        server.stop()
    log = server.full_log()
    assert QUERY_CANARY not in log, "query string retained in the gunicorn log"
    assert PATH_CANARY not in log, "hostile path retained in the gunicorn log"
    assert '"category":"access"' in log, "safe access category missing from the log"


# ---------------------------------------------------------------------------
# Bounded oversized input and stalled clients on the production pool
# ---------------------------------------------------------------------------


def test_oversized_post_is_bounded_and_pool_stays_responsive() -> None:
    # Small/large controls with a valid CSRF token prove the oversized
    # rejection happens at the actual body limit, not by an early 403
    # (missing CSRF before body parsing) or a 301 redirect false pass.
    server = ProductionGunicornServer(_shipped_production_args(), "oversized-post", LOOPBACK_PEERS)
    try:
        _ready(server)
        csrf_cookie = _fetch_csrf_cookie(server.port)

        # Small control: valid CSRF and a small body must pass CSRF and
        # body parsing and reach the view. With the dead database the
        # invalid login form re-renders (200) without touching the DB.
        small_status, small_ms, small_note = _send_multipart_post(
            server.port, csrf_cookie=csrf_cookie, field_size=1024
        )
        assert small_status == 200, (
            f"small control must reach the view (200 form re-render), "
            f"got {small_status} after {small_ms:.1f}ms ({small_note})"
        )

        # Large control: valid CSRF and a non-file field above
        # DATA_UPLOAD_MAX_MEMORY_SIZE (2.5 MiB) must be rejected with 400
        # while parsing the body, before any view runs.
        large_status, large_ms, large_note = _send_multipart_post(
            server.port, csrf_cookie=csrf_cookie, field_size=OVERSIZED_BODY_BYTES
        )
        assert large_status == 400, (
            f"oversized POST must be rejected at the body limit with 400, "
            f"got {large_status} after {large_ms:.1f}ms ({large_note})"
        )
        assert large_ms < 15_000.0, f"oversized POST handling was not bounded: {large_ms:.1f}ms"

        # The pool must still serve immediately (dead database: no view may
        # need it). The trusted loopback probe carries X-Forwarded-Proto.
        for _ in range(3):
            hstatus, _h, hms, hnote = _request(
                BIND,
                server.port,
                "/health/live",
                headers={"X-Forwarded-Proto": "https"},
                read_timeout_s=3.0,
            )
            assert hstatus == 200 and hms < PROMPT_MS, (
                f"health after oversized POST: {hstatus} {hms:.1f}ms ({hnote})"
            )
    finally:
        server.stop()


def test_partial_header_clients_do_not_stall_production_pool() -> None:
    server = ProductionGunicornServer(_shipped_production_args(), "partial-stall", LOOPBACK_PEERS)
    partial: list[socket.socket] = []
    try:
        _ready(server)
        for _ in range(2):
            partial.append(_open_idle_client(server.port, send_partial=True))
        time.sleep(SETTLE_S)  # pool threads accept and stall on the header reads

        status, _h, ms, note = _request(
            BIND,
            server.port,
            "/health/live",
            headers={"X-Forwarded-Proto": "https"},
            read_timeout_s=3.0,
        )
        assert status == 200 and ms < PROMPT_MS, (
            f"health while 2 partial-header clients held: {status} {ms:.1f}ms ({note})"
        )

        for sock in partial:
            sock.setblocking(False)
            try:
                data = sock.recv(1)
            except BlockingIOError:
                state = "held-open"
            except OSError:
                state = "closed-error"
            else:
                state = "data-arrived" if data else "eof"
            assert state == "held-open", f"partial client not held: {state}"
    finally:
        for sock in partial:
            sock.close()
        orphans = server.stop()
    assert orphans == 0, f"orphan gunicorn children after shutdown: {orphans}"
