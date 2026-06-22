from __future__ import annotations

import pytest
from django.core.management import call_command


def test_django_check_succeeds() -> None:
    call_command("check")


@pytest.mark.django_db
def test_no_model_migration_drift() -> None:
    call_command("makemigrations", check=True, dry_run=True, verbosity=0)
