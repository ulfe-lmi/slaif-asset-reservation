"""Real-server Gunicorn responsiveness regression (OAP 031-a).

These tests launch the real installed Gunicorn with the real Django WSGI
application on a unique loopback port and exercise the anonymous
``/health/live`` and ``/login/`` GETs. They prove that the supported
deployment defaults (Dockerfile CMD, development Compose, production
Compose example) run the ``gthread`` worker pool, that held idle and
partial-header clients cannot starve new connections under that
pool, and that the old sync worker configuration actually starves
new connections under held idle and partial-header clients
(negative control, both held-client shapes).

Safety properties:

- anonymous ``/health/live`` and ``/login/`` GETs never touch the
  database; the child process gets a dead ``DATABASE_URL`` so any
  accidental database contact fails fast instead of reaching a
  foreign database;
- every server run is a subprocess in its own session with bounded
  setup/request/shutdown limits; the bounded stop is idempotent, and
  children are terminated, force-killed and reaped even when a
  readiness check or an assertion (including a deliberately injected
  one) fails before an explicit stop;
- log diagnostics are finite: while the server process is still alive,
  ``log_tail`` returns a bounded marker instead of blocking on the
  pipe, so a readiness-failure assertion can never be held up by its
  own failure message and its teardown always runs; after bounded
  teardown the stopped process's real log tail is readable;
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
import threading
import time
from pathlib import Path

import pytest
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
# Bounded settle so the server actually accepts the stalled clients and
# its workers/threads block on the missing bytes before probing; without
# it a probe could run before the blockers occupy the pool (false pass).
PARTIAL_SETTLE_S = 1.5
# Bounded liveness probe of the OLD unbounded-read behavior (031-c): a
# pipe read without EOF cannot return, so a reader still blocked after
# this wait proves the old failure message would hang the cleanup path.
OLD_READ_PROBE_S = 0.5
# Upper bound for the fixed diagnostics: log_tail must return promptly
# whether the process is alive (bounded marker) or stopped (EOF tail).
LOG_TAIL_PROMPT_MS = 500.0
# Budget for the full forced readiness-failure path: assertion message
# plus the bounded graceful/forced teardown and the orphan audit.
READINESS_FAILURE_PATH_MS = 15_000.0
# Returned by log_tail while the server process is still running.
LIVE_LOG_MARKER = (
    "log tail unavailable: gunicorn still running; "
    "bounded marker, full log readable after bounded teardown"
)


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
        self._stopped = False
        self._orphans = 0

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
        """Terminate/kill/reap the whole session; return the orphan count.

        Idempotent once complete: later calls return the recorded count
        without touching the session again. ``_stopped`` is set only
        after the full bounded teardown succeeded, so a ``finally`` chain
        that observes a mid-teardown failure can retry the teardown.
        """
        if self._stopped:
            return self._orphans
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
        self._orphans = 0
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
                self._orphans += 1
        self._stopped = True
        return self._orphans

    def log_tail(self) -> str:
        """Bounded log tail; finite even while the server process is alive.

        A ``stdout.read`` on a live process blocks until EOF, which would
        hold up an assertion message and its ``finally`` teardown (031-c).
        While the process is alive we return a bounded marker instead;
        after bounded teardown the pipe has reached EOF and the real tail
        (e.g. a stopped startup failure) is read.
        """
        if self.proc.poll() is None:
            return LIVE_LOG_MARKER
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
        time.sleep(PARTIAL_SETTLE_S)  # pool threads accept and stall on the header reads

        states = [_held_state(sock) for sock in partial]
        assert all(state == "held-open" for state in states), (
            f"partial clients not held before probing: {states}"
        )

        for path in PROBE_PATHS:
            status, ms, note = _get(server.port, path, read_timeout_s=3.0)
            assert status == 200 and ms < PROMPT_MS, (
                f"probe {path} while {len(partial)} partial-header clients held: "
                f"{status} {ms:.1f}ms ({note})"
            )

        states = [_held_state(sock) for sock in partial]
        assert all(state == "held-open" for state in states), (
            f"partial clients not held after probing: {states}"
        )
    finally:
        for sock in partial:
            sock.close()
        server.stop()


@pytest.mark.parametrize(
    "send_partial",
    [False, True],
    ids=["silent-idle", "partial-header"],
)
def test_old_sync_configuration_starves_new_connections(send_partial: bool) -> None:
    """Negative control: the old sync 3-worker config must starve probes.

    Runs for both held-client shapes: silent idle connections (workers
    blocked on the first request read) and partial-header connections
    (workers blocked inside the header block). A test that only opens
    sockets could falsely pass; this launches the real old configuration
    (sync pool, 3 workers) and expects held clients to make bounded probe
    attempts time out on both endpoints, then expects prompt recovery
    once the blockers close.
    """
    label = "sync-3-partial" if send_partial else "sync-3-idle"
    server = GunicornServer(["--workers", "3"], label=label)
    held: list[socket.socket] = []
    try:
        _require_ready(server)
        for path in PROBE_PATHS:
            status, ms, note = _get(server.port, path, read_timeout_s=2.0)
            assert status == 200, f"warm {path}: {status} ({note})"

        for _ in range(HOLD_IDLE_COUNT):
            held.append(_open_idle_client(server.port, send_partial=send_partial))
        time.sleep(SYNC_SETTLE_S)  # workers accept and block on the stalled reads

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
    """Shutdown must reap the whole server session even after a failure.

    The stop lives in ``finally``: a readiness failure or a failed
    assertion before the explicit stop must still terminate, force-kill
    and reap the owned session instead of leaking its children.
    """
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
        server.stop()  # idempotent; completes teardown when an earlier step failed


def test_gthread_cleanup_survives_injected_failure() -> None:
    """A deliberate failure inside the protected region still reaps the session.

    Regression closed in 031-b: the 031-a cleanup test only stopped the
    server on the happy path. Here the assertion is injected inside the
    try region, the ``finally`` must execute the bounded teardown, and
    the session audit must show no matching gunicorn children left. The
    outer ``finally`` stops the server too (idempotent), so this test
    cannot leak children on its own failure either.
    """
    server = GunicornServer(["--workers", "2", "--threads", "4"], label="cleanup-inject")
    held: list[socket.socket] = []
    orphans: int | None = None
    try:
        assert server.wait_ready(), f"server not ready; log tail:\n{server.log_tail()}"
        held.append(_open_idle_client(server.port, send_partial=True))
        held.append(_open_idle_client(server.port, send_partial=True))
        time.sleep(0.5)  # let the pool threads block on the header reads
        with pytest.raises(AssertionError, match="injected protected-region failure"):
            try:
                raise AssertionError("injected protected-region failure")
            finally:
                orphans = server.stop()
    finally:
        for sock in held:
            sock.close()
        server.stop()  # idempotent; also covers readiness failure above
    assert orphans == 0, f"orphan gunicorn children after injected-failure cleanup: {orphans}"


def test_readiness_failure_diagnostics_bounded_while_server_alive() -> None:
    """A readiness failure with the server still alive must not block cleanup.

    Regression closed in 031-c: the readiness-failure assertion message
    evaluated ``log_tail()``, which performed an unbounded ``stdout.read``
    on the still-alive process; that read blocks until EOF, so the
    assertion could not raise and its ``finally`` teardown could not run.
    The forced readiness result is fixture injection only: the gunicorn
    process, worker and loopback port are real. Sensitivity of the old
    behavior is demonstrated on the live process through an owned daemon
    reader thread with bounded coordination, joined after bounded
    teardown, so this test can neither hang nor leave the thread behind.
    This is a fixture-safety test: it complements, not replaces, the real
    six-socket sync negative controls and the gthread positives.
    """
    server = GunicornServer(["--workers", "1", "--threads", "2"], label="cleanup-live")
    orphans: int | None = None
    try:
        assert server.wait_ready(), f"server not ready; log tail:\n{server.log_tail()}"

        # Sensitivity probe of the OLD behavior: an unbounded stdout.read
        # on the live process must still be blocked after the bounded
        # wait (the strategy-observed fault shape).
        old_read: dict[str, object] = {}

        def _old_behavior_read() -> None:
            try:
                old_read["result"] = server.proc.stdout.read()
            except Exception:
                old_read["result"] = None

        reader = threading.Thread(target=_old_behavior_read, name="oap-031c-old-read", daemon=True)
        reader.start()
        time.sleep(OLD_READ_PROBE_S)
        assert reader.is_alive(), (
            "sensitivity check failed: the old unbounded read unexpectedly "
            "returned while the owned gunicorn is alive"
        )

        # The fixed diagnostics are finite while the process is alive...
        started = time.monotonic()
        live_tail = server.log_tail()
        live_ms = (time.monotonic() - started) * 1000.0
        assert live_ms < LOG_TAIL_PROMPT_MS, f"live log_tail not prompt: {live_ms:.1f}ms"
        assert live_tail == LIVE_LOG_MARKER, (
            f"live log_tail must return the bounded marker, got: {live_tail!r}"
        )

        # ...and the real readiness-failure path (forced result, real
        # process) completes through the same message/assert/finally
        # shape within the bounded teardown budget.
        server.wait_ready = lambda: False  # fixture injection; server stays alive
        started = time.monotonic()
        with pytest.raises(AssertionError, match="server not ready"):
            try:
                assert server.wait_ready(), f"server not ready; log tail:\n{server.log_tail()}"
            finally:
                orphans = server.stop()
        failure_path_ms = (time.monotonic() - started) * 1000.0
        assert failure_path_ms < READINESS_FAILURE_PATH_MS, (
            f"readiness-failure path not bounded: {failure_path_ms:.1f}ms"
        )

        # Bounded teardown delivered EOF: the old read must finish now, and
        # no owned thread, socket or child may remain.
        reader.join(timeout=READINESS_DEADLINE_S)
        assert not reader.is_alive(), "old-read probe thread survived bounded teardown"
        assert orphans == 0, f"orphan gunicorn children after readiness failure: {orphans}"

        # Diagnostics remain bounded and readable after the stop.
        started = time.monotonic()
        stopped_tail = server.log_tail()
        stopped_ms = (time.monotonic() - started) * 1000.0
        assert stopped_ms < LOG_TAIL_PROMPT_MS, f"stopped log_tail not prompt: {stopped_ms:.1f}ms"
        assert isinstance(stopped_tail, str)
    finally:
        server.stop()  # idempotent; also covers any failure of this test itself
