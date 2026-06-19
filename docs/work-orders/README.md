# Work Orders

GitHub issues are the live source of truth for implementation tasks. Files in this directory are strategic templates or milestone baselines that may be copied into an issue after current repository state is re-verified.

Never launch Codex from an old work-order file without checking current `main`, open PRs, accepted ADRs, and CI.

## Required structure

```markdown
# Title

## Governing instructions

## Current verified state

## Goal

## Domain behavior

## Scope

## Non-goals

## Acceptance criteria

## Files/areas to inspect

## Implementation requirements

## Tests required

## Documentation required

## Local setup allowed

## Workflow

## Final report
```

## Review rule

One work order should normally produce one PR. Repair findings stay on the same branch unless the strategic review explicitly requests a separate repair PR.
