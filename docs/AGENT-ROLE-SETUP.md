# AGENT ROLE SETUP — Codex-only, separate homes

Generation 1. Both operational roles use the installed Codex client. Bootstrap
recorded `codex-cli 0.153.4` (`codex exec` available) at materialization on 2026-09-13;
model identifiers, provider argv and authentication remain **UNCONFIGURED** by design.

## Checks to perform (record results; do not guess)

1. `codex --version`, `codex --help`, `codex exec --help` on the operational host.
2. Configuration behavior: how global/ancestor/root/nested `AGENTS.md` discovery and
   instruction limits apply for cwd `~/codex-work/slaif-asset-reservation` and cwd `~/codex-supervision/slaif-asset-reservation`; verify the root router is
   the only repository-root instruction file and no ancestor directory injects a
   conflicting role. Do not modify unrelated ancestor/global instructions.
3. Safe instruction-discovery observation without live model calls (help/config
   introspection only). A later authorized live client probe is separate and
   cost-bounded.
4. Fill supported invocation argv in `~/codex-supervision/slaif-asset-reservation/runtime.env`:
   `OAP_CODING_ARGV_JSON`, `OAP_STRATEGIC_ARGV_JSON` (exact arrays; the wrapper never
   shell-evals them) and model identifiers only if explicitly approved.
5. Historical coding preference `chatgpt-5.5-high` is preserved as a user-specified
   preference; it is **not** asserted to be a valid installed model ID. No automatic
   fallback.

## Homes (created by bootstrap, empty except generated config)

- `~/codex-supervision/slaif-asset-reservation/agent-homes/coding` — private CODEX_HOME for coding rounds.
- `~/codex-supervision/slaif-asset-reservation/agent-homes/strategic` — private CODEX_HOME for the strategic role.

Neither contains copied authentication, sessions or histories. Each role authenticates
independently later. Directories are mode 0700; config/FIFOs mode 0600.

## Refusals

Missing or conflicting explicit role: no operational mutation. Missing model/argv/auth:
setup shells still work; operation is BLOCKED (never silently re-provisioned).
Contradictory inherited role obligations are reported and reconciled, not overridden.
