# Repository Bootstrap Instructions

This bundle is the constitution-and-design bootstrap for `ulfe-lmi/slaif-asset-reservation`.

## Apply as the bootstrap PR

From a clean clone of the current repository:

```bash
git switch main
git pull --ff-only
git switch -c bootstrap/constitution
# Copy the contents of this bundle into the repository root.
git add AGENTS.md README.md CONTRIBUTING.md SECURITY.md \
  BOOTSTRAP_INSTRUCTIONS.md .editorconfig .gitattributes \
  .github docs data
git commit -m "docs: establish project constitution and architecture"
git push -u origin bootstrap/constitution
```

Open a pull request. This initial PR contains no application implementation and should not claim executable verification beyond file-format and content review.

## After merge

1. Configure repository settings from `docs/repository-settings.md`.
2. Create a GitHub issue using the Codex work-order form.
3. Copy the content of `docs/work-orders/0001-application-scaffold.md` into that issue, resolving any repository-state placeholders.
4. Assign the approved issue to the configured Codex programming agent.
5. Codex creates the implementation branch and PR; it does not merge.
6. The strategic model inspects the PR, CI, tests, migrations, and report and returns a merge/repair/reject decision brief.
7. A human maintainer makes the merge decision.

`AGENTS.md` becomes active for Codex after the bootstrap PR is merged.
