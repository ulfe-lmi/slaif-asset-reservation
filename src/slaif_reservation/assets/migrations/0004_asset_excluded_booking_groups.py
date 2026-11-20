from django.db import migrations, models


class Migration(migrations.Migration):
    """Exact-asset group booking denylist (order 065-a, SAR-057).

    Adds ``excluded_booking_groups``, an optional M2M to the EXISTING
    ``auth.Group`` model: members of any selected group are denied NEW
    bookings on exactly this asset, whether the asset is restricted or
    unrestricted, and the exclusion wins over ``allowed_booking_groups``
    (dual membership is denied). Blank/default-empty means every existing
    asset migrates with NO excluded groups: no data backfill, no rewrite
    of existing asset rows' allow-lists and no change to any reservation,
    policy or audit record. Forward-only assets migration; it touches no
    merged migration, no reservation model and no exclusion constraint.
    """

    dependencies = [
        ("assets", "0003_booking_access"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.AddField(
            model_name="asset",
            name="excluded_booking_groups",
            field=models.ManyToManyField(
                blank=True,
                help_text=(
                    "Existing permission groups whose members may never "
                    "book this asset. Exclusion wins over the allowed list "
                    "and applies to this exact asset whether it is "
                    "restricted or unrestricted; membership in an excluded "
                    "group denies booking even when the member also belongs "
                    "to an allowed group. Existing assets start with no "
                    "excluded groups."
                ),
                related_name="excluded_booking_assets",
                to="auth.group",
            ),
        ),
    ]
