<!-- OAP-META
{
  "id": "035-a",
  "round": "a",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "0a81b931a11e6598540c2a6071b1e99ee895499e",
  "issue_number": 69,
  "branch": "codex/69-oap-035-a-default-policy",
  "pr_mode": "CREATE_OR_RESUME",
  "allowed_paths": [
    "src/slaif_reservation/reservations/initialization.py",
    "src/slaif_reservation/reservations/management/__init__.py",
    "src/slaif_reservation/reservations/management/commands/__init__.py",
    "src/slaif_reservation/reservations/management/commands/initialize_default_policy.py",
    "src/slaif_reservation/config/operational.py (initializer registration only)",
    "tests/test_default_policy.py",
    "tests/test_operational_hardening.py (command registration only if necessary)",
    "QUICKSTART.md",
    "INSTALL.md",
    "docs/deployment.md (policy initialization only)",
    "docs/human-ui.md (default values only)",
    "TESTING.md (new evidence commands only)",
    "deploy/rehearse_internal_alpha_deployment.sh (initializer after migrations only)",
    "deploy/rehearse_https_boundary.sh (policy fixture adaptation only if necessary)",
    ".github/workflows/ci.yml (initializer after migrate only)",
    "ARCHITECTURE.md (exact A-15 amendment below only)",
    "ARCHITECTURE-for-agents.md (exact SAR-041 clause below and actual full-source digest only)",
    "docs/governance/DEFAULT-POLICY-PROJECTION-REVIEW.md",
    "oap/active",
    "oap/orders/035-a-default-policy.md",
    "oap/reports/035-a-default-policy.md"
  ],
  "forbidden_resources": [
    "application model/schema/dependency/inventory/old migration changes",
    "generic system-staff bypass, HTTP or startup initialization, other UI/theme/API/network features",
    "OAP machinery/immutable history changes",
    "real deployment/exposure/secrets/DNS/TLS/firewall/private production/lab/legacy data",
    "foreign resources/reset/clean/stash/forcepush/auth copying"
  ],
  "requirements": [
    "SAR-008",
    "SAR-009",
    "SAR-025",
    "SAR-031",
    "SAR-037",
    "SAR-041"
  ],
  "decision_class": "D0",
  "target_gate": "M-INTERNET-UX-PILOT development only; real exposure remains human D2",
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "06dd0f50e778b9843e2a709caa0ae1f0c97f48baee726f4e3a1397cc6a198d8c",
    "PLAN.md": "b19219e2d727af5a9554e011ba45a786f1bb61f25c001011fc18006cae665d08"
  },
  "previous_round": null
}
-->

# 035-a — Fresh-install default reservation policy

H: human requirement2 and latest instruction to resume CODING for this and all
subsequent implementation tasks. A: A-15/SAR-041, preserved008/009/025/031/037.
E: PR68 merged0a81b931a11e6598540c2a6071b1e99ee895499e; final implementation
5205296eaa620e7c164d2075c2d25f3c1b51280d and reportcfe4e2cfc99596c737b869c8e65851ef3c1e4464 all5 CI checks SUCCESS; final owned local787 passed716.37s.
I: fresh independent all47 ICA remains required after selected implementation.
C: D0/DHA_NONE. One purpose: safe supported fresh default-policy initialization.

## Acceptance
1. Trusted initialize_default_policy command, mandatory immediately after
   migrate in supported QUICKSTART/INSTALL/rehearsal/CI initialization. No HTTP,
   AppConfig/worker startup side effect or data migration. Dedicated narrow
   initializer; do not add a general allow_system staff bypass to create_policy.
2. Only when NO policy rows exist, atomically create active global(assetNULL)
   name default: min1/max2880minutes, START horizon7days, lead/cutoff0,
   purposeFalse, upcoming50 and proposed-interval overlap8 per principal across
   assets and tokens. No operating-hour window. Preserve current overlap-count
   semantics; document that it counts intersecting records, not a simultaneous
   sweep. These are chosen explicit defaults, not permission to change policy
   evaluation. Staff can later manage them through existing audited services.
3. Any existing policy config(active/inactive/global/specific) => no writes,
   audit or reactivation. Repeated/concurrent initialization => exactly one
   policy and audit. Serialize absence+insert against ordinary policy inserts
   with appropriate PostgreSQL locking; existing active-global uniqueness stays.
   Couple existing policy.created audit atomically, actorNULL/sourceadmin and
   safe metadata/correlation for trusted CLI; no fabricated account. Audit
   failure rolls back. Empty upgrades may explicitly initialize; migrations
   alone do not silently broaden configured or empty installations.
4. Real PG tests: fresh/repeat/concurrent/race with configured insertion,
   active/inactive global and specific upgrade preservation, audit rollback,
   exact defaults, real accepted booking and existing duration/horizon/principal
   limits. Preserve domain/CSRF/privacy/audit/exclusion/staff-only protections.
   Exercise fresh owned Docker migration+initializer+sanitized assets+synthetic
   administrator+booking and repetition. Shipped source/commands, isolated
   test-only port adaptations if needed; no real external host.
5. Operator docs state actual initialization/defaults/upgrade no-op, replace
   manual fresh-policy prerequisite, retain policy priority/ambiguity fail-closed.
   No work ledger or Internet/production qualification claim.
6. Apply only exact canonical A-15 replacement below (old paragraph starts
   "A supported fresh initialization path" and ends "real booking."). Apply
   exact compact SAR-041 clause below, then actual full-source SHA256 after
   semantic comparison. All001–038 bodies/other clauses/PLAN unchanged. Add
   concise successor semantic mapping/context review; do not rewrite historical
   032 coverage. Projection<=20000bytes/mandatory context<=50000; no truncation,
   superficial hash update or extra mandatory full source reads.
7. Focused tests while editing; full standard suite at final implementation
   head, five exact-head quality/test/security/container/oap-harness and normal
   report-head CI. Short immutable report literal implementation head/SELF,
   actual commands/counts/failures/limits; open PR for issue69 with Closes #69.
   Coding never merges. Stay inside acceptance; optional refinements separate.

## Owned resources and execution efficiency
Use owned disposable source copies/PG17, NEVER valuable checkout .env/default
foreign5432. Existing owned DB receipt:
/home/ubuntu/codex-supervision/slaif-asset-reservation/workorders/033b-owned-test-db.json
contains exact ID/nonce/environment_file; validate ID/label before using it.
Read private env into a Python child-env dictionary, never source/eval/print
credentials. /usr/lib/postgresql/17/bin tools, Chromium, Caddy2.11.6 and locked
repo .venv are installed. Clone tracked source into owned temporary checkout;
copy only named in-scope new/changed files for focused work, never ignored .env
or auth homes. Existing operational tests/rehearsals have destructive fixtures:
full tests only owned checkout. For Docker use unique project/nonce, verified
owned IDs/volume identities and private loopback ports; never blanket down -v
or prune. compose.yaml fixed5432 collides with foreign PG16: safe test-only
ports override/adaptation required; do not touch foreign service or source
Compose semantics. Capture private test output and emit summaries, never
credential-bearing failures, browser traces or raw client data.

Wait for coding/CI outside the model with existing helpers. Concrete edit or
small diagnostic within15min of loaded required read set. Do not reread full
strategy books/old rounds, restart a published round, repeat unchanged full
suites or broaden scope. Before implementation report, collect and fix safe
in-scope failures; after frozen report, no mutation in this round.

## Exact architecture amendment
Supported fresh initialization runs `initialize_default_policy` immediately after migrations.
It atomically creates an active global fallback named `default` only when no policy rows exist:
asset NULL; minimum duration 1 minute; maximum 2880 minutes (48 hours / 2 days); booking horizon
7 days by reservation START; minimum lead 0; cancellation cutoff 0; purpose optional; no
restricted operating-hour window; upcoming limit 50 and proposed-interval overlap limit 8 per
principal across assets and that principal's tokens. The overlap limit counts existing blocking
records intersecting the proposed interval, not a maximum simultaneous-occupancy sweep.
These required caps remain visible and documented. The trusted initializer couples policy and
policy-created audit atomically with no fabricated account. Repetition/races cannot duplicate
creation. Any prior policy configuration, including inactive or asset-specific rows, prevents
initialization changes or audit events: no silent overwrite, reactivation or upgrade entitlement.
An empty upgraded installation may deliberately run the same explicit initializer; migrations
and application startup never invoke it implicitly. Fresh assets are immediately reservable
subject to the initialized policy. Staff retain the existing audited policy-management route.
Manual policy creation is not a prerequisite on the supported fresh path. Tests prove fresh,
repeat, configured-upgrade, concurrency, audit rollback and real accepted booking behavior.

## Exact executor clause
**SAR-041 / Default fresh-install policy:** Run initialize_default_policy after migrate: atomic audited active global `default` (asset NULL; duration1..2880min; START horizon7d; no hours; lead/cutoff0; purpose optional; upcoming50/overlap8 per principal across assets/tokens; overlap counts intersecting blocking records). Fresh booking works; repeats/races unique; any existing policy including inactive/specific prevents writes/reactivation/audit. Empty-upgrade init explicit; no migration/startup grant or manual fresh-policy step. Caps visible/documented; staff mutations unchanged; audit rollback tested.

## Strongest reason against the change
A default can undo intentional disabling or broaden upgrades. Prevent this by
preserving ANY prior policy configuration, requiring trusted explicit operator
initialization and proving serialized absence/audit rollback/upgrade negatives.
No actual deployment, D2 action, new feature or authority-model change.

## Deferred human adjudication
- Decision: NONE
