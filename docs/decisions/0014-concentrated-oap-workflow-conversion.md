# ADR 0014: Concentrated OAP workflow conversion for the existing repository

**Status:** Proposed (candidate, unadopted)
**Date:** 2026-09-13
**Supersedes (process only):** the human-per-merge development loop described in the
pre-conversion `AGENTS.md` (archived at `docs/bootstrap/1/previous/AGENTS.pre-concentrated.md`)
and in `docs/oap-workflow.md` (archived at
`docs/bootstrap/1/previous/oap-workflow.pre-concentrated.md`). No product decision,
ADR 0001-0013, application behavior, or merged history is superseded.

## Context

The repository has completed Work Orders 0001-0013 at main
`1fcc2c91d793556a91711365abef562604b62f84`. The accountable human requested, for this existing project, a conversion to
the Concentrated OAP profile according to the attached bootstrap generator: separated
long-lived strategic and fresh-per-round coding Codex roles, compact executor context,
HWP/HJP/DHA discipline, D0/D1/D2 decision classes, tested local helpers and FIFO
transport, exact order/report publication, and Independent Closure Audit. Operation is
Codex-only; no operational CLAUDE.md is retained or generated.

## Decision

1. **Root architecture consolidation.** A new canonical root `ARCHITECTURE.md`
   (consolidation, not a rename) becomes the current architecture; the accepted
   `docs/architecture.md` is archived byte-identically and its path becomes a
   compatibility pointer. Root `PLAN.md` and a zero-entry `CRITICAL.md` seed are
   installed when absent (a discovered pre-existing register is preserved, never
   reseeded).
2. **Role and router/context model.** The repository root `AGENTS.md` becomes a tiny
   role router. Dense executor law lives in `oap/coding-instructions/`; full strategic
   law is versioned in `oap/strategic-instructions/` and installed byte-identically into
   a separate private strategic home. Compact projections are hash-bound to canonical
   sources and coverage-mapped in `oap/governance/DISTILLATION-MAP.md`.
3. **Manual adoption exception.** The one-time conversion-adoption PR (WO0014) is
   created and merged only by explicit human authorization through the existing
   human-merge workflow. Bootstrap materialization commits nothing and activates
   nothing; the adoption session cannot self-approve.
4. **Conditional delegated merge.** After adoption and separately attributable
   activation, strategy may merge development PRs only under scoped delegation, exact
   required CI at the reviewed head, complete D1 registration, and verified absence of
   unapproved external merge side effects. Coding never merges. D2 boundaries and all
   release/exposure/private-data/real-lab actions remain human.
5. **Independent closure.** M-CONVERSION and any later milestone require an
   architecture-derived ICA at the exact merged revision with independently provenanced
   audit context, followed by human milestone judgment.

## Consequences

- New local governance tree (`oap/`), `tests/oap/` harness, and targeted doc edits as
  listed in the conversion manifest; application bytes, migrations, lockfile,
  sanitized inventory and history remain unchanged.
- Activation prerequisites (models, authentication, runtime, remote merge side effects,
  human adjudication provenance) remain explicitly unconfigured and block activation,
  not safe materialization.
- Old work orders, PRs and reports remain history; no replay, renumbering or
  rebranding of merged evidence.
