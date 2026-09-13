"""BA-38/BA-39 — setup tmux before credentials; operation prerequisite refusal
and strict runtime.env data parsing (never evaluated).
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "oap" / "bin"))

import oaplib  # noqa: E402
import oaptestlib as t  # noqa: E402


def _tmux_base(socket):
    return [t.TMUX, "-L", socket] if t.TMUX else []


class Ba38SetupTmux(unittest.TestCase):
    def setUp(self):
        if not t.TMUX:
            t.record_blocked("BA-38", "tmux not installed in this environment")
            self.skipTest("tmux not installed")
        self.td = Path(tempfile.mkdtemp(prefix=t.unique_name("ba38")))
        self.repo = self.td / "repo"
        self.repo.mkdir()
        self.home = self.td / "home"
        self.home.mkdir()
        t.write_runtime_env(self.home, self.repo, activation=False)
        self.socket = t.tmux_socket()

    def tearDown(self):
        t.tmux_run(self.socket, ["kill-server"])

    def test_ba38_two_side_by_side_panes_correct_cwds(self):
        rc, out, err, js = t.run_cli(
            "oap_launch.py",
            [
                "setup-tmux",
                "--repo",
                str(self.repo),
                "--strategic-home",
                str(self.home),
                "--socket",
                self.socket,
            ],
            expect_json=True,
        )
        self.assertEqual(rc, 0, out + err)
        self.assertTrue(js["ok"])
        rc, out, err = t.tmux_run(
            self.socket, ["list-panes", "-t", "oap-setup", "-F", "#{pane_id}|#{pane_current_path}"]
        )
        self.assertEqual(rc, 0, err)
        lines = [line for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 2, f"exactly two panes expected: {out!r}")
        paths = {line.split("|", 1)[1] for line in lines}
        self.assertEqual(paths, {str(self.home), str(self.repo)})
        # nothing activated: no active order, no operational FIFOs, no config mutation
        self.assertFalse((self.repo / "oap" / "active").exists())
        self.assertFalse((self.home / "control.fifo").exists())
        env_after = (self.home / "runtime.env").read_text()
        self.assertIn("OAP_ACTIVATION_ENABLED=false", env_after)

    def test_ba38_refuses_to_repurpose_existing_session(self):
        args = [
            "setup-tmux",
            "--repo",
            str(self.repo),
            "--strategic-home",
            str(self.home),
            "--socket",
            self.socket,
        ]
        rc1, out1, err1, _ = t.run_cli("oap_launch.py", args, expect_json=True)
        self.assertEqual(rc1, 0, out1 + err1)
        rc2, out2, err2, js2 = t.run_cli("oap_launch.py", args, expect_json=True)
        self.assertEqual(rc2, 1)
        self.assertIn("already exists", out2 + err2)
        # first session untouched: still exactly two panes
        rc, out, err = t.tmux_run(self.socket, ["list-panes", "-t", "oap-setup"])
        self.assertEqual(rc, 0)
        self.assertEqual(len([line for line in out.splitlines() if line.strip()]), 2)

    def test_ba38_print_only_writes_nothing(self):
        before = t.snapshot(str(self.td))
        rc, out, err, js = t.run_cli(
            "oap_launch.py",
            [
                "setup-tmux",
                "--repo",
                str(self.repo),
                "--strategic-home",
                str(self.home),
                "--print-only",
            ],
            expect_json=True,
        )
        self.assertEqual(rc, 0)
        self.assertTrue(js["print_only"])
        after = t.snapshot(str(self.td))
        self.assertEqual(before, after)
        rc, out, err = t.tmux_run(self.socket, ["has-session", "-t", "oap-setup"])
        self.assertNotEqual(rc, 0, "print-only must not create a session")


class Ba39OperationPrereqs(unittest.TestCase):
    def setUp(self):
        self.td = Path(tempfile.mkdtemp(prefix=t.unique_name("ba39")))
        self.repo = self.td / "repo"
        self.repo.mkdir()
        self.home = self.td / "home"
        self.fake_log = self.td / "fake-codex.log"

    def _run_coding(self, extra_env=None):
        env = {"OAP_FAKE_LOG": str(self.fake_log)}
        if extra_env:
            env.update(extra_env)
        return t.run_cli(
            "oap_launch.py",
            ["coding", "--repo", str(self.repo), "--strategic-home", str(self.home)],
            env=env,
            expect_json=True,
        )

    def test_ba39_activation_disabled_refused(self):
        t.write_runtime_env(
            self.home,
            self.repo,
            activation=False,
            authority=True,
            coding_argv=["/nonexistent/fake-codex"],
            model="fixture-model",
        )
        rc, out, err, js = self._run_coding()
        self.assertNotEqual(rc, 0)
        self.assertEqual(js["step"], "prerequisites")
        self.assertIn("activation disabled", js["error"])
        self.assertFalse(self.fake_log.exists(), "no model invocation while blocked")

    def test_ba39_no_authority_refused(self):
        t.write_runtime_env(
            self.home,
            self.repo,
            activation=True,
            authority=False,
            coding_argv=["/nonexistent/fake-codex"],
            model="fixture-model",
        )
        rc, out, err, js = self._run_coding()
        self.assertNotEqual(rc, 0)
        self.assertIn("authority", js["error"])
        self.assertFalse(self.fake_log.exists())

    def test_ba39_no_argv_refused(self):
        t.write_runtime_env(
            self.home,
            self.repo,
            activation=True,
            authority=True,
            coding_argv=[],
            model="fixture-model",
        )
        rc, out, err, js = self._run_coding()
        self.assertNotEqual(rc, 0)
        self.assertIn("ARGV", js["error"])
        self.assertFalse(self.fake_log.exists())

    def test_ba39_no_model_refused(self):
        t.write_runtime_env(
            self.home,
            self.repo,
            activation=True,
            authority=True,
            coding_argv=["/nonexistent/fake-codex"],
            model="",
        )
        rc, out, err, js = self._run_coding()
        self.assertNotEqual(rc, 0)
        self.assertIn("model", js["error"])
        self.assertFalse(self.fake_log.exists())

    def test_ba39_conflicting_role_refused(self):
        t.write_runtime_env(
            self.home,
            self.repo,
            activation=True,
            authority=True,
            coding_argv=["/nonexistent/fake-codex"],
            model="fixture-model",
        )
        rc, out, err, js = self._run_coding(extra_env={"OAP_ROLE": "STRATEGIC"})
        self.assertNotEqual(rc, 0)
        self.assertEqual(js["step"], "role")
        self.assertFalse(self.fake_log.exists())

    def test_ba39_strategic_same_prerequisites(self):
        t.write_runtime_env(
            self.home,
            self.repo,
            activation=True,
            authority=True,
            strategic_argv=[],
            model="fixture-model",
        )
        rc, out, err, js = t.run_cli(
            "oap_launch.py",
            [
                "strategic",
                "--repo",
                str(self.repo),
                "--strategic-home",
                str(self.home),
                "--print-only",
            ],
            expect_json=True,
        )
        self.assertEqual(rc, 0, "print-only is always allowed")
        self.assertIn("UNCONFIGURED", out)
        rc2, out2, err2, js2 = t.run_cli(
            "oap_launch.py",
            ["strategic", "--repo", str(self.repo), "--strategic-home", str(self.home)],
            expect_json=True,
        )
        self.assertNotEqual(rc2, 0)
        self.assertIn("ARGV", js2["error"])


class Ba39RuntimeEnvParser(unittest.TestCase):
    def test_ba39_strict_parse_rejects_interpolation_and_commands(self):
        base = "OAP_PROFILE_VERSION=1\n"
        cases = {
            "$": base + "OAP_TARGET_MILESTONE=hello $HOME\n",
            "backtick": base + "OAP_TARGET_MILESTONE=`whoami`\n",
            "semicolon": base + "OAP_TARGET_MILESTONE=a;b\n",
            "ampersand": base + "OAP_TARGET_MILESTONE=a&b\n",
            "backslash": base + "OAP_TARGET_MILESTONE=a\\b\n",
            "unknown_key": base + "OAP_SOMETHING_ELSE=1\n",
            "duplicate_key": base + "OAP_BASE_BRANCH=main\nOAP_BASE_BRANCH=main2\n",
            "bad_bool": base + "OAP_ACTIVATION_ENABLED=maybe\n",
            "bad_int": base + "OAP_PROFILE_VERSION=1x\n",
            "bad_jsonlist": base + 'OAP_CODING_ARGV_JSON={"not":"a list"}\n',
            "jsonlist_bad_token": base + 'OAP_CODING_ARGV_JSON=["ok", "$HOME"]\n',
            "relative_path": base + "OAP_CODING_HOME=relative/path\n",
            "not_key_value": base + "just some text\n",
        }
        for name, text in cases.items():
            values, errs = oaplib.parse_runtime_env(text)
            self.assertTrue(errs, f"{name} must be rejected: {text!r}")
        # $ and friends are data, never evaluated: a side-effect marker cannot appear
        marker = self.td_marker = Path(tempfile.gettempdir()) / f"oap-eval-{os.getpid()}"
        values, errs = oaplib.parse_runtime_env(base + f"OAP_TARGET_MILESTONE=$(touch {marker})\n")
        self.assertTrue(errs)
        self.assertFalse(marker.exists(), "parser must never evaluate shell constructs")

    def test_ba39_strict_parse_accepts_clean_data(self):
        text = (
            "OAP_PROFILE_VERSION=1\n"
            "OAP_REPO_ROOT=/abs/repo\n"
            "OAP_BASE_BRANCH=main\n"
            "OAP_ACTIVATION_ENABLED=false\n"
            "OAP_DEVELOPMENT_MERGE_ENABLED=false\n"
            'OAP_CODING_ARGV_JSON=["/abs/codex", "exec"]\n'
            "OAP_CODING_MODEL=\n"
            "# a comment line\n\n"
        )
        values, errs = oaplib.parse_runtime_env(text)
        self.assertEqual(errs, [])
        self.assertIs(values["OAP_ACTIVATION_ENABLED"], False)
        self.assertEqual(values["OAP_CODING_ARGV_JSON"], ["/abs/codex", "exec"])
        self.assertEqual(values["OAP_CODING_MODEL"], "")

    def test_ba39_runtime_env_file_load_rejects_errors(self):
        td = Path(tempfile.mkdtemp(prefix=t.unique_name("ba39env")))
        p = td / "runtime.env"
        p.write_text("OAP_ACTIVATION_ENABLED=TRUE\n")
        with self.assertRaises(oaplib.ValidationError):
            oaplib.load_runtime_env(p)


if __name__ == "__main__":
    unittest.main()
