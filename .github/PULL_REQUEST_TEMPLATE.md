## Goal

Closes #

## Scope implemented

- <!-- describe -->

## Non-goals confirmed

- <!-- describe -->

## Files changed

- <!-- describe -->

## Verification

| Command/check | Result |
|---|---|
| `...` | passed / failed / skipped / not run / blocked |

Include exact counts and relevant CI links. A skipped or unrun check is not a pass.

## Database and migrations

- [ ] No database change.
- [ ] Migrations added and reviewed.
- [ ] Migration drift check passed.
- [ ] PostgreSQL-specific behavior tested against PostgreSQL.

Details:

## Security and privacy impact

- Authentication/authorization impact:
- Secrets/token impact:
- Personal-data impact:
- Dependency/supply-chain impact:

## Documentation impact

- [ ] Docs updated in this PR.
- [ ] No docs change required; reason:

## Known limitations / not run

- <!-- describe -->

## Agent report

- Branch:
- Commit:
- Work-order issue:
- Local tools or dependencies installed:
- No production systems or secrets touched: yes / no
- No unrelated files changed: yes / no
- Agent did not merge or self-approve: yes / no

## Human review checklist

- [ ] Goal and scope match the approved work order.
- [ ] Negative-path tests prove the relevant risk.
- [ ] CI/check evidence is sufficient.
- [ ] Migrations and API changes are intentional.
- [ ] Security/privacy impact is acceptable.
- [ ] Documentation and readiness language are honest.
## Workflow classification

- Legacy work order (human-merged): fill the agent report from the execution evidence.
- Concentrated OAP round (post-adoption only): the agent report section is completed
  from the immutable published `oap/reports/<ID>-<slug>.md` (implementation head, result,
  CI separation). The conversion adoption PR (WO0014) is human-merged; agent-merged PRs
  are not part of the legacy workflow.
- This PR did not activate OAP, run product orders, merge for itself or deploy.
