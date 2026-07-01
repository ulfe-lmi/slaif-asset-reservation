# Runbook: API Token Pepper Rotation Limitation

The current token verifier uses one server-side `SLAIF_API_TOKEN_PEPPER`.

Rotating this pepper invalidates every existing API token because no key-ring or verifier version is
implemented yet. A planned rotation requires:

- maintenance announcement to token owners;
- deployment of the new pepper through the protected secret store;
- restart of application workers;
- users creating replacement tokens;
- revocation or expiry tracking for old tokens.

Emergency rotation is appropriate if the pepper may have leaked. Do not print either the old or new
pepper in operational records.
