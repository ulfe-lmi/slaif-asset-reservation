"""Real-server Gunicorn responsiveness regression (OAP 031-a).

These tests launch the real installed Gunicorn with the real Django WSGI
application on a unique loopback port and exercise the anonymous
``/health/live`` and ``/login/`` GETs. They prove that the supported
deployment defaults (Dockerfile CMD, development Compose, production
Compose example) run the ``gthread`` worker pool, that held idle and
partial-header clients cannot starve new connections under that
pool, and that the old sync worker configuration actually starves
new connections under held idle clients (negative control).

Safety properties:

- anonymous ``/health/live`` and ``/login/`` GETs never touch the
  database; the child process gets a dead ``DATABASE_URL`` so any
  accidental database contact fails fast instead of reaching a
  foreign database;
- every server run is a subprocess in its own session with bounded
  setup/request/shutdown limits; children are terminated, force-killed
  and reaped even after a failed assertion;
- unique loopback ports and owned sockets only; no container, global
  signal, or shared-state cleanup.

Only status codes and latencies are asserted or recorded; no response
bodies, headers, cookies or CSRF values are captured.
"""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
BIND = "127.0.0.1"
# Anonymous live/login GETs are DB-free; a dead URL guarantees that no
# product database (foreign or otherwise) can be contacted by mistake.
DEAD_DATABASE_URL = "postgres://slaif:slaif@127.0.0.1:1/slaif_reservation"
PROBE_PATHS = ("/health/live", "/login/")
READINESS_DEADLINE_S = 30.0
PROMPT_MS = 2000.0
SYNC_PROBE_TIMEOUT_S = 1.5
SYNC_PROBE_ATTEMPTS = 2
SYNC_SETTLE_S = 1.5
HOLD_IDLE_COUNT = 6
HOLD_PARTIAL_COUNT = 6


def _free_port() -> int:
    sock = socket.socket()
    sock.bind((BIND, 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _get(
    port: int, path: str, read_timeout_s: float, host: str = BIND
) -> tuple[int | None, float, str]:
    """One request on a fresh connection. Returns (status|None, ms, note)."""
    started = time.monotonic()
    sock: socket.socket | None = None
    try:
        sock = socket.create_connection((BIND, port), timeout=3.0)
        sock.settimeout(read_timeout_s)
        sock.sendall(f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n".encode())
        data = sock.recv(8192)
        elapsed_ms = (time.monotonic() - started) * 1000.0
        if not data:
            return None, elapsed_ms, "empty-response"
        status_line = data.split(b"\r\n", 1)[0].decode("latin-1")
        return int(status_line.split(" ", 2)[1]), elapsed_ms, "ok"
    except TimeoutError:
        return None, (time.monotonic() - started) * 1000.0, "read-timeout"
    except OSError as exc:
        return None, (time.monotonic() - started) * 1000.0, f"connect:{type(exc).__name__}"
    finally:
        if sock is not None:
            sock.close()


def _held_state(sock: socket.socket) -> str:
    sock.setblocking(False)
    try:
        data = sock.recv(1)
    except BlockingIOError:
        return "held-open"
    except OSError:
        return "closed-error"
    return "data-arrived" if data else "eof"


def _open_idle_client(port: int, send_partial: bool) -> socket.socket:
    sock = socket.create_connection((BIND, port), timeout=3.0)
    if send_partial:
        # Request line plus one header, then stall: the missing blank-line
        # terminator keeps the server reading the header block.
        sock.sendall(b"GET /health/live HTTP/1.1\r\nHost: 127.0.0.1\r\n")
    return sock


def _open_kept_client(port: int) -> tuple[socket.socket, int | None]:
    """Full request, read the complete response, keep the connection open.

    The whole response (headers plus Content-Length body bytes) is drained
    so that a later non-blocking recv on the held socket sees no buffered
    data: only a truly idle keep-alive connection can then be observed.
    """
    sock = socket.create_connection((BIND, port), timeout=3.0)
    sock.settimeout(3.0)
    sock.sendall(f"GET /health/live HTTP/1.1\r\nHost: {BIND}\r\n\r\n".encode())
    buf = b""
    while buf.find(b"\r\n\r\n") < 0:
        chunk = sock.recv(8192)
        if not chunk:
            return sock, None
        buf += chunk
    head, body = buf.split(b"\r\n\r\n", 1)
    status_line = head.split(b"\r\n", 1)[0].decode("latin-1")
    status = int(status_line.split(" ", 2)[1])
    for line in head.decode("latin-1").split("\r\n")[1:]:
        name, _, value = line.partition(":")
        if name.strip().lower() == "content-length":
            while len(body) < int(value.strip()):
                chunk = sock.recv(8192)
                if not chunk:
                    break
                body += chunk
    return sock, status


class GunicornServer:
    """Real gunicorn subprocess with bounded setup and cleanup."""

    def __init__(self, args: list[str], label: str) -> None:
        self.port = _free_port()
        self.label = label
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "PYTHONPATH": str(REPO_ROOT / "src"),
            "DJANGO_SETTINGS_MODULE": "slaif_reservation.config.settings.test",
            "DATABASE_URL": DEAD_DATABASE_URL,
            "TEST_DATABASE_URL": DEAD_DATABASE_URL,
            "PYTHONUNBUFFERED": "1",
        }
        cmd = [
            sys.executable,
            "-m",
            "gunicorn",
            "slaif_reservation.config.wsgi:application",
            "--bind",
            f"{BIND}:{self.port}",
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

    def wait_ready(self) -> bool:
        deadline = time.monotonic() + READINESS_DEADLINE_S
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                return False
            status, _ms, _note = _get(self.port, "/health/live", read_timeout_s=2.0)
            if status == 200:
                return True
            time.sleep(0.25)
        return False

    def stop(self) -> int:
        """Terminate/kill/reap the whole session; return orphan count."""
        try:
            os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            self.proc.wait(timeout=10)
        orphans = 0
        marker = f"--bind {BIND}:{self.port}"
        for pid in os.listdir("/proc"):
            if not pid.isdigit():
                continue
            try:
                with open(f"/proc/{pid}/cmdline", "rb") as fh:
                    cmdline = fh.read().replace(b"\x00", b" ").decode("utf-8", "replace")
            except OSError:
                continue
            if marker in cmdline and int(pid) != self.proc.pid:
                orphans += 1
        return orphans

    def log_tail(self) -> str:
        try:
            tail = self.proc.stdout.read().splitlines()[-8:]
        except Exception:  # pragma: no cover - stream already consumed
            tail = []
        return "\n".join(tail)


def _require_ready(server: GunicornServer) -> None:
    if not server.wait_ready():
        server.stop()
        raise AssertionError(
            f"{server.label}: gunicorn did not become ready; log tail:\n{server.log_tail()}"
        )


# ---------------------------------------------------------------------------
# Supported command parsing
# ---------------------------------------------------------------------------


def _flags_from_tokens(tokens: list[str]) -> dict[str, str]:
    flags: dict[str, str] = {}
    i = 1  # skip the program name
    while i < len(tokens):
        token = tokens[i]
        if token.startswith("--"):
            flags[token[2:]] = tokens[i + 1]
            i += 2
        else:
            i += 1
    return flags


def _dockerfile_command() -> dict[str, str]:
    for line in (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("CMD ["):
            tokens = json.loads(stripped[len("CMD ") :])
            assert tokens[0] == "gunicorn", f"Dockerfile CMD is not gunicorn: {tokens[0]}"
            return _flags_from_tokens(tokens)
    raise AssertionError('Dockerfile has no CMD ["gunicorn", ...] line')


def _compose_command(path: Path) -> dict[str, str]:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    command = config["services"]["app"]["command"]
    assert isinstance(command, str), f"{path.name}: app command is not a string"
    tokens = command.split()
    assert tokens[0] == "gunicorn", f"{path.name}: app command is not gunicorn"
    return _flags_from_tokens(tokens)


def _supported_commands() -> dict[str, dict[str, str]]:
    return {
        "dockerfile": _dockerfile_command(),
        "compose.yaml": _compose_command(REPO_ROOT / "compose.yaml"),
        "compose.production.example.yaml": _compose_command(
            REPO_ROOT / "compose.production.example.yaml"
        ),
    }


def _shipped_gthread_args() -> list[str]:
    """Pool flags exactly as declared by the supported defaults (Dockerfile)."""
    flags = _dockerfile_command()
    return [
        "--workers",
        flags["workers"],
        "--threads",
        flags["threads"],
        "--keep-alive",
        flags["keep-alive"],
        "--timeout",
        flags["timeout"],
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_supported_commands_declare_gthread_baseline() -> None:
    """Reverting any supported default back to the sync pool is caught here."""
    commands = _supported_commands()
    for name, flags in commands.items():
        assert flags.get("bind") == "0.0.0.0:8000", f"{name}: bind changed"
        assert flags.get("workers") == "3", f"{name}: workers changed"
        # gthread is only active with threads > 1; the baseline is 8.
        assert flags.get("threads") == "8", f"{name}: gthread baseline (8 threads) missing"
        assert flags.get("keep-alive") == "5", f"{name}: keep-alive baseline changed"
        assert flags.get("timeout") == "30", f"{name}: worker timeout baseline changed"
    production = commands["compose.production.example.yaml"]
    assert production.get("access-logfile") == "-", "production: access log flag lost"
    assert production.get("error-logfile") == "-", "production: error log flag lost"


def test_gthread_serves_promptly_with_held_idle_clients() -> None:
    """Kept-alive idle connections must not delay new requests (gthread)."""
    server = GunicornServer(_shipped_gthread_args(), label="gthread-idle")
    held: list[socket.socket] = []
    try:
        _require_ready(server)
        for path in PROBE_PATHS:
            status, ms, note = _get(server.port, path, read_timeout_s=2.0)
            assert status == 200 and ms < PROMPT_MS, f"warm {path}: {status} {ms:.1f}ms ({note})"

        for _ in range(HOLD_IDLE_COUNT):
            sock, status = _open_kept_client(server.port)
            assert status == 200, "kept client did not receive a 200"
            held.append(sock)

        for path in PROBE_PATHS:
            status, ms, note = _get(server.port, path, read_timeout_s=3.0)
            assert status == 200 and ms < PROMPT_MS, (
                f"probe {path} while {len(held)} idle clients held: {status} {ms:.1f}ms ({note})"
            )
        states = [_held_state(sock) for sock in held]
        assert all(state == "held-open" for state in states), f"held clients not held: {states}"
    finally:
        for sock in held:
            sock.close()
        server.stop()


def test_gthread_serves_promptly_with_partial_header_clients() -> None:
    """Slow clients stalling in the header block must not delay new requests."""
    server = GunicornServer(_shipped_gthread_args(), label="gthread-partial")
    partial: list[socket.socket] = []
    try:
        _require_ready(server)
        for path in PROBE_PATHS:
            status, ms, note = _get(server.port, path, read_timeout_s=2.0)
            assert status == 200 and ms < PROMPT_MS, f"warm {path}: {status} {ms:.1f}ms ({note})"

        for _ in range(HOLD_PARTIAL_COUNT):
            partial.append(_open_idle_client(server.port, send_partial=True))

        for path in PROBE_PATHS:
            status, ms, note = _get(server.port, path, read_timeout_s=3.0)
            assert status == 200 and ms < PROMPT_MS, (
                f"probe {path} while {len(partial)} partial-header clients held: "
                f"{status} {ms:.1f}ms ({note})"
            )
    finally:
        for sock in partial:
            sock.close()
        server.stop()


def test_old_sync_configuration_starves_new_connections() -> None:
    """Negative control: the old sync 3-worker config must starve probes.

    A test that only opens sockets could falsely pass; this launches the
    real old configuration (sync pool, 3 workers) and expects held idle
    clients to make bounded probe attempts time out, then expects prompt
    recovery once the blockers close.
    """
    server = GunicornServer(["--workers", "3"], label="sync-3")
    held: list[socket.socket] = []
    try:
        _require_ready(server)
        for path in PROBE_PATHS:
            status, ms, note = _get(server.port, path, read_timeout_s=2.0)
            assert status == 200, f"warm {path}: {status} ({note})"

        for _ in range(HOLD_IDLE_COUNT):
            held.append(_open_idle_client(server.port, send_partial=False))
        time.sleep(SYNC_SETTLE_S)  # workers accept and start blocking reads

        for path in PROBE_PATHS:
            for attempt in range(SYNC_PROBE_ATTEMPTS):
                status, ms, note = _get(server.port, path, read_timeout_s=SYNC_PROBE_TIMEOUT_S)
                assert status is None, (
                    f"sync negative control lost sensitivity: {path} "
                    f"attempt {attempt + 1} answered {status} in {ms:.1f}ms while held"
                )
                assert note == "read-timeout", f"sync probe {path}: unexpected {note}"
        states = [_held_state(sock) for sock in held]
        assert all(state == "held-open" for state in states), f"held clients not held: {states}"

        for sock in held:
            sock.close()
        time.sleep(0.5)
        for path in PROBE_PATHS:
            status, ms, note = _get(server.port, path, read_timeout_s=3.0)
            assert status == 200 and ms < PROMPT_MS, (
                f"recovery {path}: {status} {ms:.1f}ms ({note})"
            )
    finally:
        for sock in held:
            sock.close()
        orphans = server.stop()
    assert orphans == 0, f"orphan gunicorn children after shutdown: {orphans}"


def test_gthread_shutdown_cleans_children_on_failure() -> None:
    """Shutdown must reap the whole server session even after a failure."""
    server = GunicornServer(["--workers", "2", "--threads", "4"], label="cleanup")
    held: list[socket.socket] = []
    try:
        assert server.wait_ready(), f"server not ready; log tail:\n{server.log_tail()}"
        held.append(_open_idle_client(server.port, send_partial=True))
        held.append(_open_idle_client(server.port, send_partial=True))
        time.sleep(0.5)  # let the pool threads block on the header reads
        orphans = server.stop()
        assert orphans == 0, f"orphan gunicorn children after shutdown: {orphans}"
    finally:
        for sock in held:
            sock.close()
