# SmartScheduling Migration Runbook

This runbook is for a future human-supervised rehearsal. It does not authorize scraping,
credential reuse, browser automation against SmartScheduling, or committing private exports.

## Privacy Rules

- Keep private exports outside Git, for example under an operator-controlled `legacy_exports/`
  directory that is ignored by this repository.
- Do not store cookies, browser local storage, screenshots, traces, service credentials, phone
  numbers, raw email exports, or private notes in the repository, CI, PR descriptions, logs, or
  issue comments.
- Use synthetic fixtures in CI and development unless a maintainer explicitly approves a private
  rehearsal on a disposable host.

## Synthetic Verification

Inspect a synthetic export:

```bash
uv run --env-file .env python manage.py inspect_smartscheduling_export \
  --input data/synthetic/smartscheduling_export.yaml \
  --source smartscheduling-synthetic \
  --timezone Europe/Ljubljana \
  --mapping tests/fixtures/smartscheduling_mapping.example.yaml
```

Plan a dry-run import and write a redacted report:

```bash
uv run --env-file .env python manage.py plan_smartscheduling_import \
  --input data/synthetic/smartscheduling_export.yaml \
  --source smartscheduling-synthetic \
  --timezone Europe/Ljubljana \
  --mapping /path/to/synthetic-or-private-mapping.yaml \
  --report-json /tmp/slaif-smartscheduling-plan.json
```

Apply only after reviewing the plan, taking a database backup, and reconciling unmapped records:

```bash
uv run --env-file .env python manage.py import_smartscheduling_export \
  --apply \
  --input /path/to/operator-controlled-export.yaml \
  --source smartscheduling-approved-rehearsal \
  --timezone Europe/Ljubljana \
  --mapping /path/to/operator-controlled-mapping.yaml \
  --report-json /tmp/slaif-smartscheduling-apply.json
```

## Reconciliation Checklist

- Map every legacy person to an existing SLAIF user UUID; do not auto-create production users.
- Map every legacy resource to an existing SLAIF asset by safe provenance, explicit UUID, or
  documented unambiguous slug fallback.
- Review unmapped assets/users, inactive/non-reservable assets, missing policies, blackout
  conflicts, and reservation conflicts before apply.
- Treat cancelled/no-show records as skipped unless a future ADR changes the status semantics.
- Treat `legacy_changed` as a stop-and-review condition; the importer does not overwrite imported
  reservations.

## Cutover and Rollback Posture

1. Take a PostgreSQL backup with the operational backup wrapper.
2. Run the dry-run planner against the exact export and mapping files intended for apply.
3. Review the redacted JSON report and command counts.
4. Apply against a disposable rehearsal database before any production attempt.
5. Verify imported reservations, audit events, and `LegacyImportRecord` idempotency evidence.
6. If the rehearsal is wrong, restore the database backup; the importer does not implement a
   partial rollback command.

No production cutover, restore drill against production, or real SmartScheduling export is performed
by Work Order 0009.
