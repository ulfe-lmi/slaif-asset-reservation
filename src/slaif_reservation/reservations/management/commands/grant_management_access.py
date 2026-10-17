"""Explicit legacy-staff setup for the A16 management capabilities.

Grants the nine A16 management/read-all application capabilities
(every documented reservations-namespace permission except the separate
baseline ``book_assets``) as DIRECT individual permissions to explicitly
selected existing active non-service-account staff accounts.

These are direct application grants, not implicit ``is_staff`` authority:
``is_staff`` alone still confers no application booking or management
bypass, superusers keep Django's permission semantics, and per-model
Administration access remains governed by the framework's model
permissions. The command never creates users, changes staff/superuser
flags, changes groups or removes existing grants, and it never grants
anything to users that were not explicitly selected.

Dry-run by default; ``--apply`` performs the (atomic, idempotent) write.
Every selection is validated before ANY write, so a mixed valid/invalid
batch writes nothing.
"""

from __future__ import annotations

import uuid as uuid_module
from typing import Any

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from slaif_reservation.accounts.authorization import (
    MANAGEMENT_PERMISSIONS,
    RESERVATIONS_APP_LABEL,
    permission_label,
)
from slaif_reservation.accounts.models import User


class Command(BaseCommand):
    help = (
        "Grant the nine A16 management capabilities (all documented "
        "reservations-namespace permissions except book_assets) as direct "
        "individual permissions to explicitly selected existing active "
        "non-service-account staff accounts. Dry-run by default; pass "
        "--apply to write. Direct application grants, not implicit is_staff "
        "authority; per-model Administration access and superuser semantics "
        "are separate."
    )

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--user",
            action="append",
            dest="users",
            required=True,
            metavar="USER_UUID",
            help=(
                "UUID of an existing active non-service-account staff "
                "account. Repeat the flag for every selected account."
            ),
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply the grants (default is a dry-run that writes nothing).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        raw_selections: list[str] = options["users"]
        apply: bool = options["apply"]

        problems: list[str] = []
        parsed: dict[str, uuid_module.UUID] = {}
        for position, raw in enumerate(raw_selections, start=1):
            try:
                user_id = uuid_module.UUID(raw.strip())
            except (ValueError, AttributeError):
                problems.append(f"selection {position}: not a valid UUID")
                continue
            if str(user_id) in parsed:
                continue
            parsed[str(user_id)] = user_id

        users = {user.id: user for user in User.objects.filter(id__in=list(parsed.values()))}
        for key, user_id in parsed.items():
            user = users.get(user_id)
            if user is None:
                problems.append(f"selection {key}: no such user")
                continue
            if not user.is_staff:
                problems.append(f"selection {key}: not a staff account")
            elif not user.is_active:
                problems.append(f"selection {key}: account is inactive")
            elif user.is_service_account:
                problems.append(f"selection {key}: service accounts cannot be selected")
        if problems:
            for problem in problems:
                self.stderr.write(f"refused: {problem}")
            raise CommandError(f"{len(problems)} selection problem(s); nothing was changed.")

        content_type = ContentType.objects.get(
            app_label=RESERVATIONS_APP_LABEL, model="reservation"
        )
        codenames = list(MANAGEMENT_PERMISSIONS)
        permissions = {
            perm.codename: perm
            for perm in Permission.objects.filter(content_type=content_type, codename__in=codenames)
        }
        missing = [codename for codename in codenames if codename not in permissions]
        if missing:
            raise CommandError(
                "reservations permissions are missing from the database "
                "(run 'manage.py migrate' first): " + ", ".join(missing)
            )

        if not apply:
            self.stdout.write("DRY RUN — nothing will be changed.")
        mode = "will be granted" if apply else "would be granted (dry-run)"
        total_to_add = 0
        for key in parsed:
            user = users[parsed[key]]
            already = {
                perm_codename
                for perm_codename in codenames
                if user.user_permissions.filter(
                    content_type=content_type, codename=perm_codename
                ).exists()
            }
            to_add = [codename for codename in codenames if codename not in already]
            total_to_add += len(to_add)
            self.stdout.write(
                f"user {key}: {len(already)}/{len(codenames)} direct grant(s) "
                f"present; {mode} {', '.join(to_add) if to_add else 'nothing (idempotent)'}"
            )
        self.stdout.write(
            f"{len(parsed)} selected user(s); {len(codenames)} capabilities "
            f"each; {total_to_add} grant(s) "
            + ("will be added" if apply else "would be added (dry-run)")
            + "."
        )
        self.stdout.write(
            "Capabilities: " + ", ".join(permission_label(codename) for codename in codenames)
        )

        if not apply:
            return
        with transaction.atomic():
            for key in parsed:
                user = users[parsed[key]]
                for codename in codenames:
                    user.user_permissions.add(permissions[codename])
        self.stdout.write(
            f"Applied: {total_to_add} grant(s) added across {len(parsed)} user(s); "
            "existing grants and groups unchanged."
        )
