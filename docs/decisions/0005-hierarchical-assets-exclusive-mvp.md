# ADR 0005: Hierarchical Asset Model with Exclusive MVP

- **Status:** Accepted
- **Date:** 2026-06-19

## Context

The lab has named machines with independently reservable GPUs. Future resources may include whole machines, CPU pools, services, or non-compute assets. Modeling only GPUs would be narrow; implementing generic capacity sharing now would be speculative.

## Decision

Use a hierarchical `Asset` model with optional parent:

- machine parent;
- GPU or other reservable child;
- type/kind, tags, capabilities, status, timezone, and provenance;
- stable UUID and slug;
- initial `booking_mode = exclusive` only.

Do not infer physical device identity from legacy resource IDs or names. Capacity/shared booking modes require a future ADR and different integrity rules.

## Consequences

### Positive

- matches current machine/GPU inventory;
- supports machine-level browsing and policy inheritance;
- leaves room for other assets;
- keeps first concurrency invariant simple.

### Negative

- shallow hierarchy and inheritance rules must be defined carefully;
- shared/MIG/fractional resources are deferred;
- capabilities need schema/administrator verification.
