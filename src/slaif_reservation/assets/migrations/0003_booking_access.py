from django.db import migrations, models


class Migration(migrations.Migration):
    """Explicit per-asset booking access for the selected A16 target.

    Adds the additive application-capability surface for exact-asset group
    eligibility (SAR-049): whether booking the asset is restricted to an
    explicit list of existing permission groups, and that list itself.
    Every existing asset migrates ``booking_restricted=False`` with no
    allowed groups, i.e. unchanged (unrestricted) booking access. This is a
    forward-only assets migration; it touches no merged migration, no
    reservation model and no exclusion constraint.
    """

    dependencies = [
        ("assets", "0002_asset_legacy_source_id_meaningful"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.AddField(
            model_name="asset",
            name="booking_restricted",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Restrict booking of this asset to members of the "
                    "selected allowed groups. Unrestricted assets remain "
                    "bookable by any user holding the booking permission."
                ),
            ),
        ),
        migrations.AddField(
            model_name="asset",
            name="allowed_booking_groups",
            field=models.ManyToManyField(
                blank=True,
                help_text=(
                    "Existing permission groups whose members may book "
                    "this asset while it is restricted. Membership in any "
                    "one selected group is sufficient. Ignored while the "
                    "asset is unrestricted."
                ),
                related_name="allowed_booking_assets",
                to="auth.group",
            ),
        ),
    ]
