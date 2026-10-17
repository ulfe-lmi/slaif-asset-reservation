# GROUP-AUTHORIZATION-PROJECTION-REVIEW — A-16 coverage and measured coding context

Order: 047-a (2026-10-17). This is a **semantic coverage record and measured context
record** for the selected group-authorization target. It is a deliberate semantic
comparison, not an ICA, and it grants no authority beyond what the order grants.

## 1. Scope of this review

- Canonical source after 047-a: root `ARCHITECTURE.md` (2026-10-17 edition),
  SHA-256 `4566e797b709b71f13b2929572a2d1145d15a5a7ab8b41db50ebfdab962628cd`. The
  pre-edit accepted identity
  `2d300121b37b62eeeb0676764d5d82739adf006a13e70d35ff62b84c59f7eb43` is preserved below
  as historical provenance, not a hash rewrite.
- Compact projection after 047-a: `ARCHITECTURE-for-agents.md`,
  SHA-256 `fa3f9e5ffd4a466fb727c42145a6671a249dd959c5320e9b35fbc414eccbe4cb`. The
  pre-047-a projection SHA-256
  `a0a31be7b4efbf9f61c76488888b081cc0db296ff75c8eaae74b712b72ac32a6` is historical.
- `PLAN.md` after 047-a: SHA-256
  `2c856ae47ec985b953a8d26edbe2c07fd343833a41bc45aefcd304a7e67c1432`; pre-edit
  `d30d89981907dd2af475b7a5f27aa0715defed3a78c6431b76e7e05204ef833f` is historical.
- New guide after 047-a: `docs/authorization.md`, SHA-256
  `3131df14d1f3da9cbde41cb1a1c32a2db7939b6e01538bbb801f4cdadc30f6e3`.
- Pre-edit accepted-source identities, as bound by the 047-a order metadata and verified
  byte-identical before editing: `ARCHITECTURE.md`
  `2d300121b37b62eeeb0676764d5d82739adf006a13e70d35ff62b84c59f7eb43`; `PLAN.md`
  `d30d89981907dd2af475b7a5f27aa0715defed3a78c6431b76e7e05204ef833f`;
  `ARCHITECTURE-for-agents.md`
  `a0a31be7b4efbf9f61c76488888b081cc0db296ff75c8eaae74b712b72ac32a6`;
  `oap/coding-instructions/AGENTS.md`
  `1611e9700de5b311deeb45460162464f7f24462e74790dddfcec2bb016b30394` (unchanged by this
  order).
- The projection embeds the current full-source SHA-256 identity and preserves the
  initial projection source SHA-256 (`9e7c60e4...`) as historical provenance.
- The generation-1 context budget record remains archived at
  `docs/bootstrap/archive/CONTEXT-BUDGET.md` (byte ceilings 50000 total / 20000
  projection); this document is its successor for this target and reports the ceiling
  status honestly in section 4. It does not overwrite or renumber the archived record.

## 2. A-16 facet -> requirement ID -> compact clause mapping

Provenance note (honest scope): the raw human transcript (request 2026-10-17, sections
1–11) is outside the coding read set. The strategy-authored A-16 payload in order 047-a
is the authorized record of that human scope (order provenance H), and this review traces
the A-16 facet paragraphs — which carry sections 1–11 per that provenance — to full and
compact clauses. No transcript bytes were loaded or quoted.

| A-16 obligation facet (root A-16, 2026-10-17) | Requirement ID (root A-14 map) | Compact projection clause |
|---|---|---|
| Controlled evolution of prior requirements: SAR-001–SAR-047 IDs and preservation retained; SAR-008 adds booking capability + exact-asset eligibility; SAR-010 replaces implicit staff lifecycle authority with the relevant explicit capability, owner rights preserved; SAR-012 preserves owner-only routes and permits only the named cross-user read surface; SAR-013 replaces blanket staff admission with explicit capabilities; SAR-014/016/017 add only the read-all scope and separate compatible read interface, existing tokens/endpoints never widen; SAR-018/019/021 unchanged; SAR-036 deferral superseded only by A-16; A-04/A-07/A-08/A-09/A-15 staff-only/group-deferred statements are historical baseline context | SAR-008, SAR-010, SAR-012, SAR-013, SAR-014, SAR-016, SAR-017, SAR-018, SAR-019, SAR-021, SAR-036 rows | Revisions with explicit "A-16 (selected target)" applicability sentences in the SAR-010, SAR-012, SAR-013, SAR-016 and SAR-036 compact clauses; all other 42 pre-existing clauses byte-identical; no row deleted |
| One additive grant system: Django Group/membership + individual permissions; union across groups and individual assignments; no parallel membership, no hardcoded operator group names, no explicit deny; ten documented reservations-namespace application permissions (book_assets; view_all_reservations; cancel_others_reservations; release_others_reservations; view_booking_policies; manage_booking_policies incl. read; view_maintenance_blackouts; manage_maintenance_blackouts incl. read; view_audit_history; export_audit_history), distinct from Administration model View permissions; active non-service-account human required; staff = /admin/ admission only; superusers keep Django semantics + protected-record restrictions + exact-asset eligibility; server-side enforcement at endpoints and shared services; partial-capability management landing without unauthorized counts/data/links/actions; no incidental cross-owner disclosure; protected Administration records read-only/service-backed | SAR-048 | `SAR-048 / Additive application capabilities` + `Selected group authorization target (A-16)` > One additive grant system |
| Booking eligibility: explicitly unrestricted or group-restricted assets; restricted requires membership in at least one allowed existing group; restricted with no allowed groups fails closed; check only the booked asset, no parent inheritance; all existing assets migrate unrestricted; shared authoritative browser/bearer check around the existing reservation service; token creation also requires its action scope and the owner's current capability/membership; active/reservable/exclusive, UTC/DST, policies/counters, PostgreSQL exclusion/locking and atomic audit unchanged; assets browsable with eligibility shown, no sensitive account/group metadata; access changes never rewrite existing bookings; owners retain list/inspect/cancel/release of accepted reservations after losing capability or membership | SAR-049 | `SAR-049 / Exact-asset booking eligibility` + `Selected group authorization target (A-16)` > Booking eligibility |
| Separate cross-user read surfaces: All reservations browser view requires view_all_reservations; existing validated asset, status/lifecycle, time filters and pagination; owner pages private; viewers see owner, asset, original times, effective end, status and lifecycle; mutation controls only for the corresponding capability; forged mutations denied; policy/blackout/audit capabilities do not imply read-all; overlap previews without read-all show only safe confirmation information | SAR-050 | `SAR-050 / Explicit cross-user browser visibility` + `Selected group authorization target (A-16)` > Separate cross-user read (browser facet) |
| Explicit read-all bearer authority: reservations:read_all scope; cross-user list/detail require BOTH scope AND current owner view_all_reservations, rechecked at use; reservations:read owner-only even for staff/superusers; existing scope records never auto-change; issuance refuses authority-exceeding read-all/create scopes; expiry/revocation/activity/service-account and shared abuse controls apply; group/permission removal effective on subsequent requests, no process-global grant cache; no cross-user bearer mutation surface; minimal explicit cross-user representation (reservation/asset UUID, safe asset identity, owner UUID + external_identifier null when unset, aware original start/end, effective_end, status/lifecycle, release/cancellation timestamps, unambiguous blocking/effective interval semantics) excluding email/display/profile/admin flags, secrets, private locators, unrelated metadata and private free text; owner representations compatible | SAR-051 | `SAR-051 / Explicit read-all bearer authority` + `Selected group authorization target (A-16)` > Separate cross-user read (bearer facet) + Current API boundaries target note |
| External identifier: optional external_identifier on User; opaque case-sensitive string, at most 128 characters; numeric strings and leading zeroes preserved; populated values unique; unset NULL, multiple users may be unset; no inference or backfill; admin-only edit in existing Administration; member profile and bearer input cannot modify it; neither a credential nor Linux UID validation; external enforcer owns account mapping, enforcement, polling, caches/refresh and outages; no SSH/PAM, synchronization, workload/container execution, GPU allocation or automatic machine login grants; reservation entitlement is not login authority; cancelled rows do not block, confirmed/released preserve [start,effective_end) aware timestamps | SAR-052 | `SAR-052 / Opaque external user identifier` + `Selected group authorization target (A-16)` > External identifier |
| Deliberate upgrade: inventory every current management route/action and map its grant; explicit migrations and setup docs preserve users/groups/reservations/policies/audits/tokens and old individual permissions; one-time baseline booking-permission assignment to existing non-service-account users (exact scope documented, tested against a populated pre-upgrade database); new accounts receive no automatic grants or privileged-group membership; current staff access NOT silently retained through is_staff (dry-run-first explicit idempotent operator setup); never infer read-all from Administration View permissions; deployed DB changes operator-owned with backup/rollback guidance; migrations tested only on owned synthetic databases; example group names never authorization constants | SAR-053 | `SAR-053 / Authorization upgrade and qualification` + `Selected group authorization target (A-16)` > Deliberate upgrade |
| Evidence and closure: focused positive/negative tests per purpose (direct endpoint/service denial, nonstaff partial grants, additive multi-group and individual grants, staff/no-grant and superuser boundaries, viewer mutation denial, browser/API asset parity, removal while tokens stay valid, missing scopes, owner-only tokens for privileged owners, inactive/service accounts, retained owner lifecycle access, opaque/unique/unset identifiers, minimal-response canaries, unchanged conflicts/lifecycle/audit/idempotency); meaningful Chromium flows/screenshots for new controls; upgrade tests; generated OpenAPI; docs links; full normal exact-head checks; final independent audit starts from this human scope, full current architecture and the exact merged revision, maps all applicable stable requirements, records limits; not strategic self-certification or deployment authorization | SAR-053 (qualification facet); SAR-038 (ICA facet) | `Selected group authorization target (A-16)` > Evidence + header UNPROVEN classification for SAR-048..SAR-053 |

Coverage statement: every normative facet paragraph of root A-16 maps to at least one
stable requirement ID above, and every new ID (SAR-048–SAR-053) appears as a compact
clause in the projection. The six new full-source rows were inserted before A-15
verbatim from the order; no existing row, ID or historical prose was deleted or
renumbered. The `Selected group authorization target (A-16)` projection clause carries
the A-16 executor obligations directly so the full architecture and A-16 remain
reference-only for coding, and `docs/authorization.md` carries the labeled
selected-target guide.

## 3. Strategy-only decisions (explicit; properly scoped future D0 decisions, each decided only when its objective is strategy-issued)

1. Exact codename, arguments and output contract of the dry-run-first idempotent
   legacy-staff capability setup command/procedure (purpose 048, SAR-053).
2. Placement and exact field set of the reservation-eligibility configuration within
   existing asset administration (purpose 049, SAR-049).
3. Concrete route paths and filter parameter names of the new All reservations browser
   view and cross-user list/detail API surfaces (purposes 050/051, SAR-050/SAR-051).
4. Token-issuance UX and exact stable problem codes for authority-exceeding read-all and
   create scope issuance (purpose 051, SAR-051).
5. OpenAPI description wording for the new cross-user read surfaces (purpose 051,
   SAR-051).
6. Issuance, ordering, base and PR mode of every future development order in the PLAN
   P-08 purpose sequence 048–052 (DRAFT until strategy issues each order; no PR/SHA
   exists).
7. Disposition of the measured context byte growth reported in section 4 (accept the new
   measured set, or order a later faithful redistillation).
8. Human-only (not strategy): milestone acceptance, release, real Internet exposure,
   DNS/TLS/firewall, identity, secrets and private data (D2).

## 4. Measured context (exact UTF-8 bytes, measured on the working-tree files at 047-a report time)

Transitive mandatory coding read set per the generation-1 convention (archived
`docs/bootstrap/archive/CONTEXT-BUDGET.md`): the routine coding read set excluding the
active order and product code:

| Component (installed path) | Exact bytes | Generation-1 ceiling |
|---|---:|---:|
| `AGENTS.md` | 1058 | 2048 |
| `oap/coding-instructions/AGENTS.md` | 6403 | 12000 |
| `ARCHITECTURE-for-agents.md` | 36124 | 20000 (exceeded; see below) |
| `OAP-COMMUNICATION-coding-agent.md` | 4105 | 10000 |
| `oap/coding-instructions/SECURITY-CORE.md` | 1410 | — |
| `oap/coding-instructions/TESTING-CORE.md` | 1947 | — |
| **Total (excluding order/code)** | **51047** | **50000 (exceeded by 1047 bytes)** |

Ceiling status (honest): the archived ceilings are the 2026-10-04 (A-15) generation-1
budget convention. Order 047-a's acceptance clause 3 mandates that ALL A-16 executor
obligations (eligibility, every capability boundary/partial visibility, scope + current
grants, minimal owner data, explicit upgrades, no execution/deployment) be carried
directly in the compact projection, and that the routine coding read set be measured and
reported. After faithful redistillation (clause-level revision plus the six new SAR
clauses and the A-16 target clause; no truncation of any obligation), the projection is
36124 bytes and the routine read set total is 51047 bytes. Both exceed the archived
A-15-era ceilings (projection by 16124 bytes; total by 1047 bytes). This overage is
reported, not hidden; its disposition is strategy-owned (section 3, item 7). The 047-a
order file itself is order-scoped and not part of the routine transitive set, per the
generation-1 convention.

Tokens: **UNMEASURED** — no qualified tokenizer for the configured model was run;
character estimates are not presented as exact counts (same convention as generation 1).

## 5. Method and limitations

- The projection was recomposed after the full canonical source was authored; the
  embedded full-source SHA-256 was computed from the post-edit `ARCHITECTURE.md` bytes.
- Semantic comparison (clause-by-clause against root A-14/A-16) was performed
  deliberately. Against the pre-047-a projection
  (`a0a31be7b4efbf9f61c76488888b081cc0db296ff75c8eaae74b712b72ac32a6`), the only
  changed pre-existing clauses are: the header identity/scope lines; the SAR-010,
  SAR-012, SAR-013, SAR-016 and SAR-036 rows (explicit A-16 applicability sentences
  appended); and the appended target note in Current API boundaries. All other
  pre-existing clauses are byte-identical. This is not an ICA and certifies nothing at
  runtime.
- No hidden mandatory read of full architecture, PLAN or history is introduced: the
  routine read set is exactly the section 4 table plus the exact active order when one
  exists; root A-15 and A-16 are reference-only for coding.
- No product, runtime, test, dependency, migration, deployment or bootstrap byte was
  changed by this order (verified by git diff against base
  `dad6e29d4f8e4fd941843b230474d35dafb69d1a`); no CRITICAL change.
- All SAR-048–SAR-053 rows are initially UNPROVEN; they are selected-target
  obligations, not implemented controls, and remain so until a fresh isolated ICA at the
  exact merged revision.
- `docs/authorization.md` is a clearly labelled SELECTED TARGET / NOT IMPLEMENTED guide;
  it publishes no operator commands or endpoints as existing, and carries no product
  history ledger.
- Limitations: the compact clauses are faithful condensations of the A-16 facets — the
  full facet wording remains in root A-16 (reference only) and in the section 2 mapping;
  byte figures are measured on committed bytes; tokens remain UNMEASURED.

## 6. Accepted-vs-candidate changes

- The 047-a order metadata `source_hashes` bind the accepted PRE-EDIT source; all four
  were verified byte-identical before any write (section 1).
- Candidate (post-edit) identities: `ARCHITECTURE.md`
  `4566e797b709b71f13b2929572a2d1145d15a5a7ab8b41db50ebfdab962628cd` (80910 bytes);
  `PLAN.md` `2c856ae47ec985b953a8d26edbe2c07fd343833a41bc45aefcd304a7e67c1432`
  (19643 bytes); `ARCHITECTURE-for-agents.md`
  `fa3f9e5ffd4a466fb727c42145a6671a249dd959c5320e9b35fbc414eccbe4cb` (36124 bytes);
  `docs/authorization.md` `3131df14d1f3da9cbde41cb1a1c32a2db7939b6e01538bbb801f4cdadc30f6e3`
  (9052 bytes); plus this review and the order/pointer/report files.
- This review's committed byte count: 17069 (measured on the committed file).
