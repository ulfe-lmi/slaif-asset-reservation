# SLAIF Asset Reservation

A professional reservation authority for shared laboratory assets, designed for both authenticated humans and authenticated software agents.

The initial deployment targets scattered Linux compute machines and their GPUs. The domain model remains asset-oriented so that other exclusive laboratory resources can be added without recreating the legacy appointment-salon abstraction.

## Status

**Architecture and repository bootstrap. No deployable application exists yet.**

The first implementation work is defined in `docs/work-orders/0001-application-scaffold.md` and must be delivered through a pull request.

## Product promise

A reservation accepted by the system is:

- conflict-free for its asset and time range;
- evaluated under the same policy for web and API clients;
- attributable to an authenticated principal;
- auditable;
- revocable or releasable through explicit state transitions.

## Intended clients

- **Humans:** browser-based resource discovery, availability, reservation, cancellation, and administration.
- **Agents:** versioned REST API with scoped, expiring tokens; idempotent mutations; stable machine-readable errors.
- **Future execution gateways:** deterministic services that verify reservation entitlement before using a machine or accelerator. Workload execution is deliberately outside the core application.

## Chosen shape

- Django 5.2 LTS monolith
- Django REST Framework 3.16
- PostgreSQL 17
- server-rendered UI, progressively enhanced
- OpenAPI-described `/api/v1/`
- Docker Compose deployment on an external Linux server behind HTTPS

See:

- [Discovery brief](docs/discovery-brief.md)
- [Architecture](docs/architecture.md)
- [Domain model](docs/domain-model.md)
- [API contract](docs/api-contract.md)
- [Human UI requirements](docs/human-ui.md)
- [Security model](docs/security-model.md)
- [OAP/Codex workflow](docs/oap-workflow.md)
- [Roadmap](docs/roadmap.md)

## Repository workflow

All implementation is performed through issue-scoped pull requests. Codex reads `AGENTS.md`, implements one approved work order, runs verification, opens a PR, and does not merge it. The strategic model reviews evidence and prepares a decision brief; a human maintainer decides whether to merge.

## Legacy system

The current scheduler repurposes SmartScheduling employees as GPUs and services as fixed reservation durations. Its sanitized resource inventory is retained in `data/bootstrap/assets.yaml` only as migration input. The new application does not preserve salon-specific concepts.

## License

Apache License 2.0. See `LICENSE`.
