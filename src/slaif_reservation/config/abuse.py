"""Shared, bounded PostgreSQL abuse budgets for authentication and API traffic."""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import math
import secrets
from collections.abc import Callable
from datetime import UTC, datetime

from django.conf import settings
from django.db import DatabaseError, connection, transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render


class BudgetExceeded(Exception):
    def __init__(self, wait: int) -> None:
        self.wait = max(1, wait)
        super().__init__("Request budget exceeded.")


class BudgetUnavailable(Exception):
    pass


def client_identity(request: HttpRequest) -> str:
    raw = getattr(request, "client_ip", None) or request.META.get("REMOTE_ADDR", "")
    try:
        return str(ipaddress.ip_address(raw))
    except ValueError:
        return "unknown"


def consume(scope: str, identity: str, *, timestamp: float | None = None) -> None:
    limit, seconds = settings.ABUSE_RATES[scope]
    now = datetime.now(UTC).timestamp() if timestamp is None else timestamp
    end = (math.floor(now / seconds) + 1) * seconds
    material = f"abuse-v1:{scope}:{seconds}:{end}:{identity}".encode()
    key = hmac.new(settings.SECRET_KEY.encode(), material, hashlib.sha256).hexdigest()
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT set_config('lock_timeout', '1000ms', true)")
                cursor.execute("SELECT set_config('statement_timeout', '2000ms', true)")
                cursor.execute(
                    'INSERT INTO api_abuse_bucket ("key", count, expires_at) VALUES (%s, 1, %s) '
                    'ON CONFLICT ("key") DO UPDATE SET count = '
                    "LEAST(api_abuse_bucket.count + 1, %s) "
                    "RETURNING count",
                    [key, datetime.fromtimestamp(end, UTC), limit + 1],
                )
                row = cursor.fetchone()
                if row is None:
                    raise BudgetUnavailable("Security budget unavailable.")
                allowed = int(row[0]) <= limit
    except DatabaseError:
        raise BudgetUnavailable("Security budget unavailable.") from None
    if secrets.randbelow(128) == 0:
        try:
            purge_expired(apply=True, batch=100)
        except DatabaseError:
            pass  # Cleanup failure cannot change the already committed security decision.
    if not allowed:
        raise BudgetExceeded(math.ceil(end - now))


def purge_expired(*, apply: bool = False, batch: int = 1000) -> int:
    from slaif_reservation.api.models import AbuseBucket

    cutoff = datetime.now(UTC)
    if not apply:
        return AbuseBucket.objects.filter(expires_at__lte=cutoff).count()
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('lock_timeout', '1000ms', true)")
            cursor.execute("SELECT set_config('statement_timeout', '2000ms', true)")
            cursor.execute(
                'DELETE FROM api_abuse_bucket WHERE "key" IN '
                '(SELECT "key" FROM api_abuse_bucket WHERE expires_at <= %s '
                "ORDER BY expires_at LIMIT %s FOR UPDATE SKIP LOCKED)",
                [cutoff, batch],
            )
            return int(cursor.rowcount)


def consume_authenticated(*, owner: str, token: str) -> None:
    consume("api_owner", owner)
    consume("api_token", token)


class AbuseControlMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        api = request.path.startswith("/api/v1/")
        login = request.method == "POST" and request.path in {"/login/", "/admin/login/"}
        if not api and not login:
            return self.get_response(request)
        try:
            if api:
                consume("api_ip", client_identity(request))
            else:
                consume("login_ip", client_identity(request))
                identity = str(request.POST.get("username", ""))[:320].strip().casefold()
                consume("login_identity", identity)
        except (BudgetExceeded, BudgetUnavailable) as error:
            limited = isinstance(error, BudgetExceeded)
            status = 429 if limited else 503
            response: HttpResponse
            if api:
                from slaif_reservation.api.problem import problem_response

                problem = problem_response(
                    request=request,
                    status_code=status,
                    code="rate_limited" if limited else "service_unavailable",
                    detail="Too many requests. Retry later."
                    if limited
                    else "Service temporarily unavailable.",
                )
                response = JsonResponse(
                    problem.data, status=status, content_type="application/problem+json"
                )
                response["X-Request-ID"] = problem["X-Request-ID"]
            else:
                # Shared branded error page (see config/views.py); the template
                # avoids user/message/session access, so it also renders when
                # the security database is unavailable. Status and headers
                # keep the existing abuse-control behavior.
                response = render(
                    request,
                    "web/error.html",
                    {
                        "status_code": status,
                        "error_title": "Too many requests" if limited else "Service unavailable",
                        "error_message": (
                            "Too many sign-in attempts. Please wait and retry."
                            if limited
                            else "Sign-in is temporarily unavailable. Please retry later."
                        ),
                    },
                    status=status,
                )
            response["Cache-Control"] = "no-store"
            if isinstance(error, BudgetExceeded):
                response["Retry-After"] = str(error.wait)
            return response
        return self.get_response(request)
