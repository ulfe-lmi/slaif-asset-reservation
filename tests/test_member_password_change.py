"""Logged-in own-password change (order 056-a, SAR-054).

Focused positive/negative coverage for the member route: admission
boundary (anonymous/inactive/service-account/bearer-only denial), current
password requirement, normal validator set without a weakened path, CSRF,
session semantics (current session retained, other sessions invalidated),
own-account-only mutation and no credential material in rendered output.
"""

from __future__ import annotations

import re

import pytest
from django.contrib.auth import authenticate
from django.test import Client

from slaif_reservation.accounts.models import User
from slaif_reservation.accounts.services import issue_api_token

URL = "/profile/password/"
LOGIN_URL = "/login/"


@pytest.fixture
def member_user() -> User:
    return User.objects.create_user(
        email="pw-member@example.com",
        password="not-a-secret",
        display_name="Password Member",
        timezone="Europe/Ljubljana",
    )


@pytest.fixture
def other_user() -> User:
    return User.objects.create_user(
        email="pw-other@example.com",
        password="not-a-secret",
        display_name="Password Other",
        timezone="UTC",
    )


@pytest.fixture
def service_account() -> User:
    return User.objects.create_user(
        email="pw-agent@example.com",
        password="not-a-secret",
        is_service_account=True,
    )


@pytest.fixture
def inactive_user() -> User:
    return User.objects.create_user(
        email="pw-inactive@example.com",
        password="not-a-secret",
        is_active=False,
    )


def _input_value(html: str, control_id: str) -> str:
    match = re.search(rf'<input[^>]*id="{control_id}"[^>]*>', html)
    assert match, f"missing control {control_id}"
    value = re.search(r'value="([^"]*)"', match.group(0))
    return value.group(1) if value else ""


@pytest.mark.django_db
def test_anonymous_get_and_post_are_denied(client: Client) -> None:
    get = client.get(URL)
    assert get.status_code == 302
    assert get["Location"].startswith(LOGIN_URL)
    post = client.post(URL, {"old_password": "x", "new_password1": "y", "new_password2": "y"})
    assert post.status_code == 302
    assert post["Location"].startswith(LOGIN_URL)


@pytest.mark.django_db
def test_inactive_user_is_denied_and_session_terminated(
    client: Client, inactive_user: User
) -> None:
    client.force_login(inactive_user)
    get = client.get(URL)
    assert get.status_code == 302
    assert get["Location"].startswith(LOGIN_URL)
    # The disallowed session is cleared, not carried into another route.
    assert not client.session.get("_auth_user_id")


@pytest.mark.django_db
def test_service_account_is_denied_and_session_terminated(
    client: Client, service_account: User
) -> None:
    client.force_login(service_account)
    assert client.get(URL).status_code == 302
    post = client.post(
        URL, {"old_password": "not-a-secret", "new_password1": "a", "new_password2": "a"}
    )
    assert post.status_code == 302
    assert post["Location"].startswith(LOGIN_URL)
    service_account.refresh_from_db()
    assert service_account.check_password("not-a-secret")
    assert not client.session.get("_auth_user_id")


@pytest.mark.django_db
def test_bearer_only_request_is_denied(client: Client, member_user: User) -> None:
    result = issue_api_token(
        owner=member_user, name="Bearer-only", scopes=["reservations:read"], lifetime_days=1
    )
    headers = {"HTTP_AUTHORIZATION": f"Bearer {result.token}"}
    get = client.get(URL, **headers)
    assert get.status_code == 302
    assert get["Location"].startswith(LOGIN_URL)
    post = client.post(
        URL,
        {"old_password": "not-a-secret", "new_password1": "a", "new_password2": "a"},
        **headers,
    )
    assert post.status_code == 302
    assert post["Location"].startswith(LOGIN_URL)


@pytest.mark.django_db
def test_get_renders_branded_guided_page_without_secrets(client: Client, member_user: User) -> None:
    client.force_login(member_user)
    html = client.get(URL).content.decode()
    assert "Change password — SLAIF Asset Reservation" in html
    for fragment in (
        "Current password",
        "New password",
        "New password confirmation",
        "at least 8 characters",
        'autocomplete="current-password"',
        'autocomplete="new-password"',
    ):
        assert fragment in html
    for control_id in ("id_old_password", "id_new_password1", "id_new_password2"):
        assert _input_value(html, control_id) == "", f"{control_id} prefills a value"
    assert "pbkdf2_sha256" not in html
    assert "not-a-secret" not in html
    assert "Django" not in html


@pytest.mark.django_db
def test_forged_post_without_csrf_is_denied(client: Client, member_user: User) -> None:
    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(member_user)
    post = csrf_client.post(
        URL, {"old_password": "not-a-secret", "new_password1": "a", "new_password2": "a"}
    )
    assert post.status_code == 403
    member_user.refresh_from_db()
    assert member_user.check_password("not-a-secret")


@pytest.mark.django_db
def test_wrong_current_password_fails_without_db_change(client: Client, member_user: User) -> None:
    client.force_login(member_user)
    stored = member_user.password
    response = client.post(
        URL,
        {
            "old_password": "leak-old-secret-1",
            "new_password1": "brand-new-passw0rd",
            "new_password2": "brand-new-passw0rd",
        },
    )
    assert response.status_code == 200
    html = response.content.decode()
    assert "Check the highlighted fields" in html
    member_user.refresh_from_db()
    assert member_user.password == stored
    # Submitted values are never echoed back in the re-rendered page.
    assert "leak-old-secret-1" not in html
    assert "brand-new-passw0rd" not in html
    assert "pbkdf2_sha256" not in html


@pytest.mark.django_db
def test_missing_fields_fail_without_db_change(client: Client, member_user: User) -> None:
    client.force_login(member_user)
    stored = member_user.password
    response = client.post(URL, {})
    assert response.status_code == 200
    member_user.refresh_from_db()
    assert member_user.password == stored


@pytest.mark.django_db
def test_mismatched_new_passwords_fail_without_db_change(client: Client, member_user: User) -> None:
    client.force_login(member_user)
    stored = member_user.password
    response = client.post(
        URL,
        {
            "old_password": "not-a-secret",
            "new_password1": "brand-new-passw0rd",
            "new_password2": "different-passw0rd",
        },
    )
    assert response.status_code == 200
    member_user.refresh_from_db()
    assert member_user.password == stored


@pytest.mark.django_db
@pytest.mark.parametrize(
    "new_password",
    [
        "short",
        "password",
        "12345678",
    ],
    ids=["too-short", "common", "numeric"],
)
def test_normal_validators_still_apply_without_db_change(
    client: Client, member_user: User, new_password: str
) -> None:
    client.force_login(member_user)
    stored = member_user.password
    response = client.post(
        URL,
        {
            "old_password": "not-a-secret",
            "new_password1": new_password,
            "new_password2": new_password,
        },
    )
    assert response.status_code == 200
    member_user.refresh_from_db()
    assert member_user.password == stored


@pytest.mark.django_db
def test_valid_change_updates_hash_and_current_session_continues(
    client: Client, member_user: User, other_user: User
) -> None:
    client.force_login(member_user)
    other_hash = other_user.password
    response = client.post(
        URL,
        {
            "old_password": "not-a-secret",
            "new_password1": "brand-new-passw0rd",
            "new_password2": "brand-new-passw0rd",
        },
    )
    assert response.status_code == 302
    assert response["Location"] == "/profile/"
    member_user.refresh_from_db()
    assert member_user.check_password("brand-new-passw0rd")
    assert authenticate(username=member_user.email, password="not-a-secret") is None
    assert authenticate(username=member_user.email, password="brand-new-passw0rd") is not None
    # The current session stays signed in and shows the nonsecret notice.
    profile = client.get("/profile/")
    assert profile.status_code == 200
    assert "Password changed" in profile.content.decode()
    # A different account is untouched.
    other_user.refresh_from_db()
    assert other_user.password == other_hash
    assert authenticate(username=other_user.email, password="not-a-secret") is not None


@pytest.mark.django_db
def test_other_sessions_for_the_account_are_invalidated(client: Client, member_user: User) -> None:
    client.force_login(member_user)
    second = Client()
    second.force_login(member_user)
    assert second.get("/profile/").status_code == 200

    response = client.post(
        URL,
        {
            "old_password": "not-a-secret",
            "new_password1": "brand-new-passw0rd",
            "new_password2": "brand-new-passw0rd",
        },
    )
    assert response.status_code == 302

    # The browser that changed the password is still signed in...
    assert client.get("/profile/").status_code == 200
    # ...while the other session for the account is no longer admitted.
    denied = second.get("/profile/")
    assert denied.status_code == 302
    assert denied["Location"].startswith(LOGIN_URL)
