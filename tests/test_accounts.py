from __future__ import annotations

import uuid

import pytest
from django.db import IntegrityError, transaction

from slaif_reservation.accounts.models import User


@pytest.mark.django_db
def test_custom_user_creation_uses_uuid_and_normalized_email() -> None:
    user = User.objects.create_user(
        email="Example.User@Example.COM",
        password="not-a-secret",
        display_name="Example User",
    )

    assert isinstance(user.id, uuid.UUID)
    assert user.email == "example.user@example.com"
    assert user.check_password("not-a-secret")
    assert user.timezone == "Europe/Ljubljana"


@pytest.mark.django_db
def test_email_uniqueness_is_case_insensitive() -> None:
    User.objects.create_user(email="case@example.com", password="not-a-secret")

    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create(email="CASE@example.com")
