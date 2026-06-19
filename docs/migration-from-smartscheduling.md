# Migration from SmartScheduling

**Status:** migration design; no private export has been approved or included

## 1. Objective

Migrate useful reservation-system truth without preserving the wrong salon/appointment domain or copying unnecessary personal data.

## 2. Legacy-to-new mapping

| SmartScheduling | New system | Migration rule |
|---|---|---|
| Business/account | Deployment/organization context | configuration, not a domain row initially |
| Staff record representing GPU | `Asset` | import sanitized identity and legacy provenance |
| Human staff/admin | User/role | create through approved identity process, not asset import |
| Service duration | Policy/time range | do not import as a service entity |
| Appointment | Reservation | import only approved history/upcoming records |
| Client | User or legacy actor reference | minimize; do not bulk-import automatically |
| Work hours | Availability rule | translate only after administrator validation |
| Calendar block | Blackout or reservation | classify explicitly |
| Staff iCalendar secret | Nothing | never import or store |

## 3. Sanitized inventory source

`data/bootstrap/assets.yaml` contains the public resource names and hardware descriptions observed on 2026-06-17, plus one disabled GPU noted in administrator inventory. It intentionally excludes:

- administrator/person records;
- emails and phone numbers;
- client records;
- appointment details;
- cookies, anti-forgery tokens, Turnstile tokens;
- iCalendar secret URLs;
- physical host credentials;
- inferred hostnames, CUDA indices, and GPU UUIDs.

Legacy resource IDs remain provenance only. Several suffixes do not match displayed GPU numbers; never infer identity from them.

## 4. Duration services

The old account contains fixed durations and three distinct 12-hour service IDs. The new system accepts an explicit start/end or duration constrained by policy.

Migration consequences:

- do not create ten `Service` rows;
- do not preserve duplicate 12-hour products;
- use legacy service duration to reconstruct appointment end time if the export lacks it;
- preserve original service IDs only in migration provenance where needed for audit;
- decide global duration and horizon policy independently.

## 5. Users and personal data

The legacy public flow requires name and phone; email is optional. The new application should use authenticated institutional identity and normally needs name/email, not phone.

Default migration position:

- create current users from an approved account/identity roster;
- do not bulk-import all legacy clients;
- do not use phone number as identity;
- import historical reservation ownership only when a deterministic approved mapping exists;
- otherwise preserve a non-identifying legacy actor label or aggregate history according to policy;
- document retention and user notice before importing personal history.

## 6. Reservations

Potential source paths:

1. supported administrator export;
2. approved backup export;
3. authenticated admin API capture only if export is insufficient and the contract is documented;
4. public HTML scraping is a last resort and unsuitable for private history.

Never automate around Turnstile or copy authenticated browser cookies into repository tooling.

Reservation import fields:

- legacy appointment ID;
- mapped asset ID;
- start/end in source timezone with normalized UTC;
- source status;
- approved owner mapping;
- safe purpose/description only if retention permits;
- original import timestamp and batch ID.

## 7. Migration phases

### Phase 0: policy approval

Decide:

- upcoming only versus historical import;
- personal fields allowed;
- retention and visibility;
- authoritative cutover time;
- who approves reconciliations.

### Phase 1: inventory verification

For every imported machine/asset, verify:

- display name and slug;
- active/reservable state;
- actual hostname;
- device UUID/local locator where execution integration is planned;
- hardware/capability values;
- responsible manager;
- default policy;
- legacy resource ID.

Do not make physical identifiers public unless needed.

### Phase 2: export inspection

Use a separate approved environment. Record:

- format and encoding;
- counts;
- field meanings;
- timezone;
- duplicate IDs;
- cancelled/deleted semantics;
- missing end time or service dependence;
- personal data present.

Store real exports outside Git with access controls.

### Phase 3: importer

Management command requirements:

```text
import_smartscheduling --input <path> --dry-run
import_smartscheduling --input <path> --apply --batch-id <id>
```

- dry-run by default or explicit dry-run available;
- schema validation;
- deterministic ID mapping;
- idempotent re-run;
- transaction boundaries;
- rejected-row report without secret leakage;
- reconciliation totals;
- no silent truncation;
- synthetic fixtures in Git, real exports outside Git.

### Phase 4: rehearsal

- restore a production-like empty database;
- import sanitized/approved export;
- compare machine, asset, reservation, user, status, and time totals;
- manually sample Neumann and several mismatched legacy IDs;
- verify timezone/day-boundary cases;
- test rollback by discarding/rebuilding rehearsal DB.

### Phase 5: cutover

Recommended:

1. announce freeze window;
2. take final export/backup;
3. disable or make legacy booking read-only;
4. run final import;
5. reconcile;
6. enable new writes;
7. monitor and retain legacy read-only for an agreed period;
8. archive final migration evidence.

Avoid two authoritative writers. If a parallel-read period is needed, only one system accepts mutations.

## 8. Reconciliation report

Every import batch reports:

- source file hash;
- importer version/commit;
- batch ID and timestamp;
- resources read/imported/skipped/unmapped;
- reservations read/imported/skipped/unmapped;
- user mappings resolved/unresolved;
- duplicate/conflict counts;
- earliest/latest timestamps;
- timezone assumptions;
- validation errors;
- no raw personal rows in the report.

## 9. Conflict handling

Imported upcoming reservations may overlap due to legacy double booking or mapping mistakes. Do not silently choose one.

- report each conflict;
- keep the database invariant enabled where feasible;
- require administrator resolution;
- allow a controlled migration staging table if needed;
- record the final decision in migration evidence.

## 10. Rollback

Before cutover:

- retain final legacy export/backup;
- back up the new database;
- keep import batch identity;
- support deletion/rollback of one unaccepted import batch only through an explicit administrator command tested in rehearsal;
- after users create new reservations, rollback becomes an incident/cutover decision, not a simple importer undo.

## 11. Records deliberately not migrated by default

- SmartScheduling service products;
- duplicate 12-hour service definitions;
- salon-oriented business settings;
- public-page photos unless explicitly wanted;
- reminder templates;
- staff login credentials;
- iCalendar tokens;
- anti-forgery/cookie/browser state;
- phone numbers;
- arbitrary client notes/files;
- disabled human staff as assets;
- `ChatGPT Pro` until its product semantics are defined.
