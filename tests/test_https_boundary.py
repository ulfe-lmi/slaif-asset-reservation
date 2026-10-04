"""Owned real-HTTPS boundary qualification wrapper (OAP 033-b).

These tests drive ``deploy/rehearse_https_boundary.sh`` as a bounded
subprocess. The script itself owns every resource it touches (a fresh work
directory, an image built from a tracked-file snapshot, an owned copy of
the production Compose file under a uniquely named project, the pinned
Caddy v2.11.6 edge on a loopback port, owned process sessions) and refuses
foreign resources; the tests here add the ownership guarantees a
subprocess wrapper must enforce:

- an honest skip (42) when the pinned Caddy or tooling is absent, never a
  fake pass;
- the captured script output never carries the synthetic database
  password (sentinel value set by this test, held in memory only);
- rehearsal-owned container/volume/image identities are gone after a run;
- a foreign container that already holds an expected owned name is
  refused, not adopted, and is left untouched;
- a foreign container that claims the app name AFTER the script's
  pre-creation check (a creation race) is left untouched by the failed
  create;
- an injected mid-run failure (the Caddy session leader SIGKILLed while
  its child survives) leaves no owned container, volume, image or
  process-session residue, and does not kill a foreign session.

No public exposure, no OS trust-store change, no inherited environment:
the script unsets DATABASE_URL/TEST_DATABASE_URL and never loads the
repository .env.
"""

from __future__ import annotations

import os
import re
import subprocess
import time
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
REHEARSAL_SCRIPT = REPO_ROOT / "deploy" / "rehearse_https_boundary.sh"
# Synthetic sentinel: if it ever appears in captured output, a secret
# leaked. Held in memory only; it is a test-owned synthetic value.
DB_PASSWORD_SENTINEL = "synthetic-oap-033b-boundary-db-password-000000"
FULL_RUN_TIMEOUT_S = 1800.0
FAST_RUN_TIMEOUT_S = 300.0


def _docker(*args: str) -> str:
    result = subprocess.run(["docker", *args], capture_output=True, text=True, check=False)
    return result.stdout


def _script_env(**extra: str) -> dict[str, str]:
    env = dict(os.environ)
    # Never let inherited product configuration into the rehearsal.
    for name in list(env):
        if name.startswith("SLAIF") or name in {
            "DATABASE_URL",
            "TEST_DATABASE_URL",
            "DJANGO_SETTINGS_MODULE",
        }:
            env.pop(name, None)
    env.update(extra)
    return env


def _run_rehearsal(
    timeout: float = FULL_RUN_TIMEOUT_S, **extra: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(REHEARSAL_SCRIPT)],
        cwd=REPO_ROOT,
        env=_script_env(**extra),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _fixed_project(tag: str) -> str:
    return f"slaif033b-fixtest-{tag}-{uuid.uuid4().hex[:8]}"


def _parse(state_line: str, output: str) -> str:
    match = re.search(rf"https-boundary: {re.escape(state_line)}(\S+)", output)
    assert match, f"{state_line} not logged by the rehearsal"
    return match.group(1)


def _owned_containers(project: str) -> list[str]:
    names = _docker("ps", "-a", "--format", "{{.Names}}").splitlines()
    return [name.strip() for name in names if name.strip().startswith(project)]


def _owned_volumes(project: str) -> list[str]:
    volumes = _docker("volume", "ls", "--format", "{{.Name}}").splitlines()
    return [name.strip() for name in volumes if name.strip().startswith(f"{project}_")]


def _image_exists(tag: str) -> bool:
    # Docker prints [] on stdout for a failed JSON inspection. Exit status,
    # rather than nonempty stdout, is the existence boundary.
    result = subprocess.run(["docker", "image", "inspect", tag], capture_output=True, check=False)
    return result.returncode == 0


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _procs_with_marker(marker: str) -> list[str]:
    pids = []
    for entry in Path("/proc").glob("[0-9]*"):
        try:
            cmdline = (entry / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
        except OSError:
            continue
        if marker and marker in cmdline and entry.name != str(os.getpid()):
            pids.append(entry.name)
    return pids


def _foreign_standin(name: str) -> str:
    created = _docker(
        "run",
        "-d",
        "--name",
        name,
        "-l",
        "com.example.oap033b=foreign-standin",
        "alpine:3.20",
        "sleep",
        "600",
    )
    assert created.strip(), "could not create test-owned foreign container"
    return created.strip()


def _assert_foreign_untouched(name: str) -> None:
    state = _docker("inspect", name, "--format", "{{.State.Running}}").strip()
    assert state == "true", "foreign container was stopped or removed"
    label = _docker(
        "inspect", name, "--format", '{{index .Config.Labels "com.example.oap033b"}}'
    ).strip()
    assert label == "foreign-standin", "foreign container labels were modified"


@pytest.fixture(scope="module")
def rehearsal() -> SimpleNamespace:
    # Owned ignored-file sentinel: proves the build snapshot excludes
    # git-ignored valuable paths (the rehearsal logs the sentinel absence).
    sentinel_dir = REPO_ROOT / "private_exports"
    sentinel: Path | None = None
    created_dir = False
    if not sentinel_dir.exists():
        sentinel_dir.mkdir(parents=True)
        created_dir = True
        sentinel = sentinel_dir / f"oap033b-boundary-sentinel-{uuid.uuid4().hex[:12]}.txt"
        sentinel.write_text("sentinel-content-not-for-builds", encoding="utf-8")
    try:
        result = _run_rehearsal(SLAIF033B_BOUNDARY_DB_PASSWORD=DB_PASSWORD_SENTINEL)
        yield SimpleNamespace(result=result, sentinel=sentinel)
    finally:
        if sentinel is not None:
            sentinel.unlink(missing_ok=True)
            if created_dir:
                try:
                    sentinel_dir.rmdir()
                except OSError:
                    pass


def test_https_boundary_rehearsal_passes(rehearsal: SimpleNamespace) -> None:
    result = rehearsal.result
    if result.returncode == 42:
        pytest.skip(
            "HTTPS boundary qualification prerequisites missing "
            "(pinned Caddy v2.11.6 / openssl / curl / docker); "
            "the rehearsal script exited 42, no check was faked"
        )
    assert result.returncode == 0, "owned HTTPS rehearsal failed; inspect private diagnostics"
    assert "https-boundary=FAIL" not in result.stdout
    assert result.stdout.strip().splitlines()[-1] == "https-boundary=ok"
    if rehearsal.sentinel is not None:
        assert "snapshot-ignored-absent=private_exports" in result.stdout
        assert "snapshot-leak" not in result.stdout


def test_https_boundary_output_leaks_no_db_password(rehearsal: SimpleNamespace) -> None:
    result = rehearsal.result
    if result.returncode == 42:
        pytest.skip("rehearsal prerequisites missing (script exited 42)")
    output = f"{result.stdout}\n{result.stderr}"
    assert DB_PASSWORD_SENTINEL not in output, "database password leaked in output"


def test_no_owned_residue_after_rehearsal(rehearsal: SimpleNamespace) -> None:
    result = rehearsal.result
    if result.returncode == 42:
        pytest.skip("rehearsal prerequisites missing (script exited 42)")
    assert result.returncode == 0
    project = _parse("project=", result.stdout)
    image = _parse("image=", result.stdout)
    assert _owned_containers(project) == [], "owned rehearsal containers remain"
    assert _owned_volumes(project) == [], "owned rehearsal volumes remain"
    assert not _image_exists(image), "owned rehearsal image remains"


def test_https_boundary_refuses_foreign_container() -> None:
    # A container that already holds an expected owned name is foreign:
    # the script must refuse (non-zero exit, not 42) and leave it
    # untouched. The container is owned by this test.
    project = _fixed_project("foreignctr")
    foreign = f"{project}-app-1"
    _foreign_standin(foreign)
    try:
        result = _run_rehearsal(timeout=FAST_RUN_TIMEOUT_S, SLAIF033B_BOUNDARY_PROJECT=project)
        if result.returncode == 42:
            pytest.skip("rehearsal prerequisites missing (script exited 42)")
        assert result.returncode != 0, (
            "rehearsal must refuse a foreign container holding an expected name"
        )
        assert "refusing-to-adopt" in result.stdout + result.stderr
        _assert_foreign_untouched(foreign)
        assert _owned_volumes(project) == []
    finally:
        subprocess.run(["docker", "rm", "-f", foreign], capture_output=True, check=False)
        assert _docker("inspect", foreign, "--format", "{{.Id}}").strip() == ""


def test_https_boundary_refuses_foreign_volume() -> None:
    # A volume that already holds an expected owned name is foreign:
    # refusal, not adoption; the volume survives.
    project = _fixed_project("foreignvol")
    volume = f"{project}_postgres-data"
    assert _docker("volume", "create", volume).strip() == volume
    try:
        result = _run_rehearsal(timeout=FAST_RUN_TIMEOUT_S, SLAIF033B_BOUNDARY_PROJECT=project)
        if result.returncode == 42:
            pytest.skip("rehearsal prerequisites missing (script exited 42)")
        assert result.returncode != 0, (
            "rehearsal must refuse a foreign volume holding an expected name"
        )
        assert "refusing-to-adopt" in result.stdout + result.stderr
        assert volume in _owned_volumes(project), "foreign volume was removed"
    finally:
        subprocess.run(["docker", "volume", "rm", volume], capture_output=True, check=False)
        assert volume not in _owned_volumes(project)


def test_creation_race_leaves_foreign_untouched() -> None:
    # The pre-creation check passes (names free); after the script's own
    # db container exists, this test claims the app name. The failed
    # create must exit non-zero, clean up ONLY this run's resources, and
    # leave the foreign container untouched.
    project = _fixed_project("race")
    foreign = f"{project}-app-1"
    proc = subprocess.Popen(
        ["bash", str(REHEARSAL_SCRIPT)],
        cwd=REPO_ROOT,
        env=_script_env(
            SLAIF033B_BOUNDARY_PROJECT=project,
            SLAIF033B_BOUNDARY_SLOW_APP_UP_S="10",
        ),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    foreign_created = False
    stdout = stderr = ""
    try:
        # Wait until the run's own db container exists: the pre-creation
        # checks have long since passed by then, so claiming the app name
        # now is a genuine creation race.
        deadline = time.monotonic() + 1500
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                break
            if _docker("inspect", f"{project}-db-1", "--format", "{{.Id}}").strip():
                break
            time.sleep(2)
        if proc.poll() is None:
            _foreign_standin(foreign)
            foreign_created = True
        stdout, stderr = proc.communicate(timeout=FULL_RUN_TIMEOUT_S)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.communicate()
    try:
        if proc.returncode == 42:
            pytest.skip("rehearsal prerequisites missing (script exited 42)")
        assert proc.returncode == 1, "creation race did not fail safely"
        assert "app-create-refused" in stderr
        if foreign_created:
            # The failed create and the project-scoped cleanup must have
            # left the foreign stand-in untouched: still running, labels
            # intact, and the ONLY surviving name under the project prefix.
            _assert_foreign_untouched(foreign)
            assert _owned_containers(project) == [foreign]
        # This run's own resources (db container, project volume) are gone.
        assert _owned_volumes(project) == []
    finally:
        if foreign_created:
            subprocess.run(["docker", "rm", "-f", foreign], capture_output=True, check=False)
            assert _docker("inspect", foreign, "--format", "{{.Id}}").strip() == ""


def test_injected_failure_cleans_up() -> None:
    # Fault injection after the edge is ready: every owned resource
    # (containers, volume, image) must be removed despite the failure.
    project = _fixed_project("faultedge")
    result = _run_rehearsal(
        SLAIF033B_BOUNDARY_PROJECT=project, SLAIF033B_BOUNDARY_FAULT="after-edge-up"
    )
    if result.returncode == 42:
        pytest.skip("rehearsal prerequisites missing (script exited 42)")
    assert result.returncode == 1, "injected failure did not fail safely"
    assert "fault-after-edge-up" in result.stdout + result.stderr
    assert _owned_containers(project) == []
    assert _owned_volumes(project) == []
    image = _parse("image=", result.stdout)
    assert not _image_exists(image)


def test_caddy_leader_death_leaves_no_orphans() -> None:
    # The Caddy session leader is SIGKILLed mid-run while its child
    # survives: cleanup must still terminate the orphaned child via the
    # process group, leave no work-path processes behind, and must not
    # touch a foreign session.
    foreign = subprocess.Popen(["sleep", "300"], start_new_session=True, stdout=subprocess.DEVNULL)
    try:
        project = _fixed_project("leaderdeath")
        result = _run_rehearsal(
            SLAIF033B_BOUNDARY_PROJECT=project,
            SLAIF033B_BOUNDARY_FAULT="kill-caddy-leader",
        )
        if result.returncode == 42:
            pytest.skip("rehearsal prerequisites missing (script exited 42)")
        assert result.returncode == 1, "leader-death injection did not fail safely"
        assert "fault-kill-caddy-leader" in result.stdout + result.stderr
        work = _parse("work=", result.stdout)
        assert _procs_with_marker(work) == [], "owned process sessions survived cleanup"
        assert _pid_alive(foreign.pid), "foreign session was killed by the rehearsal"
        assert _owned_containers(project) == []
        assert _owned_volumes(project) == []
        image = _parse("image=", result.stdout)
        assert not _image_exists(image)
    finally:
        if _pid_alive(foreign.pid):
            foreign.kill()
        foreign.wait()


def test_shipped_proxy_preserves_stricter_headers_and_supplies_only_defaults(
    tmp_path: Path,
) -> None:
    """Real edge regression: removing '?' reproduces the old weakening."""
    import http.server
    import shutil
    import signal
    import socket
    import ssl
    import threading
    import urllib.request

    caddy = shutil.which("caddy")
    if not caddy:
        pytest.skip("pinned Caddy unavailable")

    class Backend(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            if self.path == "/strict":
                self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cache-Control", "no-store, private")
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, *args: object) -> None:
            pass

    backend = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Backend)
    worker = threading.Thread(target=backend.serve_forever, daemon=True)
    worker.start()
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    listener.close()
    cert, key = tmp_path / "cert.pem", tmp_path / "key.pem"
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-days",
            "1",
            "-subj",
            "/CN=localhost",
            "-addext",
            "subjectAltName=DNS:localhost,IP:127.0.0.1",
            "-keyout",
            str(key),
            "-out",
            str(cert),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    source = (REPO_ROOT / "deploy/Caddyfile.example").read_text()
    anchor = "{\n\temail admin@example.org\n"
    assert source.count(anchor) == 1
    source = source.replace(anchor, "{\n\tadmin off\n\tauto_https off\n")
    source = source.replace(
        "reservation.example.org {",
        f"https://localhost:{port} {{\n\tbind 127.0.0.1\n\ttls {cert} {key}",
    )
    source = source.replace(
        "reverse_proxy 127.0.0.1:8000 {", f"reverse_proxy 127.0.0.1:{backend.server_port} {{"
    )
    config = tmp_path / "Caddyfile"
    config.write_text(source)
    env = {
        "PATH": os.environ["PATH"],
        "XDG_DATA_HOME": str(tmp_path / "data"),
        "XDG_CONFIG_HOME": str(tmp_path / "config"),
    }
    log = (tmp_path / "caddy.log").open("w")
    proc = subprocess.Popen(
        [caddy, "run", "--config", str(config)],
        env=env,
        stdout=log,
        stderr=log,
        start_new_session=True,
    )
    context = ssl.create_default_context(cafile=str(cert))
    try:
        for _ in range(100):
            try:
                with urllib.request.urlopen(
                    f"https://localhost:{port}/strict", context=context, timeout=1
                ) as response:
                    assert response.headers["Referrer-Policy"] == "no-referrer"
                    assert response.headers["Cache-Control"] == "no-store, private"
                    break
            except OSError:
                time.sleep(0.05)
        else:
            pytest.fail("owned edge did not start", pytrace=False)
        with urllib.request.urlopen(
            f"https://localhost:{port}/default", context=context, timeout=2
        ) as response:
            assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
            assert response.headers["Cache-Control"] == "no-store, private"
            assert response.headers.get("Server") is None
        backend.shutdown()
        backend.server_close()
        try:
            urllib.request.urlopen(
                f"https://localhost:{port}/proxy-privacy-canary?private=query-canary",
                context=context,
                timeout=3,
            )
        except urllib.error.HTTPError as error:
            assert error.code == 502
            error.close()
        else:
            pytest.fail("unavailable upstream was not rejected", pytrace=False)
        time.sleep(0.1)
        # Never render captured logs in assertion diagnostics.
        leaked = "proxy-privacy-canary" in (tmp_path / "caddy.log").read_text()
        if leaked:
            pytest.fail("proxy error log retained private request URI", pytrace=False)
    finally:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=5)
        log.close()
        backend.shutdown()
        backend.server_close()
        worker.join(timeout=3)


def test_volume_creation_race_never_mounts_or_removes_foreign_volume() -> None:
    project = _fixed_project("volumerace")
    volume = f"{project}_postgres-data"
    proc = subprocess.Popen(
        ["bash", str(REHEARSAL_SCRIPT)],
        cwd=REPO_ROOT,
        env=_script_env(
            SLAIF033B_BOUNDARY_PROJECT=project, SLAIF033B_BOUNDARY_SLOW_VOLUME_CREATE_S="5"
        ),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    created = False
    prefix = []
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            prefix.append(line)
            if "volume-create-window" in line:
                assert (
                    _docker(
                        "volume", "create", "--label", "slaif.fixture.foreign=true", volume
                    ).strip()
                    == volume
                )
                created = True
                identity = _docker(
                    "volume", "inspect", volume, "--format", "{{.CreatedAt}} {{json .Labels}}"
                )
                break
        stdout, stderr = proc.communicate(timeout=300)
        if proc.returncode == 42:
            pytest.skip("rehearsal prerequisites unavailable")
        assert created, "volume creation window was not reached"
        assert proc.returncode == 1
        assert "refusing-to-adopt-raced-volume" in stderr
        assert (
            _docker("volume", "inspect", volume, "--format", "{{.CreatedAt}} {{json .Labels}}")
            == identity
        )
        assert _owned_containers(project) == [], "foreign volume reached a running container"
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.communicate(timeout=20)
        if created:
            subprocess.run(
                ["docker", "volume", "rm", volume],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
