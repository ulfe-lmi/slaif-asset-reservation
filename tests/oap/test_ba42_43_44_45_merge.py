"""BA-42..BA-45 — no-self-merge (015-a slim round).

The merge-side machinery of the concentrated conversion is strategy/human owned:
the fixture remote adapter has no merge capability at all, and the coding law
forbids self-merge. All other BA-42..45 cases exercised superseded gate
dimensions and were trimmed with the simplification.
"""

import unittest

import oaptestlib as t


class Ba45NoSelfMerge(unittest.TestCase):
    def test_ba45_fixture_remote_has_no_merge_method(self):
        names = {n.lower() for n in dir(t.oaplib.FixtureRemote)}
        for bad in ("merge", "mergpr", "auto_merge", "merge_pr"):
            self.assertNotIn(bad, names)
        self.assertNotIn("merge", vars(t.oaplib.FixtureRemote))

    def test_ba45_coding_constitution_never_merges(self):
        law = t.REPO_ROOT / "oap" / "coding-instructions" / "AGENTS.md"
        if not law.is_file():
            t.record_blocked("BA-45", "materialized coding law not present in this environment")
            self.skipTest("materialized coding law absent")
        text = law.read_text("utf-8", "replace")
        self.assertIn("NEVER merges", text)


if __name__ == "__main__":
    unittest.main()
