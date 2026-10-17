from __future__ import annotations

from typing import Any

from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AdminSplitDateTime
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
        "Enabling this flag blocks member and administration sign-in and API token issuance/use. "
        "Service-account API access is not supported. For automation, use an active human "
        "owner's scoped API token."
    ),
    "is_active": _("Inactive accounts cannot sign in anywhere, member or staff."),
    "is_staff": _(
        "Grants access to the management area and this administration. "
        "Entry follows this flag with an active, non-service-account "
        "session; it is not granted by individual permission selections. "
        "The matching model permissions are additionally required for "
        "per-model administration operations in this administration "
        "only; management itself needs none of them."
    ),
    "is_superuser": _(
        "Full administrative rights, including managing users. Superuser "
        "status does not bypass the active-human/staff admission gate: an "
        "inactive or service-account superuser is still denied everywhere."
    ),
    "groups": _(
        "Permission groups. Each group's permissions apply to all of its "
        "members additively, together with their individual permissions. "
        "This includes the documented reservations-namespace application "
        "permissions: a group carrying reservations.book_assets lets its "
        "members create new reservations, and membership in a group listed "
        "on a restricted asset's allowed groups is what lets a member book "
        "that asset. Groups are not project or membership authorization "
        "and grant no machine or login access. They do not admit a session "
        "by themselves; staff entry requires the active staff flag."
    ),
    "user_permissions": _(
        "Individual permissions, combined additively with all group "
        "permissions. Includes the documented reservations-namespace "
        "application permissions: selecting reservations.book_assets lets "
        "this account create new reservations (restricted assets "
        "additionally require membership in the asset's allowed groups). "
        "The remaining management and cross-user capabilities are "
        "documented for their planned purposes and take effect when their "
        "enforcement is active. They do not grant management access, "
        "which follows the active staff flag, and they do not admit a "
        "session by themselves."
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


class _BoundHelpSplitDateTime(AdminSplitDateTime):
    """Split date/time widget whose help div keeps a bindable id.

    Django 5.2's admin fieldset template assigns an id to a help div
    only when the field's ``id_for_label`` yields a single control id.
    A MultiWidget reports none (its inputs are ``id_<name>_0``/``_1``),
    so the rendered sub-inputs still carry the automatic
    ``aria-describedby`` pointing at a help div that never received an
    id. Reporting the first sub-input id makes the help div
    ``id_<name>_0_helptext`` and the binding real. No rendering,
    format or behavior change.
    """

    def id_for_label(self, id_: Any, index: Any = None) -> str:
        if index is None and id_:
            return f"{id_}_0"
        return super().id_for_label(id_)


class _BoundHelpRadioSelect(forms.RadioSelect):
    """RadioSelect whose help div keeps a bindable id.

    Django's RadioSelect reports no single control id (its choices are
    ``id_<name>_0``/``_1``), so Django's admin templates give the help
    div no id and the rendered choices no ``aria-describedby``.
    Reporting the first choice's id makes the help div
    ``id_<name>_0_helptext``; the matching ``aria-describedby`` is set
    on the widget's attrs so BOTH rendered choices bind it. Choice ids,
    choice labels, values, keyboard and submit behavior are unchanged.
    """

    def id_for_label(self, id_: Any, index: Any = None) -> str:
        if index is None and id_:
            return f"{id_}_0"
        return super().id_for_label(id_, index)


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

    Only the ``usable_password`` help text and its accessible binding
    change. The built-in warning, validators, hashing, the conditional
    field (present only while the user has a usable password), the
    submit actions and all admin permissions are inherited unchanged.
    The choice's help div keeps a bindable id (see
    ``_BoundHelpRadioSelect``) and both rendered choices carry the
    matching ``aria-describedby``.
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

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        field = self.fields.get("usable_password")
        if field is None:
            return
        old_widget = field.widget
        widget = _BoundHelpRadioSelect(attrs=dict(getattr(old_widget, "attrs", {}) or {}))
        widget.choices = list(getattr(old_widget, "choices", []) or [])
        # Bind BOTH rendered choices to the help div that the template
        # now renders with the first choice's id.
        widget.attrs["aria-describedby"] = "id_usable_password_0_helptext"
        field.widget = widget


@admin.register(User)
class UserAdmin(DjangoUserAdmin):  # type: ignore[type-arg]
    ordering = ["email"]

    @property
    def media(self) -> forms.Media:
        # Narrow local association helper for the JS-generated
        # select-filter list boxes (presentation only).
        return super().media + forms.Media(js=["web/admin-form-guidance.js"])

    list_display = ["email", "display_name", "is_staff", "is_service_account", "is_active"]
    search_fields = ["email", "display_name"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Profile",
            {"fields": ("display_name", "timezone", "is_service_account", "external_identifier")},
        ),
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
    change_password_form = SlaifAdminPasswordChangeForm

    def formfield_for_dbfield(self, db_field: Any, request: HttpRequest, **kwargs: Any) -> Any:
        form_field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "external_identifier" and isinstance(form_field, forms.CharField):
            # The opaque value must round-trip with EVERY character
            # (spaces, case, leading zeroes) exactly as entered: the form
            # must not strip or otherwise normalize it. The exact empty
            # value means "unset" and clears the stored value to NULL.
            form_field.strip = False
        return form_field

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
                    "external_identifier",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            )
            # Editable important dates: explain meaning and correction
            # impact (the product's created_at stays the immutable
            # record). Their help binds to the first split sub-input
            # (see _BoundHelpSplitDateTime).
            for name in ("last_login", "date_joined"):
                date_field = form.base_fields.get(name)
                if date_field is None:
                    continue
                if not date_field.help_text:
                    date_field.help_text = _USER_FIELD_HELP[name]
                widget = _BoundHelpSplitDateTime()
                widget.attrs["aria-describedby"] = f"id_{name}_0_helptext"
                date_field.widget = widget
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
    @property
    def media(self) -> forms.Media:
        # Narrow local association helper for the JS-generated
        # select-filter list boxes (presentation only).
        return super().media + forms.Media(js=["web/admin-form-guidance.js"])

    def formfield_for_manytomany(self, db_field: Any, request: HttpRequest, **kwargs: Any) -> Any:
        if db_field.name == "permissions":
            kwargs["help_text"] = _(
                "Permissions granted through this group, applied "
                "additively to each of its members. Includes the "
                "documented reservations-namespace application "
                "permissions: a group with reservations.book_assets lets "
                "its members create new reservations, and membership in "
                "this group can also satisfy a restricted asset's "
                "allowed-group requirement. They do not grant management "
                "access (which follows the active staff flag) and are "
                "not project or membership authorization."
            )
        form_field = super().formfield_for_manytomany(db_field, request=request, **kwargs)
        if db_field.name == "permissions" and form_field is not None:
            form_field.widget.attrs["aria-describedby"] = "id_permissions_helptext"
        return form_field


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
