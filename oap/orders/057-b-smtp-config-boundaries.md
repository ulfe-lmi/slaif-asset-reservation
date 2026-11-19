<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "057-b",
  "objective": 57,
  "round": "b",
  "slug": "smtp-config-boundaries",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "2df6341d4d89dd45c835e3ac1af67ce076e54346",
  "issue_number": 118,
  "branch": "codex/118-oap-057-a-external-smtp-config",
  "pr_mode": "AMEND",
  "pr_number": 119,
  "previous_round": "057-a",
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "src/slaif_reservation/config/email.py": "9ea889a991b4f67ecee8ad1b4cad2eb197dcb05b40dbf4f66d61503a8ae4b3fa",
    "src/slaif_reservation/config/env.py": "6aae85bbe79471813be9f2f7919371ea79e5bb19819a96bf852aacd62739582d",
    "tests/test_account_email_settings.py": "e271a8d71724036dc58dad3f0d79d0118d54e3907b0ed7a9d897aa5635b4046b"
  },
  "requirements": ["SAR-023", "SAR-026", "SAR-055"],
  "allowed_paths": [
    "src/slaif_reservation/config/email.py",
    "src/slaif_reservation/config/env.py",
    "tests/test_account_email_settings.py",
    "oap/active",
    "oap/orders/057-b-smtp-config-boundaries.md",
    "oap/reports/057-b-smtp-config-boundaries.md"
  ],
  "forbidden_resources": [
    "No settings module, operator docs/env example, user/admin/web/email send, model/migration/auth/API/reservation, dependencies/lock/Compose/Docker/proxy, architecture/PLAN/projection/CRITICAL/CI/OAP helper or prior order/report edit.",
    "No real SMTP/recipient/credential, private data/production DB/host/exposure/DNS/TLS/firewall/deployment, foreign PR113 branch/resource mutation, merge/automerge by CODING."
  ],
  "provenance": [
    {"marker":"H","source":"Human 2026-11-09 external SMTP account delivery and 2026-11-10 urgency for implementation","section_or_evidence":"Same issue118/PR119 transport objective, no new feature; correct fail-closed validation and secret representation before merge and next onboarding objective."},
    {"marker":"A","source":"ARCHITECTURE.md A-17/SAR-055, SAR-023 fail-closed and SAR-026 safe logging; order057-a acceptance2/5","section_or_evidence":"Canonical HTTPS URL without userinfo/whitespace, valid sender, category-only errors and no credential disclosure even in representations/logging. Production-enabled SMTP is security-sensitive."},
    {"marker":"E","source":"Frozen 057-a implementation cdb3f68978d7650ee34960808c0ff8bfedc74883 / PR119, direct root source/test review and synthetic diagnostic","section_or_evidence":"Exact synthetic probes: validate_canonical_service_url('https://@reservation.example.test') ACCEPTS and normalizes empty userinfo; resolve_account_email_settings with leading/trailing URL spaces ACCEPTS because it strips before validation; malformed SLAIF_SMTP_FROM='bad-address' ACCEPTS (only nonempty checked); repr(AccountEmailSettings) includes a synthetic SMTP password. Wildcard SMTP host was rejected correctly. No real relay touched. 057-a report-head CI must be terminal before activation."},
    {"marker":"I","source":"config/env.py validate_canonical_service_url and config/email.py resolver/AccountEmailSettings","section_or_evidence":"Check parsed.username/password is not None or '@' in authority; pass untrimmed nonempty canonical URL into validator; validate bare sender with Django EmailValidator and catch ValidationError to safe category-only ImproperlyConfigured; dataclass field(repr=False,compare=False) for host_password. Tests negative matrix and repr without echoing secret in assertion diagnostics."},
    {"marker":"C","source":"One consolidated frozen-head strategic correction; CRITICAL empty","section_or_evidence":"D0/DHA NONE. Strongest reason not to merge 057-a: an invalid sender survives settings load and a credential-bearing dataclass can expose the SMTP secret if logged. Four narrow fixes in two source files plus focused tests, no transport redesign."}
  ],
  "decision_class": "D0",
  "target_gate": "Accept same opt-in SMTP transport PR only after four fail-closed/secret-repr corrections and five exact-head green CI checks; no real email or deployment",
  "expected_report_path": "oap/reports/057-b-smtp-config-boundaries.md",
  "tests": [
    "Observe all terminal 057-a report-head CI jobs and preserve immutable report; test four synthetic failures against current source before edits if needed.",
    "Focused tests: empty userinfo in canonical HTTPS URL rejected; surrounding whitespace rejected by resolver (not silently stripped); malformed and header-injection sender rejected at settings load with category-only message; synthetic SMTP secret absent from repr/str of AccountEmailSettings. Valid sender/base URL still accepted. No secret in error diagnostics.",
    "Existing 057-a production negative matrix/synthetic local SMTP sink and disabled dummy backend remain green; ruff/format/mypy/check/no-migrations/diff; normal five CI checks at exact implementation/report heads. Prior application/settings/operator docs and container semantics unchanged by this correction."
  ]
}
-->

# 057-b — close SMTP validation and secret-representation gaps

## Scope and evidence

Same issue118/PR119/branch as 057-a. Root reviewed its complete frozen implementation/source/tests/docs once and ran a read-only synthetic diagnostic (no real host/relay). Four concrete fail-closed/privacy gaps are proven: empty URL userinfo accepted; outer URL whitespace silently trimmed; malformed sender accepted; `AccountEmailSettings.__repr__` includes the SMTP password. Correct these only, leaving prior order/report immutable and every other file byte-identical. No account delivery begins in this round.

## Numbered acceptance

1. `validate_canonical_service_url()` rejects even empty userinfo in the URL authority (for example `https://@reservation.example.test`) rather than normalizing it away. The resolver passes the raw configured base URL through canonical validation without stripping leading/trailing whitespace. Missing/empty base URL still gets a safe required-setting error. Add direct validator and resolver tests for both negative paths; ordinary canonical URL with/without port remains valid.
2. Require `SLAIF_SMTP_FROM` to be a valid bare email address at enabled settings load. Reject malformed, whitespace and CRLF/header-injection forms; catch Django validation exceptions and raise a category-only ImproperlyConfigured message without echoing raw values/credentials. Existing valid sender and local synthetic sink still work.
3. Mark the `host_password` field of frozen AccountEmailSettings as excluded from repr/str (and comparison if appropriate), while preserving the actual value for Django's SMTP backend. Add synthetic canary tests proving the secret does not appear in repr/str/error output; never print or commit real credentials.
4. Focused 057 tests and normal exact-head five CI as metadata. No settings module/operator-doc change needed: their current claims become true with these fixes. Amend PR119 only as needed; `Closes #118` remains. CODING commits implementation+order/pointer, then report-only child with literal implementation SHA/SELF, remote verify and FIFO OK; no merge.

## Recovery / strongest objection

Wait for 057-a report-head CI to become terminal before activating this suffix; current candidate may be internally green yet still has these source-proven holes. Fresh CODING context through sourced supervision `codex.sh`, `--yolo --profile early-beta` in right pane. Preserve foreign PR113 and all existing data/resources; no reset/clean/force or real email/deployment. Strongest risk is a misconfigured sender or object repr causing leakage despite otherwise correct TLS settings. No CRITICAL entry for this bounded D0 correction.

## Deferred human adjudication
- Decision: NONE
