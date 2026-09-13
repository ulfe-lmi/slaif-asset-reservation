# Template only — not a live CRITICAL entry

Copy structure only after strategy confirms all five admission conditions. This template must not
be appended as-is. Replace every placeholder; real PR/objective must already exist. Payload ends
with LF; order contains exact payload digest and trusted prior register identity.

```markdown
## CRIT-0001 — Short decision title

- **Status:** OPEN — HUMAN ADJUDICATION REQUIRED
- **Introduced by:** <actual PR and OAP objective>
- **Category:** security | authorization | data integrity | privacy | operations | architecture | dependency | other
- **Severity:** low | medium | high | critical
- **Decision confidence:** low | medium | high
- **Required human gate:** <specific applicable target boundary>
- **Affected components:** ...

### Dilemma
...

### Decision taken
...

### Reasoning
...

### Alternatives considered
...

### Strongest argument that this decision is wrong
...

### Assumptions
...

### Failure mode and blast radius
...

### Mitigations and evidence
...

### Reversibility and rollback
...

### Safe autonomous continuation
<exact work that may continue, and work that remains blocked>

### Exact human gate
<boundary before which a human disposition must exist>

### Exact question for the human adjudicator
...

### Strategic attestation
ALL FIVE CRITICAL-ENTRY CONDITIONS SATISFIED

### Human disposition
PENDING — append separately; do not edit this entry.

### Resolution
PENDING — cleared only by the latest appended human ACCEPTED disposition.
```

Evidence-only append uses a separate exact ordered payload headed
`## EVIDENCE APPEND — CRIT-NNNN — <unique UUID>` with actual evidence/mitigation references.
It may not alter original text or substitute for human adjudication.
