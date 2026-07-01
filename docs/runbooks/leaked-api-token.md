# Runbook: Leaked API Token

1. Revoke the affected token through the owner token page or a reviewed shell operation.
2. Search logs and audit metadata for the safe display prefix only, never for a full bearer token.
3. Review recent API activity for the token owner and correlation IDs.
4. Ask the owner to create a new token with the minimum required scopes.
5. If the pepper is suspected compromised, rotate `SLAIF_API_TOKEN_PEPPER`; this invalidates all
   existing tokens until a future key-ring design is implemented.

Do not paste bearer tokens into issues, PRs, chat, logs, screenshots, or runbooks.
