# Executor security core

SC-01. Private repository; no visibility/publication expansion. No production/lab/Neumann/real legacy
access, DNS/TLS/firewall/identity/secret administration or deployment without explicit human D2 grant.
Only separately authorized Git development publication and bounded synthetic tests are allowed.
SC-02. No credentials/verifiers/peppers/passwords/cookies/CSRF/Authorization/raw payload/private text
in Git, reports, logs, assertions, screenshots or traces. No auth-home copying. No OS sidecars.
SC-03. Keep session/bearer/management/owner boundaries separate; CSRF and POST-only mutations remain.
Only exact authorized CRITICAL append; never human adjudication. No self-merge/auto-merge.
SC-04. Preserve user files, migration history, inventory verification, existing register and active
state. No reset/clean/stash/force-push; no destructive cleanup without test-owned resource identity.
Product operational tests/rehearsal must run in disposable copy with no real deploy/env.production,
secret files, real DB URLs or unrelated Docker resources. Same OS user is not a role sandbox.
SC-05. Failed validation never licenses disabling tests, widening auth, broad exception masking,
real-service calls or adding dependencies. Isolate the first failing boundary and report safe evidence.
Relevant full security contracts require only an order-scoped read when changing that boundary.
