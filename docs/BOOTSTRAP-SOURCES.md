# BOOTSTRAP-SOURCES — provenance and drift record (generation 1)

This file records where the conversion candidate came from, which bytes were
preserved, and the explicit source reconciliations. Integrity domains stay
separate: immutable input snapshots (this file + `oap/bootstrap-sources.lock.json`),
current canonical/projection identities (`oap/governance/MANIFEST.json`), installed
copy identities (same manifest), and dynamic state (`oap/orders`, `oap/reports`,
`oap/active`, `CRITICAL.md`) which are checked by history/content/authorization,
never by seed equality.

## Input package snapshots (docs/bootstrap/1/inputs/)

| Snapshot | SHA-256 | Note |
|---|---|---|
| `inputs/AGENTS.md` | `09b72445b5d0ce26cd12b531148151f1293f51d5abee555dde3fe01c6280cb8d` |  |
| `inputs/ARCHITECTURE.md` | `9e7c60e4ef6cee99d5baf20ee5ef6afcff38b10aa2eaa74a5a27084ff515a0c4` | newly authored canonical architecture candidate |
| `inputs/CRITICAL.md` | `f5c4d78ed599ac9a8ce44687925dab29f221d8b65a2350a4f858c9f32a92c672` | zero-entry register seed (installed only because no local register existed) |
| `inputs/INSTRUCTIONS.md` | `197bc6cdedcef13f3de9293d7dc8a328b77fc8723ec7ae76b23ed56f1e9f34ca` | materialization work specification |
| `inputs/PACKAGE-CHECKS.md` | `9f713bf85dd4cedc7f5d740ed126773a58220af3b1685944ca68cc267f0c7fda` | designer's input-package checks |
| `inputs/PLAN.md` | `d5677519a1546906eca644cb5be34a93f038a73fa20d6ba241cfdd0add6b9ef6` | newly synthesized product agreement candidate |
| `inputs/README.md` | `28b8bf41d940810067eacf3812e15b6a67a23fbeba1d60e874fb68b319f94666` | package README |
| `inputs/REPOSITORY-OBSERVATIONS.json` | `0a79f1660291b0bc31ebc3619aa4ac2c92f4c9840e107d376864d15595200370` | curated read-only source observations, 2026-09-07 |
| `inputs/SOURCE-MAP.md` | `5b2e5e435ddc7392629410d1321ab5e362cce0bec822589b2dd7c0bd1f5b00e7` | source relationships and reconciliations |
| `inputs/bootstrap-generator-prompt.md` | `09b72445b5d0ce26cd12b531148151f1293f51d5abee555dde3fe01c6280cb8d` | selected operational bootstrap profile v1.0 (user-uploaded) |
| `inputs/oap.md` | `d4daeb2a4a8963691e0a15ebf8f4e46bdfe36c792c9685e5117396ff17f60989` | ordinary OAP manual v1.0.1 (user-supplied; historical Claude examples retained as history) |

Archived bootstrap constitution (renamed to prevent instruction discovery):
`docs/bootstrap/1/BOOTSTRAP-GENERATOR.md` — byte-identical copy of the
package archive-root `AGENTS.md` (SHA-256 `09b72445b5d0ce26cd12b531148151f1293f51d5abee555dde3fe01c6280cb8d`).

## Pre-conversion bytes archived (docs/bootstrap/1/previous/)

| Original path | Archive | Original SHA-256 |
|---|---|---|
| `.dockerignore` | `previous/dockerignore.pre-concentrated` | `bdc82b5545f7de133be59d5d16d723611f5ae4378b286c42b965991469236f0b` |
| `.github/ISSUE_TEMPLATE/codex_work_order.yml` | `previous/codex_work_order.pre-concentrated.yml` | `23c86666a0c38acda857555fad4cf0ac08ab1e19aeda408167272ce37ed8778c` |
| `.github/PULL_REQUEST_TEMPLATE.md` | `previous/PULL_REQUEST_TEMPLATE.pre-concentrated.md` | `93484d6bb52bd24be8ee486a8120cee59425d721df5e182765e94ace14de88e2` |
| `.github/workflows/ci.yml` | `previous/ci.pre-concentrated.yml` | `aa02a7f083d248e16d45e046657d1d6c002c041943bf7e63a5b4dfd4949419f0` |
| `.gitignore` | `previous/gitignore.pre-concentrated` | `0e1d31f7d5a86477ed5456286f5413454871173eaa5bd223c2cf7e0d0c7cdec5` |
| `AGENTS.md` | `previous/AGENTS.pre-concentrated.md` | `99822d8eea31e01bfb58dbea2dcfc3d8ec5c91e86d831c34ca1cc4fb65299ff1` |
| `CONTRIBUTING.md` | `previous/CONTRIBUTING.pre-concentrated.md` | `74e31b8e2d8695b186310888129f6f5ac3e93250c18f5127f845b42f37cff7ae` |
| `README.md` | `previous/README.pre-concentrated.md` | `e63ef8510d9199d35f46083643fefd080de4e79dfb520e23f13d4f1a69ec0dfc` |
| `SECURITY.md` | `previous/SECURITY.pre-concentrated.md` | `fdf25060d1f5676bfdb6904908aa41bbfc6ade8b722ac64559fd915626c7ee88` |
| `docs/README.md` | `previous/docs-README.pre-concentrated.md` | `562ae9c58570601b6febac2839eeffa0abfff63e974a358789f0ec759b4d360c` |
| `docs/architecture.md` | `previous/docs-architecture.md` | `bcc8e46886eef1dc902c3bf142346603c3dd4ab47ee07a2c43b4e056b9d1f7dc` |
| `docs/oap-workflow.md` | `previous/oap-workflow.pre-concentrated.md` | `eb8863e8ceddee6b829ac0e3b77bbe2cd3974175260ab24174d97a964d86705c` |
| `docs/project-handoff.md` | `previous/docs-project-handoff.pre-concentrated.md` | `d1672201a7c6e18ab8b54005b9a81e570b9f9a74413c5210f8327bede822894c` |
| `docs/roadmap.md` | `previous/docs-roadmap.pre-concentrated.md` | `75a327fb3bfe62b977de28da32ee2d06bd263a8716ca78e8c57739a4b5d49db7` |

## Preserved accepted source identities (verified at materialization)

| Item | Git blob | Verified |
|---|---|---|
| `docs/architecture.md` (before pointer replacement) | `246870a7771452ce3878c228b9ad7ffd8e71eda0` | YES |
| `data/bootstrap/assets.yaml` (untouched product file) | `7c9ed1e4a072173960ebb9bdd886ce4c1fafe3a1` | YES |
| observed baseline main | commit `1fcc2c91d793556a91711365abef562604b62f84` | YES (local HEAD; remote main verified identical) |

## Explicit drift reconciliation (from SOURCE-MAP)

- Old AGENTS human-per-merge rule vs new conditional strategic development merge:
  old law archived; new authority applies only after supervised human adoption
  and attributable activation; adoption PR itself human-merged.
- `docs/architecture.md` S4.1 (REST mutations deferred) vs implemented bearer API
  (WO0006): historical text preserved; current architecture labels actual routes.
- Legacy `end_at` prose vs accepted ADR 0007 `effective_end_at`: canonical
  architecture preserves immutable original end plus blocking effective end; no
  data/code migration.
- Old module-table authz (groups/projects) vs accepted alpha deferral: deferred
  intent preserved, not claimed implemented.
- Blackout ownership (assets vs reservations): described as actually implemented
  (reservations/management_ui); original source preserved.
- Production-shaped observability diagrams vs observed code: target vs current
  state labeled; no operational readiness claimed.
- Historical alpha report (no blocker findings) vs new ICA: kept as report claim;
  not self-certified for any milestone.
- Old squash-merge prose vs actual two-parent merge history: history preserved;
  future merge method separately configured.
- Readiness query ordering / rehearsal test ownership: investigation candidates
  for 016-a/017-a, not reproduced failures.

## Boundary statements

- No full Concentrated OAP chapter snapshot was retrieved; the bundled generator is
  the self-contained selected profile. `inputs/oap.md` historical examples (other
  clients, images, bibliography) remain unchanged historical sources, not active
  instructions; their unbundled links are outside the verified local-link graph.
- No tracked CLAUDE.md existed at the baseline; none is generated. Untracked or
  externally owned CLAUDE.md files are preserved and reported, never deleted.
- `.env`, dumps, credentials and private exports are never inputs to this package.
