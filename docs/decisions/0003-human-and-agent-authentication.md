# ADR 0003: Separate Human Sessions and Agent API Tokens

- **Status:** Accepted
- **Date:** 2026-06-19

## Context

Humans need browser authentication, while agents need non-interactive access that can be scoped, expired, revoked, and audited independently. Reusing passwords or browser cookies for agents is unsafe and operationally brittle.

## Decision

- define a custom Django user model before the first migration;
- use secure Django sessions and CSRF for browser users;
- use separately issued bearer tokens for API agents;
- store only a one-way/HMAC-derived token verifier and non-secret prefix;
- associate each token with an accountable owner, scopes, expiry, and optional resource/project restrictions;
- design for later institutional OIDC without guessing provider details now.

## Consequences

### Positive

- agents do not store human passwords/cookies;
- one token can be revoked without disabling the user;
- least-privilege scopes are possible;
- token use is auditable.

### Negative

- custom token implementation and security tests are required;
- operators need token lifecycle UI/runbooks;
- local login remains temporary until OIDC is configured.

## Rejected

- DRF's basic plaintext database token as the long-term design;
- shared API key for all agents;
- automation of browser login;
- storing recoverable token plaintext.
