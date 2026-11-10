<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "057-a",
  "objective": 57,
  "round": "a",
  "slug": "external-smtp-config",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "2df6341d4d89dd45c835e3ac1af67ce076e54346",
  "issue_number": 118,
  "branch": "codex/118-oap-057-a-external-smtp-config",
  "pr_mode": "CREATE_OR_RESUME",
  "pr_number": null,
  "previous_round": null,
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "f7b5c98876a40b052c2d2fe057e57281e917ac5a72508e98caca512c1f0d1286",
    "PLAN.md": "e15eb06f6559886808916812dc555c244cc038ff42996a12276b58319562f864",
    "ARCHITECTURE-for-agents.md": "66d578e9fc263a77ceb4500bb2e8dac88b6080bf8f38890942fd46bc718f60ca",
    "src/slaif_reservation/config/settings/base.py": "68606562cf58e46e5316e1fa194ef200bd15122c5cb861d753c6809788991bf0",
    "src/slaif_reservation/config/settings/production.py": "10179c0160185bbcdf4105f6345bc922a0c8d9b57da2fff85242240631242542",
    "src/slaif_reservation/config/settings/local.py": "cd363cf0cd5d09f5d18bfd751e17c8da6fec744db1810bfcc84f2111b67ce3ec",
    "src/slaif_reservation/config/settings/test.py": "23cc982548546dc07f678ee48b22a331728cc1f508094bb6937835362c9c4009",
    "src/slaif_reservation/config/env.py": "2c71cc4909f4f6b886f5d03f6c6dc36377dda7ee34d738eb2daa2103f0ed5ce6",
    "deploy/env.production.example": "848426a3a4b601f18674af64102d5f96d2139c54530e45651821a3f422a44e89",
    "INSTALL.md": "73e9a7dbc41e57e565c363c6c057ba75f947f5cc923996a78879a4cae6dbd879",
    "docs/deployment.md": "75959d1ef9e2f98b6d89e1923e9212cbfc64420d9c4dc94c3d8bf4e9c377c917"
  },
  "requirements": ["SAR-023", "SAR-026", "SAR-037", "SAR-055"],
  "allowed_paths": [
    "src/slaif_reservation/config/settings/base.py",
    "src/slaif_reservation/config/settings/production.py",
    "src/slaif_reservation/config/settings/local.py",
    "src/slaif_reservation/config/settings/test.py",
    "src/slaif_reservation/config/env.py",
    "src/slaif_reservation/config/email.py",
    "deploy/env.production.example",
    "INSTALL.md",
    "docs/deployment.md",
    "tests/test_account_email_settings.py",
    "tests/test_settings.py",
    "oap/active",
    "oap/orders/057-a-external-smtp-config.md",
    "oap/reports/057-a-external-smtp-config.md"
  ],
  "forbidden_resources": [
    "No administrator user-add behavior, email send on account creation, six-character credential, password-change route, user model/migration, general notifications, queue/Celery/Gateway runtime dependency, public reset/self-registration, reservation/API/group/auth mutation.",
    "No real SMTP relay/recipient/credential or private data, production DB/host/DNS/TLS/firewall/exposure, Docker/Compose runtime topology change, package/dependency/lock change, ARCHITECTURE/PLAN/projection/CRITICAL/OAP helper/old order-report rewrite, foreign PR113.",
    "No logging of SMTP credentials or message bodies in tests, errors, docs, reports or CI; no merge/automerge by CODING."
  ],
  "provenance": [
    {"marker":"H","source":"Human 2026-11-09 request for administrator-created user email login data, explicit reference to sibling SLAIF API Gateway external SMTP option; 2026-11-10 demand to proceed with implementation","section_or_evidence":"External SMTP support is required to deliver later onboarding. No real relay/secret/recipient use is authorized for development."},
    {"marker":"A","source":"Merged ARCHITECTURE.md A-17/SAR-055 and SAR-023/026/037, PLAN P-09 purpose057; current docs/audit/ICA-PROTOCOL.md","section_or_evidence":"Explicit opt-in, canonical configured HTTPS URL, host/port/auth/sender, TLS, bounded timeout, fail closed on incomplete production config, secret-safe logs; no queue or Gateway dependency. General email workflow remains unimplemented until objective058."},
    {"marker":"E","source":"Live merged main 2df6341d4d89dd45c835e3ac1af67ce076e54346 / PR117, current settings and compose env_file; sibling Gateway config.py/email_service.py bounded excerpts","section_or_evidence":"No current SMTP production config or account email. Gateway shape SMTP_HOST/PORT/USERNAME/PASSWORD/FROM/USE_TLS/STARTTLS/TIMEOUT is the style reference; this Django service can use its built-in SMTP backend. compose.production.example.yaml already loads protected deploy/env.production, so no topology edit needed. Foreign PR113 still open on web files, untouched."},
    {"marker":"I","source":"Django 5.2 official email/settings docs and source inspection","section_or_evidence":"Map SLAIF-prefixed operator env values to Django EMAIL_HOST/PORT/HOST_USER/HOST_PASSWORD/DEFAULT_FROM_EMAIL/USE_SSL/USE_TLS/TIMEOUT. Disabled production uses dummy backend and does not send. Enabled production requires one encrypted SMTP mode, bounded timeout and canonical HTTPS origin; tests use synthetic local sink only."},
    {"marker":"C","source":"One proof-sized transport purpose; CRITICAL empty","section_or_evidence":"D0/DHA NONE. Strongest objection: misconfigured SMTP can leak credentials or let attacker-controlled Host shape links. Validate TLS/auth pairing/canonical URL at settings load, avoid echoing secrets, test fail-closed negative matrix. No actual delivery or product release claim."}
  ],
  "decision_class": "D0",
  "target_gate": "Reviewed development PR delivering opt-in validated SMTP transport settings only; no account email until separate onboarding objective, no real SMTP/deployment authorization",
  "expected_report_path": "oap/reports/057-a-external-smtp-config.md",
  "tests": [
    "Production settings with email disabled retain startup and have no outbound SMTP backend; enabled valid config selects Django SMTP with canonical HTTPS URL, exact mapped host/port/sender/auth/TLS/timeout. Invalid/missing host/from/base URL, non-HTTPS URL, userinfo/path/query/fragment, mismatch with allowed host/origin, missing paired auth fields, both/neither TLS modes, invalid port/timeout all fail closed without echoing raw values/secrets.",
    "Synthetic local SMTP sink proves Django backend can send one simple message under test overrides, with no real recipient/relay; disabled configuration sends nothing. No account creation email or user/migration change. No credentials/body in logs or errors.",
    "Production Compose renders with documented env; protected env example and INSTALL/deployment pointers are truthful and do not place real secrets in Git. Focused settings/transport tests, ruff/format/mypy/check/no-migrations, diff/link checks, normal five CI jobs at exact implementation and report heads, then reviewed merge."
  ]
}
-->

# 057-a — validated external SMTP transport for onboarding

## Goal and read set

Prepare the SMTP transport required for the human-selected administrator onboarding, without yet sending any account email. This is one implementation purpose after merged 056-b (member self-change), issue118, exact base/branch in metadata. CODING reads normal compact startup set and this order; bounded current config/settings/base.py, production.py, local.py, test.py, config/env.py helpers, deploy/env.production.example, INSTALL/deployment relevant sections, focused settings tests, and sibling Gateway config/email_service external SMTP excerpts only. Do not load the whole sibling repo or any `.env` contents into prompts/logs. Foreign PR113 remains separate.

## Numbered acceptance / negative paths

1. Add an explicit disabled-by-default account-email capability setting and canonical service URL setting. Prefer operator keys `SLAIF_ACCOUNT_EMAIL_ENABLED`, `SLAIF_PUBLIC_BASE_URL`, `SLAIF_SMTP_HOST`, `SLAIF_SMTP_PORT`, `SLAIF_SMTP_USERNAME`, `SLAIF_SMTP_PASSWORD`, `SLAIF_SMTP_FROM`, `SLAIF_SMTP_USE_SSL` (implicit TLS), `SLAIF_SMTP_STARTTLS` (explicit STARTTLS), `SLAIF_SMTP_TIMEOUT_SECONDS`; use those names consistently in code/example/docs unless a source-level collision demands a bounded clarification. Map to Django's built-in SMTP backend/EMAIL_* settings; no new package or Gateway service dependency. Default-disabled production must not send email. Current deployments without SMTP config continue to start and current admin add behavior stays as-is in this objective.
2. When enabled in production, validate at settings load: explicit SMTP host and sender, valid port1..65535, credential username/password pair consistency, exactly one of implicit TLS or STARTTLS, bounded positive timeout (1..60 seconds), and a canonical HTTPS base URL with no userinfo/path/query/fragment. Ensure its host is an allowed host and its origin is trusted for CSRF; never derive later email links from request Host. Fail closed with safe setting-name messages that do not echo raw SMTP values/credentials. SMTP connection is not attempted merely by importing settings. Keep `DEBUG=False`/proxy/cookies/DB/secret behavior unchanged.
3. Local/test settings remain safe for synthetic development: no real relay/recipient by default; test settings retain locmem backend unless a focused test intentionally overrides it. A local fake SMTP sink may exercise Django's backend without TLS to prove transport mechanics, but production-enabled configuration never permits plaintext SMTP. Do not add a queue, scheduler or general notification system, and do not send a real account message in this objective.
4. Update `deploy/env.production.example` with commented safe opt-in configuration and explanatory placeholders, no real secret. INSTALL gives a concise optional pre-user-creation step pointing to the full `docs/deployment.md` transport/security reference; both state that account delivery itself arrives in the next implementation objective, so no current claim that admin creation already emails. Existing Compose already has env_file and must render unchanged topology; no Compose edit. No README feature claim yet.
5. Focused positive/negative settings/synthetic transport tests, relevant existing production-settings negative tests, no secret values in errors/logs/report, no schema/migration/API/runtime topology change, five normal exact-head CI jobs and truthful immutable report. `Closes #118`; CODING never merges. Strategy reviews frozen head and only then conditionally merges.

## Strongest objection / recovery

SMTP configuration can silently permit plaintext credential delivery or unsafe links if an operator forgets TLS/URL settings. Production validation and synthetic tests must prove fail-closed behavior, while disabled default preserves current installs. No real SMTP/DNS/TLS/firewall/identity/deployment action is authorized. Fresh CODING context in right pane, source supervision `codex.sh` FROM development checkout before `codex --yolo --profile early-beta`; interrupted work resumes same ID/branch/PR without reset/clean/force. Prior 056-b order/report stay immutable. Report literal implementation head/SELF, report-only last commit, remote first-parent/path/PR verification, exact response FIFO OK; do not claim report-head CI before it exists.

## Deferred human adjudication
- Decision: NONE
