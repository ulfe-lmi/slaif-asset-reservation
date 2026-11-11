from __future__ import annotations

import uuid
from functools import partial
from typing import Any

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.widgets import AdminSplitDateTime
from django.contrib.auth.admin import GroupAdmin as DjangoGroupAdmin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX, identify_hasher
from django.contrib.auth.models import Group as AuthGroup
from django.core.exceptions import PermissionDenied
from django.db import router, transaction
from django.db.models import QuerySet
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters

from slaif_reservation.accounts import onboarding
from slaif_reservation.accounts.forms import SlaifUserCreationForm
from slaif_reservation.accounts.models import ApiToken, User

csrf_protect_m = method_decorator(csrf_protect)
sensitive_post_parameters_m = method_decorator(sensitive_post_parameters())

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
        "Grants admission to this administration (/admin/) only, with an "
        "active, non-service-account session and the matching model "
        "permissions for per-model administration operations. Staff status "
        "alone confers NO management-area access: /manage/ pages and "
        "management services require the documented reservations-namespace "
        "application permissions (granted through groups or individual "
        "permissions, e.g. via grant_management_access)."
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
        "members create new reservations, membership in a group listed on a "
        "restricted asset's allowed groups is what lets a member book that "
        "asset, and the nine management capabilities (for example "
        "reservations.view_booking_policies or "
        "reservations.view_all_reservations) admit the member to the "
        "matching /manage/ pages and services. Groups are not project or "
        "membership authorization and grant no machine or login access. "
        "They do not admit a session by themselves; administration entry "
        "requires the active staff flag."
    ),
    "user_permissions": _(
        "Individual permissions, combined additively with all group "
        "permissions. Includes the documented reservations-namespace "
        "application permissions: selecting reservations.book_assets lets "
        "this account create new reservations (restricted assets "
        "additionally require membership in the asset's allowed groups). "
        "The nine management capabilities are enforced now: the view or "
        "manage capability for booking policies, maintenance blackouts, "
        "all reservations, audit history and audit export admits this "
        "account to the matching /manage/ pages and services, and "
        "cancel/release-others allow cross-user lifecycle operations on "
        "their own. They do not grant administration access, which "
        "follows the active staff flag, and they do not admit a session "
        "by themselves."
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
    add_form = SlaifUserCreationForm
    # Per-model templates so the onboarding guidance and the reissue
    # control are presented on this product's own pages (they extend the
    # product's global administration change-form overrides).
    add_form_template = "admin/accounts/user/add_form.html"
    change_form_template = "admin/accounts/user/change_form.html"

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
            form_class: Any = form
            # The add form's own password guidance (temporary-credential
            # vs regular initial password) is owned by
            # SlaifUserCreationForm, which knows the account-email state.
            if form_class.base_fields.get("password2"):
                form_class.base_fields["password2"].help_text = _(
                    "Re-enter the same password to confirm it."
                )
            form_class.base_fields["is_staff"].help_text = _USER_FIELD_HELP["is_staff"]
            form_class.base_fields["is_superuser"].help_text = _USER_FIELD_HELP["is_superuser"]
            _wire_user_field_help(
                form_class,
                ("email", "password1", "password2", "is_staff", "is_superuser"),
            )
            # Finally bind the signed prefill proof (a digest only, never
            # the credential) and the per-administrator-session nonce from
            # the session, so a submitted six-character value can be proved
            # to be the generated one without ever storing it in plaintext.
            # No token was issued (email disabled, or the form was not
            # opened first) -> nothing to verify; the normal validators
            # apply to whatever is submitted.
            nonce = request.session.get(onboarding.NONCE_SESSION_KEY)
            proof = request.session.get(onboarding.PREFILL_PROOF_SESSION_KEY)
            if nonce is not None or proof is not None:
                form = partial(  # type: ignore[assignment]
                    form_class,
                    onboarding_nonce=nonce,
                    onboarding_prefill_proof=proof,
                )
        return form

    def get_changeform_initial_data(self, request: HttpRequest) -> dict[str, Any]:
        """Prefill the add form with a fresh generated temporary password.

        Every add GET generates a fresh six-character value in BOTH
        password controls plus a short-lived signed digest (in the
        session, never rendered) bound to this administrator's session —
        whether or not account email is enabled: with email enabled the
        value is the onboarding credential, with email disabled it shows
        the prefilled form whose submissions are refused until the
        transport is configured. Each GET generates a fresh value.
        """
        value = onboarding.generate_temporary_password()
        nonce = onboarding.session_nonce(request.session)
        request.session[onboarding.PREFILL_PROOF_SESSION_KEY] = onboarding.sign_prefill_proof(
            value, nonce
        )
        return {"password1": value, "password2": value}

    def save_model(self, request: HttpRequest, obj: Any, form: Any, change: bool) -> None:
        if change:
            super().save_model(request, obj, form, change)
            return
        if not settings.ACCOUNT_EMAIL_ENABLED:
            # Unreachable through the form, which refuses every add POST
            # while account email is disabled. Fail closed regardless:
            # never write an account without the delivery workflow.
            raise RuntimeError(
                "Admin account add requires the account email transport to "
                "be enabled; the add form refuses it while disabled."
            )
        # Onboarding add — the generated six-character prefill or a
        # manually entered normal-validator password: commit the account
        # INACTIVE/PENDING with only the password hash and the nonsecret
        # expiry metadata, then register exactly one post-commit send.
        # Activation happens only when the SMTP backend reports
        # acceptance of THIS exact credential generation (see onboarding
        # module); the credential must be changed on first login.
        temporary = str(form.cleaned_data["password1"])
        onboarding.start_onboarding(obj, temporary)
        super().save_model(request, obj, form, change)
        request.session.pop(onboarding.PREFILL_PROOF_SESSION_KEY, None)
        transaction.on_commit(
            partial(
                onboarding.deliver_onboarding_email,
                user_pk=obj.pk,
                temporary_password=temporary,
                request=request,
                sent_hash=obj.password,
                sent_expires_at=obj.onboarding_password_expires_at,
            )
        )

    def render_change_form(
        self, request: HttpRequest, context: Any, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        if kwargs.get("add"):
            # The add page explains the generated temporary credential.
            context["onboarding_email_enabled"] = settings.ACCOUNT_EMAIL_ENABLED
        else:
            obj = kwargs.get("obj")
            if obj is not None:
                # The change page shows the onboarding status block and the
                # reissue control only for accounts still pending their
                # first forced change (and only to editors).
                context["onboarding_pending"] = onboarding.is_pending_onboarding(obj)
                context["onboarding_expires_at"] = obj.onboarding_password_expires_at
                context["onboarding_can_reissue"] = self.has_change_permission(request, obj)
                # The reissue control is offered only while the account
                # email transport is configured; the page text is
                # state-specific (active vs inactive pending account).
                context["onboarding_email_enabled"] = settings.ACCOUNT_EMAIL_ENABLED
                context["onboarding_active"] = bool(obj.is_active)
                # The nonsecret delivery outcome from this administrator's
                # last send (persisted by the post-commit delivery step)
                # warns while the account is still pending. It is scoped
                # to THIS account: a failed send for another user must not
                # show on this page.
                context["onboarding_delivery_undelivered"] = (
                    onboarding.is_pending_onboarding(obj)
                    and onboarding.delivery_status_for(request, obj.pk) == "undelivered"
                )
        response = super().render_change_form(request, context, *args, **kwargs)
        if kwargs.get("add"):
            # The add form carries (or re-renders) the generated temporary
            # credential: it must never be cacheable.
            response["Cache-Control"] = "no-store"
        return response

    def get_urls(self) -> list[Any]:
        urls = [
            path(
                "<uuid:pk>/onboarding-reissue/",
                self.admin_site.admin_view(self.onboarding_reissue),
                name="accounts_user_onboarding_reissue",
            ),
        ]
        return urls + super().get_urls()

    @csrf_protect_m
    def onboarding_reissue(self, request: HttpRequest, pk: uuid.UUID) -> HttpResponse:
        """Explicit, permission-checked reissue of onboarding login details.

        GET shows a confirmation page explaining rotation and ambiguous
        delivery; POST (CSRF-checked) generates a NEW credential, invalidates
        the previous hash and expiry, and registers exactly one post-commit
        send. Restricted to accounts still in onboarding state; the admin
        must hold the model change permission; the secret is never shown.
        While account email is disabled the route refuses (GET and POST)
        before any mutation: no rotation, no expiry change, no audit entry
        and no send — a disabled transport must never invalidate a
        possibly working temporary password.
        """
        user = self.get_object(request, str(pk))
        if user is None:
            raise Http404(
                _("%(name)s object with primary key %(key)r does not exist.")
                % {"name": self.opts.verbose_name, "key": pk}
            )
        if not self.has_change_permission(request, user):
            raise PermissionDenied
        change_url = reverse("admin:accounts_user_change", args=[user.pk])
        if not onboarding.is_pending_onboarding(user):
            messages.error(
                request,
                "This account is not in onboarding state, so there is no "
                "temporary credential to reissue.",
            )
            return HttpResponseRedirect(change_url)
        if not settings.ACCOUNT_EMAIL_ENABLED:
            # No mail transport, no reissue: reissuing would rotate the
            # credential (invalidating a possibly working password and
            # making the account inactive again) with no way to deliver
            # the replacement. Refuse on BOTH GET and POST, before any
            # mutation: no rotation, no expiry change, no audit entry,
            # no send registration.
            messages.error(
                request,
                "Account email is not configured, so the login details "
                "cannot be sent and the onboarding credential cannot be "
                "reissued. Configure the account email transport first, "
                "then reissue.",
            )
            return HttpResponseRedirect(change_url)
        if request.method == "POST":
            value = onboarding.generate_temporary_password()
            with transaction.atomic(using=router.db_for_write(self.model)):
                onboarding.rotate_onboarding(user, value)
                user.save()
                self.log_change(
                    request,
                    user,
                    "Reissued onboarding login details (previous temporary "
                    "credential invalidated).",
                )
                transaction.on_commit(
                    partial(
                        onboarding.deliver_onboarding_email,
                        user_pk=user.pk,
                        temporary_password=value,
                        request=request,
                        sent_hash=user.password,
                        sent_expires_at=user.onboarding_password_expires_at,
                        reissue=True,
                    )
                )
            return HttpResponseRedirect(change_url)
        context = {
            **self.admin_site.each_context(request),
            "title": _("Reissue onboarding login details: %s") % user.email,
            "user": user,
            "opts": self.opts,
            "original": user,
            "expires_at": user.onboarding_password_expires_at,
            "change_url": change_url,
            "is_popup": False,
            "add": False,
            "has_change_permission": True,
            "app_label": self.opts.app_label,
        }
        request.current_app = self.admin_site.name
        return render(request, "admin/accounts/user/onboarding_reissue.html", context)


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
                "its members create new reservations, membership in this "
                "group can also satisfy a restricted asset's "
                "allowed-group requirement, and the nine management "
                "capabilities (view/manage policies, view/manage blackouts, "
                "view all reservations, cancel/release others, view/export "
                "audit) admit members to the matching /manage/ pages and "
                "services. They do not grant administration access "
                "(which follows the active staff flag) and are not "
                "project or membership authorization."
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
