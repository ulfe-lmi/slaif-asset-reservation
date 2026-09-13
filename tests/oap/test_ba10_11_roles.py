"""BA-10/BA-11 — Codex-only routing and instruction discovery.

Missing/conflicting explicit roles refuse operational mutation; source inspection
or a cwd change never switches roles; the fake client records the exact visible
role prompt/cwd/CODEX_HOME. No copied bootstrap AGENTS, no Claude launcher, no
operational CLAUDE.md.
"""

import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import oaptestlib as t


def _ready_home(td: Path, repo: Path, fake: Path, activation: bool = True):
    home = td / "home"
    (home / "agent-homes" / "coding").mkdir(parents=True)
    (home / "agent-homes" / "strategic").mkdir(parents=True)
    t.write_runtime_env(
        home,
        repo,
        activation=activation,
        authority=True,
        coding_argv=[str(fake)],
        model="fixture-model",
    )
    t.make_fifo(home / "control.fifo")
    return home


class Ba10Routing(unittest.TestCase):
    def test_ba10_conflicting_role_refuses(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba10")) as td:
            td = Path(td)
            repo = td / "repo"
            t.make_repo(repo, {"AGENTS.md": b"router\n"})
            fake = t.install_fake_client(td)
            home = _ready_home(td, repo, fake)
            log = td / "fake.jsonl"
            env = {"OAP_ROLE": "STRATEGIC", "OAP_FAKE_LOG": str(log)}
            rc, out, err, js = t.run_cli(
                "oap_launch.py",
                ["coding", "--repo", str(repo), "--strategic-home", str(home)],
                env=env,
                timeout=30,
            )
            self.assertNotEqual(rc, 0, "conflicting role must refuse")
            self.assertIn("role", js["step"] if js else out)
            self.assertFalse(log.exists(), "no model invocation under a foreign role")

    def test_ba10_publish_and_append_require_roles(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba10b")) as td:
            td = Path(td)
            repo = td / "repo"
            t.make_repo(repo, {"AGENTS.md": b"x\n"})
            home = td / "home"
            home.mkdir()
            t.write_runtime_env(home, repo, activation=True, authority=True)
            # publish without STRATEGIC role
            rc, out, err, js = t.run_cli(
                "publish_order.py",
                [
                    "--repo",
                    str(repo),
                    "--strategic-home",
                    str(home),
                    "--order",
                    str(t.make_order_file(td)),
                    "--dry-run",
                    "--json",
                ],
                env={"OAP_ROLE": "CODING"},
                timeout=30,
                expect_json=True,
            )
            self.assertNotEqual(rc, 0)
            self.assertEqual(js["status"], "REFUSED_ROLE")
            # append_critical with a bootstrap/audit role
            rc2, out2, err2, js2 = t.run_cli(
                "append_critical.py",
                ["--repo", str(repo), "--order", "x.md", "--json"],
                env={"OAP_ROLE": "BOOTSTRAP"},
                timeout=30,
                expect_json=True,
            )
            self.assertNotEqual(rc2, 0)
            self.assertEqual(js2["status"], "REFUSED_ROLE")

    def test_ba10_inspection_and_cd_never_switch_role(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba10c")) as td:
            td = Path(td)
            repo = td / "repo"
            t.make_repo(repo, {"AGENTS.md": b"router\n", "docs/architecture.md": b"arch\n"})
            fake = t.install_fake_client(td)
            home = _ready_home(td, repo, fake)
            log = td / "fake.jsonl"
            env = {"OAP_ROLE": "CODING", "OAP_FAKE_LOG": str(log)}
            t.activate_order(repo)
            p = subprocess.Popen(
                [
                    sys.executable,
                    str(t.BIN / "oap_launch.py"),
                    "coding",
                    "--repo",
                    str(repo),
                    "--strategic-home",
                    str(home),
                ],
                env={**os.environ, **env},
                cwd=str(home),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                time.sleep(0.6)
                t.fifo_write(home / "control.fifo")
                time.sleep(1.4)
            finally:
                p.send_signal(signal.SIGTERM)
                try:
                    p.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    p.kill()
            recs = t.read_fake_log(log)
            self.assertEqual(len(recs), 1, "exactly one fresh invocation")
            self.assertEqual(recs[0]["OAP_ROLE"], "CODING")
            self.assertEqual(
                recs[0]["cwd"],
                os.path.realpath(str(repo)),
                "cwd is the repository even when launched from the home",
            )
            self.assertEqual(
                recs[0]["CODEX_HOME"], os.path.realpath(str(home / "agent-homes" / "coding"))
            )
            prompt = recs[0]["argv"][-1]
            self.assertIn("ROLE=CODING", prompt)
            self.assertIn("oap/active", prompt)


class Ba11Discovery(unittest.TestCase):
    def test_ba11_no_claude_or_archived_agents_discovered(self):
        """The materialized tree contains no operational CLAUDE.md and no AGENTS.md
        other than the root router and the two role instructions."""
        agents = sorted(p for p in t.REPO_ROOT.rglob("AGENTS.md") if ".git" not in p.parts)
        rels = {str(p.relative_to(t.REPO_ROOT)) for p in agents}
        allowed = {
            "AGENTS.md",
            "oap/coding-instructions/AGENTS.md",
            "oap/strategic-instructions/AGENTS.md",
        }
        self.assertEqual(rels, allowed, f"unexpected AGENTS.md discovered: {rels}")
        for p in t.REPO_ROOT.rglob("CLAUDE.md"):
            if ".git" not in p.parts:
                self.fail(f"operational CLAUDE.md present: {p}")
        home = t.real_strategic_home("BA-11")
        if home is not None:
            self.assertFalse((home / "CLAUDE.md").exists())
            self.assertTrue((home / "AGENTS.md").is_file())

    def test_ba11_fake_client_visible_prompt(self):
        """The visible prompt is the tiny role prompt file content, not an
        instruction discovery dump."""
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba11")) as td:
            td = Path(td)
            repo = td / "repo"
            t.make_repo(repo, {"AGENTS.md": b"router\n"})
            fake = t.install_fake_client(td)
            home = _ready_home(td, repo, fake)
            log = td / "fake.jsonl"
            env = {"OAP_ROLE": "CODING", "OAP_FAKE_LOG": str(log)}
            t.activate_order(repo)
            p = subprocess.Popen(
                [
                    sys.executable,
                    str(t.BIN / "oap_launch.py"),
                    "coding",
                    "--repo",
                    str(repo),
                    "--strategic-home",
                    str(home),
                ],
                env={**os.environ, **env},
                cwd=str(repo),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                time.sleep(0.6)
                t.fifo_write(home / "control.fifo")
                time.sleep(1.4)
            finally:
                p.send_signal(signal.SIGTERM)
                try:
                    p.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    p.kill()
            recs = t.read_fake_log(log)
            self.assertEqual(len(recs), 1)
            prompt = recs[0]["argv"][-1]
            self.assertLess(len(prompt), 600, "prompt must stay tiny")
            self.assertNotIn("oap.md", prompt)
            self.assertNotIn("BOOTSTRAP-GENERATOR", prompt)


if __name__ == "__main__":
    unittest.main()
