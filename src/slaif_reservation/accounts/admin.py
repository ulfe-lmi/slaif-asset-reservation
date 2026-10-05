from __future__ import annotations

from typing import Any

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as DjangoGroupAdmin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX, identify_hasher
from django.contrib.auth.models import Group as AuthGroup
from django.contrib.auth.password_validation import password_validators_help_text_html
from django.db.models import QuerySet
from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from slaif_reservation.accounts.models import ApiToken, User

_USER_FIELD_HELP: dict[str, Any] = {
    "email": _(
        "Sign-in identifier for the account. Accounts are created by an "
        "administrator; self-registration is not available."
    ),
    "display_name": _(
        "Shown to staff in management views and on reservation records. "
        "Leave blank to show only the email."
    ),
    "timezone": _(
        "IANA time zone name (for example Europe/Ljubljana) used when this user books from the web."
    ),
    "is_service_account": _(
        "Machine account for API automation. Service accounts cannot sign in "
        "to the member site or the administration."
    ),
    "is_active": _("Inactive accounts cannot sign in anywhere, member or staff."),
    "is_staff": _(
        "Grants access to the management area and this administration. "
        "Entry follows this flag with an active, non-service-account "
        "session; it is not granted by individual permission selections. "
        "Per-model operations additionally require the matching model "
        "permissions."
    ),
    "is_superuser": _(
        "Full administrative rights, including managing users. Superuser "
        "status does not bypass the active-human/staff admission gate: an "
        "inactive or service-account superuser is still denied everywhere."
    ),
    "groups": _(
        "Site permission groups only: they grant the group's per-model site "
        "permissions. Groups are NOT project or membership authorization "
        "and do not change who can reserve assets. They do not admit a "
        "session by themselves; entry requires the active staff flag."
    ),
    "user_permissions": _(
        "Individual site permissions. They control per-model administration "
        "and management access only, not reservable-asset policy, and they "
        "do not admit a session by themselves; entry requires the active "
        "staff flag."
    ),
    "last_login": _(
        "When the user last signed in successfully (stored in UTC). Updated "
        "automatically on sign-in; edit only to correct a wrong value. "
        "Booking and availability logic never reads it."
    ),
    "date_joined": _(
        "When the account was created (stored in UTC). Editing it changes "
        "only this value; the separate created_at timestamp is the "
        "immutable product record."
    ),
}


class _SafePasswordStatusWidget(forms.Widget):
    """Renders a safe password status plus the real change action.

    Replaces the inherited hash summary: no algorithm, salt or hash fragment
    is rendered. The change action is the per-user password form
    (permission-checked and audited by the admin), not the inherited relative
    link. The stored hash is only used to compute a safe status.
    """

    template_name = "admin/safe_password_status.html"
    read_only = True

    def __init__(self, attrs: dict[str, Any] | None = None, *, user_pk: Any = None) -> None:
        super().__init__(attrs)
        self.user_pk = user_pk

    def get_context(self, name: str, value: Any, attrs: Any) -> dict[str, Any]:  # noqa: N802
        context = super().get_context(name, value, attrs)
        if not value:
            status = _("No password set — the account cannot sign in with a password yet.")
            action_label = _("Set password")
        elif str(value).startswith(UNUSABLE_PASSWORD_PREFIX):
            status = _("Password disabled — the account cannot sign in with a password.")
            action_label = _("Change password")
        else:
            try:
                identify_hasher(str(value))
            except ValueError:
                status = _("Stored password has an unrecognized format.")
                action_label = _("Change password")
            else:
                status = _("Password set.")
                action_label = _("Change password")
        context["password_status"] = status
        context["password_action_label"] = action_label
        context["password_action_url"] = (
            reverse("admin:auth_user_password_change", args=[self.user_pk])
            if self.user_pk is not None
            else ""
        )
        return context


def _wire_user_field_help(form: Any, names: tuple[str, ...]) -> None:
    for name in names:
        field = form.base_fields.get(name)
        if field is None:
            continue
        if not field.help_text:
            field.help_text = _USER_FIELD_HELP.get(name)
        if field.help_text:
            field.widget.attrs["aria-describedby"] = f"id_{name}_helptext"


class SlaifAdminPasswordChangeForm(AdminPasswordChangeForm):  # type: ignore[type-arg]
    """Per-user password change with product-accurate guidance.

    Only the ``usable_password`` help text and its accessibility wiring
    change. The built-in warning, validators, hashing, the conditional
    field (present only while the user has a usable password), the
    submit actions and all admin permissions are inherited unchanged.
    """

    # The built-in Django warning is preserved verbatim at the end of the
    # product help; only the generic backend sentence is replaced.
    usable_password_help_text = _(
        "Whether this user can sign in with a password. If you "
        "disable it, the current password is lost and password sign-in "
        "is blocked for this user. This deployment provides no other "
        "human login backend (no single sign-on or LDAP), so a "
        "disabled user cannot sign in until an administrator sets a "
        "new password here."
    ) + (
        '<ul id="id_unusable_warning" class="messagelist"><li class="warning">'
        "If disabled, the current password for this user will be lost."
        "</li></ul>"
    )

    def __init__(self, user: Any, *args: Any, **kwargs: Any) -> None:
        super().__init__(user, *args, **kwargs)
        if "usable_password" in self.fields:
            self.fields["usable_password"].widget.attrs["aria-describedby"] = (
                "id_usable_password_helptext"
            )


@admin.register(User)
class UserAdmin(DjangoUserAdmin):  # type: ignore[type-arg]
    ordering = ["email"]
    list_display = ["email", "display_name", "is_staff", "is_service_account", "is_active"]
    search_fields = ["email", "display_name"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("display_name", "timezone", "is_service_account")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_superuser"),
            },
        ),
    )
    readonly_fields = ["created_at", "updated_at"]
    password_change_form = SlaifAdminPasswordChangeForm

    def get_form(
        self,
        request: HttpRequest,
        obj: Any = None,
        change: bool = False,
        **kwargs: Any,
    ) -> Any:
        form = super().get_form(request, obj, change=change, **kwargs)
        if obj is not None:
            # Replace the inherited hash-summary password display with a safe
            # status and the real per-user password-change action. Hashing,
            # validation and model permissions are unchanged.
            form.base_fields["password"] = forms.Field(
                label=_("Password"),
                help_text=_(
                    "The stored password is never displayed. Use the action "
                    "below to set or change it."
                ),
                required=False,
                disabled=True,
                widget=_SafePasswordStatusWidget(attrs={"id": "id_password"}, user_pk=obj.pk),
            )
            # Precise product effects override the generic inherited model
            # help for the permission flags.
            form.base_fields["is_staff"].help_text = _USER_FIELD_HELP["is_staff"]
            form.base_fields["is_superuser"].help_text = _USER_FIELD_HELP["is_superuser"]
            form.base_fields["groups"].help_text = _USER_FIELD_HELP["groups"]
            form.base_fields["user_permissions"].help_text = _USER_FIELD_HELP["user_permissions"]
            _wire_user_field_help(
                form,
                (
                    "email",
                    "display_name",
                    "timezone",
                    "is_service_account",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                    "last_login",
                    "date_joined",
                ),
            )
        else:
            if form.base_fields.get("password1"):
                form.base_fields["password1"].help_text = (
                    _(
                        "Choose the initial password for this account. "
                        "Members cannot change their own password: the "
                        "profile page edits display name and timezone only, "
                        "so an administrator sets or changes it from this "
                        "user page. It must satisfy the site password rules:"
                    )
                    + password_validators_help_text_html()
                )
            if form.base_fields.get("password2"):
                form.base_fields["password2"].help_text = _(
                    "Re-enter the same password to confirm it."
                )
            form.base_fields["is_staff"].help_text = _USER_FIELD_HELP["is_staff"]
            form.base_fields["is_superuser"].help_text = _USER_FIELD_HELP["is_superuser"]
            _wire_user_field_help(
                form, ("email", "password1", "password2", "is_staff", "is_superuser")
            )
        return form


if AuthGroup in admin.site._registry:
    admin.site.unregister(AuthGroup)


@admin.register(AuthGroup)
class GroupAdmin(DjangoGroupAdmin):
    def formfield_for_manytomany(self, db_field: Any, request: HttpRequest, **kwargs: Any) -> Any:
        if db_field.name == "permissions":
            kwargs["help_text"] = _(
                "Site permissions granted through this group (administration "
                "and management access). These are NOT project or membership "
                "authorization and do not change who can reserve assets."
            )
            kwargs["widget"].attrs["aria-describedby"] = "id_permissions_helptext"
        return super().formfield_for_manytomany(db_field, request=request, **kwargs)


@admin.register(ApiToken)
class ApiTokenAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = [
        "id",
        "owner",
        "name",
        "display_prefix",
        "scopes",
        "created_at",
        "expires_at",
        "revoked_at",
        "last_used_at",
    ]
    list_filter = ["revoked_at", "expires_at", "created_at"]
    search_fields = ["owner__email", "name", "id"]
    readonly_fields = [
        "id",
        "owner",
        "name",
        "display_prefix",
        "scopes",
        "created_at",
        "expires_at",
        "revoked_at",
        "revoked_by",
        "last_used_at",
    ]
    exclude = ["verifier"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[ApiToken]:
        return super().get_queryset(request).select_related("owner", "revoked_by")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: ApiToken | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: ApiToken | None = None) -> bool:
        return False

    def get_actions(self, request: HttpRequest) -> dict[str, Any]:
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions
