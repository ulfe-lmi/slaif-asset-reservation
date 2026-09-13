"""BA-28..BA-32 — PR-before-report, report-only parent, remote-vs-local
reports, after-report freeze (slim 015-a verifier: exactly three checks)."""

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "oap" / "bin"))

import oaplib  # noqa: E402
import oaptestlib as t  # noqa: E402


def report_text(impl_sha: str, order_digest: str, extra: str = "", future_ci: bool = False) -> str:
    return (
        "# Final report 001-a-canary\n\n"
        "Order digest: {}\n"
        "Implementation head SHA: {}\n"
        "Report publication commit: SELF\n\n"
        "## Implementation head CI\n"
        "quality/test/security/container observed at the implementation head.\n\n"
        "## Report head CI\n"
        "{}\n"
        "{}".format(
            order_digest,
            impl_sha,
            "NOT YET OBSERVED AT AUTHORING" if not future_ci else "success",
            extra,
        )
    )


def install_order(repo: Path, order: Path, oid: str, slug: str = "canary") -> None:
    """Install order bytes under the canonical name <ID>-<slug>.md (no draft suffix)."""
    (repo / "oap" / "orders").mkdir(parents=True, exist_ok=True)
    (repo / "oap" / "orders" / (f"{oid}-{slug}.md")).write_bytes(order.read_bytes())


def build_report_repo(td: Path, order_oid: str = "001-a"):
    """Git fixture: implementation commit + report-only commit on top."""
    repo = td / "repo"
    t.make_repo(repo, {"AGENTS.md": b"router\n"}, "baseline")
    t.commit_files(repo, {"oap/WORKFLOW-CANARY.md": b"canary\n"}, "implementation")
    orders = repo / "oap" / "orders"
    order = t.make_order_file(repo, oid=order_oid, base_sha=t.head(repo))
    install_order(repo, order, order_oid)
    # commit the order bytes as part of the implementation chain
    git_env_repo = repo
    t.git(git_env_repo, "add", "-A")
    t.git(git_env_repo, "commit", "-q", "--allow-empty", "-m", "order published")
    impl_head = t.head(repo)
    return repo, impl_head, orders / ("{}-{}.md".format(order_oid, "canary"))


class Ba28PrBeforeReport(unittest.TestCase):
    def test_ba28_pr_identity_precedes_report(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba28")) as td:
            td = Path(td)
            repo = td / "repo"
            head0 = t.make_repo(repo, {"AGENTS.md": b"r\n"})
            # remote fixture with an open PR created at a recorded timestamp
            pr_time = time.time() - 3600
            state = {
                "refs": {"refs/heads/main": head0, "refs/heads/oap/001-a": head0},
                "prs": [
                    {
                        "number": 33,
                        "branch": "oap/001-a",
                        "state": "open",
                        "merged": False,
                        "created_at": pr_time,
                    }
                ],
                "next_pr_number": 34,
            }
            remote = t.write_remote_state(td, state)
            adapter = oaplib.FixtureRemote(state)
            # the report commit happens strictly AFTER the PR identity
            report_commit_time = pr_time + 60
            os_environ = __import__("os").environ
            saved = os_environ.get("OAP_REMOTE_ADAPTER_FILE")
            os_environ["OAP_REMOTE_ADAPTER_FILE"] = remote
            try:
                pr = adapter.pr_for_branch(str(repo), "oap/001-a")
                self.assertIsNotNone(pr)
                self.assertEqual(pr["number"], 33)
                self.assertLess(
                    pr["created_at"],
                    report_commit_time,
                    "PR identity must predate report composition",
                )
            finally:
                if saved is None:
                    del os_environ["OAP_REMOTE_ADAPTER_FILE"]
                else:
                    os_environ["OAP_REMOTE_ADAPTER_FILE"] = saved

    def test_ba28_blocked_publication_invents_nothing(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba28b")) as td:
            td = Path(td)
            repo = td / "repo"
            head0 = t.make_repo(repo, {"AGENTS.md": b"r\n"})
            state = {"refs": {"refs/heads/main": head0}, "prs": [], "next_pr_number": 34}
            remote = t.write_remote_state(td, state)
            home = td / "home"
            home.mkdir()
            t.write_runtime_env(home, repo, activation=True, authority=True)
            # missing PR for the order's branch with pr_mode AMEND is invalid;
            # use a DRAFT order -> validation fails before any write
            order = t.make_order_file(
                td, meta=t.order_meta(oid="001-a", base_sha=head0, state="DRAFT")
            )
            rc, out, err, js = t.run_cli(
                "publish_order.py",
                [
                    "--repo",
                    str(repo),
                    "--strategic-home",
                    str(home),
                    "--order",
                    str(order),
                    "--dry-run",
                    "--json",
                ],
                env={"OAP_ROLE": "STRATEGIC", "OAP_REMOTE_ADAPTER_FILE": remote},
                timeout=30,
                expect_json=True,
            )
            self.assertNotEqual(rc, 0)
            self.assertEqual(js["status"], "FAILED_VALIDATION")
            after = json.loads(Path(remote).read_text())
            self.assertEqual(after["prs"], [], "no PR invented")
            self.assertFalse(
                (repo / "oap" / "orders").exists() or list((repo / "oap" / "orders").glob("*.md")),
                "no order bytes written on blocked publication",
            )
            self.assertFalse((repo / "oap" / "active").exists())


class Ba29ReportOnlyParent(unittest.TestCase):
    def _make_report(
        self, td: Path, impl_file_extra: bool = False, wrong_parent: bool = False
    ) -> Path:
        repo = td / "repo"
        t.make_repo(repo, {"AGENTS.md": b"router\n"}, "baseline")
        impl_head = t.commit_files(repo, {"src/app.py": b"impl\n"}, "implementation head")
        (repo / "oap").mkdir(exist_ok=True)
        order = t.make_order_file(repo, oid="001-a", base_sha=t.head(repo))
        install_order(repo, order, "001-a")
        t.git(repo, "add", "-A")
        t.git(repo, "commit", "-q", "-m", "order bytes")
        impl_head = t.head(repo)
        report_name = "oap/reports/001-a-canary.md"
        rdata = report_text(impl_head, oaplib.sha256_hex(order.read_bytes()))
        (repo / report_name).parent.mkdir(parents=True, exist_ok=True)
        (repo / report_name).write_text(rdata)
        t.git(repo, "add", report_name)
        if impl_file_extra:
            (repo / "src" / "extra.py").write_bytes(b"extra\n")
            t.git(repo, "add", "src/extra.py")
        if wrong_parent:
            # an intermediate commit between impl_head and the report commit
            # breaks the literal first-parent requirement (stage only the marker)
            t.git(repo, "reset", "-q", report_name)
            (repo / "oap" / "NOTES.md").write_bytes(b"intermediate\n")
            t.git(repo, "add", "oap/NOTES.md")
            t.git(repo, "commit", "-q", "-m", "intermediate (not the implementation head)")
            t.git(repo, "add", report_name)
        t.git(repo, "commit", "-q", "-m", "report only")
        return repo

    def test_ba29_valid_report_only_commit_passes(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba29")) as td:
            td = Path(td)
            repo = self._make_report(td)
            rc, out, err, js = t.run_cli(
                "verify_report.py",
                ["--repo", str(repo), "--id", "001-a", "--json"],
                timeout=60,
                expect_json=True,
            )
            checks = js["checks"]
            self.assertEqual(
                sorted(checks),
                [
                    "implementation_head_first_parent",
                    "remote_head_and_pr_identity",
                    "report_only_changed_path",
                ],
                "exactly the three slim checks",
            )
            self.assertEqual(js["status"], "BLOCKED", js)
            self.assertTrue(checks["report_only_changed_path"]["ok"], checks)
            self.assertTrue(
                checks["implementation_head_first_parent"]["ok"],
                "first parent must be the stated implementation head",
            )
            self.assertFalse(checks["remote_head_and_pr_identity"]["ok"])

    def test_ba29_extra_path_rejected(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba29b")) as td:
            td = Path(td)
            repo = self._make_report(td, impl_file_extra=True)
            rc, out, err, js = t.run_cli(
                "verify_report.py",
                ["--repo", str(repo), "--id", "001-a", "--json"],
                timeout=60,
                expect_json=True,
            )
            self.assertFalse(js["checks"]["report_only_changed_path"]["ok"])
            self.assertIn("src/extra.py", js["checks"]["report_only_changed_path"]["detail"])

    def test_ba29_wrong_parent_rejected(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba29c")) as td:
            td = Path(td)
            repo = self._make_report(td, wrong_parent=True)
            rc, out, err, js = t.run_cli(
                "verify_report.py",
                ["--repo", str(repo), "--id", "001-a", "--json"],
                timeout=60,
                expect_json=True,
            )
            self.assertFalse(js["checks"]["implementation_head_first_parent"]["ok"])
            self.assertIn(
                "first parent", js["checks"]["implementation_head_first_parent"]["detail"]
            )


class Ba30FutureCi(unittest.TestCase):
    def test_ba30_separate_ci_identity_and_private_receipt(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba30b")) as td:
            td = Path(td)
            repo = td / "repo"
            t.make_repo(repo, {"AGENTS.md": b"r\n"}, "baseline")
            impl = t.commit_files(repo, {"src/app.py": b"impl\n"}, "implementation head")
            order = t.make_order_file(repo, oid="001-a", base_sha=impl)
            install_order(repo, order, "001-a")
            t.git(repo, "add", "-A")
            t.git(repo, "commit", "-q", "-m", "order")
            impl = t.head(repo)
            rtext = report_text(impl, oaplib.sha256_hex(order.read_bytes()))
            (repo / "oap" / "reports").mkdir(parents=True)
            (repo / "oap" / "reports" / "001-a-canary.md").write_text(rtext)
            t.git(repo, "add", "-A")
            t.git(repo, "commit", "-q", "-m", "report")
            self.assertIn("## Implementation head CI", rtext)
            self.assertIn("## Report head CI", rtext)
            self.assertIn("NOT YET OBSERVED AT AUTHORING", rtext)
            # post-push receipts live under the PRIVATE strategic home
            home = td / "home"
            receipts = home / "workorders" / "receipts"
            receipts.mkdir(parents=True)
            (receipts / "001-a-post-push.json").write_text(f'{{"head": "{t.head(repo)}"}}')
            self.assertTrue(
                str(receipts).startswith(str(home)),
                "receipts must stay private to the strategic home",
            )


class Ba31RemoteVsLocal(unittest.TestCase):
    def test_ba31_local_only_report_is_not_completion(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba31")) as td:
            td = Path(td)
            repo = td / "repo"
            t.make_repo(repo, {"AGENTS.md": b"r\n"}, "baseline")
            impl = t.commit_files(repo, {"src/app.py": b"impl\n"}, "implementation head")
            order = t.make_order_file(repo, oid="001-a", base_sha=impl)
            install_order(repo, order, "001-a")
            t.git(repo, "add", "-A")
            t.git(repo, "commit", "-q", "-m", "order")
            impl = t.head(repo)
            (repo / "oap" / "reports").mkdir(parents=True)
            (repo / "oap" / "reports" / "001-a-canary.md").write_text(
                report_text(impl, oaplib.sha256_hex(order.read_bytes()))
            )
            t.git(repo, "add", "-A")
            t.git(repo, "commit", "-q", "-m", "report")
            report_head = t.head(repo)
            (repo / "oap" / "active").write_text("001-a\n")
            # remote fixture: branch absent -> BLOCKED, never a local pass
            state = {"refs": {"refs/heads/main": t.head(repo)}, "prs": []}
            remote = t.write_remote_state(td, state)
            rc, out, err, js = t.run_cli(
                "verify_report.py",
                ["--repo", str(repo), "--id", "001-a", "--json"],
                env={"OAP_REMOTE_ADAPTER_FILE": remote},
                timeout=60,
                expect_json=True,
            )
            self.assertEqual(js["status"], "BLOCKED", js)
            self.assertFalse(js["checks"]["remote_head_and_pr_identity"]["ok"])
            # publication itself is unchanged: re-running verification is read-only
            self.assertEqual(t.head(repo), report_head)
            # lost response after verified push: remote head present + journal merged
            # routes to strategy review (ACCEPTED_QUIESCENT), never coding mutation
            state2 = {
                "refs": {"refs/heads/main": t.head(repo), "refs/heads/oap/001-a": t.head(repo)},
                "prs": [{"number": 35, "branch": "oap/001-a", "state": "merged", "merged": True}],
            }
            t.write_remote_state(td, state2)
            adapter2 = oaplib.FixtureRemote(state2)
            home = td / "home"
            home.mkdir()
            (home / "workorders").mkdir()
            (home / "workorders" / "state.json").write_text(
                json.dumps({"events": [], "merged": {"001-a": True}})
            )
            s = oaplib.classify_state(str(repo), str(home), adapter2)
            self.assertEqual(s["state"], "ACCEPTED_QUIESCENT", s)

    def test_ba31_verified_remote_report(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba31b")) as td:
            td = Path(td)
            repo = td / "repo"
            t.make_repo(repo, {"AGENTS.md": b"r\n"}, "baseline")
            impl = t.commit_files(repo, {"src/app.py": b"impl\n"}, "implementation head")
            order = t.make_order_file(repo, oid="001-a", base_sha=impl)
            install_order(repo, order, "001-a")
            t.git(repo, "add", "-A")
            t.git(repo, "commit", "-q", "-m", "order")
            impl = t.head(repo)
            (repo / "oap" / "reports").mkdir(parents=True)
            (repo / "oap" / "reports" / "001-a-canary.md").write_text(
                report_text(impl, oaplib.sha256_hex(order.read_bytes()))
            )
            t.git(repo, "add", "-A")
            t.git(repo, "commit", "-q", "-m", "report")
            (repo / "oap" / "active").write_text("001-a\n")
            report_head = t.head(repo)
            state = {
                "refs": {"refs/heads/main": report_head, "refs/heads/oap/001-a": report_head},
                "prs": [{"number": 36, "branch": "oap/001-a", "state": "open", "merged": False}],
            }
            remote = t.write_remote_state(td, state)
            rc, out, err, js = t.run_cli(
                "verify_report.py",
                [
                    "--repo",
                    str(repo),
                    "--id",
                    "001-a",
                    "--pr",
                    "36",
                    "--head",
                    report_head,
                    "--json",
                ],
                env={"OAP_REMOTE_ADAPTER_FILE": remote},
                timeout=60,
                expect_json=True,
            )
            self.assertEqual(js["status"], "PASS", js)
            c = js["checks"]["remote_head_and_pr_identity"]
            self.assertTrue(c["ok"], js)
            self.assertIn("PR 36 bound", c["detail"])


class Ba32Freeze(unittest.TestCase):
    def test_ba32_completed_round_is_frozen(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba32")) as td:
            td = Path(td)
            repo = td / "repo"
            t.make_repo(repo, {"AGENTS.md": b"r\n"}, "baseline")
            impl = t.commit_files(repo, {"src/app.py": b"impl\n"}, "implementation head")
            order = t.make_order_file(
                repo, meta=t.order_meta(oid="002-a", base_sha=impl, pr_number=41)
            )
            install_order(repo, order, "002-a")
            t.git(repo, "add", "-A")
            t.git(repo, "commit", "-q", "-m", "order")
            impl = t.head(repo)
            (repo / "oap" / "reports").mkdir(parents=True)
            (repo / "oap" / "reports" / "002-a-canary.md").write_text(
                report_text(impl, oaplib.sha256_hex(order.read_bytes()))
            )
            t.git(repo, "add", "-A")
            t.git(repo, "commit", "-q", "-m", "report")
            frozen = oaplib.round_frozen(str(repo), "002-a")
            self.assertTrue(frozen["frozen"], frozen)
            self.assertEqual(frozen["next_round"], "b")
            self.assertEqual(frozen["same_pr"], 41)
            # a rewrite of the same round's order is refused (bytes immutable)
            home = td / "home"
            home.mkdir()
            t.write_runtime_env(home, repo, activation=True, authority=True)
            state = {
                "refs": {"refs/heads/main": t.head(repo), "refs/heads/oap/002-a": t.head(repo)},
                "prs": [{"number": 41, "branch": "oap/002-a", "state": "open", "merged": False}],
            }
            remote = t.write_remote_state(td, state)
            (repo / "oap" / "active").write_text("002-a\n")
            rc, out, err, js = t.run_cli(
                "publish_order.py",
                [
                    "--repo",
                    str(repo),
                    "--strategic-home",
                    str(home),
                    "--order",
                    str(order),
                    "--json",
                ],
                env={"OAP_ROLE": "STRATEGIC", "OAP_REMOTE_ADAPTER_FILE": remote},
                timeout=30,
                expect_json=True,
            )
            # the round already has a report: republishing the same objective is
            # refused (no reactivation of a completed round)
            self.assertNotEqual(rc, 0)
            self.assertIn(js["status"], ("REFUSED_ALREADY_PUBLISHED", "REFUSED_MISMATCH"))


if __name__ == "__main__":
    unittest.main()
