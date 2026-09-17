# Independent Closure Audit Report — M-LOCAL-PILOT-EVIDENCE

## Identity and scope

**Milestone:** M-LOCAL-PILOT-EVIDENCE — first controlled internal-alpha deployment target,
through the documented Docker/Compose path (per docs/audit/ICA-PROTOCOL.md: includes all
applicable product boundaries, full live ARCHITECTURE.md SAR index SAR-001..SAR-038, approved
deferrals recorded out-of-target).

**Human scope (verbatim, attributable in-session human instruction 2026-09-17):**
> Objective: "We now want to determine whether SLAIF Asset Reservation is genuinely ready for its
> first controlled internal-alpha deployment. The service MUST be deployable through the
> documented Docker/Compose path."
> Exclusions: "Do not interpret this instruction as authorization to perform a real deployment,
> create/rotate real secrets, configure real DNS/TLS, expose a host, touch production/private
> data, or cross any other D2 boundary."

Human milestone acceptance and release/deployment authority remain separate from this audit.

**Repository:** ulfe-lmi/slaif-asset-reservation (private)

**Exact audited product revision:** `21f6204d5f03c304991d4cd5c45a74aecdcb686a`
(025-c quiescent; merge of PR #50 objective 025 rounds a+b+c at this revision).

**Main-identity note:** local worktree HEAD at audit start = `2df70187126dd246a05a6510f29cccf09f421737`
(2df7018…, 026-a quiescent after merge of PR #52, which materialized this audit request).
`git diff --name-only 21f6204d5f03c304991d4cd5c45a74aecdcb686a..HEAD` returned exactly:

```text
docs/audit/requests/local-pilot.DRAFT.md   (deleted, -18 lines)
docs/audit/requests/local-pilot.md         (+178)
oap/orders/026-a-ica-request-local-pilot.md (+262)
oap/reports/026-a-ica-request-local-pilot.md (+346)
```

i.e., HEAD differs from 21f6204 ONLY by the audit request file and OAP 026-a round bytes
(governance/docs; no product paths). `git status --porcelain` was empty (clean tree) at start and
after all audit activity. All product bytes audited are those of 21f6204.

**Canonical identities at audited revision (sha256sum, re-derived live by this audit):**
- ARCHITECTURE.md: `182d9cf924931e846bc7965a762af807196ca0b87f8dffdf863`
  (verified identical in worktree and in `git show 21f6204:ARCHITECTURE.md`).
  NOTE: the audit input order carried a 51-hex-char value
  `182d9cf924931e846bc7965a762af807196ca0b87f8dffdf863` — not a valid SHA-256 (13 chars short);
  its first 24 hex chars match the true digest. The materialized request
  (docs/audit/requests/local-pilot.md) records the correct full 64-char digest. See finding F-003.
- PLAN.md: `d03eb29713cfbdb7e227413618396e6bb2a7a08749225979c3055dacfd461d06` (worktree == revision blob).

**Auditor identity (honest record):**
- auditor = Codex sub-agent context freshly spawned by the strategy role on 2026-09-17
  (start 2026-09-17T05:19:21Z, UTC).
- model = qwen3.8-27b — SAME model family as the development roles. This is fresh isolation,
  NOT an independent human auditor; recorded honestly per request.
- session origin = spawned fresh with no forked/inherited context; no prior involvement in the
  rounds under audit (025-a/b/c, 026-a) or in earlier OAP rounds.
- mandate = read-only with report-artifact write only (this file). No implementation, no merge,
  no CRITICAL disposition, no release approval. No D2 boundary crossed; no real deployment,
  secrets, DNS/TLS, or real lab/Neumann/production contact. Audit-local disposable resources
  were created and removed (see Evidence appendix): local PG role `ica`, scratch databases
  `ica_dev`, `ica_drill_src`, `ica_drill_tgt` (dropped), gitignored `build/` artifact (moved to
  /tmp), local docker image `slaif-ica-audit:21f6204` (disposable, left tagged locally).

**Excluded systems/data:** real lab machines/Neumann, private SmartScheduling exports,
production databases, real secrets/identity providers, DNS/TLS, any deployment target.
**Evaluated runtime:** audit host (Ubuntu 24.04, Python 3.12.3 host / repo venv Python 3.13.15,
local PostgreSQL 16.15 at 127.0.0.1:5432, Docker 29.1.3, gh 2.45.0, Playwright chromium cached).
CI runtime: ubuntu-24.04 with postgres:17 service (CI test job).

**Audit date:** 2026-09-17 (UTC).

## Requirement assessment

Method: for every SAR row I (a) read the enforcing source at 21f6204, (b) located and read the
named tests, (c) executed the full pytest suite locally (610/611 passed; the single failure is an
audit-environment PG16 limitation, root-caused — see Evidence appendix and F-004), (d) verified
real CI execution at the exact heads via GitHub API, and (e) ran targeted read-only operational
checks (documented dev-workflow CLI steps, rehearsal `--config-only`, docker build + image
inspection). CI runs at the exact heads are treated as execution evidence, not claims. All rows
start UNPROVEN and are substantiated below or kept UNPROVEN.

Legend: audited revision = 21f6204… for every row. "Local" = this audit's execution on the
audit host (PG16, full suite 610 passed / 1 env-fail, 218.62s). "CI@21f6204" = CI run
35182282171 (test job: 611 passed in 128.39s on postgres:17; quality/security/container all
success). "CI@979882e" = CI run 35182271284 (all four jobs success).

| SAR | Scope/deferral | Enforcing path / actual boundary | Actual test/command/evidence | Named negative path — verified | Result | Limits | Audited revision | Confidence | Required remediation |
|---|---|---|---|---|---|---|---|---|---|
| SAR-001 One reservation authority | in-target | src/slaif_reservation/reservations/services.py (create/cancel/release/policy/blackout services); adapters web/views.py, api/reservation_views.py, management_ui/forms.py+views.py, legacy_import/importer.py all call these services; no parallel booking logic found in source | Local: full suite incl. tests/test_reservations_services.py, tests/test_pilot_path.py::test_integrated_pilot_path_shared_state_across_surfaces (web+API+management on shared records); CI@21f6204 611 passed | An adapter-only or parallel create/cancel/release bypassing service enforcement: not found — every adapter routes through services; service tests assert policy/exclusivity enforcement; no second write path in source | IMPLEMENTED | Concurrency proof relies on PG17 CI + local PG16 threads (both green) | 21f6204… | high | none |
| SAR-002 Entitlement is not execution | in-target | config/urls.py, api/urls.py, wsgi/asgi imports; product src/ grep for ssh/paramiko/subprocess: only management commands wrapping pg_dump/pg_restore (recovery tooling, not lab execution) | Local: source inspection of all urlconf/imports; no execution side effects in any route | Any route/import activating jobs/SSH/inference/containers/GPU enforcement/power: none exist in product code; gateway explicitly out of product per A-01/A-02 | IMPLEMENTED | Absence verified by source inspection + greps, not by an executable negative (nothing to invoke) | 21f6204… | high | none |
| SAR-003 Stable resource identity | in-target | assets/models.py (UUID pk, legacy pair constraints), assets/bootstrap.py (idempotent apply, conflict fail-closed), data/bootstrap/assets.yaml (neumanngpu4→neumann-gpu-0 explicit, `ordinal_hint_unverified`) | Local: tests/test_bootstrap_assets.py (8 tests) passed, incl. test_import_preserves_explicit_neumann_mapping_without_inference, test_import_apply_creates_exact_inventory_and_second_apply_is_idempotent; test_assets_models.py legacy-pair tests passed | Re-import changing UUID/slug: second apply reports unchanged (idempotent), conflicting mapping fails closed (test_import_conflict_fails_closed_and_leaves_database_unchanged); no CUDA/GPU-UUID/hostname/readiness inference (ordinal kept unverified) | IMPLEMENTED | bootstrap counts (47/1 excluded) verified by live `import_bootstrap_assets` dry-run: planned=47 excluded=1 conflicted=0 | 21f6204… | high | none |
| SAR-004 Asset verification | in-target | assets/bootstrap.py (verification_required preserved, dry-run default), assets/selectors.py (safe read selectors) | Local: tests/test_bootstrap_assets.py passed incl. test_import_does_not_invent_private_or_verified_hardware_identity, test_import_excludes_chatgptpro_and_preserves_disabled_askljof; live dry-run showed excluded=1 (chatgptpro in excluded_legacy_records with reason) | Verification flags overwritten / unknown locator erased / chatgptpro made reservable: all negated by passing tests + assets.yaml (verification_required: true retained; chatgptpro excluded with decision reason) | IMPLEMENTED | — | 21f6204… | high | none |
| SAR-005 UTC and DST | in-target | reservations/time_utils.py (explicit fold; nonexistent/ambiguous rejected), accounts/validators.py (zone validation), web/forms.py | Local: tests/test_reservations_time.py (6 tests) passed (spring gap, autumn fold, aware-local rejected, malformed/overlong/NUL zone); tests/test_reservations_services.py DST duration/lead/horizon boundary tests passed; web form DST rejection test passed | Naive instant accepted / silent DST guess: rejected — `require_aware_utc` raises InstantError; ambiguous wall time requires explicit fold; no candidate → LocalTimeError | IMPLEMENTED | — | 21f6204… | high | none |
| SAR-006 Half-open effective-end history | in-target | reservations/models.py (check constraints: effective_end<=end, released fields valid; exclusion over [start, effective_end)), migrations/0001_initial.py | Local: tests/test_reservations_models.py passed incl. test_postgresql_exclusion_allows_adjacent_and_different_asset_ranges, test_released_reservation_blocks_only_historical_effective_interval, test_cancelled_reservation_does_not_block; service tests keep end_at immutable on cancel/release | Historical consumed interval erased (end/effective drift): service never mutates end_at; DB constraints enforce released: effective_end==released_at; cancelled row blocks nothing (exclusion condition status in confirmed/released) | IMPLEMENTED | — | 21f6204… | high | none |
| SAR-007 PostgreSQL exclusivity | in-target | reservations/migrations/0001_initial.py (BtreeGistExtension + ExclusionConstraint `reservation_no_overlap_per_asset`), services.py (`_is_named_reservation_constraint` translation) | CI@21f6204: real PG17; test log shows actual `ERROR: conflicting key value violates exclusion constraint "reservation_no_overlap_per_asset"` from concurrency tests; tests/test_reservations_concurrency.py::test_two_simultaneous_overlapping_creates_one_conflicts (real parallel transactions, exactly one commits) passed locally (PG16) and in CI | Two concurrent overlapping commits: negated (one-conflicts test, repeated blackout-race tests `exactly_one_commits_across_repeats`); unrelated integrity failure: test_unrelated_integrity_error_is_reraised (not reclassified as conflict) passed | IMPLEMENTED | Local concurrency ran on PG16; PG17 evidence is CI@21f6204 (exact head) | 21f6204… | high | none |
| SAR-008 Policies and counters | in-target | services.py `_resolve_effective_policy` (exact→parent→global, fail closed), `_enforce_policy` (duration/lead/horizon/purpose/upcoming/concurrent) | Local: tests/test_reservations_services.py passed: test_missing_policy_fails_closed, test_equal_priority_policy_ambiguity_fails_closed, boundary inclusive tests, upcoming/concurrent limits, test_active_reservation_starting_exactly_now_is_not_counted_as_upcoming; concurrency test_serialize_principal_upcoming_limit passed | Fail-open on missing/ambiguous/inactive policy: negated (POLICY_NOT_CONFIGURED/POLICY_AMBIGUOUS raised); counter raced past limit: negated (real concurrent upcoming-limit test) | IMPLEMENTED | — | 21f6204… | high | none |
| SAR-009 Atomic audited lifecycle | in-target | services.py (transaction.atomic around domain+audit), accounts/services.py (token issue/revoke atomic), legacy_import/importer.py (apply transaction) | Local: fault-injection rollback tests passed for create/cancel/release/policy create-update-deactivate/token issue-revoke/blackout create-deactivate/imported reservation (test_audit_failure_rolls_back_*); lock-order wait test test_policy_update_waits_for_reservation_operation_policy_lock passed | Audit row rolled back while domain row persisted (or vice versa): negated by fault-injection tests asserting both rows absent and audit count unchanged; deadlock from inconsistent lock ordering: consistent principal→asset→policy order in all write paths; no deadlock observed in concurrency suite | IMPLEMENTED | Fault injection is monkeypatched service failure (realistic but not DB-crash level); cross-adapter deadlock not exhaustively exercised under all interleavings | 21f6204… | high | none |
| SAR-010 Reducing entitlement remains possible | in-target | services.py release_reservation (no policy resolution; asset lock without _validate_asset), cancel_reservation (cutoff via active policy) | Local: test_staff_can_release_another_users_reservation_after_asset_deactivation, test_release_succeeds_after_policy_deactivation, cancellation cutoff/ownership transition tests all passed | Release rejected after asset/policy deactivation: negated (both tests pass; release path never consults policy and does not re-validate asset state); cutoff/ownership violations: negated by transition tests | IMPLEMENTED | Boundary observation: cancellation computes its cutoff from the CURRENT active policy; if no active policy exists, cancel fails closed (POLICY_NOT_CONFIGURED). This is outside the named negative (which targets release) and is fail-safe, but is untested territory worth a documentation note | 21f6204… | high | optional doc note (not a defect vs named negative) |
| SAR-011 Human session boundary | in-target | web/auth.py (active_human_required: authenticated+active+non-service, safe logout+redirect), web/views.py decorators | Local: tests/test_web_human_mvp.py matrix tests passed (test_member_routes_require_active_human_account, test_disallowed_authenticated_sessions_terminate_and_clear_session, test_post_only_logout, test_csrf_required_for_state_changing_forms, test_get_action_routes_do_not_mutate, login service-account denial) | Inactive/service-account session entering member routes: negated (decorator + matrix tests); CSRF-less POST or mutating GET: negated (CSRF tests + GET non-mutation tests) | IMPLEMENTED | — | 21f6204… | high | none |
| SAR-012 Member ownership | in-target | web/selectors.py + web/views.py `_owned_or_404`, api/reservation_views.py owner filtering | Local: test_own_reservation_routes_hide_other_user_and_do_not_mutate_on_get, test_staff_member_routes_cannot_access_or_mutate_other_user_reservations, API test_reservation_list_detail_cancel_and_release_are_owner_scoped, test_reservation_not_found_codes_are_endpoint_specific_and_non_disclosing — all passed | Other-owner/guessed ID disclosing existence: negated — non-disclosing 404 with endpoint-specific codes (no 200/leak) through real web and API adapters | IMPLEMENTED | — | 21f6204… | high | none |
| SAR-013 Management authority | in-target | management_ui/auth.py (management_required: active staff, non-service-account), views.py/forms.py call audited services; reservations/admin.py read-only | Local: test_management_access_role_matrix, test_management_mutations_require_csrf, test_management_get_requests_do_not_mutate_post_only_actions, admin read-only tests, cross-user management + audit tests — all passed | Non-staff/service-account performing /manage/ mutation: negated (role matrix, 403); management mutation without audit event: negated (audit written via services; audit-failure rollback tests) | IMPLEMENTED | — | 21f6204… | high | none |
| SAR-014 Token secrecy and lifecycle | in-target | accounts/tokens.py (sar_<32hex>_<32B CSPRNG secret>, HMAC-SHA256+pepper, compare_digest, scope allowlist), api/authentication.py (revocation/expiry/owner checks, redaction) | Local: tests/test_api_tokens.py passed: failure matrix (malformed/revoked/expired/exact-boundary), test_token_format_parser_and_verifier_uses_compare_digest, scope normalization, lifetime bounds, failed-auth-no-last-use (test_record_api_token_use_is_monotonic_and_best_effort), verifier-not-plaintext stored | Revoked/expired token authenticating: negated (exact expiry boundary test); plaintext persistence: negated (verifier stored, repr redacted); scope beyond allowlist honored: negated; failed auth mutating last-use: negated | IMPLEMENTED | — | 21f6204… | high | none |
| SAR-015 One-time secret handling | in-target | web/views.py token_create (Cache-Control no-store,private; Referrer-Policy no-referrer; one-time display), accounts/tokens.py sensitive_variables, config/logging.py redaction | Local: test_token_web_lifecycle_one_time_display_and_redaction, ExceptionReporter redaction tests (auth/malformed/format/verifier/token-created template), audit rejection of token material — all passed | Secret reappearing in History Back/URL/session/message/log/audit/report/trace: negated by no-store+no-referrer on one-time response, prefix-only listing, redacted repr/exception frames (caplog + ExceptionReporter assertions), recursive audit metadata rejection | IMPLEMENTED | Real-browser History-Back behavior not separately exercised beyond Playwright suite (8 browser tests passed, incl. token flows in human-mvp browser tests) | 21f6204… | medium-high | none |
| SAR-016 Scoped API adapters | in-target | api/urls.py, api/permissions.py (HasApiTokenScope per-action), assets/api.py (SessionAuthentication+IsAdminUser only) | Local: test_bearer_authentication_and_scope_matrix, test_staff_asset_api_remains_session_only, test_bearer_token_does_not_access_staff_asset_api, test_no_token_lifecycle_routes_in_openapi_root — all passed | Valid token alone reaching staff-session asset list/detail or admin surface: negated (asset API has no bearer authenticator; 403/401 tests); action beyond token scopes: negated (scope matrix) | IMPLEMENTED | — | 21f6204… | high | none |
| SAR-017 Strict API contract | in-target | api/serializers.py (bounded fields, aware instants), api/problem.py (problem details, no ORM text), reservation_views.py | Local: test_mutation_requires_valid_idempotency_key_and_aware_timestamps, test_reservation_list_rejects_unknown_and_invalid_time_window_filters, test_reservation_not_found_codes_are_endpoint_specific_and_non_disclosing, problem-detail assertions across API tests — all passed | Error leaking SQL/constraint/ORM text/other-user identity: negated (problem.py maps domain errors to safe codes; no ORM/SQL strings in serializers/views source); unknown fields/naive instants silently accepted: negated (400 + problem detail) | IMPLEMENTED | — | 21f6204… | high | none |
| SAR-018 Idempotent API mutations | in-target | api/idempotency.py (key validation, canonical hash, replay/conflict/expired semantics), api/models.py (unique owner/token/action/key, 24h TTL) | Local: test_reservation_create_is_idempotent_and_replays_without_duplicate_audit, test_idempotency_conflict_rejects_same_key_different_request, test_expired_idempotency_record_fails_without_replay_or_mutation, test_same_key_different_token_is_independent, REAL concurrent tests test_concurrent_identical_create_mutates_once / test_concurrent_different_body_same_key_conflicts_once — all passed; CI log shows real unique-constraint violation under concurrent-conflict-1 | Duplicate reservation/audit from concurrent identical-key replays: negated (concurrent identical → one mutation, one audit; DB unique constraint as final arbiter visible in CI log); changed request treated as replay: negated (idempotency_conflict); expired record auto-resolving: negated (idempotency_expired, no new write) | IMPLEMENTED | Safe replay header allowlist is Location-only (by design) | 21f6204… | high | none |
| SAR-019 Advisory private availability | in-target | web/availability.py (clip/merge/complement, lead/horizon, "Unavailable" labels, no foreign UUID), api/reservation_views.py availability | Local: test_availability_clips_merges_and_hides_other_user_private_fields, test_availability_busy_free_rules_are_exact_and_private, test_availability_local_day_boundaries_are_explicit_and_safe, API privacy tests incl. blackouts without reason/identity — all passed | Other user's identity/email/purpose/reason/UUID exposed: negated (foreign intervals labeled "Unavailable", reservation_id None; blackout reason never emitted); cancelled/released reported beyond valid bounds: negated (cancelled excluded; released clipped at effective_end_at) | IMPLEMENTED | Advisory nature (no hold) is by design, not a gap | 21f6204… | high | none |
| SAR-020 Blackout integrity | in-target | reservations/services.py create_blackout (locked, confirmed_overlap required), `_raise_if_blackout_overlap` in create path, models.py blackout constraints | Local: test_blackout_blocks_web_and_api_reservation_creation_and_half_open_boundary, test_blackout_model_services_and_creation_confirmation, test_blackout_audit_failure_rolls_back_creation_and_deactivation, REAL races test_reservation_vs_blackout_race_exactly_one_commits_across_repeats, test_deactivation_vs_booking_race_never_books_over_active_blackout — all passed | New booking over active blackout succeeding: negated (service check inside locked txn + real race tests); auto-cancel/release on blackout creation: negated (overlapping reservations reported, explicit confirm flag, no lifecycle writes); missing audit/rollback coupling: negated (rollback tests) | IMPLEMENTED | Blackout-vs-reservation final arbiter is the locked-transaction application check (A-06 explicitly notes PG exclusion does not cover blackout ordering); races covered by repeated real-transaction tests | 21f6204… | high | none |
| SAR-021 Bounded audit evidence | in-target | audit/models.py (append-only manager/queryset), audit/validators.py (recursive forbidden keys + token plaintext regex, 4KB cap), management_ui export (filtered, CSV-safe) | Local: test_audit_event_is_append_only_and_admin_read_only, test_audit_event_blocks_ordinary_overwrite_update_and_delete, bulk entry-point block tests, test_audit_metadata_rejects_forbidden_nested_keys/oversized, management export/privacy filter tests — all passed | Bulk/admin silently rewriting/removing audit rows: negated (queryset/manager/admin all raise or read-only); credential-like metadata accepted: negated (recursive key + plaintext-token rejection, incl. nested); unfiltered raw-forensic export: negated (allowlisted filters, bounded windows, CSV escaping tests) | IMPLEMENTED | Application/ORM boundary only — not tamper-proof vs privileged DB operator (explicitly acknowledged in A-05 and docs/security-model.md §6; hardening is an approved deferral) | 21f6204… | high | none (deferral recorded out-of-target) |
| SAR-022 Reproducible monolith | in-target | pyproject.toml (Python >=3.13,<3.14; Django >=5.2,<5.3; DRF >=3.16,<3.18; Gunicorn/WhiteNoise/drf-spectacular+sidecar), uv.lock, Dockerfile (python:3.13-slim@digest, uv sync --locked, non-root) | Local: full venv from committed lockfile used for all runs (Django 5.2.17, DRF 3.17.2 locked); docker build succeeded; CI quality job (ruff/mypy/git diff --check) + container job (docker build, image User check, static/bootstrap file tests) success at 21f6204 | Drifted lockfile/pyproject (new production dep or bump without decision): negated for the audited window — only change vs baseline is 016-a ordered pip-audit remediation (PR-tracked); CI `uv sync --locked` enforces lockfile integrity | IMPLEMENTED | See F-001: executor projection cites DRF3.16 while canonical/lock say 3.17 (projection drift, recorded under SAR-037) | 21f6204… | high | none (see F-001 under SAR-037) |
| SAR-023 Production fail closed | in-target | config/env.py (env_required, UNSAFE_SECRET_KEYS, min 32 bytes), settings/production.py (raises ImproperlyConfigured; DEBUG forced off; secure cookies; private docs; HSTS opt-in), accounts/tokens.py pepper validation | Local: tests/test_settings.py full negative matrix passed (placeholder/short/committed secrets, hosts/CSRF origins, ASGI fail-closed, HSTS bounds); CI security job runs a live subprocess import of production settings that MUST fail without env — success at 21f6204 | Production booting with placeholder/missing secrets/pepper/DB/hosts: negated (settings raise at import; live subprocess negative in CI); local/test values authorizing deployment: negated (UNSAFE sets reject committed local/test values in production) | IMPLEMENTED | — | 21f6204… | high | none |
| SAR-024 Topology and exposure | in-target | compose.yaml (dev: 127.0.0.1-only binds), compose.production.example.yaml (app 127.0.0.1:${SLAIF_APP_HOST_PORT:-8000} only; db NOT published; secrets file mount; user 10001:10001; read_only+tmpfs; healthcheck with X-Forwarded-Proto), Dockerfile (USER 10001:10001, collected static + data/bootstrap) | Local: `docker build` from 21f6204 worktree → image User `10001:10001`; `test -f` inside image passed for web/site.css, admin base.css, swagger-ui bundle, data/bootstrap/assets.yaml + schema.json; rehearsal `--config-only` rendered production compose with synthetic env (ok); CI container job verified rendered prod config healthcheck + image properties at 21f6204 | Binding beyond loopback / db published / root image / missing static-bootstrap assets: all negated (compose source + live image inspection + rendered-config CI guard). No DNS/TLS/host changes made by any development order | IMPLEMENTED | Real reverse-proxy/TLS is operator-owned (D2 boundary; Caddyfile.example provided); live-socket exposure only observed at loopback in dev/rehearsal shapes | 21f6204… | high | none |
| SAR-025 Health and diagnostics | in-target | config/views.py (health_live no DB; health_ready safe-fail), config/operational.py, api/management/commands/{operational_check,pilot_readiness_check,purge_*}.py | Local (live on disposable DB): `manage.py migrate` ok, `operational_check` → database/migrations/static/bootstrap/idempotency_cleanup all ok; `purge_expired_idempotency_records` → expired=0 deleted=0; tests/test_health.py (liveness DB-independent, readiness privacy-safe failure) passed; pilot_readiness_check suite (14 tests incl. read-only proof, hard gates on DB/migration failure, service-account cannot satisfy human-staff gate) passed | Liveness depending on DB: negated (test + source: no DB call in health_live); readiness crashing: negated (exception→503 safe path tested); pilot_readiness_check writing or being a release certificate: negated (read-only test asserts zero row changes; docs state aggregate-only) | IMPLEMENTED | — | 21f6204… | high | none |
| SAR-026 Safe logs | in-target | config/logging.py (JsonLogFormatter: safe fields only, recursive redaction, token/authorization/pepper/SECRET_KEY scrubbing), config/middleware.py (method/path/status/duration/request_id only) | Local: test_json_log_formatter_redacts_secret_fields, test_request_logging_middleware_emits_safe_fields_without_headers_or_body, test_production_json_logging_configuration_loads, authentication log secret tests (caplog) — all passed | Hostile sentinel (credential header/cookie/password/purpose/private locator/cancellation reason) in structured logs directly or via inner exception locals: negated (FORBIDDEN_FIELD_NAMES redaction incl. purpose/cancellation_reason; exception text scrubbed; middleware emits no headers/body) | IMPLEMENTED | Sentinel exercise is via formatter/middleware unit paths (real log entry points), not a full A/B of every view's log lines | 21f6204… | high | none |
| SAR-027 Recovery tooling | in-target | api/management/commands/{backup_database,restore_database,purge_expired_idempotency_records,restore_drill}.py, _postgres_tools.py | Local: refusal/dry-run/missing-URL/password-redaction tests passed (test_operational_hardening.py); REAL round-trip test_restore_drill.py::test_real_round_trip_verifies_and_cleans_up FAILED LOCALLY on PG16 (root cause: pg_restore 17 issues `SET transaction_timeout`, PG16 rejects — environment, not product; see F-004); CI@21f6204: `tests/test_restore_drill.py .........` (9/9) passed on postgres:17 as part of 611 passed | Apply without explicit authorized isolated target: negated (dry-run default; --apply required; restore into nonempty target handled by --clean --if-exists on operator-named isolated target); purge deleting non-expired: negated (test expired=0/deleted=0 semantics); drill cleans up its own target | IMPLEMENTED | Local re-execution of the PG17 round-trip was environment-blocked (PG16 host); the real round-trip evidence at the exact head is CI@21f6204 on postgres:17. Drill is specified for PG17 (matches the compose-deployed image) | 21f6204… | medium-high | none (F-004 informational) |
| SAR-028 Synthetic migration boundary | in-target | legacy_import/parser.py (URL_SCHEME_RE, private-field/unknown-status/duplicate-ID/DST-time rejection), mapping.py (explicit maps only) | Local: tests/test_legacy_import.py parser/mapping suites passed (URL schemes refused incl. report paths, private fields, duplicate IDs, nonexistent/ambiguous local times, unmapped user/asset classifications); test_input_url_schemes_are_refused | Parser accepting URL schemes/private fields/unknown statuses/duplicate IDs: negated (failing-fixture tests); user autocreation or inferred physical mapping: negated (no user-creation code path in importer; mapping requires explicit maps) | IMPLEMENTED | — | 21f6204… | high | none |
| SAR-029 Migration plan is not authority | in-target | legacy_import/planner.py (read-only plan), importer.py `apply_import`/`_revalidate_for_apply` (locked revalidation of user/asset/policy/blackout/reservation/import-record) | Local: test_dry_run_writes_no_reservations_or_audit_events, test_apply_revalidates_new_blackout/new_reservation_conflict/asset_state/user_state/missing_future_policy/existing_legacy_import_record (all in-transaction), test_changed_legacy_record_is_reported_not_overwritten, test_audit_failure_rolls_back_imported_reservation, legacy-import concurrency tests — all passed | Dry-run creating rows: negated (assertion on zero reservation/audit counts); apply on stale plan without revalidation: negated (each revalidation test injects post-plan state change and asserts classification/rollback); missing rollback: negated | IMPLEMENTED | — | 21f6204… | high | none |
| SAR-030 Historical import exception | in-target | legacy_import/importer.py + planner.py (past-completed migration exception; future records obey current policy/exclusivity/blackouts) | Local: test_status_asset_policy_classifications, test_future_import_uses_current_policy_boundaries, past/future/skipped handling in apply tests — all passed | Future confirmed record bypassing current policies/exclusivity/blackouts: negated (future records go through `_enforce_policy` + blackout/overlap revalidation); cancelled/no-show inventing blocking history: negated (per ADR0013 classifications; no blocking rows invented) | IMPLEMENTED | Real SmartScheduling cutover remains an approved deferral (synthetic fixtures only) — out-of-target, not a pass gap | 21f6204… | high | none |
| SAR-031 Resource ownership in rehearsal | in-target | deploy/rehearse_internal_alpha_deployment.sh (owned-project prefix `slaif-alpha-rehearsal-`, refuses pre-existing deploy/env.production + secrets, port precheck, cleanup-only-owned), tests/test_operational_hardening.py | Local: rehearsal `--config-only` ran clean (temporary synthetic env created+removed, git tree untouched); hardening tests passed (refuse existing production env, owned-residue refusal without up/down, cleanup-owned removes only owned project, status read-only, port precheck refuses owned/foreign occupants); CI@21f6204 deployment-rehearsal run (workflow_dispatch, actor jpers1) executed the FULL script on a disposable CI runner: success | Adopting/deleting pre-existing env/containers/volumes: negated (refusal + label-scoped ownership); existing or non-loopback port binding: negated (precheck tests + 127.0.0.1-only compose shape); residue after failed startup: negated (trap cleanup + owned-residue handling) | IMPLEMENTED | Full-compose live run evidence is the CI runner execution at 21f6204 (disposable); this audit did not start a full compose stack locally (loopback-only, and not required beyond the CI evidence) | 21f6204… | high | none |
| SAR-032 Evidence before readiness | in-target | tests/ (611 tests at this revision), .github/workflows/ci.yml (quality/test/security/container with postgres:17), deployment-rehearsal.yml, oap.yml | CI@21f6204 run 35182282171: quality/test/security/container all `success`; test job `611 passed in 128.39s` on real postgres:17, playwright chromium, named commands; CI@979882e run 35182271284: all four success; deployment-rehearsal run 35182574499 success; oap harness runs success at both heads; Local: same suite 610/611 (1 env-fail, root-caused) | Readiness claim resting on mocked boundaries/stale counts/unnamed revisions: negated — this audit re-derived from source at 21f6204; the historical 419-test figure is labeled historical in PLAN.md and not used as proof; all four required CI jobs green at the exact head | IMPLEMENTED | Historical 419 count superseded by current 611-test exact-head evidence | 21f6204… | high | none |
| SAR-033 Preserve existing project | in-target | entire tracked application and Git history | Local: `git merge-base --is-ancestor 1fcc2c91…(baseline) 21f6204` = true; `git diff --name-only 1fcc2c91… 21f6204` product-path changes confined to four ordered, PR-tracked rounds: 8f83dcb 017-a (restore drill), 7bb4536 016-a (pip-audit remediation), 14ccae1 024-a (docs), ccd11d1 025-a (deployment qualification) — no scaffold regeneration, no module deletion/recreation; OAP orders/reports numbered sequentially 015-a…026-a with matching implementation heads; 21f6204..HEAD delta only the 026-a audit-request bytes | Out-of-allowlist application-byte changes by the conversion: negated (conversion rounds touched oap/docs/governance; every product diff maps to an ordered product round with PR ancestry); reset numbering/history: negated (linear PR-merge ancestry from baseline); fabricated OAP reports: negated (spot-checked round↔PR↔head consistency) | IMPLEMENTED | Full byte-level diff of the 51-commit window not re-listed per file; mapping verified at round-commit granularity | 21f6204… | high | none |
| SAR-034 Codex-only role separation | in-target | AGENTS.md (role router), oap/bin/launch-*.sh → oap_launch.py (explicit launcher), oap/strategic-instructions/ + oap/coding-instructions/ (separate homes/read sets) | Local: no CLAUDE.md anywhere in tree (find); "claude" occurrences only negative statements ("No operational CLAUDE.md or Claude launcher"); oap harness (tests/oap, incl. role-conflict/inheritance tests ba10/11) success in oap CI runs at 21f6204/979882e | Operational CLAUDE.md/Claude launcher on discovery path: negated; implicit role switch by cd/source inspection: negated (router requires explicit launcher/human assignment; "reading another role's source never changes your role") | IMPLEMENTED | Private role-home state (STRATEGIC_HOME) is outside the repo by design; verified only the repo-side router/launchers | 21f6204… | high | none |
| SAR-035 Private infrastructure boundary | in-target | runtime constraints (oap/runtime.env.example: no keys/tokens stored; Codex-only clients), product code (no LLM/ssh/network egress), private activation record (out-of-repo by design) | Local: product src/ contains no LLM/ssh/paramiko imports; no deployment targets/hosts in code; runtime.env.example explicitly forbids storing credentials; this audit itself performed no real-infrastructure contact (only loopback-local + CI-run reads via GitHub API) | Development test/rehearsal touching real lab machine/Neumann/private export/production DB/long-lived credential/DNS-TLS/deployment target: negated in-repo (no such endpoints or fixtures; rehearsal uses synthetic values + owned disposable resources); no secret copying (oaplib secret-line regex guard + policy) | IMPLEMENTED | "Private activation record" lives outside the repo (by design) — repo-side constraints verified only | 21f6204… | medium-high | none |
| SAR-036 Deferred product scope stays visible | in-target | PLAN.md P-04, docs/roadmap.md, INSTALL.md §12 (9 known alpha limitations), docs/security-model.md §6, ARCHITECTURE.md A-04/A-10 | Local: source inspection — no OIDC/membership/notifications/monitoring/scheduler/gateway/management-REST implementation present (greps + urlconf/OpenAPI surface: only the A-08 interface map exists); deferrals recorded with authority in the audit request (7 items) | New deferred-scope surface appearing without accepted decision: negated (OpenAPI schema contains no token-lifecycle/admin REST routes — test_token_lifecycle_routes_are_not_exposed_as_api; no new surfaces in 21f6204); draft silently authorizing deferred scope: negated (request records all 7 deferrals out-of-target with authority) | IMPLEMENTED | The 7 approved deferrals (OIDC/password-reset/email; projects/memberships/resource restrictions; execution gateway; notifications; monitoring stack; SmartScheduling cutover; DB role separation/backup hardening) are OUT-OF-TARGET with recorded authority — neither passes nor omissions | 21f6204… | high | none |
| SAR-037 Canonical governance and projection | in-target | oap/governance/ (HUMAN-AUTHORITY.example.json), ARCHITECTURE-for-agents.md (executor projection), root ARCHITECTURE.md/PLAN.md canonical | Local: semantic comparison of all 38 projection SAR rows vs canonical index (scripted, line-by-line) → exactly ONE drift: projection SAR-022 says "DRF3.16", canonical + uv.lock say DRF3.17 (locked 3.17.2); projection header hash-binds to the INITIAL architecture (9e7c60e4…) — the canonical was re-issued since (182d9cf9…) without projection recomposition; also the canonical header's preserved-snapshot path is stale (see F-002) | Projection drifting from canonical source while treated as independent law: PARTIALLY MET NEGATIVE — one-token semantic drift exists (DRF3.16 vs 3.17); mitigated by the projection header ("Not independent architecture or approval", "initial SHA-256") and canonical precedence, but the hash-bound coverage map is not current | PARTIAL | Drift is a single version label in one row; no product behavior impact; canonical and lockfile agree | 21f6204… | high (finding), n/a | F-001: reconstitute the SAR-022 line (or re-bind projection to current canonical hash with explicit delta note) |
| SAR-038 Human target and ICA | in-target | CRITICAL.md (empty register — zero CRIT entries), oap/audit/ (path referenced by index; not present at this revision — planned), docs/READINESS.md (separated dimensions) | Local: CRITICAL.md contains "No CRIT entries at initialization" and no dispositions; this report is a fresh isolated context bound to the exact merged revision (identity recorded above); READINESS.md keeps merge ≠ release/deployment/acceptance; oap runtime template ships OAP_DEVELOPMENT_MERGE_ENABLED=false (merge disabled absent attributable activation) | Strategic development merge treated as release/deployment/milestone acceptance: negated (no such claim in any round report at 21f6204; merge disabled by default; this audit makes no acceptance claim); ICA without fresh independent context bound to exact revision: negated (fresh context, 21f6204-bound, same-model-family limitation recorded honestly) | IMPLEMENTED | Auditor is same model family as development roles (fresh isolation, not an independent human) — recorded as a limitation, not a defect; oap/audit/ directory absent (planned path) | 21f6204… | high | none |

**Classification counts (38 rows):** IMPLEMENTED = 37, PARTIAL = 1 (SAR-037), ABSENT = 0, UNPROVEN = 0.

## Findings and contrary evidence

**F-001 — Executor projection drift: DRF version label (LOW, SAR-037)**
- Provenance: ARCHITECTURE-for-agents.md line 12 (SAR-022 row: "Preserve Python3.13, Django5.2,
  **DRF3.16**, PostgreSQL17, …") vs canonical ARCHITECTURE.md line 526 (SAR-022: "DRF3.17") and
  uv.lock (`djangorestframework` version 3.17.2; pyproject `>=3.16,<3.18`).
- Observation: scripted comparison of all 38 projection rows vs the canonical index shows this is
  the ONLY semantic drift. The projection is hash-bound to the initial architecture
  (9e7c60e4…); the canonical was re-issued (182d9cf9…) after the 016-a dependency remediation,
  and the projection was not recomposed.
- Impact: a coding round trusting the projection label could cite the wrong DRF minor version in
  a change justification. No product behavior, security, or deployment impact (canonical +
  lockfile agree and are authoritative).
- Strongest reason not to fix now: documentation-only drift in a file that explicitly declares
  itself non-authoritative ("Not independent architecture or approval", "initial SHA-256"); the
  deployment target does not depend on it; fixing it would open a governance-doc round outside
  this audit's read-only mandate.
- Narrow repair (if ordered): H = SAR-037 (projection must be coverage-mapped/hash-bound);
  A = ARCHITECTURE.md A-14 SAR-022 row (canonical text); E = this finding + uv.lock DRF 3.17.2;
  I = ARCHITECTURE-for-agents.md (reconstitute the one line, or re-bind the header to the current
  canonical hash with an explicit delta note); C = canonical ARCHITECTURE.md SAR-022 wording.

**F-002 — Canonical header cites a nonexistent preserved-snapshot path (LOW, documentation)**
- Provenance: ARCHITECTURE.md line 5: "preserved unchanged in `sources/repository/docs-architecture.md`
  (Git blob 246870a7771452ce3878c228b9ad7ffd8e71eda0)". At 21f6204 there is no `sources/` path in
  the tree. The actual preserved snapshot is `docs/bootstrap/1/previous/docs-architecture.md`,
  whose Git blob IS 246870a7771452ce3878c228b9ad7ffd8e71eda0 (verified via `git ls-tree`), and
  `docs/architecture.md` is the 12-line compatibility pointer per A-12.
- Observation: `sources/repository/…` is the input-package staging path (see
  docs/bootstrap/1/inputs/SOURCE-MAP.md line 74), not a repository path. Byte preservation is
  intact (blob identity verified); only the stated location is wrong/ambiguous.
- Strongest reason not to fix now: the preservation obligation is substantively met and
  independently verifiable via blob ID; a one-line path correction in the canonical header is a
  governance-doc edit outside this read-only mandate.
- Narrow repair (if ordered): correct the header path to docs/bootstrap/1/previous/docs-architecture.md
  (or explicitly mark sources/repository/… as the input-package staging path). H = A-12;
  A = ARCHITECTURE.md header; E = this finding; I = ARCHITECTURE.md line 5; C = git ls-tree blob evidence.

**F-003 — Input order carried a malformed (51-hex) architecture hash (INFORMATIONAL, publication hygiene)**
- Provenance: audit input order step 2 specified SHA-256
  `182d9cf924931e846bc7965a762af807196ca0b87f8dffdf863` (51 chars — not a valid SHA-256).
- Observation: the live-computed digest of ARCHITECTURE.md at 21f6204 is
  `182d9cf924931e846bc7965a762af807196ca0b87f8dffdf863`; the order's value matches its first 24
  hex chars and is missing 13. The materialized request (docs/audit/requests/local-pilot.md)
  records the correct full digest. Audit proceeded on the computed digest (worktree == revision blob).
- Strongest reason not to fix now: no product/governance byte is affected; the request doc is
  correct; only the transient input order wording is malformed.
- Repair: none in-target; note for strategy publication hygiene (digests in orders must be full 64-hex).

**F-004 — Audit-environment limitation: local PG16 cannot run the PG17 restore drill (INFORMATIONAL, not product)**
- Provenance: tests/test_restore_drill.py::test_real_round_trip_verifies_and_cleans_up FAILED in
  this audit's local run; root cause reproduced manually: pg_restore 17.11 sends
  `SET transaction_timeout = 0`, which PostgreSQL 16.15 rejects
  (`unrecognized configuration parameter "transaction_timeout"`).
- Observation: the drill is specified for PostgreSQL 17 (test docstring; compose image
  postgres:17 pinned by digest; CI installs the PG17 client for a reason). CI@21f6204 ran the full
  9-test file green on postgres:17 (log line: `tests/test_restore_drill.py .........`).
- Strongest reason not to fix now: not a product defect — the deployment target ships PG17; the
  local host simply has PG16. No code change is indicated.
- Repair: none; if local drills on this host are wanted, run the drill against a disposable
  postgres:17 container (documented dev path), which this audit did not do.

**Observation (SAR-010 boundary, not a finding):** cancellation resolves the cutoff from the
CURRENT active policy (`lock_effective_policy` in cancel_reservation); with no active policy,
cancellation of a confirmed future reservation fails closed (POLICY_NOT_CONFIGURED). Release is
unaffected (no policy reference) and both deactivation-release negatives are tested. This is
fail-safe behavior outside the named negative; recorded for completeness (see SAR-010 row).

## Judgment and boundary register

- **CRITICAL register:** CRITICAL.md at 21f6204 contains zero CRIT entries ("No CRIT entries at
  initialization") and no human dispositions. There are therefore NO open DHA gates to clear for
  this milestone, and none were created by this audit.
- **D2 boundaries:** none crossed. Real deployment, real secrets, DNS/TLS, host exposure,
  production/private data, lab/Neumann contact: all excluded by the human scope and untouched.
  Operator-owned items (real SECRET_KEY/pepper, TLS proxy, host/firewall/backup storage) remain
  human/operator prerequisites for an actual deployment — prerequisites, not code blockers.
- **Human dispositions:** none applicable (no CRIT entries). Human milestone acceptance for
  M-LOCAL-PILOT-EVIDENCE and any release/deployment decision remain separate, attributable human
  judgments not made here.
- **Combined risk:** the 37 IMPLEMENTED classifications accumulate on a common evidence base
  (exact-head CI + local re-derivation). The shared limitations are: (a) auditor is same model
  family as development (fresh isolation, not human independence), (b) structural validators
  (oap/bin/check_ica.py etc.) prove form, not correctness, (c) live exposure (TLS proxy, real
  secrets, real host) is unexercised by design. None of these converts into a product defect at
  21f6204.
- **Residual uncertainty:** real-world deployment characteristics (operator proxy behavior, real
  secret handling, backup storage, host hardening) can only be evidenced at actual controlled
  deployment time, which this audit neither performs nor approves.

## Blockers — first controlled internal-alpha Docker deployment (in-target only)

**No in-target code/evidence blockers were found** for the service being deployable through the
documented Docker/Compose path at 21f6204:
- Image builds reproducibly from the exact revision (CI container job + local rebuild); non-root
  10001:10001; static/bootstrap assets present in image.
- Documented compose shapes are loopback-only and fail-closed (dev + production example);
  production settings refuse to boot without real distinct secrets/hosts/pepper.
- Full deployment rehearsal (synthetic values, owned disposable resources, cleanup) executed
  green at the exact revision on a disposable CI runner.
- The 611-test exact-head suite (real PG17, browser, concurrency, operational) is green; the only
  local failure is the audit-host PG16 environment limitation (F-004).
- Findings F-001/F-002 are LOW documentation-drift items with no deployment impact.

**Out-of-target deferrals (NOT blockers, recorded with authority — a deferral is not a pass):**
1. Institutional OIDC / password reset / email (SAR-036; INSTALL.md §12)
2. Projects / memberships / resource restrictions (SAR-036; security-model §6 — broad
   authenticated-human authorization acceptable only under a constrained trusted pilot)
3. Execution gateway / automatic physical allocation (SAR-036; SAR-002 boundary)
4. Notification system (SAR-036; INSTALL.md §12)
5. Monitoring stack (SAR-036 Phase 4; INSTALL.md §12)
6. SmartScheduling production cutover (SAR-030 scope / ADR0013; synthetic only)
7. Database role separation + backup hardening (security-model §6 "operational work")

**Human/operator prerequisites for an actual deployment (separate from this audit):** real
operator secrets (SECRET_KEY, API_TOKEN_PEPPER, POSTGRES password), real host/firewall/TLS
reverse-proxy (operator-owned per A-03/A-24), backup storage, and the explicit human
milestone-acceptance + deployment authorization. These are D2/human steps by the stated scope.

## Closure recommendation

Assessed ONLY at the exact audited revision 21f6204d5f03c304991d4cd5c45a74aecdcb686a: the
M-LOCAL-PILOT-EVIDENCE requirement matrix (SAR-001..SAR-038) substantiates 37 rows as
IMPLEMENTED and 1 row (SAR-037) as PARTIAL due to a single low-severity projection drift
(F-001); no ABSENT or UNPROVEN rows remain. The Docker/Compose deployability target is
evidence-backed at this revision (build, fail-closed settings, loopback-only topology,
rehearsal, recovery tooling, exact-head CI). This is a structural/evidentiary assessment.
Any remediation (F-001/F-002, if the human/strategy elects to act) requires an ordered
H/A/E/I/C-linked correction round and re-audit of the architecture-to-current-main matrix at the
new exact revision — not merely closing finding IDs. Deployment, exposure, release, and final
human milestone acceptance are NOT granted by this report.

## Evidence appendix

### A. Revision and digest verification
```text
$ git rev-parse HEAD                      # 2df70187126dd246a05a6510f29cccf09f421737 (026-a quiescent)
$ git rev-parse 21f6204…                  # 21f6204d5f03c304991d4cd5c45a74aecdcb686a
$ git status --porcelain                  # (empty)
$ git diff --name-only 21f6204…..HEAD
docs/audit/requests/local-pilot.DRAFT.md  (deleted)
docs/audit/requests/local-pilot.md
oap/orders/026-a-ica-request-local-pilot.md
oap/reports/026-a-ica-request-local-pilot.md
$ sha256sum ARCHITECTURE.md
182d9cf924931e846bc7965a762af807196ca0b87f8dffdf863  ARCHITECTURE.md
$ git show 21f6204…:ARCHITECTURE.md | sha256sum   # identical (worktree == revision bytes)
$ git show 21f6204…:PLAN.md | sha256sum
d03eb29713cfbdb7e227413618396e6bb2a7a08749225979c3055dacfd461d06  -
```
The input order's architecture hash (51 hex chars) is malformed; see F-003.

### B. CI runs verified at exact heads (GitHub API, gh 2.45.0, repo ulfe-lmi/slaif-asset-reservation)
```text
run 35182282171  CI   head=21f6204…  conclusion=success  (2026-09-17T04:32:07Z)
  jobs: quality=success  test=success  security=success  container=success
  test job log (job dbId 105076825334): postgres:17@sha256:d13db94… service; Python 3.13.14;
  pytest 9.1.1; "======================= 611 passed in 128.39s (0:02:08) ========================"
  "tests/test_restore_drill.py ........." (9/9 incl. real PG17 dump/restore round-trip)
  real exclusion-constraint violations logged from concurrency tests
  ("conflicting key value violates exclusion constraint \"reservation_no_overlap_per_asset\"")
run 35182271284  CI   head=979882e… (PR #50 merge commit)  conclusion=success — all four jobs success
run 35182574499  deployment-rehearsal  head=21f6204…  conclusion=success
  event=workflow_dispatch, actor=jpers1 (2026-09-17T04:36:47Z)
  step: deploy/rehearse_internal_alpha_deployment.sh -> success (disposable CI runner)
oap harness runs at 21f6204 (35182282152) and 979882e (35182271311): success
```

### C. Local executions (audit host; repo venv via `uv run --no-sync`)
Environment: PostgreSQL 16.15 @ 127.0.0.1:5432 (disposable role `ica` CREATEDB, dropped after
audit), Playwright chromium cached, Docker 29.1.3, gh 2.45.0.
```text
$ TEST_DATABASE_URL=postgres://ica:…@127.0.0.1:5432/slaif_reservation \
    DATABASE_URL=postgres://ica:…@127.0.0.1:5432/slaif_reservation uv run --no-sync pytest -q
1 failed, 610 passed in 218.62s
FAILED tests/test_restore_drill.py::RestoreDrillRoundTrip::test_real_round_trip_verifies_and_cleans_up
  (root cause: pg_restore 17.11 `SET transaction_timeout` rejected by PG16 server — see F-004;
   reproduced manually: "pg_restore: error: could not execute query: ERROR: unrecognized
   configuration parameter \"transaction_timeout\"")
$ uv run --no-sync pytest tests/browser -v        # 8 passed in 25.03s (Playwright/Chromium)
$ uv run --no-sync pytest tests/test_restore_drill.py --deselect <round-trip>   # 8 passed, 1 deselected
```
Documented dev-workflow steps on a disposable scratch DB (`ica_dev`, dropped after audit):
```text
$ manage.py migrate --noinput                      # all migrations applied OK
$ manage.py import_bootstrap_assets --input data/bootstrap/assets.yaml
  mode=dry-run planned=47 created=47 unchanged=0 excluded=1 conflicted=0
$ manage.py operational_check
  database=ok migrations=ok static=ok bootstrap=ok idempotency_cleanup_command=ok operational_check=ok
$ manage.py purge_expired_idempotency_records      # expired=0 deleted=0 remaining_expired=0
$ manage.py makemigrations --check --dry-run       # No changes detected
$ manage.py check                                  # 0 issues
$ manage.py spectacular --file build/openapi/schema.yaml --validate --fail-on-warn   # OK (521-line schema;
  build/ is gitignored; generated artifact moved to /tmp after verification)
```
Rehearsal (documented CI step):
```text
$ SLAIF_REHEARSAL_PORT=18099 bash deploy/rehearse_internal_alpha_deployment.sh --config-only
rehearsal: rendering production Compose config with synthetic env
rehearsal: config-only=ok          (temporary synthetic env/secrets created and removed; git tree clean)
```
Container re-derivation:
```text
$ docker build --tag slaif-ica-audit:21f6204 .    # success (image sha256:c472695f…)
$ docker image inspect slaif-ica-audit:21f6204 --format '{{.Config.User}}'   # 10001:10001
$ docker run --rm --entrypoint test slaif-ica-audit:21f6204 -f <path>   # OK for:
  /app/staticfiles/web/site.css
  /app/staticfiles/admin/css/base.css
  /app/staticfiles/drf_spectacular_sidecar/swagger-ui-dist/swagger-ui-bundle.js
  /app/data/bootstrap/assets.yaml
  /app/data/bootstrap/assets.schema.json
```
Source/provenance checks:
```text
$ git merge-base --is-ancestor 1fcc2c91… 21f6204…   # true (baseline preserved in ancestry)
$ git diff --name-only 1fcc2c91… 21f6204… -- src/ pyproject.toml uv.lock Dockerfile compose*
  -> only ordered rounds: 8f83dcb(017-a) 7bb4536(016-a) 14ccae1(024-a) ccd11d1(025-a)
$ git ls-tree 21f6204… -- docs/bootstrap/1/previous/docs-architecture.md
  100644 blob 246870a7771452ce3878c228b9ad7ffd8e71eda0 …   # pre-conversion snapshot preserved (F-002)
$ grep -ril claude oap/ AGENTS.md   # only negative "no CLAUDE.md" statements; no CLAUDE.md file exists
$ grep -rn paramiko|ssh|subprocess src/slaif_reservation (product)  # only pg tool wrappers in commands
```
Semantic projection comparison (scripted, all 38 rows): exactly one drift (SAR-022 DRF3.16 vs 3.17).

### D. Not-run / blocked states (explicit)
- Restore drill real round-trip: NOT re-run successfully locally — BLOCKED by audit-host PG16
  (F-004); evidence at exact head is CI@21f6204 on postgres:17 (B).
- Full compose live stack (`deploy/rehearse_internal_alpha_deployment.sh` without --config-only):
  NOT run locally by this audit (not required; CI runner execution at 21f6204 recorded in B;
  local full-up would start a loopback stack on a shared host — avoided as unnecessary).
- No real deployment, no real secrets, no DNS/TLS, no lab/Neumann/production contact: by scope.

### E. Environment limitations
- Audit host PostgreSQL is 16.15; product target is PostgreSQL 17 (drill + compose image).
  All other suites are PG-version-insensitive for this audit's purposes and were re-executed.
- Auditor model family equals development model family (fresh isolation; not human independence).
- GitHub actor `jpers1` on the workflow_dispatch is an observed account identity; this audit does
  not independently attest it is the attributable human principal (attribution is a human/strategy
  record matter).

## Result statement

At the exact merged product revision 21f6204d5f03c304991d4cd5c45a74aecdcb686a, the
M-LOCAL-PILOT-EVIDENCE requirement matrix substantiates 37/38 rows as IMPLEMENTED and 1 row
(SAR-037) as PARTIAL (single low-severity projection drift, F-001). No ABSENT or UNPROVEN rows.
No in-target blockers to the service being deployable through the documented Docker/Compose path
were found; the seven approved deferrals remain out-of-target with recorded authority.

**These structural/audit findings do NOT constitute deployment approval, release readiness, or
milestone acceptance.** The human decides target readiness, milestone acceptance, release and
deployment separately and with explicit attribution; this audit never substitutes for that
decision, and no real deployment was performed or authorized here.

## Independence and structural-validation disclaimer

- This audit ran in a fresh isolated Codex sub-agent context (spawned 2026-09-17T05:19:21Z)
  with no forked/inherited development context and no prior involvement in the audited rounds.
- HONEST LIMITATION: the auditor model (qwen3.8-27b) is the SAME model family as the
  development roles. Fresh isolation reduces but does not eliminate common-mode bias; this is
  NOT an independent human audit. Structural validators (oap/bin/check_ica.py and similar) check
  form only; they cannot prove independence, correctness, or closure.
- Evidence is boundary-faithful: source bytes at 21f6204, tests executed locally, and CI runs
  verified at the exact heads via the GitHub API. Historical reports, PR descriptions, and
  handoff prose were used as inputs/indexes only, never as proof; every claim above re-derives
  from source, executed tests, or verified CI artifacts.
