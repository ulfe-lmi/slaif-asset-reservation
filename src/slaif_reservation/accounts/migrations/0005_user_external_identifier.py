# Hand-authored migration: adds the optional opaque external_identifier
# column (A16 authorization upgrade) and performs the one-time baseline
# booking grant. No generator provenance is claimed for this file.

from django.db import migrations, models


def grant_baseline_booking_permission(apps, schema_editor):
    """One-time baseline grant for the authorization upgrade (A16/048-a).

    Adds ONLY ``reservations.book_assets`` as a direct individual permission
    to every existing non-service-account user, including inactive rows so a
    later normal reactivation preserves their former booking baseline.
    Service accounts receive nothing; no group is created or changed and no
    other permission (management, read-all, administration) is granted.

    Permission rows are created by post_migrate only after the whole migrate
    run, so the ``book_assets`` row is ensured here through the historical
    apps (never by importing current models). Re-running a normal migrate
    never re-runs this migration and never grants newly created accounts.
    """
    user_model = apps.get_model("accounts", "User")
    permission_model = apps.get_model("auth", "Permission")
    content_type_model = apps.get_model("contenttypes", "ContentType")

    content_type, _created = content_type_model.objects.get_or_create(
        app_label="reservations", model="reservation"
    )
    permission, _created = permission_model.objects.get_or_create(
        content_type=content_type,
        codename="book_assets",
        defaults={"name": "Book assets."},
    )
    for user in user_model.objects.filter(is_service_account=False):
        user.user_permissions.add(permission)


def revert_baseline_booking_permission(apps, schema_editor):
    """Intentionally a no-op.

    Downgrading does not silently revoke the one-time booking baseline or any
    operator-configured grant; removing grants is a deliberate operator
    action outside migrations.
    """


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_alter_apitoken_options"),
        ("reservations", "0003_reservation_application_permissions"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="external_identifier",
            field=models.CharField(
                blank=True,
                help_text=(
                    "Optional opaque identifier for an external system, at most 128 "
                    "characters, case-sensitive. It may represent an external "
                    "account identifier (including a Linux UID), but the value is "
                    "opaque: it is not validated as a UID, it is not a credential "
                    "and it grants no machine access. Numeric strings and leading "
                    "zeroes are preserved exactly as entered. Populated values "
                    "must be unique; leave empty to unset it. It does not replace "
                    "the account's UUID, email, password or token identity."
                ),
                max_length=128,
                null=True,
                unique=True,
            ),
        ),
        migrations.RunPython(grant_baseline_booking_permission, revert_baseline_booking_permission),
    ]
