"""BA-42..BA-45 — remote state wins over private journal, pending/changed-head CI,
changed-head invalidation and merge side effects. Merge gate never auto-merges.
"""

import json
import tempfile
import unittest
from pathlib import Path

import oaplib
import oaptestlib as t

REQUIRED_CI = ("quality", "test", "security", "container")


def _green_checks(head):
    return {job: {"state": "success", "head": head} for job in REQUIRED_CI}


def _meta(decision="D1"):
    return {"id": "001-a", "decision_class": decision, "branch": "oap/001-a"}


class Ba42RemoteStateWins(unittest.TestCase):
    def setUp(self):
        self.td = Path(tempfile.mkdtemp(prefix=t.unique_name("ba42")))
        self.repo = self.td / "repo"
        self.head = t.make_repo(self.repo, {"hello.txt": b"world\n"})
        self.home = self.td / "home"
        self.home.mkdir()
        t.activate_order(self.repo, oid="001-a", pr_number=27)
        (self.repo / "oap" / "reports").mkdir()
        (self.repo / "oap" / "reports" / "001-a-canary.md").write_text(
            f"# report fixture\n\nImplementation head SHA: {self.head}\n"
        )
        jdir = self.home / "workorders"
        jdir.mkdir(parents=True)
        (jdir / "state.json").write_text(json.dumps({"events": [], "merged": {"001-a": True}}))
        self.remote_state = {
            "refs": {"main": self.head},
            "prs": [{"number": 27, "branch": "oap/001-a", "state": "open", "merged": False}],
        }

    def test_ba42_journal_merged_but_remote_pr_open(self):
        adapter = oaplib.FixtureRemote(self.remote_state)
        ptr_before = (self.repo / "oap" / "active").read_bytes()
        state = oaplib.classify_state(str(self.repo), str(self.home), adapter)
        self.assertEqual(state["state"], "REPORT_PUBLISHED")
        self.assertIn("remote state wins", state["detail"])
        # read-only: pointer untouched
        self.assertEqual((self.repo / "oap" / "active").read_bytes(), ptr_before)

    def test_ba42_remote_pr_merged_gives_accepted_quiescent(self):
        adapter = oaplib.FixtureRemote(self.remote_state)
        adapter.mark_merged(27)
        state = oaplib.classify_state(str(self.repo), str(self.home), adapter)
        self.assertEqual(state["state"], "ACCEPTED_QUIESCENT")
        self.assertEqual((self.repo / "oap" / "active").read_bytes(), b"001-a\n")

    def test_ba42_round_frozen_next_suffix_same_pr(self):
        adapter = oaplib.FixtureRemote(self.remote_state)
        res = oaplib.round_frozen(str(self.repo), "001-a", adapter)
        self.assertTrue(res["frozen"])
        self.assertEqual(res["next_round"], "b")
        self.assertEqual(res["same_pr"], 27)
        self.assertIn("same PR", res["reason"])

    def test_ba42_pointer_id_unchanged_across_classification(self):
        adapter = oaplib.FixtureRemote(self.remote_state)
        for _ in range(3):
            oaplib.classify_state(str(self.repo), str(self.home), adapter)
        self.assertEqual((self.repo / "oap" / "active").read_bytes(), b"001-a\n")


class Ba43PendingAndSkippedCi(unittest.TestCase):
    def test_ba43_all_green_review_permitted_never_auto_merged(self):
        res = oaplib.evaluate_merge_gate(
            _meta(),
            _green_checks("h1"),
            {},
            {"checked": True, "d2_detected": False},
            {"enabled": True, "attributable_reference": "auth"},
            "h1",
            "h1",
        )
        self.assertEqual(res["decision"], "REVIEW_PERMITTED")
        self.assertEqual(res["problems"], [])

    def test_ba43_pending_check_blocks(self):
        checks = _green_checks("h1")
        checks["quality"] = {"state": "pending", "head": "h1"}
        res = oaplib.evaluate_merge_gate(
            _meta(),
            checks,
            {},
            {"checked": True, "d2_detected": False},
            {"enabled": True, "attributable_reference": "auth"},
            "h1",
            "h1",
        )
        self.assertEqual(res["decision"], "BLOCKED")
        self.assertTrue(any("pending" in p for p in res["problems"]))

    def test_ba43_skipped_check_blocks(self):
        checks = _green_checks("h1")
        checks["test"] = {"state": "skipped", "head": "h1"}
        res = oaplib.evaluate_merge_gate(
            _meta(),
            checks,
            {},
            {"checked": True, "d2_detected": False},
            {"enabled": True, "attributable_reference": "auth"},
            "h1",
            "h1",
        )
        self.assertEqual(res["decision"], "BLOCKED")

    def test_ba43_cancelled_check_blocks(self):
        checks = _green_checks("h1")
        checks["security"] = {"state": "cancelled", "head": "h1"}
        res = oaplib.evaluate_merge_gate(
            _meta(),
            checks,
            {},
            {"checked": True, "d2_detected": False},
            {"enabled": True, "attributable_reference": "auth"},
            "h1",
            "h1",
        )
        self.assertEqual(res["decision"], "BLOCKED")

    def test_ba43_missing_check_blocks(self):
        checks = _green_checks("h1")
        del checks["container"]
        res = oaplib.evaluate_merge_gate(
            _meta(),
            checks,
            {},
            {"checked": True, "d2_detected": False},
            {"enabled": True, "attributable_reference": "auth"},
            "h1",
            "h1",
        )
        self.assertEqual(res["decision"], "BLOCKED")
        self.assertTrue(any("container" in p for p in res["problems"]))


class Ba44ChangedHead(unittest.TestCase):
    def _gate(self, checks, head, reviewed):
        return oaplib.evaluate_merge_gate(
            _meta(),
            checks,
            {},
            {"checked": True, "d2_detected": False},
            {"enabled": True, "attributable_reference": "auth"},
            head,
            reviewed,
        )

    def test_ba44_reviewed_head_moved_blocks(self):
        res = self._gate(_green_checks("h1"), "h2", "h1")
        self.assertEqual(res["decision"], "BLOCKED")
        self.assertTrue(any("reviewed head changed" in p for p in res["problems"]))

    def test_ba44_check_at_old_head_blocks(self):
        checks = _green_checks("h1")
        checks["test"] = {"state": "success", "head": "h0"}  # stale evidence
        res = self._gate(checks, "h1", "h1")
        self.assertEqual(res["decision"], "BLOCKED")
        self.assertTrue(any("test" in p and "not at reviewed head" in p for p in res["problems"]))

    def test_ba44_delegation_inactive_blocks(self):
        res = oaplib.evaluate_merge_gate(
            _meta(),
            _green_checks("h1"),
            {},
            {"checked": True, "d2_detected": False},
            {"enabled": False, "attributable_reference": "auth"},
            "h1",
            "h1",
        )
        self.assertEqual(res["decision"], "BLOCKED")
        res2 = oaplib.evaluate_merge_gate(
            _meta(),
            _green_checks("h1"),
            {},
            {"checked": True, "d2_detected": False},
            {"enabled": True, "attributable_reference": ""},
            "h1",
            "h1",
        )
        self.assertEqual(res2["decision"], "BLOCKED")

    def test_ba44_d2_preparation_never_delegated(self):
        res = oaplib.evaluate_merge_gate(
            _meta(decision="D2_PREPARATION"),
            _green_checks("h1"),
            {},
            {"checked": True, "d2_detected": False},
            {"enabled": True, "attributable_reference": "auth"},
            "h1",
            "h1",
        )
        self.assertEqual(res["decision"], "BLOCKED")


class Ba45MergeSideEffects(unittest.TestCase):
    def test_ba45_side_effects_not_checked_blocks(self):
        res = oaplib.evaluate_merge_gate(
            _meta(),
            _green_checks("h1"),
            {},
            {"checked": False},
            {"enabled": True, "attributable_reference": "auth"},
            "h1",
            "h1",
        )
        self.assertEqual(res["decision"], "BLOCKED")
        self.assertTrue(any("side effects" in p for p in res["problems"]))

    def test_ba45_d2_side_effect_detected_blocks_despite_green_ci(self):
        res = oaplib.evaluate_merge_gate(
            _meta(),
            _green_checks("h1"),
            {},
            {"checked": True, "d2_detected": True},
            {"enabled": True, "attributable_reference": "auth"},
            "h1",
            "h1",
        )
        self.assertEqual(res["decision"], "BLOCKED")
        self.assertTrue(any("D2" in p for p in res["problems"]))

    def test_ba45_fixture_remote_has_no_merge_method(self):
        names = {n.lower() for n in dir(oaplib.FixtureRemote)}
        for bad in ("merge", "mergpr", "auto_merge", "merge_pr"):
            self.assertNotIn(bad, names)
        self.assertNotIn("merge", vars(oaplib.FixtureRemote))

    def test_ba45_coding_constitution_never_merges(self):
        law = t.REPO_ROOT / "oap" / "coding-instructions" / "AGENTS.md"
        if not law.is_file():
            t.record_blocked("BA-45", "materialized coding law not present in this environment")
            self.skipTest("materialized coding law absent")
        text = law.read_text("utf-8", "replace")
        self.assertIn("NEVER merges", text)


if __name__ == "__main__":
    unittest.main()
