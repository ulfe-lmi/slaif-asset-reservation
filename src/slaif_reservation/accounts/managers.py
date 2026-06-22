from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib.auth.base_user import BaseUserManager

if TYPE_CHECKING:
    from slaif_reservation.accounts.models import User


class UserManager(BaseUserManager["User"]):
    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email: str | None) -> str:
        return super().normalize_email(email).casefold()

    def _create_user(self, email: str, password: str | None, **extra_fields: Any) -> User:
        if not email:
            msg = "Users require an email address"
            raise ValueError(msg)
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.full_clean(exclude=["password"])
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields: Any) -> User:
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(
        self, email: str, password: str | None = None, **extra_fields: Any
    ) -> User:
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            msg = "Superusers must have is_staff=True"
            raise ValueError(msg)
        if extra_fields.get("is_superuser") is not True:
            msg = "Superusers must have is_superuser=True"
            raise ValueError(msg)
        return self._create_user(email, password, **extra_fields)
