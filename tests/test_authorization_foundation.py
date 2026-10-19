"""Order 048-a: A16 authorization foundation (permissions, helper, identifier).

Covers the ten reservations-namespace permission records, the
accounts.authorization helper semantics (group union, individual grants,
staff/inactive/service/superuser gates, fresh principals), the admin
exposure of the optional opaque external_identifier, forged member/bearer
refusals and the unchanged protected-record boundaries. No enforcement is
wired in this order; these tests pin the foundation only.
"""

from __future__ import annotations

import re

import pytest
from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client

from slaif_reservation.accounts.authorization import (
    BOOKING_BASELINE_PERMISSION,
    MANAGEMENT_PERMISSIONS,
    RESERVATIONS_PERMISSIONS,
    has_reservation_permission,
)
from slaif_reservation.accounts.models import User
from slaif_reservation.accounts.services import issue_api_token
from slaif_reservation.assets.models import Asset, AssetTag
from slaif_reservation.reservations.models import Reservation


@pytest.fixture
def member_user() -> User:
    return User.objects.create_user(
        email="foundation-member@example.com",
        password="not-a-secret",
        display_name="Foundation Member",
    )


@pytest.fixture
def staff_user() -> User:
    return User.objects.create_user(
        email="foundation-staff@example.com",
        password="not-a-secret",
        display_name="Foundation Staff",
        is_staff=True,
    )


@pytest.fixture
def admin_user() -> User:
    return User.objects.create_superuser(
        email="foundation-admin@example.com",
        password="not-a-secret",
        display_name="Foundation Admin",
    )


@pytest.fixture
def reservation_content_type() -> ContentType:
    return ContentType.objects.get_for_model(Reservation)


@pytest.fixture
def application_permissions(reservation_content_type: ContentType) -> dict[str, Permission]:
    return {
        perm.codename: perm
        for perm in Permission.objects.filter(
            content_type=reservation_content_type,
            codename__in=list(RESERVATIONS_PERMISSIONS),
        )
    }


# --- permission records -----------------------------------------------------


@pytest.mark.django_db
def test_ten_documented_application_permissions_exist(
    application_permissions: dict[str, Permission],
) -> None:
    assert tuple(sorted(application_permissions)) == tuple(sorted(RESERVATIONS_PERMISSIONS))
    for _codename, permission in application_permissions.items():
        assert permission.content_type.model == "reservation"
        assert permission.name  # useful human labels are set
        assert permission.name.strip()


def test_management_set_is_all_ten_except_baseline() -> None:
    assert len(MANAGEMENT_PERMISSIONS) == 9
    assert BOOKING_BASELINE_PERMISSION not in MANAGEMENT_PERMISSIONS
    assert set(MANAGEMENT_PERMISSIONS) | {BOOKING_BASELINE_PERMISSION} == set(
        RESERVATIONS_PERMISSIONS
    )


# --- helper semantics --------------------------------------------------------


@pytest.mark.django_db
def test_helper_requires_active_authenticated_non_service_human(
    member_user: User, application_permissions: dict[str, Permission]
) -> None:
    codename = "book_assets"
    perm = application_permissions[codename]

    assert has_reservation_permission(AnonymousUser(), codename) is False

    member_user.user_permissions.add(perm)
    assert has_reservation_permission(User.objects.get(pk=member_user.pk), codename) is True

    member_user.is_active = False
    member_user.save(update_fields=["is_active"])
    assert has_reservation_permission(User.objects.get(pk=member_user.pk), codename) is False
    member_user.is_active = True
    member_user.save(update_fields=["is_active"])

    service = User.objects.create_user(
        email="foundation-service@example.com",
        password="not-a-secret",
        is_service_account=True,
    )
    service.user_permissions.add(perm)
    assert has_reservation_permission(User.objects.get(pk=service.pk), codename) is False


@pytest.mark.django_db
def test_helper_no_grant_and_staff_alone_confer_no_capability(
    member_user: User, staff_user: User
) -> None:
    assert has_reservation_permission(member_user, "book_assets") is False
    # Staff admission to /admin/ is not an application grant.
    assert has_reservation_permission(staff_user, "book_assets") is False
    assert has_reservation_permission(staff_user, "view_all_reservations") is False


@pytest.mark.django_db
def test_helper_individual_and_group_grants_combine_by_union(
    member_user: User, application_permissions: dict[str, Permission]
) -> None:
    book = application_permissions["book_assets"]
    view_all = application_permissions["view_all_reservations"]
    view_audit = application_permissions["view_audit_history"]

    group_a = Group.objects.create(name="foundation-group-a")
    group_a.permissions.add(book)
    group_b = Group.objects.create(name="foundation-group-b")
    group_b.permissions.add(view_all)
    member_user.groups.add(group_a, group_b)
    member_user.user_permissions.add(view_audit)

    fresh = User.objects.get(pk=member_user.pk)
    assert has_reservation_permission(fresh, "book_assets") is True
    assert has_reservation_permission(fresh, "view_all_reservations") is True
    assert has_reservation_permission(fresh, "view_audit_history") is True
    assert has_reservation_permission(fresh, "cancel_others_reservations") is False

    # A direct grant survives removal from the granting group.
    member_user.user_permissions.add(view_audit)  # already present; idempotent
    member_user.groups.remove(group_a)
    member_user.groups.remove(group_b)
    fresh = User.objects.get(pk=member_user.pk)
    assert has_reservation_permission(fresh, "view_audit_history") is True
    assert has_reservation_permission(fresh, "book_assets") is False
    assert has_reservation_permission(fresh, "view_all_reservations") is False


@pytest.mark.django_db
def test_helper_superuser_retains_django_semantics_but_gates_hold() -> None:
    admin = User.objects.create_superuser(
        email="foundation-su@example.com",
        password="not-a-secret",
    )
    # Trusted active superuser: Django permission semantics (no explicit
    # grants needed).
    assert has_reservation_permission(admin, "book_assets") is True
    assert has_reservation_permission(admin, "export_audit_history") is True

    # Inactive superuser with an explicit grant: still denied.
    admin.is_active = False
    admin.save(update_fields=["is_active"])
    perm = Permission.objects.get(codename="book_assets", content_type__app_label="reservations")
    admin.user_permissions.add(perm)
    assert has_reservation_permission(User.objects.get(pk=admin.pk), "book_assets") is False

    # Service-account superuser with an explicit grant: still denied.
    service_su = User.objects.create_superuser(
        email="foundation-su-service@example.com",
        password="not-a-secret",
        is_service_account=True,
    )
    service_su.user_permissions.add(perm)
    assert has_reservation_permission(User.objects.get(pk=service_su.pk), "book_assets") is False


@pytest.mark.django_db
def test_helper_rejects_unknown_codename(member_user: User) -> None:
    with pytest.raises(ValueError):
        has_reservation_permission(member_user, "not_a_real_codename")


@pytest.mark.django_db
def test_helper_tracks_current_grants_with_fresh_principals(
    application_permissions: dict[str, Permission],
) -> None:
    user = User.objects.create_user(email="foundation-fresh@example.com", password="not-a-secret")
    perm = application_permissions["view_booking_policies"]

    user.user_permissions.add(perm)
    assert has_reservation_permission(User.objects.get(pk=user.pk), "view_booking_policies") is True

    # Revocation is observed by a fresh per-request principal: no
    # process-global grant cache.
    user.user_permissions.remove(perm)
    assert (
        has_reservation_permission(User.objects.get(pk=user.pk), "view_booking_policies") is False
    )


# --- admin exposure of external_identifier ----------------------------------


def _assert_bound_help(html: str, name: str, fragment: str) -> None:
    control = re.search(rf'<(?:input|select|textarea)[^>]*id="id_{name}"[^>]*>', html)
    assert control, f"control id_{name} missing"
    assert f'aria-describedby="id_{name}_helptext"' in control.group(0)
    help_block = re.search(rf'id="id_{name}_helptext".*?</div>', html, re.S)
    assert help_block, f"help div id_{name}_helptext missing"
    assert fragment in help_block.group(0)


@pytest.mark.django_db
def test_admin_user_change_exposes_identifier_with_bound_help(
    client: Client, admin_user: User, member_user: User
) -> None:
    client.force_login(admin_user)
    html = client.get(f"/admin/accounts/user/{member_user.pk}/change/").content.decode()
    assert 'id="id_external_identifier"' in html
    _assert_bound_help(html, "external_identifier", "opaque identifier for an external system")
    # The add form stays minimal and does not expose the mapping field.
    add_html = client.get("/admin/accounts/user/add/").content.decode()
    assert 'id="id_external_identifier"' not in add_html


@pytest.mark.django_db
def test_admin_user_change_sets_and_clears_identifier(
    client: Client, admin_user: User, member_user: User
) -> None:
    client.force_login(admin_user)
    url = f"/admin/accounts/user/{member_user.pk}/change/"
    base = {
        "email": member_user.email,
        "display_name": "Foundation Member",
        "timezone": "UTC",
        "is_active": "on",
        "last_login_0": "",
        "last_login_1": "",
        "date_joined_0": member_user.date_joined.strftime("%Y-%m-%d"),
        "date_joined_1": member_user.date_joined.strftime("%H:%M:%S"),
    }

    response = client.post(url, {**base, "external_identifier": "00042-Ext"})
    assert response.status_code == 302
    member_user.refresh_from_db()
    assert member_user.external_identifier == "00042-Ext"

    # Empty input clears the opaque value back to NULL.
    response = client.post(url, {**base, "external_identifier": ""})
    assert response.status_code == 302
    member_user.refresh_from_db()
    assert member_user.external_identifier is None


@pytest.mark.django_db
def test_admin_user_change_preserves_opaque_whitespace_end_to_end(
    client: Client, admin_user: User, member_user: User
) -> None:
    client.force_login(admin_user)
    url = f"/admin/accounts/user/{member_user.pk}/change/"
    base = {
        "email": member_user.email,
        "display_name": "Foundation Member",
        "timezone": "UTC",
        "is_active": "on",
        "last_login_0": "",
        "last_login_1": "",
        "date_joined_0": member_user.date_joined.strftime("%Y-%m-%d"),
        "date_joined_1": member_user.date_joined.strftime("%H:%M:%S"),
    }

    # Surrounding spaces are content in an opaque value: the form must
    # not strip them and the stored value keeps every character.
    response = client.post(url, {**base, "external_identifier": " 00042-Ext "})
    assert response.status_code == 302
    member_user.refresh_from_db()
    assert member_user.external_identifier == " 00042-Ext "

    # The rendered change form offers the value back unchanged.
    html = client.get(url).content.decode()
    assert 'value=" 00042-Ext "' in html

    # 129 characters (spaces included) is rejected and the stored value
    # is unchanged.
    response = client.post(url, {**base, "external_identifier": " " + "y" * 128})
    assert response.status_code == 200
    assert "Ensure this value has at most 128 characters (it has 129)." in (
        response.content.decode()
    )
    member_user.refresh_from_db()
    assert member_user.external_identifier == " 00042-Ext "


@pytest.mark.django_db
def test_admin_identifier_editing_follows_model_permissions(
    client: Client,
    admin_user: User,
    staff_user: User,
    member_user: User,
) -> None:
    url = f"/admin/accounts/user/{member_user.pk}/change/"

    # Non-staff: no administration at all (admission gate unchanged).
    client.force_login(member_user)
    assert client.get(url).status_code == 302

    # Staff without the accounts.change_user model permission: refused.
    client.force_login(staff_user)
    assert client.get(url).status_code == 403

    # Forged POST denials: the SAME payload an authorized staff member may
    # submit is refused for a non-staff user and for staff without the
    # model permission, and neither attempt changes the stored identifier.
    forged = {
        "email": member_user.email,
        "display_name": "Foundation Member",
        "timezone": "UTC",
        "is_active": "on",
        "external_identifier": "00077-Priv",
        "last_login_0": "",
        "last_login_1": "",
        "date_joined_0": member_user.date_joined.strftime("%Y-%m-%d"),
        "date_joined_1": member_user.date_joined.strftime("%H:%M:%S"),
    }

    client.force_login(member_user)
    response = client.post(url, forged)
    assert response.status_code == 302
    assert "login" in response["Location"]
    member_user.refresh_from_db()
    assert member_user.external_identifier is None

    client.force_login(staff_user)
    assert client.post(url, forged).status_code == 403
    member_user.refresh_from_db()
    assert member_user.external_identifier is None

    # Staff with the per-model permission may edit the identifier
    # (valid same-payload positive control).
    privileged = User.objects.create_user(
        email="foundation-privileged@example.com",
        password="not-a-secret",
        is_staff=True,
    )
    privileged.user_permissions.add(
        Permission.objects.get(codename="change_user", content_type__app_label="accounts")
    )
    client.force_login(privileged)
    response = client.get(url)
    assert response.status_code == 200
    payload = {
        "email": member_user.email,
        "display_name": "Foundation Member",
        "timezone": "UTC",
        "is_active": "on",
        "external_identifier": "00077-Priv",
        "last_login_0": "",
        "last_login_1": "",
        "date_joined_0": member_user.date_joined.strftime("%Y-%m-%d"),
        "date_joined_1": member_user.date_joined.strftime("%H:%M:%S"),
    }
    assert client.post(url, payload).status_code == 302
    member_user.refresh_from_db()
    assert member_user.external_identifier == "00077-Priv"


@pytest.mark.django_db
def test_member_profile_cannot_see_or_modify_identifier(client: Client, member_user: User) -> None:
    client.force_login(member_user)
    html = client.get("/profile/").content.decode()
    assert "id_external_identifier" not in html

    response = client.post(
        "/profile/",
        {"display_name": "Still here", "timezone": "UTC", "external_identifier": "forged-1"},
    )
    assert response.status_code == 302
    member_user.refresh_from_db()
    assert member_user.external_identifier is None
    assert member_user.display_name == "Still here"


@pytest.fixture
def probe_asset() -> Asset:
    machine = Asset.objects.create(
        slug="foundation-machine",
        name="Foundation Machine",
        kind=Asset.KIND_MACHINE,
        active=True,
        reservable=False,
    )
    asset = Asset.objects.create(
        slug="foundation-gpu",
        name="Foundation GPU",
        kind=Asset.KIND_GPU,
        parent=machine,
        active=True,
        reservable=True,
    )
    asset.tags.add(AssetTag.objects.create(slug="foundation-tag", name="Foundation Tag"))
    return asset


@pytest.mark.django_db
def test_bearer_api_neither_reveals_nor_modifies_identifier(
    client: Client, member_user: User, probe_asset: Asset
) -> None:
    # 051-a: creating a create-scope token now requires the CURRENT booking
    # capability, so represent a LEGITIMATE historical token: grant the
    # baseline capability, issue while it holds, then revoke it before any
    # request. The stored token keeps its scope; the no-implicit-grant
    # assertions below are preserved unchanged.
    book = Permission.objects.get(codename="book_assets", content_type__app_label="reservations")
    member_user.user_permissions.add(book)
    issued = issue_api_token(
        owner=member_user,
        name="Foundation probe",
        scopes=["reservations:read", "reservations:create"],
        lifetime_days=1,
    )
    member_user.user_permissions.remove(book)
    assert not member_user.has_perm("reservations.book_assets")
    authorization = f"Bearer {issued.bearer_token}"
    me = client.get("/api/v1/me/", HTTP_AUTHORIZATION=authorization)
    assert me.status_code == 200
    assert "external_identifier" not in me.json()["principal"]

    # Forged mutation input carrying the identifier is rejected by the
    # bounded API contract; the account mapping cannot be written via API.
    response = client.post(
        "/api/v1/reservations/",
        {
            "asset_id": str(probe_asset.id),
            "start_at": "2026-10-18T09:00:00Z",
            "end_at": "2026-10-18T10:00:00Z",
            "purpose": "probe",
            "external_identifier": "forged-bearer",
        },
        content_type="application/json",
        HTTP_AUTHORIZATION=authorization,
        HTTP_IDEMPOTENCY_KEY="048a-foundation-probe-1",
    )
    assert response.status_code == 400
    body = response.json()
    assert body["detail"] == "The request parameters or body are invalid."
    # The forged identifier value is not echoed back in the safe problem
    # detail either.
    assert "forged-bearer" not in str(body)
    assert "external_identifier" not in str(body)
    member_user.refresh_from_db()
    assert member_user.external_identifier is None


@pytest.mark.django_db
def test_protected_records_remain_protected(
    client: Client, admin_user: User, member_user: User
) -> None:
    client.force_login(admin_user)
    # Tokens stay read-only/service-backed even for a superuser.
    assert client.get("/admin/accounts/apitoken/add/").status_code == 403
    assert client.get("/admin/accounts/apitoken/").status_code == 200


# --- grant_management_access setup command ---------------------------------


@pytest.mark.django_db
def test_grant_management_access_dry_run_writes_nothing(
    staff_user: User, application_permissions: dict[str, Permission]
) -> None:
    from io import StringIO

    from django.core.management import call_command

    out = StringIO()
    call_command(
        "grant_management_access",
        "--user",
        str(staff_user.pk),
        stdout=out,
        stderr=StringIO(),
    )
    assert "DRY RUN" in out.getvalue()
    assert str(staff_user.pk) in out.getvalue()
    # No email or other identifier is printed.
    assert staff_user.email not in out.getvalue()
    staff_user.refresh_from_db()
    assert staff_user.user_permissions.count() == 0


@pytest.mark.django_db
def test_grant_management_access_applies_nine_capabilities_idempotently(
    staff_user: User, application_permissions: dict[str, Permission]
) -> None:
    from io import StringIO

    from django.core.management import call_command

    book_assets = application_permissions["book_assets"]
    # Pre-existing direct grant is preserved and reported as present.
    staff_user.user_permissions.add(book_assets)

    call_command(
        "grant_management_access",
        "--user",
        str(staff_user.pk),
        "--apply",
        stdout=StringIO(),
        stderr=StringIO(),
    )
    staff_user.refresh_from_db()
    custom = {
        perm.codename
        for perm in staff_user.user_permissions.filter(codename__in=list(MANAGEMENT_PERMISSIONS))
    }
    assert custom == set(MANAGEMENT_PERMISSIONS)
    assert book_assets in staff_user.user_permissions.all()
    count_after_first = staff_user.user_permissions.count()

    # Idempotent: a second apply adds nothing.
    call_command(
        "grant_management_access",
        "--user",
        str(staff_user.pk),
        "--apply",
        stdout=StringIO(),
        stderr=StringIO(),
    )
    staff_user.refresh_from_db()
    assert staff_user.user_permissions.count() == count_after_first


@pytest.mark.django_db
def test_grant_management_access_refuses_invalid_selections_without_writes(
    staff_user: User,
    member_user: User,
    application_permissions: dict[str, Permission],
) -> None:
    import uuid as uuid_module
    from io import StringIO

    from django.core.management import call_command
    from django.core.management.base import CommandError

    inactive_staff = User.objects.create_user(
        email="foundation-inactive-staff@example.com",
        password="not-a-secret",
        is_staff=True,
        is_active=False,
    )
    service_staff = User.objects.create_user(
        email="foundation-service-staff@example.com",
        password="not-a-secret",
        is_staff=True,
        is_service_account=True,
    )

    def _attempt(*users: str) -> str:
        out, err = StringIO(), StringIO()
        with pytest.raises(CommandError):
            call_command(
                "grant_management_access",
                *users,
                "--apply",
                stdout=out,
                stderr=err,
            )
        return err.getvalue()

    # Malformed identifier.
    err = _attempt("--user", "not-a-uuid", "--user", str(staff_user.pk))
    assert "not a valid UUID" in err

    # Nonexistent user.
    err = _attempt("--user", str(uuid_module.uuid4()))
    assert "no such user" in err

    # Non-staff selection.
    err = _attempt("--user", str(member_user.pk))
    assert "not a staff account" in err

    # Inactive selection.
    err = _attempt("--user", str(inactive_staff.pk))
    assert "account is inactive" in err

    # Service-account selection.
    err = _attempt("--user", str(service_staff.pk))
    assert "service accounts cannot be selected" in err

    # Mixed valid/invalid batch: EVERY selection is validated before ANY
    # write, so the valid member receives nothing either.
    err = _attempt("--user", str(staff_user.pk), "--user", str(member_user.pk))
    assert "not a staff account" in err

    for user in (staff_user, member_user, inactive_staff, service_staff):
        user.refresh_from_db()
        assert user.user_permissions.count() == 0


@pytest.mark.django_db
def test_grant_management_access_never_touches_groups_or_flags(
    staff_user: User, application_permissions: dict[str, Permission]
) -> None:
    from io import StringIO

    from django.core.management import call_command

    group = Group.objects.create(name="foundation-setup-group")
    staff_user.groups.add(group)
    flags_before = (staff_user.is_staff, staff_user.is_superuser, staff_user.is_active)

    call_command(
        "grant_management_access",
        "--user",
        str(staff_user.pk),
        "--apply",
        stdout=StringIO(),
        stderr=StringIO(),
    )
    staff_user.refresh_from_db()
    assert (staff_user.is_staff, staff_user.is_superuser, staff_user.is_active) == flags_before
    assert set(staff_user.groups.values_list("id", flat=True)) == {group.pk}


@pytest.mark.django_db
def test_grant_management_access_missing_user_refused_without_writes(
    staff_user: User, application_permissions: dict[str, Permission]
) -> None:
    """Missing the required --user selection refuses with ZERO writes."""
    from io import StringIO

    from django.core.management import call_command
    from django.core.management.base import CommandError

    out, err = StringIO(), StringIO()
    with pytest.raises(CommandError, match="the following arguments are required: --user"):
        call_command("grant_management_access", stdout=out, stderr=err)
    staff_user.refresh_from_db()
    assert staff_user.user_permissions.count() == 0


@pytest.mark.django_db
def test_grant_management_access_rolls_back_after_a_real_grant(
    staff_user: User,
    application_permissions: dict[str, Permission],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A post-write failure rolls back the earlier real grant.

    Fault injection makes the SECOND through-table write fail after the
    first grant has actually been written inside the command's atomic
    block: the user must end with NO grants at all (earlier real writes
    rolled back, groups/flags untouched), and the failure propagates.
    """
    from io import StringIO

    from django.core.management import call_command
    from django.db.models.query import QuerySet

    through = User.user_permissions.through
    original = QuerySet.bulk_create
    calls = 0

    def fail_second(self, *args: object, **kwargs: object) -> object:
        nonlocal calls
        if self.model is through:
            calls += 1
            if calls == 2:
                raise RuntimeError("synthetic grant failure")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(QuerySet, "bulk_create", fail_second)
    with pytest.raises(RuntimeError, match="synthetic grant failure"):
        call_command(
            "grant_management_access",
            "--user",
            str(staff_user.pk),
            "--apply",
            stdout=StringIO(),
            stderr=StringIO(),
        )
    assert calls == 2
    staff_user.refresh_from_db()
    assert staff_user.user_permissions.count() == 0
    assert staff_user.is_staff and staff_user.is_active and not staff_user.is_superuser
