# Runbook: Backup and Restore

SLAIF uses PostgreSQL-native logical backup tools for the initial internal-alpha shape.

## Backup

Dry-run validation:

```bash
python manage.py backup_database --output /backups/slaif-$(date +%Y%m%d).dump
```

Create a backup:

```bash
python manage.py backup_database --output /backups/slaif-$(date +%Y%m%d).dump --apply
```

The command requires `DATABASE_URL`, refuses missing output directories, and does not print the
database password. Operators own retention, encryption, off-host copy, and failure alerts.

## Restore Drill

Never restore over production without a separate human-approved incident plan.

The isolated restore drill is codified as the `restore_drill` management command. It dumps the
source database with `pg_dump --format=custom`, restores the artifact into a target database that
the drill creates itself on the target server, verifies the round trip, and drops the drill-created
target database again. It runs entirely on loopback/disposable infrastructure and never restores
over pre-existing data: the target database must not exist yet.

Dry-run validation (zero side effects; all validations, no artifact, no target database):

```bash
python manage.py restore_drill \
  --source-url "postgres://USER:PASSWORD@HOST:5432/slaif_reservation" \
  --target-url "postgres://USER:PASSWORD@HOST:5432/slaif_restore_drill"
```

Execute the drill (`--source-url` defaults to `DATABASE_URL`; `--workdir` defaults to the
git-ignored `<repo>/build/restore-drill`):

```bash
RESTORE_DRILL_TOKEN_PROBE='sar_...' python manage.py restore_drill \
  --source-url "postgres://USER:PASSWORD@HOST:5432/slaif_reservation" \
  --target-url "postgres://USER:PASSWORD@HOST:5432/slaif_restore_drill" \
  --workdir /tmp/slaif-restore-drill --apply
```

`RESTORE_DRILL_TOKEN_PROBE` is a bearer token plaintext (shown once at creation time). It is read
from the environment deliberately so it never appears in argv or output; when unset the drill
reports `token_round_trip=skipped` and completes the other verifications.

Refusals (both dry-run and `--apply`): unparseable or non-PostgreSQL source/target URLs; a target
database equal to the source database on the same server; a target database that already exists on
the target server; missing `pg_dump`/`pg_restore` on PATH; an unwritable workdir; and a stale
`drill.dump` artifact left by a previous run.

The connecting user must have `CREATEDB` on the target server; a disposable local PostgreSQL 17
instance is sufficient. The source database must contain at least one confirmed reservation (the
drill overlaps it to prove the named GiST exclusion constraint `reservation_no_overlap_per_asset`
survives the restore and still blocks overlapping inserts) and at least one active, reservable,
exclusive asset with a resolvable policy (the point-in-time probe).

On success the command prints structured key=value evidence: per-table row counts (users, assets,
reservation policies, reservations, maintenance blackouts, audit events, API tokens, idempotency
records, and `django_migrations`) with `row_counts_equal=true` and `migrations_equal=true`,
`exclusion_constraint.present=true` and `exclusion_constraint.blocks_overlap=true`,
`token_round_trip=true` when the probe is set, `post_backup_probe.absent_on_target=true` (a
reservation created on the source after the backup must be absent from the target),
`source_unchanged=true` (the source gains exactly the drill's own probe reservation and its audit
event, and all pre-drill reservations remain), and `cleanup.target_dropped=true` plus
`cleanup.workdir_removed=true`. The probe reservation is left on the source (its id is printed);
cancel or release it through the normal paths after the drill. On failure the command prints the
failure truthfully, drops the drill-created target database when it created one, and retains the
artifact path in the output for operator inspection. Output never contains passwords or
credential-bearing URLs.

Manual fallback (wrapper commands only):

```bash
python manage.py backup_database --output /backups/slaif-YYYYMMDD.dump --apply
python manage.py restore_database --input /backups/slaif-YYYYMMDD.dump
python manage.py restore_database --input /backups/slaif-YYYYMMDD.dump --apply
python manage.py operational_check
```

After a manual restore, compare user, asset, reservation, token, idempotency, blackout, and audit
row counts against the source environment where appropriate.
