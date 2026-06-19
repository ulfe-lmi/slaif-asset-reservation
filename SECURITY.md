# Security Policy

## Project status

The project is in pre-alpha/bootstrap stage and is not approved for production use.

## Reporting a vulnerability

Report suspected vulnerabilities privately to the repository maintainers. Prefer GitHub private vulnerability reporting when enabled. Do not open a public issue containing exploit details, credentials, tokens, personal data, or production configuration.

Include:

- affected commit or release;
- concise impact description;
- reproduction steps using non-production data;
- suggested mitigation if known.

## Security principles

- no production secrets in the repository or coding-agent runtime;
- scoped, expiring, revocable API tokens stored only as one-way verifiers;
- secure sessions and CSRF protection for human users;
- object-level authorization for every asset and reservation action;
- database-enforced reservation conflict prevention;
- append-only audit evidence for privileged and mutating actions;
- minimal collection of personal data;
- HTTPS and secure-cookie settings in production;
- fail-closed behavior for unsupported or ambiguous authorization states.

See `docs/security-model.md` for the threat model and required controls.
