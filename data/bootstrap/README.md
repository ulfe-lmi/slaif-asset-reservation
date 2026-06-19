# Sanitized Bootstrap Inventory

`assets.yaml` is migration input derived from the observed SmartScheduling resource inventory on 2026-06-17.

It contains:

- 29 public GPU records grouped by machine;
- one disabled GPU record from administrator inventory;
- one explicitly excluded non-compute `ChatGPT Pro` record;
- legacy resource IDs for reconciliation;
- public hardware display text.

It does not contain:

- users or administrator identities;
- emails or phone numbers;
- clients or appointments;
- browser cookies or anti-forgery tokens;
- iCalendar secrets;
- hostnames, network addresses, SSH credentials;
- verified CUDA indices or GPU UUIDs.

## Important

All hardware descriptions and ordinal hints require administrator/physical verification. Several legacy resource IDs have suffixes that do not match displayed GPU numbers. Import code must treat `legacy.resource_id` only as provenance.

## Validation

The file is described by `assets.schema.json`. PR 2 should add an automated schema-validation and idempotent import command. Until then it is documentation/data only.

## Physical verification checklist

For each machine and child asset, administrators should supply or confirm:

- actual hostname and canonical machine slug;
- device UUID or another stable local locator;
- whether display ordinal maps to CUDA ordinal;
- vendor/model and memory;
- active/reservable state;
- responsible resource manager;
- default availability and policy;
- whether capability metadata may be publicly visible.
