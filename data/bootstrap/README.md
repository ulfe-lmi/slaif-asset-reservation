# Demo inventory and bootstrap format

`assets.yaml` contains 14 entirely fictitious assets for local evaluation:
Atlas (a workstation grouping its GPU and CPU pool), Aurora microscopy,
Forge printing, Cutline laser cutting, Vector machining, ClimateBox testing,
ScopeBench electronics, RoboCell robotics, ThermoCam field equipment,
SimWorks licence entitlement, Precision support and inactive Calibra calibration.
There are no real machines, people, accounts, hostnames or migration identifiers.

Reservations grant exclusive time-based entitlements. They do not operate equipment,
allocate CPU cores, activate licences or arrange staffing. Atlas itself is not
bookable; its GPU and entire CPU pool can be reserved independently.

## Format

The sole current format is `schema_version: 2`, validated by `assets.schema.json`:

```yaml
schema_version: 2
defaults:
  timezone: UTC
assets:
- slug: example-workstation
  name: Example workstation
  kind: machine
  active: true
  reservable: false
- slug: example-gpu
  name: Example GPU
  kind: gpu
  parent: example-workstation
  description: Exclusive use of one example GPU.
  location: Example lab
  active: true
  reservable: true
```

Each asset requires `slug`, `name`, `kind`, `active` and `reservable`.
Kinds are `machine`, `gpu`, `cpu_pool`, `service` and `other`. Optional fields:
`parent` (slug or null), `description`, `location`, `timezone` (overrides the
required default) and `verification_required` (defaults to true).
Parent records may appear anywhere in the file. Parents must be root machines;
unknown, self-referencing, cyclic and deeper/non-machine hierarchies are rejected.
Inactive assets cannot be reservable. Booking remains exclusive per asset.

The importer does not populate physical locators, capabilities or legacy provenance.
A demo label is not evidence of verified physical equipment. Operator inventories
must be prepared and verified independently; migration provenance belongs to the
separate migration tooling or deliberate administration.

## Import

```bash
python manage.py import_bootstrap_assets --input data/bootstrap/assets.yaml
python manage.py import_bootstrap_assets --input data/bootstrap/assets.yaml --apply
```

Without `--apply`, validation and planning write nothing. Apply validates before
writing, runs atomically, refuses conflicting existing records and is idempotent
for identical records. For a custom YAML file, place a copy of `assets.schema.json`
beside it. Docker operators must make both files available in the container.

**The demo is optional and intended for fresh evaluation databases. Never import
it as an upgrade step or into an existing operational inventory.** Existing
records are not changed by replacing the bundled file. The former site-specific
version-1 inventory is preserved in Git history; version 1 is no longer accepted.
