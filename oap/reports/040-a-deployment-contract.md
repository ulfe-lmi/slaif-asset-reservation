<!-- OAP-META
{
  "kind": "report",
  "id": "040-a",
  "order_path": "oap/orders/040-a-deployment-contract.md",
  "order_sha256": "477b5dffa9176ec42d8a427dd019433d1c89504bade483ff92d43db2f0b4896f",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 79,
  "pr_number": 80,
  "branch": "codex/79-oap-040-a-deployment-contract",
  "implementation_head": "ce9f0e5bb09527711fc3a29c0a4f5c18e7f94aa5",
  "base_sha": "fb135dbc4a91a6fc983f49a6785d75c4277029c2",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "ce9f0e5bb09527711fc3a29c0a4f5c18e7f94aa5",
    "runs": [
      {
        "run_id": 37362808011,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "test": "success",
          "security": "success",
          "container": "success"
        }
      },
      {
        "run_id": 37362808138,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      }
    ]
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# Operator contract and integrated qualification

Implementation head SHA: ce9f0e5bb09527711fc3a29c0a4f5c18e7f94aa5
Report publication commit: SELF

Result: COMPLETE for this bounded documentation/qualification objective.
ROOT executed directly under the human instruction to stop the coding clients.
This is strategic evidence review, not independent ICA, milestone closure,
release approval or permission for real Internet exposure.

## Result

README remains a product landing page with local evaluation and full installation
entry points, authenticated HTTPS topology, capabilities, default policy,
shared abuse budgets, operator branding and concise current limits. QUICKSTART
remains local Docker evaluation. INSTALL is the operator contract; security,
deployment, human workflows, task index and current runbooks agree with source.
Immutable engineering/audit history is preserved.

The supported contract keeps PostgreSQL private and the application published
only on host loopback behind an operator-owned HTTPS proxy. INSTALL now creates
the Compose network before discovering its actual proxy peer. For a host proxy
that peer is usually the bridge gateway; a direct container proxy presents its
own address. The in-container probe is trusted separately. Commands, variable
names, examples, cookies, forwarding, health, policy initialization, backup,
rollback, persistent-volume warnings and branding were checked against source.
The purge command uses the actual --batch-size option. Existing installation
secrets must be reused deliberately; replacing a password file does not change
an initialized PostgreSQL role's password.

Source limits are stated precisely: production SSL redirect defaults on but its
explicit off switch exists for the isolated HTTP rehearsal; Internet operation
requires it on. Secure cookies are enforced; HSTS is an operator opt-in. There is
no application CSP. Broad authenticated human resource access, shared privileged
DB role, missing institutional identity/reset/email and operator off-host backups,
monitoring/retention/incident response remain visible. An inventory readiness
check is not an Internet security or operating-capacity certification.

## Actual evidence

| Check | Result |
| --- | --- |
| Real runtime/shared abuse/default policy focused suite | `pytest tests/test_gunicorn_responsiveness.py tests/test_abuse_controls.py tests/test_abuse_http.py tests/test_default_policy.py --no-cov -q`: 40 passed, 84.05s. Old synchronous sensitivity/six held clients, multiple-process PostgreSQL limits and fresh/repeated/configured upgrades. |
| Real HTTPS production-shaped qualification | Three selected tests in tests/test_https_boundary.py: 3 passed, 184.56s, no skip. Pinned Caddy v2.11.6, actual TLS/proxy/private PostgreSQL/image, password-output negative and exact owned cleanup. |
| Supported local Docker evaluation | Canonical compose.yaml built/started with unique image/ownership and kernel-assigned loopback ports because foreign PostgreSQL occupied5432. Migrations, initializer twice, sanitized import dry/apply, operational check, genuine interactive createsuperuser, health/live+ready and browser landing/Login/Dashboard/Management passed. No credentials/transcripts retained. |
| Policy and persistence | Actual DB contains exactly one active global default, horizon7 days and maximum2880 minutes. Stop/start retains the owned persistent volume. Teardown removes only nonce/ID/creation-receipted owned objects; no project-wide down/prune or foreign cleanup. |
| Documentation | 122 changed local Markdown links/fragments resolve, zero errors. First100 README lines reviewed as a new user; normal README/QUICKSTART/INSTALL ledger search has no stale round/history narrative. Docker network Go-template discovery commands execute on a verified owned container. |
| Final full suite | CI37362808011 testjob112016001420 at literal implementation head: **964 passed, 1 warning, 543.37s**. Includes real PostgreSQL concurrency/rollback, browser auth/CSRF/privacy/forms/default+custom design, Gunicorn, settings/HTTPS/abuse negatives, policy, backup/restore and branding/same-image qualification. |
| Final five checks | CI37362808011 quality/test/security/container SUCCESS and OAP37362808138 oap-harness SUCCESS. Security runs pip-audit; container renders canonical/production Compose, builds non-root image and verifies packaged static/bootstrap files. |

All local product operations used owned disposable sources, explicit settings/DB
URLs, synthetic data, cleared role environment and exact resource receipts.
Foreign PostgreSQL16 and other Docker resources were preserved. No valuable env,
production/private data, host inventory, DNS, real TLS certificate issuance,
firewall, secret rotation or public deployment was touched.

Initial head93f7a355dcbc440059d92cd701dc0f9f3f8748d9 was superseded by one
consolidated editorial correction commit. Only the final literal head above is
acceptance evidence. Its first two CI attempts lost hosted-runner acquisition:
quality/test/container were cancelled with no runner or test steps. GitHub's
Actions incident3q1yb5m7ltvb confirmed the external outage. The existing recovery
helper waited outside the model and retried the missing checks at the same head
after official recovery. Cancelled attempts are not product passes or failures.

## Freshness and remaining gate

The base-to-implementation diff changes twelve documentation paths plus the
ordered active pointer/order. Application/runtime/configuration/schema/migration/
dependency/inventory bytes are identical to the base. Full ARCHITECTURE.md,
PLAN.md, projection and law are unchanged. A-15 already selects all eight human
requirements; the full architecture SHA-256 remains
f8a8df265d4dd452969d4bee874045c8f8a8261f9c87c96ba4c049a7dddf320d.
No requirement was removed, weakened or self-certified; no recomposition needed.

The qualification record under docs/audit is strategic, not ICA. Its initial
request/matrix derives all47 rows from the canonical index and starts each
UNPROVEN. The non-executable draft alone does not admit an audit. Strategy must
bind the actual immutable post-merge revision, human target and full architecture
first in a fresh independent read-only context, then audit every applicable row.
The older internal-pilot ICA is historical only. Findings require bounded repairs
and full architecture-to-current-main reassessment, not merely queue closure.

The previously merged design's actual four-width/default+custom screenshot
matrix, manifest identity, source relationship, visual iterations and inspection
limits are indexed in the qualification record and immutable039-a report. This
round changes no UI bytes and does not claim a new visual implementation.

Strongest reason against merge: revised deployment prose could imply unsupported
controls or real exposure permission. Actual source/rehearsals, preserved residual
limits, exact-head checks and the explicitly pending independent/human gates bound
that risk. No release or real deployment is authorized.

Report-head CI is not yet observed at authoring and remains mandatory before merge.
No same-round mutation follows report publication.

DHA operation: NONE.
