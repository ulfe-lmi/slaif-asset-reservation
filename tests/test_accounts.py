from __future__ import annotations

import uuid

import pytest
from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError, transaction

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


@pytest.mark.django_db
def test_external_identifier_fresh_persist_reload_preserves_opaque_value() -> None:
    user = User.objects.create_user(
        email="opaque-id@example.com",
        password="not-a-secret",
        external_identifier="00042-ABC",
    )
    assert user.external_identifier is not None

    reloaded = User.objects.get(email="opaque-id@example.com")
    assert reloaded.external_identifier == "00042-ABC"


@pytest.mark.django_db
def test_external_identifier_keeps_leading_zeroes_and_case() -> None:
    numeric = User.objects.create_user(
        email="leading-zeroes@example.com",
        password="not-a-secret",
        external_identifier="000123",
    )
    assert numeric.external_identifier == "000123"
    assert User.objects.get(pk=numeric.pk).external_identifier == "000123"

    # Case-sensitive opaque values: distinct casings are distinct values and
    # both may coexist.
    User.objects.create_user(
        email="case-a@example.com", password="not-a-secret", external_identifier="SlAif-1"
    )
    User.objects.create_user(
        email="case-b@example.com", password="not-a-secret", external_identifier="slaif-1"
    )
    assert {
        User.objects.get(email="case-a@example.com").external_identifier,
        User.objects.get(email="case-b@example.com").external_identifier,
    } == {"SlAif-1", "slaif-1"}


@pytest.mark.django_db
def test_external_identifier_maximum_length_is_128() -> None:
    max_ok = "x" * 128
    User.objects.create_user(
        email="max-len@example.com",
        password="not-a-secret",
        external_identifier=max_ok,
    )
    assert User.objects.get(email="max-len@example.com").external_identifier == max_ok

    user = User.objects.create_user(email="over-len@example.com", password="not-a-secret")
    user.external_identifier = "x" * 129
    with pytest.raises(ValidationError):
        user.full_clean(exclude=["password"])
    with pytest.raises(DataError), transaction.atomic():
        user.save()


@pytest.mark.django_db
def test_external_identifier_populated_values_are_unique() -> None:
    User.objects.create_user(
        email="dup-a@example.com",
        password="not-a-secret",
        external_identifier="same-value",
    )
    other = User.objects.create_user(email="dup-b@example.com", password="not-a-secret")
    other.external_identifier = "same-value"
    with pytest.raises(IntegrityError), transaction.atomic():
        other.save()


@pytest.mark.django_db
def test_external_identifier_multiple_users_may_be_unset() -> None:
    a = User.objects.create_user(email="unset-a@example.com", password="not-a-secret")
    b = User.objects.create_user(email="unset-b@example.com", password="not-a-secret")
    assert a.external_identifier is None
    assert b.external_identifier is None
    assert User.objects.filter(external_identifier__isnull=True).count() >= 2


@pytest.mark.django_db
def test_external_identifier_clearing_frees_the_value_for_reuse() -> None:
    holder = User.objects.create_user(
        email="clear-a@example.com",
        password="not-a-secret",
        external_identifier="reuse-me",
    )
    other = User.objects.create_user(email="clear-b@example.com", password="not-a-secret")

    holder.external_identifier = None
    holder.save(update_fields=["external_identifier"])
    assert holder.external_identifier is None

    other.external_identifier = "reuse-me"
    other.save(update_fields=["external_identifier"])
    assert other.external_identifier == "reuse-me"
    assert holder.external_identifier is None
