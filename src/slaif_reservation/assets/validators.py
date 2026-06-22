from __future__ import annotations

import json
from typing import Any

from django.core.exceptions import ValidationError

CAPABILITY_KEYS = frozenset({"vendor", "model", "memory_gib", "accelerator_family"})
PRIVATE_CAPABILITY_KEYS = frozenset(
    {
        "hostname",
        "host",
        "network_address",
        "ip_address",
        "physical_locator",
        "cuda_index",
        "cuda_ordinal",
        "gpu_uuid",
        "device_uuid",
    }
)
MAX_LEGACY_METADATA_BYTES = 8192


def validate_capabilities(value: Any) -> None:
    if not isinstance(value, dict):
        raise ValidationError("Capabilities must be a JSON object.")

    unknown_keys = set(value) - CAPABILITY_KEYS
    private_keys = set(value) & PRIVATE_CAPABILITY_KEYS
    if private_keys:
        raise ValidationError(
            f"Capabilities must not contain private hardware identifiers: {sorted(private_keys)}."
        )
    if unknown_keys:
        raise ValidationError(f"Unsupported capability keys: {sorted(unknown_keys)}.")

    for key in ("vendor", "model", "accelerator_family"):
        if key in value and (not isinstance(value[key], str) or not value[key].strip()):
            raise ValidationError(f"{key} must be a non-empty string.")

    if "memory_gib" in value:
        memory_gib = value["memory_gib"]
        if isinstance(memory_gib, bool) or not isinstance(memory_gib, int) or memory_gib <= 0:
            raise ValidationError("memory_gib must be a positive integer.")


def validate_legacy_metadata(value: Any) -> None:
    if not isinstance(value, dict):
        raise ValidationError("Legacy metadata must be a JSON object.")

    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    if len(encoded) > MAX_LEGACY_METADATA_BYTES:
        raise ValidationError("Legacy metadata exceeds the allowed size.")
