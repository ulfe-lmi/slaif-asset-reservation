# Recommended GitHub Repository Settings

These settings are manual administrative actions; repository files alone cannot enforce all of them.

## 1. Default branch

- default branch: `main`;
- prohibit direct routine pushes;
- automatically delete head branches after merge;
- prefer squash merge;
- disable merge commits and rebase merge if the team wants one consistent history.

## 2. Ruleset or branch protection for `main`

Enable:

- require a pull request before merging;
- require at least one approving human review;
- dismiss stale approvals when new commits materially change the PR;
- require review conversation resolution;
- require branches to be up to date if CI cost permits;
- require status checks after Work Order 0001 creates them;
- block force pushes;
- block deletion;
- include administrators/bypass roles unless emergency policy says otherwise;
- do not allow Codex identity to bypass or approve.

Initial required checks after Work Order 0001 should use stable unique job names, expected to be:

```text
quality
test
security
container
```

Only require checks that actually exist and are reliable; update the ruleset when CI names settle.

## 3. Pull requests

- enable issues and pull requests;
- require use of PR template by process;
- enable auto-merge only if human approval remains required; leaving it disabled is acceptable;
- do not permit agent self-merge;
- allow maintainers to update branches;
- use issue auto-close through `Closes #...`.

## 4. Actions permissions

- default workflow token permission: read repository contents;
- grant write permissions per workflow/job only when required;
- do not expose production deployment secrets to ordinary PR workflows;
- require environment approval for any future production deployment;
- pin third-party actions to trusted major versions or commit SHAs according to policy;
- restrict actions to approved sources if the organization supports it.

## 5. Security features

Enable where available:

- dependency graph;
- Dependabot alerts;
- secret scanning and push protection;
- private vulnerability reporting;
- code scanning/CodeQL after language scaffold exists;
- security policy recognition through `SECURITY.md`.

Automated version-update configuration should be added only after the `uv`/lockfile workflow is tested.

## 6. Labels

Suggested labels:

```text
work-order
codex
architecture
security
migration
api
ui
testing
deployment
blocked
needs-strategic-review
needs-human-decision
repair
```

Labels organize work; they do not replace acceptance criteria.

## 7. Milestones

Suggested:

- Bootstrap
- Executable foundation
- Reservation core
- Unified MVP
- Internal alpha
- Operational beta
- Gateway integration

## 8. CODEOWNERS

Add `.github/CODEOWNERS` only after real GitHub users/teams are confirmed. Do not invent a team name that makes every PR unmergeable.

Recommended ownership later:

- all files: core maintainers;
- `.github/`, deployment, and security docs: operator/security maintainers;
- migrations and domain model: core maintainers;
- gateway integration: machine owner plus core maintainers.

## 9. Repository visibility

The repository is currently private. Before making it public, review:

- issue/PR history for private data;
- legacy migration artifacts;
- hostnames and network topology;
- screenshots/logs;
- security contact and disclosure process;
- license and funding notices;
- removal/rotation of any accidentally exposed secret.
