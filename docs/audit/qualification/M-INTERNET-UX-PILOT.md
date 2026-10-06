# Authenticated Internet/UX pilot — qualification and architecture freshness

> Historical qualification snapshot. Current independent milestone evidence and
> publication assessment are in the [freshness record](M-INTERNET-UX-PILOT-FRESHNESS.md).

This is a strategic qualification record, not independent closure audit or
permission to expose a real service. The selected target is A-15 in the full
canonical [architecture](../../../ARCHITECTURE.md).

## Source and target

The documentation round starts from merged revision
`fb135dbc4a91a6fc983f49a6785d75c4277029c2`. The architecture SHA-256 is
`f8a8df265d4dd452969d4bee874045c8f8a8261f9c87c96ba4c049a7dddf320d`;
its complete stable requirement index contains SAR-001 through SAR-047.

The current full architecture already records the human-selected authenticated
Internet/UX target, default-policy initialization contract, public entry/product
identity, explained forms, safe operator appearance overrides, SLAIF design and
threaded Gunicorn responsiveness. This round reconciles older operator prose
with that selected contract; it changes no application, migration, dependency,
Docker/Compose, proxy, inventory, architecture, projection or law bytes.
Accordingly no architecture requirement is removed/redefined and no projection
recomposition is needed. This is a freshness assessment, not a declaration that
all requirements are independently IMPLEMENTED.

The old internal-pilot audit at a9c3133 remains historical evidence. It does not
qualify the changed Internet-facing target. The required next audit begins with
attributable human target scope, full architecture/digest, canonical requirement
index and one exact merged revision; every applicable row begins UNPROVEN.
The exact post-documentation revision must be retrieved after merge, not invented
in this record. Findings require bounded repairs and a full architecture-to-current-
main reassessment, not merely a closed-findings check.

## Disposable qualification

All operations below used owned disposable source, explicit settings/URLs,
synthetic accounts/configuration, local Docker and exact ownership cleanup.
No real DNS/certificate issuance, trust-store change, public listener,
production data/secrets, private legacy exports or lab/Neumann resource was used.

| Evidence | Actual command/path | Result |
| --- | --- | --- |
| Runtime, shared abuse and default policy | `pytest tests/test_gunicorn_responsiveness.py tests/test_abuse_controls.py tests/test_abuse_http.py tests/test_default_policy.py --no-cov -q` | 40 passed, 84.05s. Real Gunicorn old-sync sensitivity/six held clients; shared PostgreSQL/multiple-process budgets; fresh/repeat/configured-upgrade policy cases. |
| Real HTTPS boundary | `pytest tests/test_https_boundary.py::test_https_boundary_rehearsal_passes tests/test_https_boundary.py::test_https_boundary_output_leaks_no_db_password tests/test_https_boundary.py::test_no_owned_residue_after_rehearsal --no-cov -q` | 3 passed, 184.56s. The wrapper drove the production-shaped image/private PG through pinned Caddy v2.11.6 and checked privacy/cleanup; no skip. |
| Local Docker evaluation | Canonical `compose.yaml` runtime with unique image/ownership, precreated owned network/volume and kernel-assigned loopback host ports | Build/start, migrations, repeated initializer, sanitized import dry/apply, operational check, interactive administrator creation, health/readiness and real browser login passed. |
| Policy after evaluation | Real database inspection | Exactly one active global `default`, start horizon7 days, maximum2880 minutes. Detailed minimum/lead/cutoff/purpose/caps are pinned by the policy suite. |
| Data retention and teardown | Owned evaluation stop/start and identity-receipted cleanup | Stop/start retained the database volume. Final teardown deleted only objects matching nonce/ID/creation receipts; no project-wide prune/down or foreign cleanup. |
| Proxy-peer discovery commands | Documented Docker inspect/network Go templates against a verified owned container | Execute successfully. Fresh installation now creates the network before discovering/configuring its gateway. |

The evaluation used random loopback ports because an existing PostgreSQL service
occupied the canonical development port. Its application command/environment and
schema were unchanged; only test ownership/image/host-port plumbing differed.
The administrator command was genuinely interactive (Email, password, confirmation)
through an owned PTY. Generated credentials/transcripts were not retained; browser
checks captured no secret-bearing page, cookies, CSRF values, trace or HAR.

Production configuration rendering, container build/non-root/static checks,
real PostgreSQL concurrency/rollback, backup/restore drills, browser/CSRF/owner
privacy, settings negatives, branding safety/same-image qualification and
pip-audit are also exercised by the standard full CI suite. The final literal
implementation and immutable report heads must each have all five checks
quality/test/security/container/oap-harness successful before acceptance. Their
actual IDs/counts belong in the immutable round report; this record cannot
predict future results.

## Visual evidence

The merged visual-design implementation
`01159efce5d91302e99a99a21509c440d0989048` had 964 tests pass at CI37344926250,
with OAP37344926002 successful; report
`8f773c49179e23e7dc5c71e11a2f4c2b6aa4a618` had all five checks succeed at
CI37346880102/OAP37346880012 before the protected merge.

Real Chromium captures compare default and institutional themes at
1440/1024/768/390 pixels across 33 anonymous/member/staff/administration surfaces
plus open navigation. ROOT inspected representative contact sets covering every
surface, viewport class and theme, plus long-form detail crops. The retained
270-image manifest digest is
`4055cfee39c60b926308c87aaf832adafae8522bd562a08475b4e62b1b51d8b9`.
This does not mean every original was individually opened. The immutable
[design report](../../../oap/reports/039-a-slaif-design.md) records actual
source identity, minor final markup correction, iterations, failures and limits.

Current references slaif.si/doc.slaif.si/edu.slaif.si/trainings were actually
captured and viewed on 2026-10-05. Layout iterations corrected visible clipping,
contrast, cramped columns and navigation semantics; passing page-width checks
alone were insufficient. Stable semantic assertions and manual visual review
are used rather than pixel-perfect CI snapshots.

## Supported contract and residual limits

- Canonical service boundary: operator-owned HTTPS Caddy (qualified v2.11.6)
  to Docker-published loopback application, non-root/private Gunicorn and
  private PostgreSQL17. No public proxy Compose profile is needed.
- Trust the actual proxy socket peer, usually the Docker bridge gateway for
  a host proxy dialing the published port; separately trust the in-container
  loopback probe. A direct container proxy presents its own IP and requires
  equivalent qualification. Never infer trust from the public client header.
- Production secure session/CSRF cookies are enforced; SSL redirect defaults
  on and must stay on for the Internet-facing contract. Its explicit off switch
  is used by the separate HTTP-only local rehearsal, not a supported Internet
  configuration. HSTS is deliberate opt-in after real HTTPS/domain validation.
- Shared HMAC-derived PostgreSQL windows bound login/admin/API attempts across
  processes; they do not replace protection against distributed/volumetric
  attacks. A trusted operator-host process can reach the loopback listener and
  present forwarding headers; host security remains inside the trust boundary.
- Accounts are administrator-created with broad authenticated reservation rights
  under policy rules; project/membership and per-token asset restrictions,
  institutional OIDC/reset/email, notifications and execution integration are
  not implemented. Site groups govern administration model permissions.
- The database role is privileged/shared; ordinary ORM/admin protections do not
  stop privileged database tampering. Off-host backup scheduling, restore drills,
  monitoring, incident response and retention need operator ownership. No
  application CSP is emitted; an operator policy needs separate asset/UI testing.

These limits belong in the human deployment judgment. Qualification may support
presenting one exact immutable revision to that gate; it authorizes none of the
real exposure, identity, secret, private-data or release actions.
