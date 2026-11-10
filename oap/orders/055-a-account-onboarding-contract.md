<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "055-a",
  "objective": 55,
  "round": "a",
  "slug": "account-onboarding-contract",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "1eade24e2032b8525d3b0151daaca38830e24d03",
  "issue_number": 114,
  "branch": "codex/114-oap-055-a-account-onboarding-contract",
  "pr_mode": "CREATE_OR_RESUME",
  "pr_number": null,
  "previous_round": null,
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "4566e797b709b71f13b2929572a2d1145d15a5a7ab8b41db50ebfdab962628cd",
    "PLAN.md": "8298ef941d02b05c304c48b46734ad678aff80b9ab4e62ca0814b6f03007277f",
    "ARCHITECTURE-for-agents.md": "41c32e0b0d6427a173dfe0b722446ae8ee311f3880929db65ed0245309b3a59e",
    "docs/governance/GROUP-AUTHORIZATION-PROJECTION-REVIEW.md": "dc0085fe0b8c1a1ad4efd780bd9c1517258e5df49b3db662e2fb4c5c7986f5ca",
    "docs/security-model.md": "7fcd7abf72a7c7c5e8db9dccaa47e9d281e4662a221caf3add6bf002d6c4d1f1"
  },
  "requirements": ["SAR-014", "SAR-040", "SAR-043", "SAR-044", "SAR-053", "SAR-054", "SAR-055", "SAR-056"],
  "allowed_paths": [
    "PLAN.md",
    "ARCHITECTURE.md",
    "ARCHITECTURE-for-agents.md",
    "docs/governance/ACCOUNT-ONBOARDING-PROJECTION-REVIEW.md",
    "oap/active",
    "oap/orders/055-a-account-onboarding-contract.md",
    "oap/reports/055-a-account-onboarding-contract.md"
  ],
  "forbidden_resources": [
    "No application source, tests, models, migrations, settings, email delivery, SMTP/network calls, secrets, dependency/lock, Docker/Compose/deploy/runtime/API/auth behavior changes; this is a selected contract only.",
    "No rewrite of old architecture/PLAN requirement/history text or prior OAP orders/reports/ICA evidence/CRITICAL/role law; append a controlled A-17 and new stable rows, recomposing only the compact projection and new semantic review.",
    "No real SMTP account, recipient, credential, identity administration, host/exposure/DNS/TLS/firewall, production DB, private data, foreign PR113 work, merge/automerge by CODING."
  ],
  "provenance": [
    {"marker": "H", "source": "Attributable human message 2026-11-09: administrator-created user gets email with login data, logged-in password change, prefilled random six-character password; make OAP plan then implement", "section_or_evidence": "The human selected all three product behaviors. Development may use synthetic SMTP only; real relay/recipient/secret/deployment remains separate. Persistent prior public-repository development publication/merge delegation is subject to exact-head checks."},
    {"marker": "A", "source": "Current ARCHITECTURE.md A-15/A-16, SAR-014/040/043/044/053; PLAN.md P-04/P-08; docs/audit/ICA-PROTOCOL.md", "section_or_evidence": "Current docs defer password reset/email and normal password validation requires eight characters. This new selection narrows the deferral only for admin-created onboarding and logged-in self-change; it must preserve active-human, abuse, CSRF, token secrecy and owner boundaries. New selected milestone needs fresh independent ICA before closure."},
    {"marker": "E", "source": "Live main 1eade24e2032b8525d3b0151daaca38830e24d03; source inspection 2026-11-09; sibling slaif-api-gateway external SMTP option; official Django5.2 mail/auth docs and OWASP password guidance", "section_or_evidence": "No current member password-change route or production SMTP settings. Django admin add form uses password1/password2 and normal MinimumLengthValidator. Gateway exposes SMTP_HOST/PORT/USERNAME/PASSWORD/FROM/USE_TLS/STARTTLS/TIMEOUT shape, but is not a product runtime dependency. Open foreign PR113 touches web forms/views/docs and must be reconciled before later implementation. Normal CI green at base; OAP accepted/quiescent 054-b."},
    {"marker": "I", "source": "Current UserAdmin and settings, Gateway SMTP config/service, and security model", "section_or_evidence": "Six-character emailed passwords materially weaken a persistent credential. A CSPRNG temporary password, max24h expiry, forced first change to normal validators, active-only-after-SMTP-acceptance and no automated ambiguous-send retry are bounded mitigations. Need canonical HTTPS base URL rather than untrusted Host, no plaintext persistence/logging, TLS external relay, and manual admin reissue that rotates prior secret."},
    {"marker": "C", "source": "Private M-ACCOUNT-ONBOARDING sequence and empty CRITICAL register", "section_or_evidence": "D0/DHA NONE for this documentation contract: the explicit human selects the weak enrollment-email shape, while current strong-password/Internet-boundary law requires a temporary-only safe interpretation. Strongest objection and residual mailbox compromise risk remain visible. No real mail/identity/deployment action is authorized; no unresolved new product choice is silently posed as a gate."}
  ],
  "decision_class": "D0",
  "target_gate": "Selected M-ACCOUNT-ONBOARDING contract and implementation sequence only; no claim of delivered feature, milestone closure, real SMTP or deployment",
  "expected_report_path": "oap/reports/055-a-account-onboarding-contract.md",
  "tests": [
    "Canonical full ARCHITECTURE A-17 and stable SAR-054..056 controlled append, old SAR IDs/deferrals preserved with explicit narrowed email/self-change exception, no inaccurate implemented claim.",
    "PLAN P-09 records human provenance, selected target, five proof-sized purposes 055 contract/056 self-change/057 SMTP/058 onboarding/059 integration+fresh ICA, dependencies, no real relay/exposure and status UNPROVEN. No fake issue/PR/SHA/result for future purposes.",
    "Compact ARCHITECTURE-for-agents projection recomposed after full source: direct executor obligations and negative boundaries, new source digest, honest semantic coverage in docs/governance/ACCOUNT-ONBOARDING-PROJECTION-REVIEW.md; no mandatory full architecture link for routine CODING.",
    "Changed Markdown links/anchors, source/projection coverage, git diff --check, prove no src/tests/settings/migrations/lock/Docker/Compose/deploy/runtime changes; focused OAP/doc checks then normal five CI checks at exact implementation and report heads."
  ]
}
-->

# 055-a — selected account-onboarding contract

## Goal and ordered read set

Record the human-selected M-ACCOUNT-ONBOARDING contract before product edits. This is a DOC/ARCHITECTURE prerequisite only, issue114, new branch/base in metadata. CODING reads its compact startup set, this order, bounded current PLAN P04/P08, ARCHITECTURE A07/A08/A13/A15/A16 and SAR014/040/043/044/053, current docs/security-model password/credential paragraphs, UserAdmin add-form/settings route shapes, Gateway SMTP config/service excerpts named in provenance and official Django 5.2 mail/auth reference. Do not load the whole sibling repository or raw private runtime. Prior 054-b is completed, not executable. Foreign PR113 remains untouched.

## Numbered acceptance

1. **Canonical selected meaning.** Append PLAN P-09 with the exact three human requirements, current contradiction (normal eight-character validator vs six-character initial), bounded mitigation, five sequential purposes 055–059 from this order's metadata `tests` and private strategic sequence, and status UNPROVEN until implementation/evidence. Do not call email/password reset already implemented, and do not treat the new selection as real SMTP/identity/deployment authorization. Narrow the old deferral precisely: general OIDC, public reset/self-registration and general notifications remain deferred.
2. **Full architecture first.** Append A-17 to ARCHITECTURE.md and stable SAR-054 (logged-in own-password change), SAR-055 (operator SMTP onboarding and failure boundary), SAR-056 (six-character temporary admin creation/forced change). Record controlled evolution of prior email/reset deferrals and normal password-validator baseline. Keep old requirements/ICA historical rather than rewriting them. State an initial UNPROVEN classification for all three new rows. A-17 must define the acceptance semantics below, not infer a broader mail system.
3. **Required safety semantics.** Member password change requires current password, normal validators (including existing minimum), CSRF, active non-service human, current-session continuity and other-session invalidation; no bearer mutation. The admin add GET prepopulates BOTH controls with the same new CSPRNG six-character value; only a generated initial temporary credential receives the narrow length exception, never a global validator weakening. It expires within 24h, cannot establish a NEW login after expiry, and successful login is restricted to changing it before member/management/Admin/session-API work. Existing accounts remain unchanged. SMTP is explicitly operator-enabled; when disabled/incomplete, admin add must not claim delivery or create an active short-password account. On enabled add, commit account first in inactive/pending state, send exactly one login-details email (canonical configured HTTPS URL, email identifier, temporary password) through external SMTP, and activate only after SMTP accepts. Failure remains inactive; admin sees nonsecret status and may manually reissue a fresh temporary credential, invalidating any previous one. Do not auto-retry an ambiguous SMTP send, persist plaintext, log bodies/credentials or derive links from Host. Production-enabled external SMTP requires TLS and bounded timeout; no added queue/Celery/Gateway dependency. No real relay/recipient is contacted in development. Human/password permissions, group grants, API token records, reservations and domain services remain intact.
4. **Projection/semantic review.** Only after full A-17/SAR rows are written, recompose ARCHITECTURE-for-agents.md with the actual executor obligations and explicit retained exclusions, update its source digest and index, and add docs/governance/ACCOUNT-ONBOARDING-PROJECTION-REVIEW.md mapping H requirements and A-17/SAR-054..056 facets to compact clauses. State byte/context measurements and limitations; structural hash alone is not semantic proof. Do not force routine CODING to read the full source.
5. **Evidence and publication.** Only allowed documentation/order/pointer/report paths change. Validate no runtime behavior changed, all changed links/anchors, prior records untouched, diff clean. Normal five CI jobs must pass at the final frozen implementation and report heads. PR body `Closes #114`, no actual feature claim. CODING opens PR before immutable report, reports literal implementation SHA/SELF, remote-verifies and signals response FIFO OK; never merges.

## Strongest objection / non-goals

Emailing even a temporary six-character password exposes a credential to mailbox and relay compromise; forcing change/expiry and current shared login-rate limits reduce but do not eliminate it. Do not market this as equivalent to a password-setup link or MFA. No self-service forgotten-password reset, public account enumeration, general notifications, service-account login, broader authorizations, identity-provider work, real email, SMTP secret, host change or deployment. A17 is target design, not an implementation or ICA pass.

## Recovery and next action

Use the existing idle CODING wrapper in right tmux pane. Its qualified client script sources supervision `codex.sh` from `~/codex-work/slaif-asset-reservation` before `codex --yolo --profile qwen-neumann`, in an isolated CODING home. If interrupted, resume only this ID/issue/PR, preserve foreign PR113 and current checkout data; no reset/clean/force. After strategy's exact frozen-head review and conditional development merge, next objective is 056-a member password change with a fresh coding context. A fresh independent ICA is required before a later selected milestone-closure claim.

## Deferred human adjudication
- Decision: NONE
