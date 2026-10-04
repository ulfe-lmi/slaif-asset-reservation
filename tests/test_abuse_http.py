"""Real production Gunicorn + TLS proxy abuse-control regressions."""

from __future__ import annotations

import contextlib
import http.cookiejar
import json
import os
import re
import signal
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import override_settings
from tests.test_settings import TEST_PRODUCTION_API_TOKEN_PEPPER, TEST_PRODUCTION_SECRET_KEY

from slaif_reservation.accounts.services import issue_api_token
from slaif_reservation.api.models import AbuseBucket

ROOT = Path(__file__).resolve().parents[1]


def port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def stop(proc: subprocess.Popen[bytes]) -> None:
    with contextlib.suppress(ProcessLookupError):
        os.killpg(proc.pid, signal.SIGTERM)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait(timeout=5)


@contextlib.contextmanager
def server(tmp: Path, *, workers: int = 3, rates: dict[str, int] | None = None, dead: bool = False):
    db = settings.DATABASES["default"]
    url = (
        "postgres://"
        + urllib.parse.quote(str(db.get("USER", "")))
        + ":"
        + urllib.parse.quote(str(db.get("PASSWORD", "")))
        + "@"
        + str(db["HOST"])
        + ":"
        + str(db["PORT"])
        + "/"
        + str(db["NAME"])
    )
    app_port, edge_port = port(), port()
    origin = f"https://localhost:{edge_port}"
    # A test-only WSGI wrapper identifies the actual processes; app behavior
    # and middleware remain the real production implementation.
    module = tmp / "fixture_wsgi.py"
    module.write_text("""import os
from django.conf import settings
settings.STATIC_ROOT = os.environ["FIXTURE_STATIC_ROOT"]
from slaif_reservation.config.wsgi import application as real

def application(environ, start_response):
    def start(status, headers, exc_info=None):
        return start_response(status, headers + [("X-Test-Worker", str(os.getpid()))], exc_info)
    return real(environ, start)
""")
    env = {
        "PATH": os.environ["PATH"],
        "PYTHONPATH": str(tmp) + os.pathsep + str(ROOT / "src"),
        "DJANGO_SETTINGS_MODULE": "slaif_reservation.config.settings.production",
        "DATABASE_URL": "postgres://unused:unused@127.0.0.1:1/unused" if dead else url,
        "SLAIF_DJANGO_SECRET_KEY": TEST_PRODUCTION_SECRET_KEY,
        "SLAIF_API_TOKEN_PEPPER": TEST_PRODUCTION_API_TOKEN_PEPPER,
        "SLAIF_ALLOWED_HOSTS": "localhost,127.0.0.1",
        "SLAIF_CSRF_TRUSTED_ORIGINS": origin,
        "SLAIF_TRUSTED_PROXY_PEERS": "127.0.0.1",
        "FIXTURE_STATIC_ROOT": str(tmp / "staticfiles"),
        "SLAIF_LOGIN_WINDOW_SECONDS": "3600",
        "SLAIF_API_WINDOW_SECONDS": "3600",
    }
    env.update({key: str(value) for key, value in (rates or {}).items()})
    collect = """import os, django
from django.conf import settings
settings.STATIC_ROOT = os.environ['FIXTURE_STATIC_ROOT']
django.setup()
from django.core.management import call_command
call_command('collectstatic', verbosity=0, interactive=False)
"""
    subprocess.run(
        [sys.executable, "-c", collect],
        env=env,
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    log = (tmp / "server.log").open("wb")
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "gunicorn",
            "fixture_wsgi:application",
            "--bind",
            f"127.0.0.1:{app_port}",
            "--workers",
            str(workers),
            "--threads",
            "8",
            "--keep-alive",
            "5",
            "--timeout",
            "30",
            "--forwarded-allow-ips",
            "",
            "--header-map",
            "drop",
            "--logger-class",
            "slaif_reservation.config.gunicorn.SlaifGunicornLogger",
        ],
        cwd=ROOT,
        env=env,
        stdout=log,
        stderr=log,
        start_new_session=True,
    )
    edge = None
    edge_log = None
    try:
        for _ in range(100):
            try:
                with socket.create_connection(("127.0.0.1", app_port), timeout=0.2):
                    break
            except OSError:
                time.sleep(0.05)
        cert, key = tmp / "cert.pem", tmp / "key.pem"
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
                "-out",
                str(cert),
                "-keyout",
                str(key),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        text = (ROOT / "deploy/Caddyfile.example").read_text()
        text = text.replace("{\n\temail admin@example.org\n", "{\n\tadmin off\n\tauto_https off\n")
        text = text.replace(
            "reservation.example.org {",
            f"localhost:{edge_port} {{\n\tbind 127.0.0.1\n\ttls {cert} {key}",
        )
        text = text.replace(
            "reverse_proxy 127.0.0.1:8000 {", f"reverse_proxy 127.0.0.1:{app_port} {{"
        )
        conf = tmp / "Caddyfile"
        conf.write_text(text)
        edge_log = (tmp / "edge.log").open("wb")
        edge = subprocess.Popen(
            ["caddy", "run", "--config", str(conf)],
            env={
                "PATH": os.environ["PATH"],
                "XDG_DATA_HOME": str(tmp / "data"),
                "XDG_CONFIG_HOME": str(tmp / "config"),
            },
            stdout=edge_log,
            stderr=edge_log,
            start_new_session=True,
        )
        ctx = ssl.create_default_context(cafile=str(cert))
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
        for _ in range(100):
            try:
                with opener.open(origin + "/health/live", timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(0.05)
        else:
            pytest.fail("owned production server did not start", pytrace=False)
        time.sleep(
            0.5
        )  # All configured worker processes finish startup before the concurrent probe.
        yield origin, ctx
    finally:
        if edge is not None:
            stop(edge)
        stop(proc)
        if edge_log is not None:
            edge_log.close()
        log.close()


def request(origin: str, ctx: ssl.SSLContext, path: str, *, headers: dict[str, str] | None = None):
    req = urllib.request.Request(origin + path, headers=headers or {})
    try:
        response = urllib.request.urlopen(req, context=ctx, timeout=5)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return (
            response.status,
            {key.lower(): value for key, value in response.headers.items()},
            response.read(),
        )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("workers", [1, 3])
def test_real_workers_and_forwarded_spoofing_cannot_multiply_invalid_bearer_budget(
    tmp_path: Path, workers: int
) -> None:
    with server(tmp_path, workers=workers, rates={"SLAIF_API_IP_LIMIT": 5}) as (origin, ctx):

        def attempt(index: int):
            return request(
                origin,
                ctx,
                "/api/v1/me/",
                headers={
                    "Authorization": "Bearer invalid",
                    "X-Forwarded-For": f"198.51.100.{index}",
                    "X_Forwarded_For": f"203.0.113.{index}",
                    "Forwarded": "for=198.51.100.9",
                },
            )

        with ThreadPoolExecutor(max_workers=20) as pool:
            results = list(pool.map(attempt, range(20)))
        assert sum(status == 401 for status, _, _ in results) == 5
        assert sum(status == 429 for status, _, _ in results) == 15
        if workers > 1:
            assert len({headers["x-test-worker"] for _, headers, _ in results}) > 1
        for status, headers, body in results:
            if status == 429:
                assert int(headers["retry-after"]) > 0
                assert json.loads(body)["code"] == "rate_limited"
                assert json.loads(body)["correlation_id"] == headers["x-request-id"]
        assert request(origin, ctx, "/health/live")[0] == 200


@pytest.mark.django_db(transaction=True)
def test_owner_budget_is_shared_by_multiple_valid_tokens(tmp_path: Path) -> None:
    user = get_user_model().objects.create_user(
        email="budget-owner@example.test", password="synthetic-password"
    )
    with override_settings(API_TOKEN_PEPPER=TEST_PRODUCTION_API_TOKEN_PEPPER):
        tokens = [
            issue_api_token(
                owner=user, name=f"fixture-{n}", scopes=["reservations:read"], lifetime_days=1
            ).bearer_token
            for n in range(2)
        ]
    with server(
        tmp_path,
        rates={"SLAIF_API_IP_LIMIT": 100, "SLAIF_API_OWNER_LIMIT": 3, "SLAIF_API_TOKEN_LIMIT": 10},
    ) as (origin, ctx):
        for index in range(3):
            assert (
                request(
                    origin,
                    ctx,
                    "/api/v1/me/",
                    headers={"Authorization": "Bearer " + tokens[index % 2]},
                )[0]
                == 200
            )
        response = request(
            origin, ctx, "/api/v1/me/", headers={"Authorization": "Bearer " + tokens[1]}
        )
        assert response[0] == 429
        assert json.loads(response[2])["code"] == "rate_limited"
    for filename in ["server.log", "edge.log"]:
        leaked = any(token in (tmp_path / filename).read_text(errors="replace") for token in tokens)
        if leaked:
            pytest.fail("credential leaked in production logs", pytrace=False)


@pytest.mark.django_db(transaction=True)
def test_database_failure_fails_closed_over_real_tls_but_liveness_stays_available(
    tmp_path: Path,
) -> None:
    with server(tmp_path, dead=True) as (origin, ctx):
        status, _, body = request(origin, ctx, "/api/v1/me/")
        assert status == 503
        assert json.loads(body)["code"] == "service_unavailable"
        assert request(origin, ctx, "/health/live")[0] == 200


@pytest.mark.django_db(transaction=True)
def test_member_and_admin_login_share_budget_and_valid_accounts_recover(tmp_path: Path) -> None:
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args: object, **kwargs: object):
            return None

    with override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"]):
        user = get_user_model().objects.create_user(
            email="login-budget@example.test",
            password="synthetic-strong-password",
            is_staff=True,
            is_superuser=True,
        )
    original_password = user.password
    with server(tmp_path, rates={"SLAIF_LOGIN_IP_LIMIT": 100, "SLAIF_LOGIN_IDENTITY_LIMIT": 2}) as (
        origin,
        ctx,
    ):

        def login(path: str, *, valid: bool = False) -> int:
            jar = http.cookiejar.CookieJar()
            opener = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(jar),
                urllib.request.HTTPSHandler(context=ctx),
                NoRedirect(),
            )
            with opener.open(origin + path, timeout=5) as page:
                token = re.search(
                    r'name="csrfmiddlewaretoken" value="([^\"]+)"', page.read().decode()
                ).group(1)
            data = urllib.parse.urlencode(
                {
                    "csrfmiddlewaretoken": token,
                    "username": user.email if valid else "LOGIN-BUDGET@example.test",
                    "password": "synthetic-strong-password" if valid else "incorrect",
                }
            ).encode()
            req = urllib.request.Request(origin + path, data=data, headers={"Origin": origin})
            try:
                response = opener.open(req, timeout=5)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                return response.status

        assert login("/login/", valid=True) == 302
        assert login("/admin/login/") == 200
        assert login("/login/") == 429
        # Expiring security rows can be purged; no persistent user lockout.
        AbuseBucket.objects.all().delete()
        assert login("/admin/login/", valid=True) == 302
    user.refresh_from_db()
    assert user.is_active
    assert user.password == original_password
