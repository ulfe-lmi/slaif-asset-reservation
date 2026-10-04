# ICA requirement matrix — historical initial existing-product assessment seed

Baseline source inspection: `1fcc2c91d793556a91711365abef562604b62f84`. **Historical
seed:** this 38-row matrix was materialized for that 2026-09 baseline revision and is
preserved as-is. Current canonical requirement scope: the ARCHITECTURE.md SAR index at
the audited revision (2026-10-04 edition: SAR-001 through SAR-047); derive each new ICA
matrix dynamically per ICA-PROTOCOL.md rather than copying this seed.
**Not an independent audit.** Initial classifications are UNPROVEN for the new closure audit,
not assertions that the existing implementation is absent. Historical work/tests are context.
At audit time replace the audited revision with the actual selected merged revision and record
boundary-faithful evidence. All requirements must remain visible, including approved deferrals.

| Requirement | Current enforcing paths / inspection target | Negative boundary to exercise | New ICA classification | Audited revision / evidence |
|---|---|---|---|---|
| SAR-001 — One reservation authority | `src/slaif_reservation/reservations/services.py` | Web/API/management create-cancel-release parity; no adapter-only enforcement | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-002 — Entitlement is not execution | `config/urls.py; api/urls.py; application imports` | Inspect actual routes/imports; absence of execution side effects | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-003 — Stable resource identity | `assets/models.py; assets/bootstrap.py` | Idempotent import; neumanngpu4 mapping; no ordinal inference | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-004 — Asset verification | `assets/bootstrap.py; assets/selectors.py` | Safe import conflict/dry-run/verification-field preservation tests | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-005 — UTC and DST | `reservations/time_utils.py; accounts/validators.py; web/forms.py` | Spring gap, autumn fold, malformed/overlong/NUL zone, UTC arithmetic and visible zone | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-006 — Half-open effective-end history | `reservations/models.py; migrations/0001_initial.py` | Adjacent intervals accepted; released prefix preserved; cancelled free | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-007 — PostgreSQL exclusivity | `reservations/migrations/; reservations/services.py` | Real concurrent transactions, named constraint inspection, unrelated error test | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-008 — Policies and counters | `reservations/services.py; models.py` | Boundary and counter races; missing/ambiguous and inactive-policy tests | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-009 — Atomic audited lifecycle | `reservations/services.py; accounts/services.py; legacy_import/importer.py` | Fault injection, rollback of every affected row and audit count, deadlock/race tests | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-010 — Reducing entitlement remains possible | `reservations/services.py; web/views.py; api/reservation_views.py` | Release after deactivation; cancelled/released retry and cutoff tests | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-011 — Human session boundary | `web/auth.py; web/views.py; accounts/models.py` | Anonymous/inactive/service-account/staff/member matrix; CSRF and method tests | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-012 — Member ownership | `web/selectors.py; api/reservation_views.py` | Cross-user detail and mutation tests through real adapters | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-013 — Management authority | `management_ui/auth.py; views.py; reservations/admin.py` | Role matrix plus CSRF/GET on every mutation; admin bypass tests | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-014 — Token secrecy and lifecycle | `accounts/tokens.py; models.py; services.py; api/authentication.py` | Secret/pepper/expiry/revocation/owner/scope matrices; failed auth no last-use mutation | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-015 — One-time secret handling | `web/token templates/static; accounts/tokens.py; config/logging.py` | History Back; inner exception reports; recursive audit rejection; output canaries | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-016 — Scoped API adapters | `api/urls.py; permissions.py; assets/api.py` | Authentication/scope/ownership matrix, missing surfaces and schema | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-017 — Strict API contract | `api/serializers.py; problem.py; reservation_views.py` | Unknown fields/filter ordering/naive time/malformed JSON/endpoint-specific 404s | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-018 — Idempotent API mutations | `api/idempotency.py; api/models.py; api/migrations/` | Real concurrent identical/different requests; expiry; safe header replay | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-019 — Advisory private availability | `web/availability.py; api/reservation_views.py` | Cancelled/released/confirmed clipping, adjacency, blackout merge and privacy | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-020 — Blackout integrity | `reservations/models.py; services.py; management_ui/` | Create-vs-blackout race and adjacent boundary; confirmation; rollback | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-021 — Bounded audit evidence | `audit/models.py; validators.py; management_ui/selectors.py; views.py` | Bulk/reconstructed mutation; secret-key/value rejection; export filtering/escaping | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-022 — Reproducible monolith | `pyproject.toml; uv.lock; Dockerfile` | Locked install, lint/type/build/schema tests; no opportunistic upgrades | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-023 — Production fail closed | `config/env.py; config/settings/production.py; accounts/tokens.py` | Subprocess negative settings matrix, ASGI/WSGI fail closed | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-024 — Topology and exposure | `compose*.yaml; Dockerfile; deploy/` | Rendered config plus actual sockets/image paths; explicit exposure gate | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-025 — Health and diagnostics | `config/views.py; operational.py; api/management/commands/` | Real CLI disconnected/unmigrated/failure paths and no-write evidence | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-026 — Safe logs | `config/logging.py; middleware.py; token exception protections` | Hostile sentinels through real log entry points; no raw report leakage | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-027 — Recovery tooling | `api/management/commands/backup_database.py; restore_database.py; purge_expired_idempotency_records.py` | Refusal tests plus isolated real dump/restore round trip before recovery claim | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-028 — Synthetic migration boundary | `legacy_import/parser.py; mapping.py; management/commands/` | URL/path/schema/DST/privacy negatives; unmapped user/asset classifications | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-029 — Migration plan is not authority | `legacy_import/planner.py; importer.py; models.py` | Stale plan mutations, duplicate/changed records, apply report, audit rollback | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-030 — Historical import exception | `legacy_import/importer.py; planner.py` | Past vs future vs skipped status tests; original interval retained | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-031 — Resource ownership in rehearsal | `deploy/rehearse_internal_alpha_deployment.sh; tests/test_operational_hardening.py` | Existing files/symlinks/project collision/partial startup; actual Compose merge | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-032 — Evidence before readiness | `tests/; .github/workflows/ci.yml` | Real PostgreSQL, real entry-point smoke, negative tests, accurate skipped/blocked statuses | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-033 — Preserve existing project | `entire tracked application and history` | Pre/post manifest diff allowlist; history ancestry; no product writes at bootstrap | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-034 — Codex-only role separation | `AGENTS.md; oap/; strategic home` | Instruction inheritance/role-conflict tests; no implicit role switch or fallback | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-035 — Private infrastructure boundary | `runtime constraints; private activation record` | Safe fixture-only bootstrap tests; network/resource allowlist; no secret copying | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-036 — Deferred product scope stays visible | `PLAN.md deferred scope; source roadmap` | Architecture-to-scope matrix; no new surfaces during conversion | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-037 — Canonical governance and projection | `oap/governance/; ARCHITECTURE-for-agents.md` | Semantic comparison and mechanical drift tests, measured read set | UNPROVEN | Not audited; source-inspected baseline only |
| SAR-038 — Human target and ICA | `CRITICAL.md; oap/audit/; docs/READINESS.md` | Attribution/ICA freshness/target gate tests; no self-certification | UNPROVEN | Not audited; source-inspected baseline only |

Required assessment columns when finalized: full architecture clause/hash; human scope applicability;
classification; actual enforcing code/runtime; test/command; dangerous negative path; evidence identity;
limitations; exact audited revision; closure finding or attributable deferral. Do not promote a row
because an old report says “all tests passed.”
