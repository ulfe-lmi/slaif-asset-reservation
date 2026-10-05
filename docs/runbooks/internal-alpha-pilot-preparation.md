# Runbook: Internal-Alpha Pilot Preparation Pack

This pack helps a human operator prepare the first controlled internal lab pilot. It does not
deploy the system, approve production secrets, create real accounts, import private
SmartScheduling data, or authorize DNS, TLS, certificates, production data, or cutover.

Use this document after the deployment rehearsal in
`docs/runbooks/internal-alpha-pilot-readiness.md` is understood and before any real pilot host is
selected.

## Pilot Assumptions

- The pilot uses a limited set of lab assets selected by a named human operator.
- Only a limited set of active staff operators can use `/manage/`.
- Only a limited set of administrator-created pilot users can use the member UI.
- Account creation is manual through the existing Django/admin flow; OIDC, password reset, and
  email notification workflows are not implemented.
- Project, membership, and resource-restriction authorization is not implemented. Pilot scoping
  must be handled by choosing pilot assets carefully, marking non-pilot assets inactive or
  non-reservable as appropriate, and configuring policies conservatively.
- API-token users may exercise bearer-token reservation operations only with tokens they create
  through the member UI.
- The reservation system grants entitlement only. It does not start jobs, enforce machine access,
  or integrate with an execution gateway.
- No real SmartScheduling import or cutover is part of this pilot-preparation work order.

## Pilot Success Criteria

- Main CI is green on the intended pilot commit.
- `deploy/rehearse_internal_alpha_deployment.sh` passes on disposable local resources.
- `operational_check` passes in the rehearsed environment.
- `pilot_readiness_check --strict` passes after the pilot database has staff users, selected
  assets, ordinary pilot users, and active reservation policies configured.
- Fresh migrations apply to disposable PostgreSQL.
- Backup and restore wrapper behavior is understood, and the isolated restore drill is
  codified as the `restore_drill` management command (see `docs/runbooks/backup-and-restore.md`)
  before any real pilot data is accepted.
- Staff can configure reservation policies, create/deactivate a test blackout, inspect
  cross-user reservations, and export bounded audit records.
- Pilot users can browse selected active assets, inspect privacy-safe availability, create
  reservations, cancel future reservations, and release active reservations.
- Agent users can create an API token and use API v1 reservation operations in a fake/local test
  path without exposing token plaintext.
- Audit evidence exists for successful reservation, token, policy, blackout, and staff lifecycle
  mutations.
- No unresolved blocker, high, or medium verification finding is accepted for the pilot.

## Operator Checklist

Use this checklist as a planning aid. It is not a substitute for a deployment approval.

### Asset Selection

- [ ] Assign one human operator to own the pilot asset list.
- [ ] Choose a small set of machines and child assets for the pilot.
- [ ] Verify physical labels, public display names, and asset slugs against the lab inventory.
- [ ] Confirm that sanitized bootstrap assets are loaded or deliberately excluded.
- [ ] Mark non-pilot or unverified assets inactive or non-reservable before inviting users.
- [ ] Confirm each pilot asset has the intended booking mode and reservable state.

### Staff And Users

- [ ] Create the first staff/superuser through the approved local/admin process.
- [ ] Create only the pilot staff operators needed for the run.
- [ ] Create pilot user accounts manually; do not enable self-registration.
- [ ] Confirm service accounts cannot use the human or management UI.
- [ ] Confirm staff using member routes still sees only their own member reservations.

### Policies And Blackouts

- [ ] Configure an initial reservation policy for the pilot scope through `/manage/policies/`.
- [ ] Verify effective policy resolution for each pilot asset.
- [ ] Avoid guessed institution-wide policy defaults.
- [ ] Create a test blackout for a non-critical pilot interval.
- [ ] Confirm blackout availability is visible as unavailable without exposing the private reason
  to ordinary users or API callers.
- [ ] Deactivate the test blackout and confirm availability recovers.

### Human Reservation Flow

- [ ] Log in as a pilot user.
- [ ] Browse selected active assets.
- [ ] Inspect availability in the user's selected timezone.
- [ ] Create a test reservation.
- [ ] Confirm the reservation appears in the user's list and detail pages.
- [ ] Cancel a future reservation.
- [ ] Release an active reservation in a safe test interval.

### API Token And Agent Flow

- [ ] Create a short-lived test API token through `/tokens/new/`.
- [ ] Store token plaintext in an approved local secret store for the test only.
- [ ] Confirm the token cannot be recovered after navigating away.
- [ ] Call `/api/v1/me/` with a fake/local token only.
- [ ] Exercise API reservation create/list/detail/cancel/release against a disposable test
  reservation using `Idempotency-Key`.
- [ ] Revoke the test token when finished.

### Audit, Backup, And Operational Checks

- [ ] Export a bounded audit CSV with filters.
- [ ] Confirm exported audit rows contain no token plaintext, Authorization headers, raw request
  bodies, physical locators, or private notes.
- [ ] Run `operational_check`.
- [ ] Run `pilot_readiness_check` and resolve required failures before using `--strict` as the
  final database readiness gate.
- [ ] Run backup wrapper dry-run/refusal checks.
- [ ] Plan an isolated restore drill before accepting real pilot data.
- [ ] Run `deploy/rehearse_internal_alpha_deployment.sh`.

## Go Conditions

- All required pass gates in `docs/runbooks/internal-alpha-pilot-readiness.md` pass.
- Pilot asset ownership, policy ownership, and operator coverage are assigned.
- Pilot participants understand that the system is internal alpha, not production-ready.
- The rollback/restore posture is understood by the operator responsible for the pilot.
- There are no unresolved blocker, high, or medium findings.

## No-Go Conditions

- Real production secrets are unavailable, unapproved, printed in logs, or committed.
- Rehearsal, migration, readiness, backup/restore, or operational checks fail.
- Asset ownership or policy responsibility is unclear.
- Pilot users require OIDC, password reset, email notifications, or project/resource restrictions
  before they can safely participate.
- A real SmartScheduling import or execution-gateway enforcement is required to make the pilot
  meaningful.
- No human operator is assigned for incident handling.

## Communication Templates

Use placeholders only. Do not paste real emails, private hostnames, credentials, tokens, or
deployment URLs into repository files.

### Pilot Invitation

```text
Subject: SLAIF internal alpha reservation pilot invitation

Hello <pilot participant>,

You are invited to a limited internal alpha pilot of the SLAIF Asset Reservation system for
<pilot asset group>. The pilot starts on <date> and is intended to test reservation creation,
cancellation, release, and staff-managed availability controls.

This is not a production service. Accounts are created manually, password reset and email
notifications are not enabled, and the system does not enforce machine login or job execution.

Pilot URL: <internal alpha URL>
Support contact: <operator contact>
Pilot feedback channel: <feedback channel>

Please report reservation conflicts, access problems, confusing availability, or suspected
security/privacy issues immediately.
```

### Staff Operator Instructions

```text
Subject: SLAIF internal alpha staff operator checklist

Before inviting users, confirm:

- main CI is green for commit <commit>;
- deployment rehearsal passed;
- operational_check passed;
- pilot assets and policies are configured;
- a test blackout has been created and deactivated;
- audit export has been tested with filters;
- backup/restore drill posture is understood.

Use `/manage/` only for pilot operations. Do not create production secrets, process private
SmartScheduling exports, or manually edit reservation/policy/blackout rows outside audited
services.

Escalation contact: <operator contact>
```

### API Token Usage Note

```text
Subject: SLAIF internal alpha API-token usage

Create your API token at <internal alpha URL>/tokens/new/. The token is shown once and cannot be
recovered. Store it only in an approved local secret store.

Use tokens only for the pilot endpoints and scopes approved for <pilot asset group>. Include an
Idempotency-Key on reservation create/cancel/release requests. Revoke the token when the pilot test
is complete or immediately if it may have been exposed.

Do not paste bearer tokens into tickets, chat, logs, screenshots, browser traces, or repository
files.
```

### Incident Or Escalation Note

```text
Subject: SLAIF internal alpha pilot incident

Incident time: <timestamp and timezone>
Reporter: <reporter>
Affected asset/reservation: <safe identifier only>
Observed behavior: <short description>
Immediate user impact: <impact>
Actions already taken: <actions>
Logs or audit references: <safe references only>
Next operator: <owner>

Do not include passwords, session cookies, bearer tokens, CSRF values, private SmartScheduling
exports, phone numbers, or private notes in this incident note.
```

## Limitations To Repeat To Pilot Participants

- No production deployment has been performed by this work order.
- No OIDC, password reset, email notification, or reminder workflow exists.
- No projects, memberships, delegated resource-manager roles, or resource restrictions exist.
- No execution gateway or automatic machine enforcement exists.
- No production monitoring stack or backup scheduler exists.
- No real SmartScheduling import or cutover has been performed.
- Login and API abuse budgets coordinate through PostgreSQL across workers;
  configure and monitor them under the current [installation contract](../../INSTALL.md#shared-authentication-and-api-budgets).
- The pilot remains internal alpha and must not be described as production-ready.
