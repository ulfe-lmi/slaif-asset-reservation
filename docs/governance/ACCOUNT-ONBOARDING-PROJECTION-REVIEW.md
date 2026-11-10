# ACCOUNT-ONBOARDING-PROJECTION-REVIEW — A-17 coverage and measured coding context

Order: 055-a (2026-11-09). This is a **semantic coverage record and measured context
record** for the selected account-onboarding target. It is a deliberate semantic
comparison, not an ICA, and it grants no authority beyond what the order grants.

## 1. Scope of this review

- Canonical source after 055-a: root `ARCHITECTURE.md` (2026-11-09 edition,
  A-01..A-17, SAR-001..SAR-056), SHA-256
  `5ad0ab631696213432c8f513a80b3481fa28a8b0ab89641195ad38725e07db38` (93251
  bytes). The pre-edit accepted identity
  `4566e797b709b71f13b2929572a2d1145d15a5a7ab8b41db50ebfdab962628cd` (80910
  bytes) is preserved below as historical provenance, not a hash rewrite.
- Compact projection after 055-a: `ARCHITECTURE-for-agents.md`, SHA-256
  `f0bc75ecba257ad4c70cbec79e79754b4b803b882f6860cdf90f2a25a1ddbbf5` (42676
  bytes). The pre-055-a projection SHA-256
  `41c32e0b0d6427a173dfe0b722446ae8ee311f3880929db65ed0245309b3a59e` (36600
  bytes) is historical.
- `PLAN.md` after 055-a: SHA-256
  `f69a1a0c52d35abf1f72ee48e25aa3c2fab23fb6470cf298fa2020ad41eea0da` (28718
  bytes); pre-edit `8298ef941d02b05c304c48b46734ad678aff80b9ab4e62ca0814b6f03007277f`
  (23396 bytes) is historical.
- Unchanged by this order and byte-verified before any write:
  `docs/governance/GROUP-AUTHORIZATION-PROJECTION-REVIEW.md`
  `dc0085fe0b8c1a1ad4efd780bd9c1517258e5df49b3db662e2fb4c5c7986f5ca`;
  `docs/security-model.md`
  `7fcd7abf72a7c7c5e8db9dccaa47e9d281e4662a221caf3add6bf002d6c4d1f1`;
  `oap/coding-instructions/AGENTS.md`, `OAP-COMMUNICATION-coding-agent.md`,
  `oap/coding-instructions/SECURITY-CORE.md` and
  `oap/coding-instructions/TESTING-CORE.md` (unchanged).
- The projection embeds the current full-source SHA-256 identity and preserves
  the 2026-10-17 edition identity
  (`4566e797b709b71f13b2929572a2d1145d15a5a7ab8b41db50ebfdab962628cd`) and the
  initial projection source SHA-256 (`9e7c60e4...`) as historical provenance.
- The generation-1 context budget record remains archived at
  `docs/bootstrap/archive/CONTEXT-BUDGET.md` (byte ceilings 50000 total / 20000
  projection); its successors for the A-15 and A-16 targets are the archived
  record and `GROUP-AUTHORIZATION-PROJECTION-REVIEW.md`. This document is the
  successor for the A-17 target and reports the ceiling status honestly in
  section 4. It does not overwrite or renumber either prior record.

## 2. Human requirement / A-17 facet -> requirement ID -> compact clause mapping

Provenance note (honest scope): the raw human transcript (attributable message,
2026-11-09) is outside the coding read set. The strategy-authored H provenance
in order 055-a is the authorized record of that human scope, and this review
traces the three named product behaviors — restated verbatim in PLAN P-09 and
in root A-17 — to full and compact clauses. No transcript bytes were loaded or
quoted.

| Human requirement (2026-11-09) / A-17 facet (root A-17) | Requirement ID (root A-14 map) | Compact projection clause |
|---|---|---|
| Requirement 2 — "logged-in password change" / A-17 facet Logged-in own-password change: member-only CSRF-protected POST; current password required; normal validator set including the existing minimum length, no weakened path; active non-service-account human; current session continues, all other sessions for the account invalidated; no bearer/API mutation surface; no reset or forgotten-password flow; SAR-043/044 on the new surface | SAR-054 | `SAR-054 / Logged-in own-password change` + `Selected account onboarding target (A-17)` > Logged-in own-password change |
| Requirement 1 — "administrator-created user gets email with login data" / A-17 facet Operator SMTP onboarding and failure boundary: explicit operator enablement (standard Django email-backend settings + canonical configured HTTPS base URL); synthetic SMTP only in development, never a real relay or recipient; disabled/incomplete => no delivery claim and no active short-password account; enabled add commits the account inactive (pending onboarding) first, sends exactly one login-details email (canonical HTTPS URL, account email identifier, temporary password), activates only after SMTP accepts; failure stays inactive with nonsecret status; manual reissue rotates the previous credential; no ambiguous-send auto-retry; no plaintext persistence; no bodies/credentials in logs; links from canonical URL never Host; production-enabled relay requires TLS + bounded timeout; no queue/Celery/Gateway dependency; not a general mail system | SAR-055 | `SAR-055 / Operator SMTP onboarding and failure boundary` + `Selected account onboarding target (A-17)` > Operator SMTP onboarding and failure boundary |
| Requirement 3 — "prefilled random six-character password" / A-17 facet Six-character temporary admin creation and forced change: add GET prepopulates BOTH password controls with the same new CSPRNG six-character value; narrow temporary-only length exception, normal validators never globally weakened; expiry within 24h and no NEW login after expiry; successful login restricted to changing it before any member/management/Administration/session-API work; reissuance rotates; existing accounts unchanged (no backfill/retroactive exception/forced change); permissions, group grants, API token records and reservation domain services intact | SAR-056 | `SAR-056 / Six-character temporary admin creation and forced change` + `Selected account onboarding target (A-17)` > Six-character temporary onboarding credential |
| A-17 facet Controlled evolution of prior requirements: SAR-001–SAR-053 IDs and preservation retained; P-04/SAR-036 deferral of "OIDC/password reset/notifications" narrowed ONLY for admin-created onboarding email and logged-in own-password change, general OIDC/public reset/self-registration/general notifications remain deferred; normal validator baseline retained; SAR-014/040/043/044/053 applicability preserved; historical A-07 "members cannot change their own password" prose is baseline context, not a permanent prohibition | SAR-036 row (deferral), SAR-014, SAR-040, SAR-043, SAR-044, SAR-053 rows | Header scope line (A-17 listed) + `Selected account onboarding target (A-17)` > Retained exclusions; pre-existing compact rows unchanged (no rewrite) |
| A-17 facet Evidence and closure: focused tests per purpose (browser/CSRF password change; synthetic-SMTP accept/reject/reissue/fail-closed/plaintext-absence/URL-source/TLS-timeout negatives; temporary-credential prepopulation/expiry/forced-change/rotation/existing-accounts-unchanged; unchanged grants/tokens/reservation domain); standard five exact-head checks; meaningful Chromium flows/screenshots; fresh exact-revision independent ICA before any milestone-closure claim; not strategic self-certification or deployment authorization | SAR-054, SAR-055, SAR-056 rows (each UNPROVEN); SAR-038 (ICA facet) | `Selected account onboarding target (A-17)` > header UNPROVEN sentence + Retained exclusions (ICA/closure) + each new row's UNPROVEN classification in root A-14 |

Coverage statement: every normative facet paragraph of root A-17 maps to at
least one stable requirement ID above, and every new ID (SAR-054–SAR-056)
appears as a compact clause in the projection. The three new full-source rows
were inserted after SAR-053 (before A-15); no existing row, ID or historical
prose was deleted or renumbered. The `Selected account onboarding target
(A-17)` projection clause carries the A-17 executor obligations directly so
the full architecture and A-17 remain reference-only for coding.

## 3. Strategy-only decisions (explicit; properly scoped future D0 decisions, each decided only when its objective is strategy-issued)

1. Exact route path, form field names and help-text wording of the member
   password-change surface (purpose 056, SAR-054).
2. Exact email-backend setting names/shape (host, port, credentials, sender,
   TLS/STARTTLS, timeout) and the canonical HTTPS base-URL setting name within
   `config/settings/` (purpose 057, SAR-055).
3. Exact persistence/representation of the pending-onboarding state, the
   nonsecret delivery status and the manual reissue control (purpose 057,
   SAR-055).
4. Exact representation/field choice for the temporary-credential state and
   24h expiry clock, and the forced-change gate mechanics (purpose 058,
   SAR-056).
5. OpenAPI description wording where any API surface changes (purposes
   056–058; none is expected for this target).
6. Issuance, ordering, base and PR mode of every future development order in
   the PLAN P-09 purpose sequence 056–059 (DRAFT until strategy issues each
   order; no PR/SHA exists).
7. Disposition of the measured context byte growth reported in section 4
   (accept the new measured set, or order a later faithful redistillation).
8. Human-only (not strategy): milestone acceptance, release, real SMTP
   relay/recipient/credential, host/exposure/DNS/TLS/firewall, identity
   administration and deployment (D2).

## 4. Measured context (exact UTF-8 bytes, measured on the working-tree files at 055-a report time)

Transitive mandatory coding read set per the generation-1 convention (archived
`docs/bootstrap/archive/CONTEXT-BUDGET.md`): the routine coding read set
excluding the active order and product code:

| Component (installed path) | Exact bytes | Generation-1 ceiling |
|---|---:|---:|
| `AGENTS.md` | 1058 | 2048 |
| `oap/coding-instructions/AGENTS.md` | 6403 | 12000 |
| `ARCHITECTURE-for-agents.md` | 42676 | 20000 (exceeded; see below) |
| `OAP-COMMUNICATION-coding-agent.md` | 4105 | 10000 |
| `oap/coding-instructions/SECURITY-CORE.md` | 1410 | — |
| `oap/coding-instructions/TESTING-CORE.md` | 1947 | — |
| **Total (excluding order/code)** | **57599** | **50000 (exceeded by 7599 bytes)** |

Ceiling status (honest): the archived ceilings are the 2026-10-04 (A-15)
generation-1 budget convention; the A-16 target already exceeded them (51047
total, 36124 projection) and that overage was strategy-disposed as reported.
Order 055-a's acceptance clause 4 mandates that the A-17 executor obligations
and retained exclusions be carried directly in the compact projection and that
the routine read set be measured and reported. After faithful recomposition
(header scope/digest update, three new SAR clauses, one new A-17 target
clause; no truncation of any obligation), the projection is 42676 bytes
(+6076 over the A-16 state) and the routine read set total is 57599 bytes
(+6552 over the A-16 state). Both remain above the archived A-15-era ceilings;
this overage is reported, not hidden, and its disposition is strategy-owned
(section 3, item 7). The 055-a order file itself is order-scoped and not part
of the routine transitive set, per the generation-1 convention.

Tokens: **UNMEASURED** — no qualified tokenizer for the configured model was
run; character estimates are not presented as exact counts (same convention as
generation 1 and the A-16 record).

## 5. Method and limitations

- The projection was recomposed after the full canonical source was authored;
  the embedded full-source SHA-256
  (`5ad0ab631696213432c8f513a80b3481fa28a8b0ab89641195ad38725e07db38`) was
  computed from the post-edit `ARCHITECTURE.md` bytes.
- Semantic comparison (facet-by-facet against root A-17 and the three new
  A-14 rows) was performed deliberately. Against the pre-055-a projection
  (`41c32e0b0d6427a173dfe0b722446ae8ee311f3880929db65ed0245309b3a59e`), the
  only changed pre-existing clauses are: the header source/scope/digest lines
  (edition and identity update, including the A-17 reference-only sentence and
  the new-rows UNPROVEN sentence); no pre-existing SAR clause was rewritten,
  deleted or renumbered. All other pre-existing clauses are byte-identical. A
  structural hash alone is not semantic proof; this comparison is the recorded
  semantic check, and it is not an ICA and certifies nothing at runtime.
- No hidden mandatory read of full architecture, PLAN or history is
  introduced: the routine read set is exactly the section 4 table plus the
  exact active order when one exists; root A-15, A-16 and A-17 are
  reference-only for coding.
- No product, runtime, test, dependency, migration, deployment or bootstrap
  byte was changed by this order (verified by git diff against base
  `1eade24e2032b8525d3b0151daaca38830e24d03`); no CRITICAL change.
- All SAR-054–SAR-056 rows are initially UNPROVEN; they are selected-target
  obligations, not implemented controls, and remain so until a fresh isolated
  ICA at the exact merged revision.
- Limitations: the compact clauses are faithful condensations of the A-17
  facets — the full facet wording remains in root A-17 (reference only) and in
  the section 2 mapping; byte figures are measured on committed bytes; tokens
  remain UNMEASURED.

## 6. Accepted-vs-candidate changes

- The 055-a order metadata `source_hashes` bind the accepted PRE-EDIT source;
  all five were verified byte-identical before any write (section 1).
- Candidate (post-edit) identities: `ARCHITECTURE.md`
  `5ad0ab631696213432c8f513a80b3481fa28a8b0ab89641195ad38725e07db38` (93251
  bytes); `PLAN.md`
  `f69a1a0c52d35abf1f72ee48e25aa3c2fab23fb6470cf298fa2020ad41eea0da` (28718
  bytes); `ARCHITECTURE-for-agents.md`
  `f0bc75ecba257ad4c70cbec79e79754b4b803b882f6860cdf90f2a25a1ddbbf5` (42676
  bytes); plus this review and the order/pointer/report files.
- This review's committed byte count is reported at the report (measured on
  the committed file before publication).
