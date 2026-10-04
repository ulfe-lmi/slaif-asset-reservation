# Security Policy

## Project status

The project is in internal-alpha stage and is not approved for production use.

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
- shared, expiring PostgreSQL budgets for member/admin login and API traffic,
  including invalid bearer attempts and authenticated account/token limits;
- object-level authorization for every asset and reservation action;
- database-enforced reservation conflict prevention;
- append-only audit evidence for privileged and mutating actions;
- minimal collection of personal data;
- HTTPS and secure-cookie settings in production;
- explicit trusted-proxy-peer boundary: only configured peers
  (`SLAIF_TRUSTED_PROXY_PEERS`) may forward TLS/client identity, with
  overwrite-not-append forwarding; every other peer is a direct client
  pinned to the plain transport; ALL forwarding headers are stripped in
  both branches, the original socket peer is preserved separately from
  the normalized client identity, and the edge default `Referrer-Policy`
  is deferred so stricter per-view policies (one-time token page)
  survive the proxy;
- safe logs and error responses: raw request lines, headers, bodies and
  arbitrary exception state are never retained in logs or echoed back to
  clients;
- fail-closed behavior for unsupported or ambiguous authorization states.

See `docs/security-model.md` for the threat model and required controls.
## Concentrated OAP development security boundary

Preserve all pre-existing vulnerability reporting, licensing and application security text above.
The private repository remains private. Workflow conversion is not a product release or approval to
contact Neumann, other lab machines, an identity provider, SmartScheduling or production services.
Product and development credentials are different assets. No role home, private auth history, FIFO,
log, `.env`, dump or secret-bearing report enters the application image or Git.

Coding executes only a validated active order; it never merges, self-approves, enables auto-merge
or adjudicates DHA. Strategy may merge development work only under separately attributable scoped
activation, exact-head successful required CI, serious evidence review and verified absence of
unapproved external merge effects. It may not waive a D2 boundary or human target/release gate.
The conversion adoption PR itself remains human-merged. Role variables, hashes, typed human names,
local flags and available Git credentials are not proof of authority or technical isolation.

Runtime must be bounded and rebuildable with owned disposable databases, test files/volumes/ports
and no real product secrets. The bootstrap fixture suite never invokes actual models or real remotes.
Do not copy global Codex authentication or browse private legacy exports for convenience. No
unqualified unrestricted mode, broad home mounts, root-host cleanup or automatic-start service.
All installed role instruction sources and compact projections are drift-checked against accepted
source; candidate hashes cannot grant their own permissions. Human adjudication provenance uses a
separate verified human identity/signing path, never agent-created human-looking Markdown.

Known source evidence limits are preserved in ARCHITECTURE.md. In particular, broad readiness
counts and application/ORM immutability do not prove real operational availability or privileged-DB
resistance. Existing operational tests/rehearsal must not run against valuable deployment files.
Routine bugs need repair, not permission escalation; model reports and green CI are evidence indexes,
not independent closure or release authorization.
