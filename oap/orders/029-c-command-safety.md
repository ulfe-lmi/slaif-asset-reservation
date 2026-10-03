<!-- OAP-META
{
  "id": "029-c",
  "round": "c",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "state": "FINAL",
  "base_sha": "f406c612f52f64a50f0a145b27a7f580838c7287",
  "issue_number": 57,
  "branch": "codex/57-oap-029-a-product-documentation",
  "pr_mode": "AMEND",
  "previous_round": "029-b",
  "pr_number": 58,
  "allowed_paths": [
    "INSTALL.md (exact patch below only)",
    "docs/README.md (two labels only)",
    "oap/orders/029-c-command-safety.md",
    "oap/active",
    "oap/reports/029-c-command-safety.md"
  ],
  "forbidden_resources": [
    "application/source/migrations/tests/dependencies/lockfile/Dockerfile/Compose/settings/workflow/inventory changes",
    "canonical PLAN/ARCHITECTURE/CRITICAL and immutable prior audit/order/report/history changes",
    "real deployment/secrets/private data/SmartScheduling/lab/Neumann/DNS/TLS/firewall/public exposure",
    "other issues, unrelated branches, merge/auto-merge/protection changes",
    "auth copying or raw credential/user data in output"
  ],
  "decision_class": "D0",
  "requirements": [
    "SAR-002",
    "SAR-016",
    "SAR-022",
    "SAR-023",
    "SAR-024",
    "SAR-025",
    "SAR-027",
    "SAR-031",
    "SAR-032",
    "SAR-033",
    "SAR-036",
    "SAR-037",
    "SAR-038"
  ],
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "8483a070026f382bb9b698e9346f3cb33f7dea44f8190b231431585986ebb17d",
    "PLAN.md": "d03eb29713cfbdb7e227413618396e6bb2a7a08749225979c3055dacfd461d06"
  }
}
-->

# 029-c — Final operator-command safety corrections

FINAL. Same objective29, issue57, PR58 and branch. D0; docs only.

## Goal / provenance

H: human documentation-productization request 2026-10-03, INSTALL runnable/verified commands, safe restore and scope neutrality; normal correction loop authorized. A: S-06/S-12/S-16/S-19, SAR-023/024/027/032/033/038. E: exact 029-b implementation daa3a332a125adee5a0191430bea8a1e5bed0ecc, report f3594c7ca01ad22cc8d8406aec2d3b31c55a99b2 (verify_report3/3, remote PR58 bound). Strategy finds that angle brackets in unquoted hostname/previous-image examples are shell redirection syntax; the restore block has a do-not-restart comment but no shell failure guard; docs index mislabels CRITICAL as invariants rather than deferred human adjudication. These small fixes finish this same documentation objective. I: no milestone closure or new ICA. C: known D0 documentation defects, no all-five CRIT dilemma.

## Base / ordered reads

Main remains f406c612f52f64a50f0a145b27a7f580838c7287. Resume same branch at f3594c7ca01ad22cc8d8406aec2d3b31c55a99b2. Compact coding set, this order, only affected INSTALL sections and docs-index labels; prior report metadata/result as needed. No broad source/history reread or dependency research. Security failure is already established and remains outside scope.

## Scope and numbered acceptance

1. Apply exactly the unified patch below. Do not editorially rewrite unrelated paragraphs. Prompted quoted operator values replace shell-angle-bracket commands; Bash/Git/curl prerequisites stated; restore AND-chain prevents restart if stop/copy/restore/operational-check fails. Two specialist index labels corrected.
2. Verify bash syntax of the changed command blocks and a bounded TEMPORARY shell harness with a synthetic docker function: injected copy/pg_restore/operational-check failures must never call start; successful path must call start only last. This proves shell control flow only; no new restore claim and no real DB/restore/secret/host access. Verify quoted host/tag substitutions in a scratch shell; no public HTTPS probe or real image retag needed. No repository tests/source edits. Link targets/headings unchanged, but run cheap link/anchor check, ledger sweep and git diff --check.
3. Exact diff since b is only the two docs and c orchestration bytes. Product, lockfile, config, migrations, tests, canonical sources, all a/b orders and reports unchanged. Reuse previously named realPG17 quickstart/rehearsal evidence only under byte identity; no rerun of unchanged expensive local suites.
4. Same PR58, Closes#57, concise final scope/verification plus unresolved security blocker. Use gh api REST with a JSON payload file for PR-body update if gh pr edit hits the known deprecated Projects GraphQL field; do not retrieve credentials into command-line arguments. Observe all5 actual implementation-head checks to completion, then truthful PARTIAL/BLOCKED report if security fails. Never waive it, update urllib3, or claim all-green. Capture actual report-head ancestry and remote identity, signal response FIFO and EXIT. No more mutation after report publication.

## Exact patch

```diff
--- a/INSTALL.md
+++ b/INSTALL.md
@@ -43,6 +43,7 @@
 
 - A Linux host (`x86_64`/amd64, see section 1).
 - Docker Engine with the Docker Compose v2 plugin.
+- Git, curl, and Bash for the commands below.
 - Outbound connectivity to pull `python:3.13-slim` (pinned by digest in the
   `Dockerfile`) and the PostgreSQL service image (pinned by digest in the
   Compose files).
@@ -235,10 +236,13 @@
     secure cookies). Nginx remains acceptable if already operated
     institutionally; see `docs/deployment.md` section 8.
 
-13. **Verify HTTPS end to end** from outside the host:
+13. **Verify HTTPS end to end** from outside the host. Enter the approved
+    service hostname (without a scheme or path); reuse it for the checks
+    below in the same shell:
 
     ```bash
-    curl -fsS https://<your-hostname>/health/live
+    read -r -p "Approved service hostname: " SAR_SERVICE_HOST
+    curl -fsS "https://${SAR_SERVICE_HOST}/health/live"
     ```
 
 14. **`/health/live`** returns HTTP 200 (liveness; no database dependency).
@@ -253,7 +257,7 @@
     401 as a curl failure):
 
     ```bash
-    curl -sS -o /dev/null -w '%{http_code}\n' https://<your-hostname>/api/v1/me/
+    curl -sS -o /dev/null -w '%{http_code}\n' "https://${SAR_SERVICE_HOST}/api/v1/me/"
     # expected: 401 (body intentionally not captured here)
     ```
 
@@ -344,16 +348,17 @@
 restarted after a failed restore:
 
 ```bash
-docker compose -f compose.production.example.yaml stop app
+# Replace YYYYMMDD with the date of the selected, verified backup.
+# Each command runs only if the preceding command succeeded.
+docker compose -f compose.production.example.yaml stop app &&
 docker compose -f compose.production.example.yaml cp \
-  /backups/slaif-YYYYMMDD.dump db:/tmp/slaif-YYYYMMDD.dump
+  /backups/slaif-YYYYMMDD.dump db:/tmp/slaif-YYYYMMDD.dump &&
 docker compose -f compose.production.example.yaml exec db \
   pg_restore -U slaif -d slaif_reservation \
-  --clean --if-exists --exit-on-error /tmp/slaif-YYYYMMDD.dump
-# Only if the restore command exited 0:
+  --clean --if-exists --exit-on-error /tmp/slaif-YYYYMMDD.dump &&
+docker compose -f compose.production.example.yaml run --rm app \
+  python manage.py operational_check &&
 docker compose -f compose.production.example.yaml start app
-docker compose -f compose.production.example.yaml run --rm app \
-  python manage.py operational_check
 ```
 
 `--exit-on-error` (present in the pinned PostgreSQL 17 image's
@@ -422,13 +427,13 @@
 (section 8). Both are explicit human decisions.
 
 ```bash
-# Retag the recorded previous-commit image to the example tag
-docker tag slaif-asset-reservation:<previous-commit-short-sha> \
-  slaif-asset-reservation:internal-alpha
-# Restart the application on the previous image
-docker compose -f compose.production.example.yaml up -d app
-# Verify: readiness through the proxy, then the operational check
-curl -fsS https://<your-hostname>/health/ready
+read -r -p "Recorded previous image tag (slaif-asset-reservation:commit): " SAR_PREVIOUS_IMAGE
+read -r -p "Approved service hostname: " SAR_SERVICE_HOST
+# Verify the image exists before changing the application tag.
+docker image inspect "$SAR_PREVIOUS_IMAGE" --format '{{.Id}}' &&
+docker tag "$SAR_PREVIOUS_IMAGE" slaif-asset-reservation:internal-alpha &&
+docker compose -f compose.production.example.yaml up -d app &&
+curl -fsS "https://${SAR_SERVICE_HOST}/health/ready" &&
 docker compose -f compose.production.example.yaml run --rm app \
   python manage.py operational_check
 ```
--- a/docs/README.md
+++ b/docs/README.md
@@ -69,7 +69,7 @@
 - [PLAN.md](../PLAN.md) — the canonical product plan.
 - [ARCHITECTURE-for-agents.md](../ARCHITECTURE-for-agents.md) — the compact
   executor projection of the canonical architecture.
-- [CRITICAL.md](../CRITICAL.md) — the critical-invariants register.
+- [CRITICAL.md](../CRITICAL.md) — the deferred human adjudication register.
 - [READINESS.md](READINESS.md) — initial-conversion readiness baseline
   (governance baseline, not part of the current operator path).
 - [oap-workflow.md](oap-workflow.md) — the adopted and operational
@@ -82,7 +82,7 @@
   control-plane runtime limits.
 - [repository-settings.md](repository-settings.md) — manual GitHub
   protection settings.
-- [audit/](audit/) — independent code-audit protocol, request and report
+- [audit/](audit/) — independent closure-audit protocol, request and report
   templates, and audit reports (immutable evidence records).
 - [oap/README.md](../oap/README.md) — the local OAP control plane layout
   (orders, reports, pointer).
```

## Evidence interpretation correction (report/PR only; old reports immutable)

Strategy additionally distinguishes two advisory dates: the repository security advisory page for GHSA-vxq7-64xx-v4gw displays Sep15; the independently retrieved GLOBAL GitHub advisory API gives published_at Sep30 for allthree advisories (vxq7 14:46:18Z, gh4c15:00:38Z, 8988 14:46:04Z). The global publication thus postdates the old Sep21 green run. Neither a's nor b's blanket publication-date inference should stand without identifying the source/feed. For final PR/report simply state current observed pip-audit failure versus historical green CI; no unproved explanation of the historical data is needed. No further security investigation in this docs round; exact known finding/fix unchanged.

## Non-goals / negative paths / recovery

No lockfile/dependency/workflow/product/config/test/inventory change, no new objective/PR, no deployment, real secrets/private data or other D2 crossing, no merge. Pending human scope question about a separate minimal urllib3 security PR is NOT an authorization. No force push/reset/stash/clean or immutable-report edit. Unexpected branch/head/state => report, preserve. Runtime tests use only owned scratch files and mock shell commands for the new guards. No privileged system changes. Same-PR suffix recovery only.

## Reporting and documentation

Standard C-11/C-12 publication sequence; final report-only commit, literal full implementation SHA, SELF marker, separate unobserved report CI. Report exact local command results and current-head CI including security failure. Prior operational evidence is reused, not newly executed. Response FIFO: /home/ubuntu/codex-supervision/slaif-asset-reservation/response.fifo. Strategy owns final review, quiescence and any later dependency objective.

## Deferred human adjudication
- Decision: NONE
