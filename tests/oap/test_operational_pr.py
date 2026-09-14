"""Operational GitRemote PR identity via read-only gh (015-b).

Proves the operational parsing path with a fake `gh` executable fixture placed
on PATH: correct mapping of pr(number) and pr_for_branch, unknown (never a
fabricated identity) on non-zero exit / timeout / bad JSON / missing gh /
missing origin, and an assertion that every gh argv used is read-only (no
create/edit/close/merge/comment/approve verbs or flags). Also verifies
verify_report.py check 3 against the operational adapter: PASS when a
matching open PR resolves, BLOCKED with the adapter reason when identity is
unresolvable (never a local pass, never a mismatch-on-unknown FAIL), and FAIL
reserved for genuine branch/head mismatches.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "oap" / "bin"))

import oaplib  # noqa: E402
import oaptestlib as t  # noqa: E402

FAKE_GH = r"""#!/usr/bin/env python3
# fixture-only fake gh CLI: records argv, emits canned JSON, never mutates.
import json
import os
import sys
import time

log = os.environ.get("OAP_FAKE_GH_LOG")
if log:
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(sys.argv[1:]) + "\n")

sleep = float(os.environ.get("OAP_FAKE_GH_SLEEP", "0") or "0")
if sleep:
    time.sleep(sleep)

if os.environ.get("OAP_FAKE_GH_BADJSON"):
    sys.stdout.write("this is not json\n")
    sys.exit(int(os.environ.get("OAP_FAKE_GH_EXIT", "0") or "0"))

argv = sys.argv[1:]
exit_code = int(os.environ.get("OAP_FAKE_GH_EXIT", "0") or "0")
if argv[:2] == ["pr", "view"]:
    print(json.dumps({
        "number": int(argv[2]),
        "headRefName": os.environ.get("OAP_FAKE_GH_BRANCH", "oap/001-a"),
        "headRefOid": os.environ.get("OAP_FAKE_GH_HEAD", "0" * 40),
        "state": os.environ.get("OAP_FAKE_GH_STATE", "OPEN"),
        "mergedAt": os.environ.get("OAP_FAKE_GH_MERGED_AT") or None,
    }))
    sys.exit(exit_code)
if argv[:2] == ["pr", "list"]:
    print(json.dumps([{
        "number": 30,
        "headRefName": os.environ.get("OAP_FAKE_GH_BRANCH", "oap/001-a"),
        "state": os.environ.get("OAP_FAKE_GH_STATE", "OPEN"),
        "mergedAt": os.environ.get("OAP_FAKE_GH_MERGED_AT") or None,
    }]))
    sys.exit(exit_code)
sys.stderr.write("unexpected gh argv: %r\n" % (argv,))
sys.exit(1)
"""

FORBIDDEN_GH_TOKENS = {
    "create",
    "close",
    "merge",
    "comment",
    "approve",
    "edit",
    "ready",
    "lock",
    "unlock",
    "update",
    "delete",
    "remove",
}


class patch_env:
    """Temporarily set (or remove, value None) environment variables."""

    def __init__(self, **vars):
        self.vars = vars
        self.saved = {}

    def __enter__(self):
        for key, value in self.vars.items():
            self.saved[key] = os.environ.get(key)
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        return self

    def __exit__(self, *exc):
        for key, value in self.saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        return False


def install_fake_gh(tmp: Path) -> Path:
    d = tmp / "fake-gh-bin"
    d.mkdir(exist_ok=True)
    p = d / "gh"
    p.write_text(FAKE_GH)
    p.chmod(0o755)
    return d


def git_only_dir(tmp: Path) -> Path:
    """A PATH directory that provides git (symlink) but no gh."""
    d = tmp / "git-only"
    d.mkdir(exist_ok=True)
    src = shutil.which("git")
    assert src, "git not found on PATH"
    os.symlink(src, d / "git")
    return d


def make_repo_with_origin(tmp: Path, url="https://github.com/fixture-org/fixture-repo.git") -> Path:
    repo = tmp / "repo"
    t.make_repo(repo, {"AGENTS.md": b"r\n"}, "baseline")
    t.git(repo, "remote", "add", "origin", url)
    return repo


def git_remote_adapter(repo: Path):
    """The operational GitRemote (OAP_REMOTE_ADAPTER_FILE never set here)."""
    saved = os.environ.pop("OAP_REMOTE_ADAPTER_FILE", None)
    try:
        return oaplib.load_remote_adapter(str(repo))
    finally:
        if saved is not None:
            os.environ["OAP_REMOTE_ADAPTER_FILE"] = saved


def report_text(impl_sha: str, order_digest: str) -> str:
    return (
        f"# Final report 001-a-canary\n\n"
        f"Order digest: {order_digest}\n"
        f"Implementation head SHA: {impl_sha}\n"
        "Report publication commit: SELF\n\n"
        "## Implementation head CI\n"
        "quality/test/security/container observed at the implementation head.\n\n"
        "## Report head CI\n"
        "NOT YET OBSERVED AT AUTHORING\n"
    )


def build_published_report_repo(tmp: Path, branch: str = "oap/001-a"):
    """Fixture repo: implementation + order + report-only commit, with the round
    branch pushed to a local bare 'origin' so ls-remote resolves (no network)."""
    repo = tmp / "repo"
    t.make_repo(repo, {"AGENTS.md": b"router\n"}, "baseline")
    impl = t.commit_files(repo, {"src/app.py": b"impl\n"}, "implementation head")
    orders = repo / "oap" / "orders"
    orders.mkdir(parents=True)
    order = t.make_order_file(repo, oid="001-a", base_sha=impl)
    order_bytes = order.read_bytes()
    (orders / "001-a-canary.md").write_bytes(order_bytes)
    order.unlink()
    t.git(repo, "add", "oap/orders")
    t.git(repo, "commit", "-q", "-m", "order bytes")
    impl = t.head(repo)
    rpath = repo / "oap" / "reports" / "001-a-canary.md"
    rpath.parent.mkdir(parents=True)
    rpath.write_text(report_text(impl, oaplib.sha256_hex(order_bytes)))
    t.git(repo, "add", "oap/reports/001-a-canary.md")
    t.git(repo, "commit", "-q", "-m", "report only")
    report_head = t.head(repo)
    t.git(repo, "branch", branch, report_head)
    bare = tmp / "origin.git"
    bare.mkdir(parents=True)
    t.git(bare, "init", "-q", "--bare")
    t.git(repo, "remote", "add", "origin", str(bare))
    t.git(repo, "push", "-q", "origin", branch)
    return repo, report_head


class OperationalPrMappingBase(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory(prefix=t.unique_name("oppr"))
        self.tmp = Path(self._td.name)
        self.gh_bin = install_fake_gh(self.tmp)
        self.log = self.tmp / "gh-argv.jsonl"
        self.repo = make_repo_with_origin(self.tmp)

    def tearDown(self):
        self._td.cleanup()

    def path_with_gh(self):
        return "{}{}{}".format(self.gh_bin, os.pathsep, os.environ.get("PATH", ""))

    def base_env(self, **extra):
        env = {"OAP_FAKE_GH_LOG": str(self.log), "OAP_REMOTE_ADAPTER_FILE": None}
        env.update(extra)
        return env


class TestGitRemotePr(OperationalPrMappingBase):
    def test_pr_maps_open_pr(self):
        with patch_env(PATH=self.path_with_gh(), **self.base_env()):
            pr = git_remote_adapter(self.repo).pr(str(self.repo), 30)
        self.assertEqual(pr["number"], 30)
        self.assertEqual(pr["branch"], "oap/001-a")
        self.assertEqual(pr["head"], "0" * 40)
        self.assertEqual(pr["state"], "open")
        self.assertFalse(pr["merged"])

    def test_pr_maps_merged_pr(self):
        env = self.base_env(
            OAP_FAKE_GH_STATE="MERGED", OAP_FAKE_GH_MERGED_AT="2026-01-02T03:04:05Z"
        )
        with patch_env(PATH=self.path_with_gh(), **env):
            pr = git_remote_adapter(self.repo).pr(str(self.repo), 30)
        self.assertEqual(pr["state"], "merged")
        self.assertTrue(pr["merged"])

    def test_pr_maps_closed_pr(self):
        with patch_env(PATH=self.path_with_gh(), **self.base_env(OAP_FAKE_GH_STATE="CLOSED")):
            pr = git_remote_adapter(self.repo).pr(str(self.repo), 30)
        self.assertEqual(pr["state"], "closed")
        self.assertFalse(pr["merged"])

    def test_pr_unknown_on_nonzero_exit(self):
        with patch_env(PATH=self.path_with_gh(), **self.base_env(OAP_FAKE_GH_EXIT="1")):
            pr = git_remote_adapter(self.repo).pr(str(self.repo), 30)
        self.assertEqual(pr, {"unknown": True, "reason": "gh exited with code 1"})

    def test_pr_unknown_on_bad_json(self):
        with patch_env(PATH=self.path_with_gh(), **self.base_env(OAP_FAKE_GH_BADJSON="1")):
            pr = git_remote_adapter(self.repo).pr(str(self.repo), 30)
        self.assertEqual(pr, {"unknown": True, "reason": "gh output not parseable as JSON"})

    def test_pr_unknown_on_timeout(self):
        with patch_env(PATH=self.path_with_gh(), **self.base_env(OAP_FAKE_GH_SLEEP="2")):
            data, why = oaplib.gh_readonly(
                str(self.repo),
                ["pr", "view", "30", "--json", oaplib.GH_PR_VIEW_FIELDS],
                timeout=0.3,
            )
        self.assertIsNone(data)
        self.assertEqual(why, "gh timed out")

    def test_pr_unknown_when_gh_missing(self):
        with patch_env(PATH=str(git_only_dir(self.tmp)), **self.base_env()):
            pr = git_remote_adapter(self.repo).pr(str(self.repo), 30)
        self.assertEqual(pr, {"unknown": True, "reason": "gh executable not found"})

    def test_pr_unknown_without_origin(self):
        repo2 = self.tmp / "repo-no-origin"
        t.make_repo(repo2, {"AGENTS.md": b"r\n"}, "baseline")
        with patch_env(PATH=self.path_with_gh(), **self.base_env()):
            pr = git_remote_adapter(repo2).pr(str(repo2), 30)
        self.assertEqual(pr, {"unknown": True, "reason": "origin remote not configured"})

    def test_pr_rejects_non_positive_integer(self):
        with patch_env(PATH=self.path_with_gh(), **self.base_env()):
            adapter = git_remote_adapter(self.repo)
            for bad in ("30", 0, -1, True):
                pr = adapter.pr(str(self.repo), bad)
                self.assertEqual(
                    pr, {"unknown": True, "reason": "PR number must be a positive integer"}
                )

    def test_pr_for_branch_maps_matching_branch(self):
        with patch_env(PATH=self.path_with_gh(), **self.base_env()):
            adapter = git_remote_adapter(self.repo)
            pr = adapter.pr_for_branch(str(self.repo), "oap/001-a")
        self.assertEqual(pr["number"], 30)
        self.assertEqual(pr["branch"], "oap/001-a")
        self.assertEqual(pr["state"], "open")
        self.assertFalse(pr["merged"])
        self.assertIsNone(pr["head"], "list template does not request headRefOid")

    def test_pr_for_branch_none_when_absent(self):
        with patch_env(PATH=self.path_with_gh(), **self.base_env()):
            pr = git_remote_adapter(self.repo).pr_for_branch(str(self.repo), "other-branch")
        self.assertIsNone(pr)

    def test_pr_for_branch_prefers_open_over_merged(self):
        state_file = self.tmp / "list.json"
        state_file.write_text(
            json.dumps(
                [
                    {
                        "number": 7,
                        "headRefName": "oap/001-a",
                        "state": "MERGED",
                        "mergedAt": "2026-01-01T00:00:00Z",
                    },
                    {"number": 8, "headRefName": "oap/001-a", "state": "OPEN", "mergedAt": None},
                ]
            )
        )
        gh = self.tmp / "list-gh-bin"
        gh.mkdir()
        fake = gh / "gh"
        fake.write_text(
            "#!/usr/bin/env python3\n"
            "import json, sys\n"
            "print(json.dumps(json.load(open(r" + repr(str(state_file)) + "))))\n"
            "sys.exit(0)\n"
        )
        fake.chmod(0o755)
        with patch_env(
            PATH="{}{}{}".format(gh, os.pathsep, os.environ.get("PATH", "")), **self.base_env()
        ):
            pr = git_remote_adapter(self.repo).pr_for_branch(str(self.repo), "oap/001-a")
        self.assertEqual(pr["number"], 8, "open PR on the branch wins over merged")
        self.assertEqual(pr["state"], "open")

    def test_owner_name_url_forms(self):
        repo = self.repo
        owner, why = oaplib.gh_owner_name(str(repo))
        self.assertEqual((owner, why), ("fixture-org/fixture-repo", None))
        t.git(repo, "remote", "set-url", "origin", "git@github.com:scp-org/scp-repo.git")
        self.assertEqual(oaplib.gh_owner_name(str(repo)), ("scp-org/scp-repo", None))
        t.git(repo, "remote", "set-url", "origin", "ssh://git@github.com/ssl-org/ssl-repo.git")
        self.assertEqual(oaplib.gh_owner_name(str(repo)), ("ssl-org/ssl-repo", None))
        t.git(repo, "remote", "set-url", "origin", "not-a-url")
        owner, why = oaplib.gh_owner_name(str(repo))
        self.assertIsNone(owner)
        self.assertEqual(why, "cannot parse owner/name from origin URL")
        t.git(
            repo, "remote", "set-url", "origin", "https://github.com/fixture-org/fixture-repo.git"
        )


class TestReadOnlyGhArgv(OperationalPrMappingBase):
    def test_every_gh_argv_is_read_only(self):
        with patch_env(PATH=self.path_with_gh(), **self.base_env()):
            adapter = git_remote_adapter(self.repo)
            adapter.pr(str(self.repo), 30)
            adapter.pr_for_branch(str(self.repo), "oap/001-a")
        lines = [json.loads(line) for line in self.log.read_text().splitlines() if line.strip()]
        self.assertEqual(len(lines), 2)
        expected_view = [
            "pr",
            "view",
            "30",
            "--json",
            "number,headRefName,headRefOid,state,mergedAt",
            "--repo",
            "fixture-org/fixture-repo",
        ]
        expected_list = [
            "pr",
            "list",
            "--state",
            "all",
            "--json",
            "number,headRefName,state,mergedAt",
            "--repo",
            "fixture-org/fixture-repo",
        ]
        self.assertEqual(lines[0], expected_view)
        self.assertEqual(lines[1], expected_list)
        for argv in lines:
            self.assertEqual(argv[0], "pr")
            self.assertIn(argv[1], ("view", "list"))
            tokens = {tok.lower() for tok in argv if not tok.startswith("--")}
            self.assertFalse(tokens & FORBIDDEN_GH_TOKENS, argv)
            flags = {tok for tok in argv if tok.startswith("--")}
            wanted = {"--json", "--repo"} | ({"--state"} if argv[1] == "list" else set())
            self.assertEqual(flags, wanted, argv)


class TestVerifyReportPrIdentity(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory(prefix=t.unique_name("oprpt"))
        self.tmp = Path(self._td.name)
        self.gh_bin = install_fake_gh(self.tmp)

    def tearDown(self):
        self._td.cleanup()

    def run_verify(self, repo, report_head, args_extra, env):
        rc, out, err, js = t.run_cli(
            "verify_report.py",
            ["--repo", str(repo), "--id", "001-a", "--head", report_head, "--remote", "origin"]
            + args_extra
            + ["--json"],
            env=env,
            timeout=60,
            expect_json=True,
        )
        return rc, js

    def gh_env(self, **extra):
        env = {
            "PATH": "{}{}{}".format(self.gh_bin, os.pathsep, os.environ.get("PATH", "")),
            "OAP_REMOTE_ADAPTER_FILE": "",
            "OAP_FAKE_GH_BRANCH": "oap/001-a",
            "OAP_FAKE_GH_STATE": "OPEN",
        }
        env.update(extra)
        return env

    def test_pass_with_resolved_open_pr(self):
        repo, report_head = build_published_report_repo(self.tmp)
        rc, js = self.run_verify(
            repo,
            report_head,
            ["--pr", "30"],
            self.gh_env(OAP_FAKE_GH_HEAD=report_head),
        )
        self.assertEqual(rc, 0, js)
        self.assertEqual(js["status"], "PASS", js)
        self.assertFalse(js["test_mode_adapter"], "operational adapter, not fixture")
        for name, c in js["checks"].items():
            self.assertTrue(c["ok"], (name, js))
        self.assertIn("PR 30 bound", js["checks"]["remote_head_and_pr_identity"]["detail"])

    def test_pass_without_pr_flag(self):
        repo, report_head = build_published_report_repo(self.tmp)
        rc, js = self.run_verify(repo, report_head, [], self.gh_env(OAP_FAKE_GH_HEAD=report_head))
        self.assertEqual(rc, 0, js)
        self.assertEqual(js["status"], "PASS", js)
        detail = js["checks"]["remote_head_and_pr_identity"]["detail"]
        self.assertIn("branch oap/001-a", detail)
        self.assertNotIn("bound", detail)

    def test_blocked_when_gh_missing(self):
        repo, report_head = build_published_report_repo(self.tmp)
        env = {"PATH": str(git_only_dir(self.tmp)), "OAP_REMOTE_ADAPTER_FILE": ""}
        rc, js = self.run_verify(repo, report_head, ["--pr", "30"], env)
        self.assertEqual(js["status"], "BLOCKED", js)
        c3 = js["checks"]["remote_head_and_pr_identity"]
        self.assertFalse(c3["ok"])
        self.assertEqual(c3["status"], "BLOCKED")
        self.assertIn("PR identity unresolvable", c3["detail"])
        self.assertIn("gh executable not found", c3["detail"])
        self.assertTrue(js["checks"]["report_only_changed_path"]["ok"], js)
        self.assertTrue(js["checks"]["implementation_head_first_parent"]["ok"], js)

    def test_blocked_when_gh_missing_without_pr_flag(self):
        repo, report_head = build_published_report_repo(self.tmp)
        env = {"PATH": str(git_only_dir(self.tmp)), "OAP_REMOTE_ADAPTER_FILE": ""}
        rc, js = self.run_verify(repo, report_head, [], env)
        self.assertEqual(js["status"], "BLOCKED", js)
        self.assertIn(
            "PR identity unresolvable", js["checks"]["remote_head_and_pr_identity"]["detail"]
        )

    def test_blocked_when_gh_fails(self):
        repo, report_head = build_published_report_repo(self.tmp)
        env = self.gh_env(OAP_FAKE_GH_EXIT="1", OAP_FAKE_GH_HEAD=report_head)
        rc, js = self.run_verify(repo, report_head, ["--pr", "30"], env)
        self.assertEqual(js["status"], "BLOCKED", js)
        self.assertIn(
            "gh exited with code 1", js["checks"]["remote_head_and_pr_identity"]["detail"]
        )

    def test_branch_mismatch_stays_fail(self):
        repo, report_head = build_published_report_repo(self.tmp)
        env = self.gh_env(OAP_FAKE_GH_BRANCH="other-branch", OAP_FAKE_GH_HEAD=report_head)
        rc, js = self.run_verify(repo, report_head, ["--pr", "30"], env)
        self.assertEqual(rc, 1, js)
        self.assertEqual(js["status"], "FAIL", js)
        self.assertIn("!= order branch", js["checks"]["remote_head_and_pr_identity"]["detail"])

    def test_head_mismatch_stays_fail(self):
        repo, report_head = build_published_report_repo(self.tmp)
        env = self.gh_env(OAP_FAKE_GH_HEAD="f" * 40)
        rc, js = self.run_verify(repo, report_head, ["--pr", "30"], env)
        self.assertEqual(rc, 1, js)
        self.assertEqual(js["status"], "FAIL", js)
        self.assertIn("!= report commit", js["checks"]["remote_head_and_pr_identity"]["detail"])


if __name__ == "__main__":
    unittest.main()
