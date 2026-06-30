from __future__ import annotations

import uuid
from typing import Any, ClassVar

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower
from django.utils import timezone as django_timezone

from slaif_reservation.accounts.managers import UserManager
from slaif_reservation.accounts.tokens import (
    display_prefix_for_token_id,
    normalize_api_token_scopes,
    validate_api_token_scopes,
)
from slaif_reservation.accounts.validators import TIMEZONE_NAME_MAX_LENGTH, validate_timezone_name

API_TOKEN_SERVICE_CREATE_ATTR = "_slaif_api_token_service_create"
API_TOKEN_SERVICE_UPDATE_ATTR = "_slaif_api_token_service_update"
API_TOKEN_IMMUTABLE_FIELD_NAMES = (
    "id",
    "owner_id",
    "name",
    "verifier",
    "scopes",
    "expires_at",
    "created_at",
)
API_TOKEN_SERVICE_UPDATE_FIELDS = frozenset({"revoked_at", "revoked_by", "last_used_at"})
API_TOKEN_REVOCATION_UPDATE_FIELDS = frozenset({"revoked_at", "revoked_by"})
API_TOKEN_LAST_USE_UPDATE_FIELDS = frozenset({"last_used_at"})


class ApiTokenQuerySet(models.QuerySet["ApiToken"]):
    def bulk_create(self, objs: Any, *args: Any, **kwargs: Any) -> Any:
        raise ValidationError("API tokens must be created through the token service.")

    async def abulk_create(self, objs: Any, *args: Any, **kwargs: Any) -> Any:
        raise ValidationError("API tokens must be created through the token service.")

    def update(self, **kwargs: Any) -> int:
        raise ValidationError("API tokens must be changed through the token service.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ValidationError("API tokens cannot be hard-deleted.")


ApiTokenManagerBase = models.Manager.from_queryset(ApiTokenQuerySet)


class ApiTokenManager(ApiTokenManagerBase["ApiToken"]):
    def bulk_create(self, objs: Any, *args: Any, **kwargs: Any) -> Any:
        raise ValidationError("API tokens must be created through the token service.")

    async def abulk_create(self, objs: Any, *args: Any, **kwargs: Any) -> Any:
        raise ValidationError("API tokens must be created through the token service.")

    def bulk_update(
        self,
        objs: Any,
        fields: Any,
        batch_size: int | None = None,
    ) -> int:
        raise ValidationError("API tokens must be changed through the token service.")


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=255, blank=True)
    timezone = models.CharField(
        max_length=TIMEZONE_NAME_MAX_LENGTH,
        default="Europe/Ljubljana",
        validators=[validate_timezone_name],
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_service_account = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=django_timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects: ClassVar[UserManager] = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    class Meta:
        ordering = ["email"]
        constraints = [
            models.UniqueConstraint(Lower("email"), name="accounts_user_email_ci_unique"),
        ]

    def __str__(self) -> str:
        return self.email

    def clean(self) -> None:
        super().clean()
        self.email = type(self).objects.normalize_email(self.email)


class ApiToken(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_EXPIRED = "expired"
    STATUS_REVOKED = "revoked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="api_tokens",
    )
    name = models.CharField(max_length=100)
    verifier = models.CharField(max_length=64)
    scopes = models.JSONField(validators=[validate_api_token_scopes])
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="revoked_api_tokens",
    )
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ApiTokenManager()

    class Meta:
        base_manager_name = "objects"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["owner", "-created_at"], name="api_token_owner_created_idx"),
            models.Index(fields=["expires_at"], name="api_token_expires_idx"),
            models.Index(fields=["revoked_at"], name="api_token_revoked_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(expires_at__gt=F("created_at")),
                name="api_token_expires_after_created",
            ),
            models.CheckConstraint(
                condition=(
                    (Q(revoked_at__isnull=True) & Q(revoked_by__isnull=True))
                    | (Q(revoked_at__isnull=False) & Q(revoked_by__isnull=False))
                ),
                name="api_token_revocation_pair_valid",
            ),
            models.CheckConstraint(
                condition=Q(last_used_at__isnull=True) | Q(last_used_at__gte=F("created_at")),
                name="api_token_last_used_after_created",
            ),
            models.CheckConstraint(
                condition=~Q(scopes=[]),
                name="api_token_scopes_non_empty",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.display_prefix})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        update_fields = kwargs.get("update_fields")
        service_update = getattr(self, API_TOKEN_SERVICE_UPDATE_ATTR, False)
        service_create = getattr(self, API_TOKEN_SERVICE_CREATE_ATTR, False)
        if self._state.adding and not service_create:
            raise ValidationError("API tokens must be created through the token service.")
        if self._state.adding and self.pk and type(self)._base_manager.filter(pk=self.pk).exists():
            raise ValidationError("API tokens must be changed through the token service.")
        if self._state.adding:
            self.full_clean()
            super().save(*args, **kwargs)
            return

        if not service_update:
            raise ValidationError("API tokens must be changed through the token service.")
        self._validate_service_update_fields(update_fields)
        self._validate_immutable_history()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: object, **kwargs: object) -> tuple[int, dict[str, int]]:
        raise ValidationError("API tokens cannot be hard-deleted.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, list[str]] = {}
        self.name = self.name.strip()
        if not self.name:
            errors.setdefault("name", []).append("Token name is required.")

        try:
            self.scopes = normalize_api_token_scopes(self.scopes)
        except ValidationError as exc:
            errors.setdefault("scopes", []).extend(exc.messages)

        if self.revoked_at is None and self.revoked_by_id is not None:
            errors.setdefault("revoked_at", []).append("Revocation timestamp is required.")
        if self.revoked_at is not None and self.revoked_by_id is None:
            errors.setdefault("revoked_by", []).append("Revoking user is required.")
        if (
            self.last_used_at is not None
            and self.created_at
            and self.last_used_at < self.created_at
        ):
            errors.setdefault("last_used_at", []).append("Last use cannot be before creation.")
        if self.expires_at and self.created_at and self.expires_at <= self.created_at:
            errors.setdefault("expires_at", []).append("Expiry must be after creation.")
        if errors:
            raise ValidationError(errors)

    @property
    def display_prefix(self) -> str:
        return display_prefix_for_token_id(self.id)

    @property
    def status(self) -> str:
        if self.revoked_at is not None:
            return self.STATUS_REVOKED
        if self.expires_at <= django_timezone.now():
            return self.STATUS_EXPIRED
        return self.STATUS_ACTIVE

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes

    def _validate_service_update_fields(self, update_fields: Any) -> None:
        if update_fields is None:
            raise ValidationError("API token service updates must declare update_fields.")
        fields = frozenset(update_fields)
        if fields not in {API_TOKEN_REVOCATION_UPDATE_FIELDS, API_TOKEN_LAST_USE_UPDATE_FIELDS}:
            raise ValidationError("API token service update fields are not allowed.")
        if not fields <= API_TOKEN_SERVICE_UPDATE_FIELDS:
            raise ValidationError("API token service update fields are not allowed.")

    def _validate_immutable_history(self) -> None:
        try:
            stored = type(self)._base_manager.get(pk=self.pk)
        except type(self).DoesNotExist as exc:
            raise ValidationError("API token immutable history cannot be changed.") from exc
        for field_name in API_TOKEN_IMMUTABLE_FIELD_NAMES:
            if getattr(self, field_name) != getattr(stored, field_name):
                raise ValidationError("API token immutable history cannot be changed.")
