<!-- OAP-META
{
  "kind": "report",
  "id": "041-a",
  "order_path": "oap/orders/041-a-import-integrity.md",
  "order_sha256": "e4239087fe65fc65887da5cf7f6dab9fe8d2c438d078c725eceaf111d7341f23",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 81,
  "pr_number": 82,
  "branch": "codex/81-oap-041-a-import-integrity",
  "implementation_head": "d2571a6f1cf46bc0f92e003c5c2d173229d995d0",
  "base_sha": "cec4ed7c59dad30e841745a4842af397f40f3e0b",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "d2571a6f1cf46bc0f92e003c5c2d173229d995d0",
    "runs": [
      {
        "run_id": 37397413122,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "test": "success",
          "security": "success",
          "container": "success"
        }
      },
      {
        "run_id": 37397412586,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      }
    ]
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# Import integrity failures and atomic rollback

Implementation head SHA: d2571a6f1cf46bc0f92e003c5c2d173229d995d0
Report publication commit: SELF

Result: COMPLETE for bounded ICA F2 correction. ROOT implemented/reviewed directly
under the human takeover instruction; no coding client restarted. This is not
independent re-audit, milestone closure, release or real deployment authority.

## Change and real evidence

The importer catches the named reservation exclusion only at reservation.save,
then converts that insert-specific signal to the existing conflict category.
Audit/import-record/batch integrity errors propagate through the complete outer
transaction. Earlier successful reservations, audits, provenance and the APPLIED
batch roll back together. Ordinary booking's named matcher is reused unchanged;
no generic catch around all persistence can silently turn a fault into success.

Seven real PostgreSQL regressions qualify the boundary: actual named reservation
exclusion remains a conflict; actual audit and import-record CHECK failures in
one- and two-row batches remain IntegrityError and leave zero batch/domain/audit/
provenance artifacts. An audit CHECK deliberately named like the reservation
exclusion also propagates, proving insert location matters rather than name alone.
Scheduling seams are controlled; persistence/constraints are not mocked.

Before implementation: six negative cases failed with DID NOT RAISE IntegrityError,
one named-exclusion case passed (3.15s, owned source5ert4cll). After correction:
new integrity cases plus existing import, real import concurrency and ordinary
reservation services: **88 passed,10.31s** (owned sourcek28w633d). Initial lint
import/line formatting errors were corrected before the frozen head; final lint,
format, mypy134 source files and whitespace checks passed.

At the literal final implementation head: **quality/test/security/container/
oap-harness SUCCESS**, CI37397413122 and OAP37397412586. Testjob112056572231:
**971 passed,1 warning,579.20s**. This is the full standard suite, including
PostgreSQL concurrency/rollback, real browsers, proxy/TLS/abuse, Gunicorn held
clients, default policy, branding, recovery and governance checks; security
includes pip-audit and container build/production configuration/static checks.
No unchanged full suite was repeated locally; final CI supplied it.

The initial full independent audit at cec4ed7 is preserved byte-for-byte at
docs/audit/reports/M-INTERNET-UX-PILOT-cec4ed7.md, SHA256
2c148bbb6213a34fddb78299da3b2b0a35a53c03cb825aa6d0c1ec04c73c3305.
It remains historical evidence for that exact audited revision; its results
were not rewritten after this code change. Its remaining F1 lock inversion and
F3 cached-image ownership qualification require separate bounded corrections.
O1 readiness CLI diagnostics is an optional observation, not hidden extra scope.
After all repairs, a fresh full architecture-to-current-main audit remains
mandatory; checking only the repair queue cannot establish closure.

## Scope, publication and limits

Five implementation paths: importer.py, the new integrity regression module,
unchanged frozen audit bytes, ordered active pointer and immutable order. No
schema/model/migration/dependency/UI/API/permission/inventory/runtime configuration
or lock-order changes. Architecture/PLAN/projection/law bytes remain unchanged.
All product operations used owned source/PG17/minimal explicit environment and
exact cleanup. No real exports/data/secrets/hosts/DNS/TLS/firewall/lab jobs used.

Two Git pushes were rejected with remote server500 during GitHub incident
2kxnqcxcrr7f; the initial PR create failed because no branch was published.
Local commit was preserved unchanged. A bounded same-head retry after one hour
succeeded; actual remote head and PR82 were verified. No force push, fake PR,
source reset, runner/protection change or check waiver was used. Publication
failures are not product passes/failures. Report-head CI is not yet observed at
authoring and remains mandatory before conditional expected-head merge.

Strongest objection: broad exception handling could disguise corruption or break
legitimate import reporting. Narrow insert-specific signaling and real named/
unrelated/same-named-audit/whole-batch negatives address the demonstrated defect;
existing behavior is covered by focused and full CI. Known lock/cache findings
remain visible. No real exposure or target-completion decision is supplied.

DHA operation: NONE.
