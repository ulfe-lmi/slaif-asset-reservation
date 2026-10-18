# 050-b — execution report

Implementation head SHA: fc58681ad2e67c768946db4fdc0e578c22f130a1
Report publication commit: SELF

## Identity and result
- Order: `oap/orders/050-b-operator-authorization-guide.md` (state FINAL, Decision: NONE, class D0); active pointer `oap/active` = `050-b`.
- Repo/issue/branch/PR: ulfe-lmi/slaif-asset-reservation / #103 / codex/103-oap-050-a-management-authority / PR 104 (AMEND; "Closes #103" retained).
- Base main `b873f4cf1071bded044ba456625b0ced355407a8` unchanged; 050-a report `88dc75a0fdf874e0aec758af1752d2da7b42de71` immutable and untouched.
- Result: COMPLETE.

## Acceptance evidence
1. Concrete group setup — PASSED. `docs/authorization.md` gains "Setting up grants: groups and individual permissions (operator procedure)": create/select a group in existing Administration (auth.Group change page, "Permissions" fieldset), tick the ten application codenames (listed separately from per-model Add/Change/Delete/View), assign users via "Groups", individual "Permissions" grants supported and unchanged, union semantics, no automatic enrolment, staff flag required only for /admin/ plus model permissions. Cross-checked against source: `accounts/authorization.py` `RESERVATIONS_PERMISSIONS` and `GroupAdmin`/`UserAdmin` help in `accounts/admin.py`.
2. Illustrative role table — PASSED. Table with exact codenames (Administrators = all ten; Lab members = `book_assets`+`view_all_reservations`; Students = `book_assets`; Reservation readers = `view_all_reservations`), the three misreadings explicitly excluded (no automatic privileged membership; model View is not read-all; no administrator asset-group bypass), asset allowed-group membership on top of `book_assets` with no implicit parent inheritance, retained owner lifecycle after eligibility loss, existing tokens owner-only, `reservations:read_all` planned-not-implemented, no projects/deny/directory/machine promises.
3. Upgrade sequence discoverable — PASSED. `INSTALL.md` section 9 gains a short authorization-compatibility note between migration and app restart; the guide's Deliberate upgrade steps are ordered backup -> migrate -> choose current active human staff UUIDs (from the Administration user change URL `/admin/accounts/user/<STAFF_UUID>/change/`) -> default dry-run (no `--apply`; no `--dry-run` flag exists; repeat `--user`) -> explicit `--apply` -> verify (`9/9 direct grant(s) present`, `nothing (idempotent)`) -> restart/access check. `run --rm app` does not require the running service; the command serves only the intentionally chosen full-legacy-staff case; partial/non-staff grants use existing Administration groups/individuals; Compose project/volume identity, filenames, backup and migration/default-policy instructions preserved.
4. Precise security reference — PASSED. `docs/security-model.md` "staff-visible" wording replaced with the actual detail readers/managers (`reservations.view_maintenance_blackouts` or `reservations.manage_maintenance_blackouts`, including non-staff app-capability users), verified against `management_required(*BLACKOUT_READ_CAPABILITIES)` on `blackout_list`/`blackout_detail` and the read-only `MaintenanceBlackoutAdmin`; protected Administration model rule and member/API availability privacy preserved; audit CSV data and 500/7-day bounds untouched; no access change.
5. Scope/evidence honesty — PASSED. `docs/README.md` unchanged (not a 050-a change; needs no edit). Actual 050-a scope verified from `git show --stat 95d29b8`: 7 product docs, 17 tests (15 adapted + 2 new), 10 management_ui + 2 web templates. No browser recapture: visual freshness rests on strategy-regenerated 2 focused Chromium tests at 95d29b8 (2 PASS, 9.59 s; current All 1440 / partial 390 artifacts viewed under the private 050-frozen-browser) and root 5 independent PG probes (PASS, 3.68 s); the extra local 69-test browser run passed but its aborted full server is not qualification; the local source copy has no Git metadata and pg tools are absent locally, so no Git/Docker executable absence is claimed.
6. Verification and byte identity — PASSED. All relative links/anchors in the three changed docs resolve (both new anchors verified); every compose command retains `-p "$SAR_COMPOSE_PROJECT"` and `compose.production.example.yaml`; `git diff --check` clean; `git diff 95d29b8..fc58681` touches only the three docs + `oap/active` + the 050-b order (plus the pre-existing 050-a report already in the base); src/tests/static/deploy/config/deps byte-identical to 95d29b8. No local app/browser/harness/restore/Gunicorn/HTTPS reruns (no code change).

## Changed files and scope
- `docs/authorization.md`, `INSTALL.md`, `docs/security-model.md` (documentation only)
- `oap/orders/050-b-operator-authorization-guide.md` (published order bytes), `oap/active` (050-a -> 050-b)
- No application/static/template/test/model/migration/config/dependency/deploy changes.

## Commands and results
- sha256sum of the 8 order source hashes: all match. PASSED.
- `git show --stat 95d29b8`: 44 files; counts as in #5. PASSED.
- Link/anchor checker over the three changed docs: all resolve. PASSED.
- `git diff --check`: clean. `git diff --name-only 95d29b8 fc58681 -- src tests static deploy docs/README.md ARCHITECTURE.md PLAN.md CRITICAL.md pyproject.toml uv.lock compose.yaml compose.production.example.yaml compose.branding.example.yaml Dockerfile .github oap/coding-instructions oap/strategic-instructions oap/bin oap/templates oap/prompts`: empty. PASSED.
- Local pytest/browser/harness/restore/Gunicorn/HTTPS/rehearsal: NOT RUN by order (no code change; evidence reused by byte identity).

## CI observed before authoring
- Implementation head fc58681: CI run 39088790663 — container, security, quality, test all success (test: 1207 passed, 1 warning, 489.25 s). oap run 39088790627 — oap-harness success. 5/5 required jobs PASSED; no waiver/skip.
- Report-head CI: NOT YET OBSERVED AT AUTHORING.

## Security, data, dependencies and local tools
- No secrets or private data in this change; no real account/group/DB/secret/host/exposure operations; no merge/auto-merge/delegation.
- Tools used: git, gh (run watch/api), python3 (link checker), sha256sum. No new dependencies.

## DHA outcome and unresolved gates
- Decision: NONE. No CRITICAL append, no human adjudication, no gate clearance.

## Limitations and recommendation
- Report-head CI is pending at publication (observed separately, outside the model); this report claims nothing about it.
- Next scope remains separate: bearer `reservations:read_all`/issuance and the fresh independent closure at the exact merged revision; no merge/release here.
