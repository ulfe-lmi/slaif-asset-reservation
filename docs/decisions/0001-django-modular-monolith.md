# ADR 0001: Django Modular Monolith

- **Status:** Accepted
- **Date:** 2026-06-19

## Context

The product needs mature human authentication, sessions, CSRF, forms, administration, database migrations, a browser UI, and a machine API. The initial operator team benefits from simple deployment and transactions. The system does not yet have scale or organizational boundaries that justify multiple services.

## Decision

Implement a modular monolith using:

- Python 3.13;
- Django 5.2 LTS;
- Django REST Framework 3.16;
- server-rendered templates with progressive enhancement;
- one PostgreSQL database;
- clear internal apps/services for accounts, assets, reservations, audit, API, and web.

No JavaScript SPA, message broker, or microservice is part of the initial architecture.

## Consequences

### Positive

- mature security and admin foundations;
- one transaction boundary for reservation/audit operations;
- one deployment artifact;
- shared logic for human and agent interfaces;
- lower operational burden.

### Negative

- module boundaries require discipline rather than network enforcement;
- asynchronous/large-scale work may need later infrastructure;
- UI must be deliberately designed rather than relying on an SPA component ecosystem.

## Revisit when

- measured workload requires independent scaling;
- a component has a materially different trust boundary or release cadence;
- background retries/latency require a queue;
- an execution gateway is introduced, which should remain a separate service.
