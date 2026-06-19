# ADR 0004: Separate Reservation Authority from Workload Execution

- **Status:** Accepted
- **Date:** 2026-06-19

## Context

The future vision includes agents reserving a GPU and invoking a deterministic gateway on machines such as Neumann. Reservation policy and workload execution have different privileges, failure modes, dependencies, and host placement.

## Decision

The core application grants and records entitlement only. It will not:

- SSH to machines;
- start processes or containers;
- choose `CUDA_VISIBLE_DEVICES`;
- store host root/SSH credentials;
- terminate another user's work.

Future machine gateways are separate services. They authenticate to a minimal reservation-verification interface and independently check physical state.

## Consequences

### Positive

- compromise of the web app does not automatically grant machine execution credentials;
- reservation service remains generic and centrally deployable;
- gateways can use machine-specific dependencies and policies;
- responsibilities and audit correlation are clearer.

### Negative

- reservation alone cannot guarantee that a GPU is physically idle;
- integration requires service authentication and correlation;
- users may temporarily reserve through the service and execute through existing manual mechanisms.
