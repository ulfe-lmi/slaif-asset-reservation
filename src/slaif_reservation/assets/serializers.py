from __future__ import annotations

from rest_framework import serializers

from slaif_reservation.assets.models import Asset, AssetTag


class AssetTagSerializer(serializers.ModelSerializer):  # type: ignore[misc]
    class Meta:
        model = AssetTag
        fields = ["slug", "name"]


class AssetParentSerializer(serializers.ModelSerializer):  # type: ignore[misc]
    class Meta:
        model = Asset
        fields = ["id", "slug", "name"]


class AssetSerializer(serializers.ModelSerializer):  # type: ignore[misc]
    parent = AssetParentSerializer(read_only=True)
    tags = AssetTagSerializer(many=True, read_only=True)

    class Meta:
        model = Asset
        fields = [
            "id",
            "slug",
            "name",
            "kind",
            "parent",
            "description",
            "timezone",
            "active",
            "reservable",
            "verification_required",
            "tags",
            "capabilities",
        ]
