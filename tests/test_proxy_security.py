"""Production proxy trust boundary, error and log privacy (OAP 033-a).

These tests cover the trusted-proxy forwarding gate, the fail-closed
production configuration rules, and the log/entry-point privacy contract.
The real-Gunicorn and real-HTTPS-proxy proofs live in
``tests/test_proxy_gunicorn.py`` and ``tests/test_https_boundary.py``.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import uuid
from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.test import Client, override_settings
from django.utils import timezone

from slaif_reservation.accounts.models import (
    API_TOKEN_SERVICE_CREATE_ATTR,
    ApiToken,
)
from slaif_reservation.accounts.tokens import (
    api_token_verifier,
    format_bearer_token,
)
from slaif_reservation.config.env import (
    peer_in_trusted_networks,
    validate_csrf_origin,
    validate_trusted_proxy_entry,
)
from slaif_reservation.config.logging import (
    UNSERIALIZABLE,
    JsonLogFormatter,
    SafeDjangoResponseLogFilter,
)
from slaif_reservation.config.middleware import TrustedProxyForwardingMiddleware

User = get_user_model()

TRUSTED = ("127.0.0.1", "::1")
UNTRUSTED_PEER = "203.0.113.7"


@pytest.fixture
def production_proxy_settings(settings):
    """Production-shaped proxy settings on the test settings module."""
    settings.SECURE_SSL_REDIRECT = True
    settings.TRUSTED_PROXY_PEERS = [validate_trusted_proxy_entry(entry) for entry in TRUSTED]
    settings.ALLOWED_HOSTS = [*settings.ALLOWED_HOSTS, "reservation.example.test"]
    settings.SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    settings.MIDDLEWARE = [
        "slaif_reservation.config.middleware.TrustedProxyForwardingMiddleware",
        *settings.MIDDLEWARE,
    ]
    return settings


# ---------------------------------------------------------------------------
# env parsing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "entry,expected",
    [
        ("127.0.0.1", "127.0.0.1/32"),
        ("172.17.0.1", "172.17.0.1/32"),
        ("192.168.1.0/31", "192.168.1.0/31"),
        ("127.0.0.0/31", "127.0.0.0/31"),
        ("::1", "::1/128"),
        ("2001:db8::/127", "2001:db8::/127"),
    ],
)
def test_trusted_proxy_entries_accept_explicit_hosts_and_pairs(entry, expected) -> None:
    assert str(validate_trusted_proxy_entry(entry)) == expected


@pytest.mark.parametrize(
    "entry",
    [
        "0.0.0.0/0",
        "::/0",
        "172.16.0.0/12",
        "10.0.0.0/8",
        "192.168.0.0/24",
        "192.168.0.0/30",
        "127.0.0.1/31",  # host bits set: not a network address
        "not-an-ip",
    ],
)
def test_trusted_proxy_entries_reject_broad_or_malformed(entry) -> None:
    with pytest.raises(ImproperlyConfigured):
        validate_trusted_proxy_entry(entry)


def test_peer_in_trusted_networks_matches_ips_only() -> None:
    networks = [validate_trusted_proxy_entry(e) for e in TRUSTED]
    assert peer_in_trusted_networks("127.0.0.1", networks)
    assert peer_in_trusted_networks("::1", networks)
    assert not peer_in_trusted_networks("172.17.0.1", networks)
    assert not peer_in_trusted_networks("not-an-ip", networks)
    assert not peer_in_trusted_networks("", networks)


@pytest.mark.parametrize(
    "origin,ok",
    [
        ("https://reservation.example.org", True),
        ("http://127.0.0.1:8443", True),
        ("https://user:pass@example.org", False),
        ("https://example.org/path", False),
        ("https://example.org?x=1", False),
        ("ftp://example.org", False),
        ("https://", False),
        ("not an origin", False),
    ],
)
def test_csrf_origin_validation(origin, ok) -> None:
    if ok:
        assert validate_csrf_origin(origin) == origin
    else:
        with pytest.raises(ImproperlyConfigured):
            validate_csrf_origin(origin)


# ---------------------------------------------------------------------------
# middleware trust matrix
# ---------------------------------------------------------------------------


def _make_request(environ_overrides: dict[str, str]) -> HttpRequest:
    from django.test import RequestFactory

    request = RequestFactory().get(
        "/health/live",
        SERVER_NAME="reservation.example.test",
        SERVER_PORT="443",
        REMOTE_ADDR="127.0.0.1",
    )
    request.environ["wsgi.url_scheme"] = "http"
    for key, value in environ_overrides.items():
        request.environ[key] = value
    return request


def _run_middleware(request: HttpRequest, trusted: tuple[str, ...] = TRUSTED) -> None:
    def app(_request):
        return None  # pragma: no cover

    middleware = TrustedProxyForwardingMiddleware(app)
    # Bypass the None response: call the trust logic directly via __call__
    # with a real no-op response.
    from django.http import HttpResponse

    def app2(_request):
        return HttpResponse()

    middleware = TrustedProxyForwardingMiddleware(app2)
    settings = pytest.MonkeyPatch()  # not used; settings come from django
    del settings
    middleware.__call__(request)


@override_settings(TRUSTED_PROXY_PEERS=None)
def test_middleware_missing_setting_is_a_no_op_list() -> None:
    # Without the setting the gate trusts nothing; it must still pin http.
    def app(_request):
        from django.http import HttpResponse

        return HttpResponse()

    middleware = TrustedProxyForwardingMiddleware(app)
    request = _make_request({"REMOTE_ADDR": "127.0.0.1", "HTTP_X_FORWARDED_PROTO": "https"})
    middleware(request)
    assert request.environ["wsgi.url_scheme"] == "http"


@pytest.mark.django_db
def test_trusted_peer_honors_exact_https_scheme(production_proxy_settings) -> None:
    request = _make_request({"REMOTE_ADDR": "127.0.0.1", "HTTP_X_FORWARDED_PROTO": "https"})
    _run_middleware(request)
    assert request.environ["wsgi.url_scheme"] == "https"
    assert request.is_secure()


@pytest.mark.django_db
def test_trusted_peer_without_forwarded_proto_stays_http(production_proxy_settings) -> None:
    request = _make_request({"REMOTE_ADDR": "127.0.0.1"})
    _run_middleware(request)
    assert request.environ["wsgi.url_scheme"] == "http"
    assert not request.is_secure()


@pytest.mark.django_db
def test_trusted_peer_ambiguous_forwarded_proto_is_rejected(
    production_proxy_settings,
    caplog,
) -> None:
    request = _make_request(
        {"REMOTE_ADDR": "127.0.0.1", "HTTP_X_FORWARDED_PROTO": "https,evil.example"}
    )
    caplog.set_level(logging.WARNING, logger="slaif_reservation.proxy")
    _run_middleware(request)
    assert request.environ["wsgi.url_scheme"] == "http"
    warnings = [r for r in caplog.records if r.name == "slaif_reservation.proxy"]
    assert len(warnings) == 1
    assert "https,evil.example" not in caplog.text


@pytest.mark.django_db
def test_trusted_peer_single_hop_xff_normalizes_client(production_proxy_settings) -> None:
    request = _make_request({"REMOTE_ADDR": "172.17.0.1", "HTTP_X_FORWARDED_FOR": "198.51.100.25"})
    # 172.17.0.1 must be trusted for this scenario
    import ipaddress

    production_proxy_settings.TRUSTED_PROXY_PEERS = [
        ipaddress.ip_network("172.17.0.1"),
    ]
    _run_middleware(request)
    assert request.environ["REMOTE_ADDR"] == "198.51.100.25"
    assert request.client_ip == "198.51.100.25"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "xff",
    ["198.51.100.25, 203.0.113.9", "not-an-ip", "198.51.100.25,"],
    ids=["ambiguous-chain", "invalid-ip", "trailing-comma"],
)
def test_trusted_peer_ambiguous_xff_falls_back_to_peer(
    production_proxy_settings, caplog, xff
) -> None:
    request = _make_request({"REMOTE_ADDR": "172.17.0.1", "HTTP_X_FORWARDED_FOR": xff})
    import ipaddress

    production_proxy_settings.TRUSTED_PROXY_PEERS = [ipaddress.ip_network("172.17.0.1")]
    caplog.set_level(logging.WARNING, logger="slaif_reservation.proxy")
    _run_middleware(request)
    assert request.environ["REMOTE_ADDR"] == "172.17.0.1"
    assert request.client_ip == "172.17.0.1"
    assert xff not in caplog.text


@pytest.mark.django_db
def test_untrusted_peer_forwarding_stripped_and_scheme_pinned(production_proxy_settings) -> None:
    request = _make_request(
        {
            "REMOTE_ADDR": UNTRUSTED_PEER,
            "HTTP_X_FORWARDED_PROTO": "https",
            "HTTP_X_FORWARDED_FOR": "198.51.100.25",
            "HTTP_X_FORWARDED_HOST": "evil.example",
            "HTTP_FORWARDED": "for=198.51.100.25;proto=https",
        }
    )
    _run_middleware(request)
    assert request.environ["wsgi.url_scheme"] == "http"
    assert not request.is_secure()
    for key in (
        "HTTP_X_FORWARDED_PROTO",
        "HTTP_X_FORWARDED_FOR",
        "HTTP_X_FORWARDED_HOST",
        "HTTP_FORWARDED",
    ):
        assert key not in request.environ
    assert request.environ["REMOTE_ADDR"] == UNTRUSTED_PEER
    assert request.client_ip == UNTRUSTED_PEER


ALL_FORWARDING_KEYS = (
    "HTTP_FORWARDED",
    "HTTP_X_FORWARDED_FOR",
    "HTTP_X_FORWARDED_HOST",
    "HTTP_X_FORWARDED_PORT",
    "HTTP_X_FORWARDED_PREFIX",
    "HTTP_X_FORWARDED_PROTO",
    "HTTP_X_FORWARDED_PROTOCOL",
    "HTTP_X_FORWARDED_SSL",
    "HTTP_X_REAL_IP",
)


@pytest.mark.django_db
def test_untrusted_peer_strips_every_forwarding_variant(production_proxy_settings) -> None:
    # The contract is total: every forwarding header a client can send is
    # consumed and removed in the untrusted branch, including X-Real-IP and
    # X-Forwarded-Port which the supported proxy never supplies.
    request = _make_request(
        {
            "REMOTE_ADDR": UNTRUSTED_PEER,
            "HTTP_FORWARDED": "for=198.51.100.25;proto=https",
            "HTTP_X_FORWARDED_FOR": "198.51.100.25",
            "HTTP_X_FORWARDED_HOST": "evil.example",
            "HTTP_X_FORWARDED_PORT": "8443",
            "HTTP_X_FORWARDED_PREFIX": "/evil",
            "HTTP_X_FORWARDED_PROTO": "https",
            "HTTP_X_FORWARDED_PROTOCOL": "https",
            "HTTP_X_FORWARDED_SSL": "on",
            "HTTP_X_REAL_IP": "198.51.100.25",
        }
    )
    _run_middleware(request)
    assert request.environ["wsgi.url_scheme"] == "http"
    for key in ALL_FORWARDING_KEYS:
        assert key not in request.environ, key
    assert request.environ["REMOTE_ADDR"] == UNTRUSTED_PEER
    assert request.client_ip == UNTRUSTED_PEER


@pytest.mark.django_db
def test_trusted_peer_strips_unconsumed_forwarding_headers(production_proxy_settings) -> None:
    # Trusted branch: XFF is the only identity input (consumed and then
    # stripped), XFP the only scheme input; everything else a client can
    # still inject (X-Real-IP, X-Forwarded-Port/-Host/-Prefix, Forwarded)
    # must not survive to downstream code.
    import ipaddress

    production_proxy_settings.TRUSTED_PROXY_PEERS = [ipaddress.ip_network("172.17.0.1")]
    request = _make_request(
        {
            "REMOTE_ADDR": "172.17.0.1",
            "HTTP_X_FORWARDED_FOR": "198.51.100.25",
            "HTTP_X_FORWARDED_PROTO": "https",
            "HTTP_X_FORWARDED_PORT": "8443",
            "HTTP_X_FORWARDED_HOST": "evil.example",
            "HTTP_X_FORWARDED_PREFIX": "/evil",
            "HTTP_X_FORWARDED_PROTOCOL": "https",
            "HTTP_X_FORWARDED_SSL": "on",
            "HTTP_FORWARDED": "for=198.51.100.25;proto=https",
            "HTTP_X_REAL_IP": "198.51.100.25",
        }
    )
    _run_middleware(request)
    assert request.environ["wsgi.url_scheme"] == "https"
    for key in ALL_FORWARDING_KEYS:
        assert key not in request.environ, key
    assert request.environ["REMOTE_ADDR"] == "198.51.100.25"
    assert request.client_ip == "198.51.100.25"


@pytest.mark.django_db
def test_trusted_peer_keeps_original_peer_separate_from_client(
    production_proxy_settings,
) -> None:
    import ipaddress

    production_proxy_settings.TRUSTED_PROXY_PEERS = [ipaddress.ip_network("172.17.0.1")]
    request = _make_request({"REMOTE_ADDR": "172.17.0.1", "HTTP_X_FORWARDED_FOR": "198.51.100.25"})
    _run_middleware(request)
    assert request.remote_peer == "172.17.0.1"
    assert request.client_ip == "198.51.100.25"
    assert request.environ["REMOTE_ADDR"] == "198.51.100.25"


@pytest.mark.django_db
def test_untrusted_peer_keeps_original_peer_separate_from_client(
    production_proxy_settings,
) -> None:
    request = _make_request(
        {"REMOTE_ADDR": UNTRUSTED_PEER, "HTTP_X_FORWARDED_FOR": "198.51.100.25"}
    )
    _run_middleware(request)
    assert request.remote_peer == UNTRUSTED_PEER
    assert request.client_ip == UNTRUSTED_PEER
    assert request.environ["REMOTE_ADDR"] == UNTRUSTED_PEER


@pytest.mark.django_db
def test_server_derived_https_scheme_cannot_bypass_trust(production_proxy_settings) -> None:
    request = _make_request(
        {
            "REMOTE_ADDR": UNTRUSTED_PEER,
            "wsgi.url_scheme": "https",  # server (Gunicorn) derived
        }
    )
    _run_middleware(request)
    assert request.environ["wsgi.url_scheme"] == "http"
    assert not request.is_secure()


# ---------------------------------------------------------------------------
# full-app behavior with production-shaped settings
# ---------------------------------------------------------------------------


def test_app_ssl_redirect_trusts_only_configured_peer(production_proxy_settings) -> None:
    client = Client()
    # trusted loopback peer with the real proxy header: no redirect
    response = client.get(
        "/health/live", HTTP_X_FORWARDED_PROTO="https", SERVER_NAME="reservation.example.test"
    )
    assert response.status_code == 200

    # trusted peer without the header: redirect to https
    response = client.get("/health/live", SERVER_NAME="reservation.example.test")
    assert response.status_code == 301
    assert response["Location"].startswith("https://")

    # untrusted peer spoofing the header: still redirected
    response = client.get(
        "/health/live",
        HTTP_X_FORWARDED_PROTO="https",
        REMOTE_ADDR=UNTRUSTED_PEER,
        SERVER_NAME="reservation.example.test",
    )
    assert response.status_code == 301
    assert response["Location"].startswith("https://")


def test_response_headers_hardened_on_public_paths(production_proxy_settings) -> None:
    client = Client()
    response = client.get(
        "/health/live",
        HTTP_X_FORWARDED_PROTO="https",
        SERVER_NAME="reservation.example.test",
    )
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["X-Frame-Options"] == "DENY"
    assert response["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "Server" not in response  # Django never sets it; Caddy strips gunicorn's


# ---------------------------------------------------------------------------
# log privacy at the app and Django-error entry points
# ---------------------------------------------------------------------------


def test_json_formatter_handles_request_object_extra() -> None:
    logger = logging.getLogger("django.security.DisallowedHost")
    record = logger.makeRecord(
        "django.security.DisallowedHost",
        logging.WARNING,
        __file__,
        1,
        "Bad request (Requested host %r not permitted...) /x",
        ("evil.example",),
        None,
        extra={"status_code": 400, "request": HttpRequest()},
    )
    output = JsonLogFormatter().format(record)
    payload = json.loads(output)
    assert payload["request"] == UNSERIALIZABLE
    assert "HttpRequest" not in output
    assert "environ" not in output


def test_json_formatter_refuses_repr_and_cycles() -> None:
    class Evil:
        def __repr__(self):
            return "REPR-CANARY-SECRET"

    cyclic: dict[str, object] = {"self": None}
    cyclic["self"] = cyclic
    logger = logging.getLogger("slaif_reservation.test")
    record = logger.makeRecord(
        "slaif_reservation.test",
        logging.INFO,
        __file__,
        1,
        "m",
        None,
        None,
        extra={"obj": Evil(), "data": cyclic},
    )
    output = JsonLogFormatter().format(record)
    payload = json.loads(output)
    assert payload["obj"] == UNSERIALIZABLE
    assert "REPR-CANARY" not in output
    assert payload["data"]["self"] == "[circular]"


def test_disallowed_host_is_safe_and_logged_without_raw_record(client, caplog) -> None:
    caplog.set_level(logging.WARNING)
    response = client.get("/health/live", HTTP_HOST="canary-host.example.attacker")

    assert response.status_code == 400
    body = response.content.decode()
    assert "Traceback" not in body
    assert "canary-host.example.attacker" not in body or "400" in body
    records = [r for r in caplog.records if r.levelno in (logging.ERROR, logging.WARNING)]
    for record in records:
        if hasattr(record, "request"):
            output = JsonLogFormatter().format(record)
            json.loads(output)
            assert "HttpRequest" not in output
            assert "Logging error" not in output


# ---------------------------------------------------------------------------
# production error pages and private routes
# ---------------------------------------------------------------------------


def test_django_response_logs_never_retain_hostile_path_or_host(
    production_proxy_settings, client, caplog
) -> None:
    """Django's own 4xx/5xx log lines must not retain hostile client text.

    Django formats response logs as ``"<reason>: <request.path>"`` and
    SuspiciousOperation logs as the raw exception string (which may carry
    a hostile Host header). The production filter plus formatter must
    replace that client-controlled text while keeping the operational
    category data (logger name, status_code, exception_type).
    """
    caplog.set_level(logging.WARNING)
    client.get("/no-such-page/pathcanary033a/")
    client.get("/health/live", HTTP_HOST="canary-host-033a.example.attacker")

    target_records = [
        record
        for record in caplog.records
        if "status_code" in record.__dict__ and "request" in record.__dict__
    ]
    assert target_records, "Django response log records must exist"
    assert any(record.name == "django.security.DisallowedHost" for record in target_records), (
        "DisallowedHost must be logged through django.security"
    )

    filter_ = SafeDjangoResponseLogFilter()
    for record in target_records:
        filter_.filter(record)
        output = JsonLogFormatter().format(record)
        payload = json.loads(output)
        assert "pathcanary033a" not in output
        assert "canary-host-033a" not in output
        assert "HttpRequest" not in output
        assert "Logging error" not in output
        assert isinstance(payload["status_code"], int)


def test_production_404_is_bare(client) -> None:
    response = client.get("/no-such-page-%zz-canary/")
    assert response.status_code == 404
    body = response.content.decode()
    assert "Traceback" not in body
    assert "%zz-canary" not in body or "404" in body


def test_injected_500_is_bare_and_safe_in_logs(client, monkeypatch, caplog) -> None:
    def boom(_request):
        raise RuntimeError("injected-500-canary-payload")

    # Test-only injection: swap the bound URL pattern callback; the module
    # attribute would not change the already-resolved view reference.
    from slaif_reservation.config import urls as config_urls

    pattern = next(p for p in config_urls.urlpatterns if getattr(p, "name", None) == "health-live")
    monkeypatch.setattr(pattern, "callback", boom)
    caplog.set_level(logging.ERROR, logger="django.request")
    client.raise_request_exception = False
    response = client.get("/health/live")

    assert response.status_code == 500
    body = response.content.decode()
    assert "Traceback" not in body
    assert "injected-500-canary-payload" not in body
    error_records = [r for r in caplog.records if r.name == "django.request"]
    assert error_records, "django.request must log the error"
    for record in error_records:
        output = JsonLogFormatter().format(record)
        json.loads(output)
        assert "injected-500-canary-payload" not in output
        assert "Traceback (most recent call last)" not in output


@pytest.mark.django_db
def test_unauthorized_api_route_stays_401_with_safe_details(client) -> None:
    response = client.get("/api/v1/me/")
    assert response.status_code == 401
    payload = response.json()
    assert payload["code"] == "authentication_required"
    assert "Traceback" not in response.content.decode()


def test_read_only_token_gets_403_on_create(db, client) -> None:
    owner = User.objects.create_user(email="member-403@example.com", password="not-a-secret")
    token_id = uuid.uuid4()
    match_bearer = format_bearer_token(token_id=token_id, secret="C" * 43)
    row = ApiToken(
        id=token_id,
        owner=owner,
        name="read-only",
        verifier=api_token_verifier(bearer_token=match_bearer, pepper=settings.API_TOKEN_PEPPER),
        scopes=["reservations:read"],
        expires_at=timezone.now() + timedelta(days=1),
    )
    setattr(row, API_TOKEN_SERVICE_CREATE_ATTR, True)
    try:
        row.save()
    finally:
        if hasattr(row, API_TOKEN_SERVICE_CREATE_ATTR):
            delattr(row, API_TOKEN_SERVICE_CREATE_ATTR)

    response = client.post(
        "/api/v1/reservations/",
        data="{}",
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {match_bearer}",
        HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )
    assert response.status_code == 403
    assert "Traceback" not in response.content.decode()


# ---------------------------------------------------------------------------
# API docs/schema entry points
# ---------------------------------------------------------------------------

_DOCS_PROBE = """
import json

import django

django.setup()

from django.test import Client

client = Client()
result = {}
for path in ("/api/schema/", "/api/docs/"):
    response = client.get(
        path,
        HTTP_X_FORWARDED_PROTO="https",
        HTTP_HOST="reservation.example.test",
    )
    result[path] = response.status_code
schema = client.get(
    "/api/schema/",
    HTTP_X_FORWARDED_PROTO="https",
    HTTP_HOST="reservation.example.test",
)
result["schema_has_openapi"] = (
    "openapi" in schema.content.decode("utf-8", "replace").lower()
)
print(json.dumps(result))
"""


def _run_docs_probe(env_extra: dict[str, str]) -> dict[str, object]:
    """Probe the real production URLconf in a subprocess.

    The docs routes are registered at URLconf import time, so in-process
    ``override_settings`` can neither add nor remove them.
    """
    from tests.test_settings import production_settings_env

    env = (
        production_settings_env()
        | {
            # Dead database on purpose: the probes must not need it.
            "DATABASE_URL": "postgres://slaif:slaif@127.0.0.1:1/slaif_reservation",
        }
        | env_extra
    )
    result = subprocess.run(
        [sys.executable, "-c", _DOCS_PROBE],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_docs_schema_route_absent_when_docs_disabled_in_production() -> None:
    probe = _run_docs_probe({})  # SLAIF_ENABLE_API_DOCS unset -> disabled
    assert probe["/api/schema/"] == 404
    assert probe["/api/docs/"] == 404
    assert probe["schema_has_openapi"] is False


def test_docs_schema_anonymous_refused_in_production_when_enabled() -> None:
    probe = _run_docs_probe({"SLAIF_ENABLE_API_DOCS": "true"})
    assert probe["/api/schema/"] in (401, 403)
    assert probe["/api/docs/"] in (401, 403)
    assert probe["schema_has_openapi"] is False


def test_docs_schema_private_for_anonymous_in_process(
    db, production_proxy_settings, client
) -> None:
    # Test settings register the docs routes (API_DOCS_ENABLED=True), so the
    # access policy itself can still be exercised in-process.
    https = {"HTTP_X_FORWARDED_PROTO": "https"}
    with override_settings(API_DOCS_PUBLIC=False):
        response = client.get("/api/schema/", **https)
        assert response.status_code in (401, 403)
        assert "openapi" not in response.content.decode().lower()

        staff = User.objects.create_user(
            email="staff-docs@example.com", password="not-a-secret", is_staff=True
        )
        client.force_login(staff)
        response = client.get("/api/schema/", **https)
        assert response.status_code == 200


def test_anonymous_management_and_member_routes_do_not_disclose(
    production_proxy_settings, client
) -> None:
    https = {"HTTP_X_FORWARDED_PROTO": "https"}
    response = client.get("/manage/", **https)
    assert response.status_code in (302, 303)

    response = client.get("/tokens/", **https)
    assert response.status_code in (302, 303)

    guessed = uuid.uuid4()
    response = client.get(f"/reservations/{guessed}/", **https)
    assert response.status_code in (302, 303, 404)


def test_scoped_ipv6_forwarding_cannot_choose_a_client_identity() -> None:
    from slaif_reservation.config.middleware import TrustedProxyForwardingMiddleware

    client, ambiguous = TrustedProxyForwardingMiddleware._one_hop_client_ip(
        "127.0.0.1", "fe80::1%injected-zone"
    )
    assert ambiguous
    assert client == "127.0.0.1"
