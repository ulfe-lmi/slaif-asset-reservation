# Archive note — 015-a simplification

Order 015-a (issue #29) moved the following files from their live paths into this
directory byte-identical (git rename, content unchanged). This archive is historical
evidence of the removed bootstrap/materialization machinery, not live governance.

- MANIFEST.sha256 (root manifest; every live reference removed, no regeneration)
- oap/governance/MANIFEST.json
- oap/governance/DISTILLATION-MAP.md
- oap/governance/CONTEXT-BUDGET.md
- oap/bootstrap-sources.lock.json
- oap/bin/check_governance.py
- oap/bin/oap_materialize.py
- oap/bin/bootstrap-two-agent-oap.sh (execute bit preserved on the archive copy)
- oap/COMPLETENESS.md
- oap/templates/STRATEGIC-REVIEW-CHECKLIST.md
- oap/templates/HANDOFF-TEMPLATE.md

The ICA protocol, templates and draft requests moved from oap/audit/ to docs/audit/
(same round, byte-identical). oap/bin/check_ica.py remains in oap/bin (milestone-use,
off the normal round path).
