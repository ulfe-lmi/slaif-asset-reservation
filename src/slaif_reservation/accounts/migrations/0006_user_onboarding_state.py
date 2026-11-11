"""Onboarding state for administrator-created temporary credentials (A-17).

Adds a single nullable timestamp to ``accounts.User``:
``onboarding_password_expires_at``. It is NULL for every pre-existing
account (no data change) and is set only while an account is pending its
first forced password change after an administrator-created temporary
credential. The timestamp is metadata, never a credential: the stored
password remains the normal one-way hash.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_user_external_identifier"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="onboarding_password_expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
