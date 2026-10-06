<!-- OAP-META
{
  "kind": "report",
  "id": "044-a",
  "order_path": "oap/orders/044-a-service-account-guidance.md",
  "order_sha256": "eab197217147804bda00dd82ad6530d18f285e66a9bdbe1b4ad90b8ddd41eb2e",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 87,
  "pr_number": 88,
  "branch": "codex/87-oap-044-a-service-account-guidance",
  "implementation_head": "1c46f08252e522a77ede71ded42e009bd6c79400",
  "base_sha": "7877fbe82809c082111c8dcfe0ab47aa8620e508",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "1c46f08252e522a77ede71ded42e009bd6c79400",
    "runs": [
      {
        "run_id": 37514619957,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      },
      {
        "run_id": 37514619945,
        "workflow": "CI",
        "jobs": {
          "security": "success",
          "test": "success",
          "quality": "success",
          "container": "success"
        }
      }
    ]
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# Current service-account guidance

Implementation head SHA: 1c46f08252e522a77ede71ded42e009bd6c79400
Report publication commit: SELF

ROOT directly executed this bounded accuracy repair under human takeover;
no coding client restarted. COMPLETE is this order, not full independent
milestone closure, human acceptance or exposure authorization.

## Acceptance and evidence

1. The service-account checkbox now explains its actual current effect: enabling
   it blocks member/administration sign-in and API token issuance/use; service-
   account API support is absent, and automation uses an active human owner's
   scoped token. Only this help value changed in application source.
2. The modified rendered guidance regression failed against old text: **1 failed
   in1.74s**, owned source2pqpioif. It now couples accessible help to actual human
   token success, a real administration flag-change POST, existing bearer401/
   invalid_token and new issuance TOKEN_OWNER_INVALID. Stored password and other
   existing administrator assertions remain. Focused form/token suite: **91 passed**.
3. Initial combined focus:91 passed/1 browser failure14.02s nq2eqmbx. Failure
   was the new screenshot expression treating Playwright's string output_path
   as a Path, not a product boundary. Only its two path expressions were fixed;
   focused real Chromium administration-user form then **1 passed in7.46s**
   xtdxp25q. Desktop1440/mobile390 help is visible and associated, actions/focus/
   page overflow checks retained. ROOT actually opened both field screenshots
   in fresh owned /tmp/sar044-visual-_k9u3txh; readable wrapping/no clipping.
   No password/token/cookie/CSRF/verifier/private identity was captured.
4. Full prior fresh47-row ICA at7877fbe is preserved byte-identically in
   docs/audit/reports/M-INTERNET-UX-PILOT-7877fbe.md, digest
   88c2edbcf3983276c2e3aa035817ae724bc836bb6ec3ae67b85dcba8bf8f0197.
   Its46IMPLEMENTED/1PARTIAL result is not rewritten as success. Optional static
   prerequisite/readiness output suggestions are not implemented. Structural
   check with dynamic47-row requirements JSON passed, only structurally.
5. Exact implementation CI37514619945 and OAP37514619957: all5 SUCCESS.
   Full testjob112444230188: ================== 996 passed, 1 warning in 483.96s (0:08:03) ==================
   Exact implementation CI is filled from actual observations in metadata.
   Ruff/format/mypy134/diff checks passed. No unchanged full local rerun;
   standard exact-head CI supplies required full/security/container/OAP checks.
   Report-head CI is not yet observed at authoring and remains mandatory.

## Scope, objection and remaining gate

Six implementation paths: one admin help mapping, two regression test files,
immutable prior independent audit and exact order/active pointer. No token/
authentication/domain/backend/model/schema/migration/API/runtime/Compose/
dependency/theme/inventory/architecture/projection/law bytes changed. All product
checks used disposable source, verified owned PG17 and minimal role-cleared child
environments. No real D2/data/identity/secrets/hosts/DNS/TLS/firewall/lab actions.

Strongest reason against change: the conceptual machine-account description
could have expressed future intent. Accurate current help and explicit present
unsupported effect avoid promising that feature or quietly changing rights;
actual positive/negative token behavior and enforcing-source byte identity pin it.

After accepted merge, a NEW fresh FULL architecture-to-current-main ICA remains
mandatory. This report does not self-reclassify SAR-044 or close only the text
queue; all47 rows, evidence freshness, publication and final exact-head quiescence
remain. Human alone owns milestone acceptance and real exposure authorization.

DHA operation: NONE.
