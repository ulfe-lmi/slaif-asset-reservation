"""BA-51/BA-52 — archived source snapshots vs active instruction discovery, and
historical continuity (merged PR27 never reused; WO0014 reserved; real reports/orders
untouched).
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

import oaptestlib as t

EXPECTED_DRAFTS = {
    "015-a",
    "016-a",
    "017-a",
    "018-a",
    "019-a",
    "020-a",
}


def _materialized():
    return (t.REPO_ROOT / "docs" / "bootstrap" / "1" / "BOOTSTRAP-GENERATOR.md").is_file()


class Ba51SnapshotsVsDiscovery(unittest.TestCase):
    def test_ba51_generator_constitution_archived_renamed(self):
        if not _materialized():
            t.record_blocked("BA-51", "materialized candidate not present in this environment")
            self.skipTest("materialized candidate absent")
        gen = t.REPO_ROOT / "docs" / "bootstrap" / "1" / "BOOTSTRAP-GENERATOR.md"
        self.assertTrue(gen.is_file())
        self.assertGreater(gen.stat().st_size, 500)
        text = gen.read_text("utf-8", "replace")
        self.assertIn("Bootstrap agent constitution", text)
        # byte-identical to the package archive-root AGENTS.md when provided
        pkg = os.environ.get("OAP_TEST_BOOTSTRAP_AGENTS")
        if pkg:
            self.assertEqual(gen.read_bytes(), Path(pkg).read_bytes())

    def test_ba51_no_discoverable_instruction_basenames_under_bootstrap(self):
        if not _materialized():
            t.record_blocked("BA-51", "materialized candidate not present in this environment")
            self.skipTest("materialized candidate absent")
        root = t.REPO_ROOT / "docs" / "bootstrap"
        offenders = []
        for p in root.rglob("*"):
            if p.is_file() and p.name.lower() in ("agents.md", "claude.md"):
                offenders.append(str(p.relative_to(root)))
        self.assertEqual(
            offenders, [], f"discovered instruction basenames under bootstrap/: {offenders}"
        )

    def test_ba51_no_repo_claude_md_and_input_snapshots_present(self):
        if not _materialized():
            t.record_blocked("BA-51", "materialized candidate not present in this environment")
            self.skipTest("materialized candidate absent")
        self.assertFalse((t.REPO_ROOT / "CLAUDE.md").exists())
        inputs = t.REPO_ROOT / "docs" / "bootstrap" / "1" / "inputs"
        required = [
            "bootstrap-generator-prompt.md",
            "oap.md",
            "REPOSITORY-OBSERVATIONS.json",
            "INSTRUCTIONS.md",
            "PLAN.md",
            "ARCHITECTURE.md",
            "CRITICAL.md",
            "SOURCE-MAP.md",
            "PACKAGE-CHECKS.md",
            "README.md",
        ]
        missing = [n for n in required if not (inputs / n).is_file()]
        self.assertEqual(missing, [])
        previous = t.REPO_ROOT / "docs" / "bootstrap" / "1" / "previous"
        prev_required = [
            "AGENTS.pre-concentrated.md",
            "docs-architecture.md",
            "oap-workflow.pre-concentrated.md",
            "SECURITY.pre-concentrated.md",
        ]
        missing_prev = [n for n in prev_required if not (previous / n).is_file()]
        self.assertEqual(missing_prev, [])

    def test_ba51_compact_coding_read_set_clean_of_bootstrap_inputs(self):
        if not _materialized():
            t.record_blocked("BA-51", "materialized candidate not present in this environment")
            self.skipTest("materialized candidate absent")
        read_set = [
            "oap/coding-instructions/AGENTS.md",
            "oap/coding-instructions/SECURITY-CORE.md",
            "oap/coding-instructions/TESTING-CORE.md",
            "OAP-COMMUNICATION-coding-agent.md",
            "ARCHITECTURE-for-agents.md",
            "AGENTS.md",
        ]
        for rel in read_set:
            p = t.REPO_ROOT / rel
            self.assertTrue(p.is_file(), f"missing read-set file {rel}")
            text = p.read_text("utf-8", "replace")
            self.assertNotIn("docs/bootstrap", text, f"{rel} references bootstrap inputs")
            self.assertNotIn("oap.md", text, f"{rel} references oap.md as a read")


class Ba52HistoricalContinuity(unittest.TestCase):
    def _publish_env(self, prefix, pr_state):
        td = Path(tempfile.mkdtemp(prefix=t.unique_name(prefix)))
        repo = td / "repo"
        head = t.make_repo(repo, {"a.txt": b"a\n"})
        home = td / "home"
        home.mkdir()
        outside = td / "outside"
        outside.mkdir()
        authority = outside / "authority.json"
        authority.write_text(json.dumps({"attributed": True}))
        t.write_runtime_env(home, repo, activation=True, authority=True)
        envp = home / "runtime.env"
        envp.write_text(
            envp.read_text().replace("/abs/attributable-authority.json", str(authority))
        )
        remote = t.write_remote_state(
            td,
            {
                "refs": {"refs/heads/main": head},
                "prs": pr_state,
            },
        )
        return td, repo, head, home, remote

    def test_ba52_round_a_cannot_bind_merged_historical_pr(self):
        prs = [{"number": 27, "branch": "oap/001-a", "state": "merged", "merged": True}]
        td, repo, head, home, remote = self._publish_env("ba52a", prs)
        order = t.make_order_file(
            td,
            oid="001-a",
            base_sha=head,
            meta=t.order_meta(oid="001-a", base_sha=head, pr_number=27),
        )
        rc, out, err, js = t.run_cli(
            "publish_order.py",
            ["--repo", str(repo), "--strategic-home", str(home), "--order", str(order), "--json"],
            env={"OAP_ROLE": "STRATEGIC", "OAP_REMOTE_ADAPTER_FILE": remote},
            expect_json=True,
        )
        self.assertEqual(rc, 1)
        detail = " ".join(s["detail"] for s in js["steps"])
        self.assertIn("merged historical PR", detail)
        self.assertFalse((repo / "oap" / "active").exists())
        self.assertFalse(
            (repo / "oap" / "orders").exists() and any((repo / "oap" / "orders").iterdir())
        )

    def test_ba52_branch_of_merged_pr_refused_with_null_pr_number(self):
        prs = [{"number": 27, "branch": "oap/001-a", "state": "merged", "merged": True}]
        td, repo, head, home, remote = self._publish_env("ba52b", prs)
        order = t.make_order_file(td, oid="001-a", base_sha=head)  # pr_number null, round a
        rc, out, err, js = t.run_cli(
            "publish_order.py",
            ["--repo", str(repo), "--strategic-home", str(home), "--order", str(order), "--json"],
            env={"OAP_ROLE": "STRATEGIC", "OAP_REMOTE_ADAPTER_FILE": remote},
            expect_json=True,
        )
        self.assertEqual(rc, 1)
        detail = " ".join(s["detail"] for s in js["steps"])
        self.assertIn("MERGED historical PR", detail)

    def test_ba52_real_reports_orders_history_untouched(self):
        if not _materialized():
            t.record_blocked("BA-52", "materialized candidate not present in this environment")
            self.skipTest("materialized candidate absent")
        # continuity: every published report binds a published order of the same
        # name; no fabricated reports; no report cites WO0001-WO0013 as OAP rounds
        orders_dir = t.REPO_ROOT / "oap" / "orders"
        reports_dir = t.REPO_ROOT / "oap" / "reports"
        orders = {p.name for p in orders_dir.glob("*.md")} if orders_dir.is_dir() else set()
        reports = {p.name for p in reports_dir.glob("*.md")} if reports_dir.is_dir() else set()
        self.assertEqual(reports - orders, set(), "fabricated report without a published order")
        for p in reports_dir.glob("*.md"):
            text = p.read_text("utf-8", "replace")
            self.assertNotIn("WO000", text, "legacy work orders are not OAP rounds")
        # pointer (when present) binds exactly one order
        ptr = t.oaplib.read_pointer(t.REPO_ROOT / "oap" / "active")
        if ptr["state"] == "ACTIVE":
            self.assertEqual(
                len([n for n in orders if n.startswith(ptr["id"] + "-")]),
                1,
                "pointer must bind exactly one order",
            )

    def test_ba52_drafts_exactly_the_six_seeds_no_014(self):
        if not _materialized():
            t.record_blocked("BA-52", "materialized candidate not present in this environment")
            self.skipTest("materialized candidate absent")
        d = t.REPO_ROOT / "oap" / "strategic-instructions" / "initial-orders"
        self.assertTrue(d.is_dir())
        names = sorted(p.name for p in d.glob("*.md"))
        ids = {n.split("-", 2)[0] + "-" + n.split("-", 2)[1] for n in names}
        self.assertEqual(ids, EXPECTED_DRAFTS)
        self.assertEqual(len(names), 6)
        # 0014 must appear NOWHERE as a materialized draft/order
        for base in (t.REPO_ROOT / "oap",):
            for p in base.rglob("*.md"):
                self.assertFalse(
                    p.name.startswith("014-"), f"0014 reserved for human adoption: {p.name}"
                )

    def test_ba52_roadmap_reserves_0014(self):
        if not _materialized():
            t.record_blocked("BA-52", "materialized candidate not present in this environment")
            self.skipTest("materialized candidate absent")
        roadmap = t.REPO_ROOT / "oap" / "strategic-instructions" / "INITIAL-ROADMAP.md"
        text = roadmap.read_text("utf-8", "replace")
        self.assertIn("WO0014", text)
        self.assertIn("reserved", text)
        # and the ADR 0014 exists as the process record
        adr = t.REPO_ROOT / "docs" / "decisions" / "0014-concentrated-oap-workflow-conversion.md"
        self.assertTrue(adr.is_file())
        adr_text = adr.read_text("utf-8", "replace")
        self.assertIn("Proposed", adr_text)


if __name__ == "__main__":
    unittest.main()
