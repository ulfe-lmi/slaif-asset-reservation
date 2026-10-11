"""Current-home portability without interpolation, foreign-home or guard bypass."""

import argparse
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "oap" / "bin"))
import oap_launch  # noqa: E402
import oaplib  # noqa: E402
import oaptestlib as t  # noqa: E402


class HomePaths(unittest.TestCase):
    def test_configuration_is_independent_of_cwd_and_account_name(self):
        text = (
            "OAP_REPO_ROOT=~/codex-work/project\n"
            "OAP_STRATEGIC_HOME=~/codex-supervision/project\n"
            'OAP_CODING_ARGV_JSON=["~/bin/codex","--profile","example","~/prompt.md"]\n'
        )
        for home in (Path("/fixture/account-a"), Path("/different/account-b")):
            with self.subTest(home=home), patch.object(oaplib.Path, "home", return_value=home):
                values, errors = oaplib.parse_runtime_env(text)
                self.assertEqual(errors, [])
                self.assertEqual(values["OAP_REPO_ROOT"], str(home / "codex-work/project"))
                self.assertEqual(
                    values["OAP_STRATEGIC_HOME"], str(home / "codex-supervision/project")
                )
                self.assertEqual(
                    values["OAP_CODING_ARGV_JSON"],
                    [str(home / "bin/codex"), "--profile", "example", str(home / "prompt.md")],
                )
        self.assertEqual(oaplib.resolve_home_path("file.md"), "file.md")
        self.assertEqual(oaplib.resolve_home_path("/absolute/path"), "/absolute/path")
        self.assertEqual(oaplib.resolve_home_path("~"), str(Path.home()))

    def test_rejects_foreign_home_escape_nul_and_shell_evaluation(self):
        bad = (
            "~another/project",
            "~/../outside",
            "~/a/../../outside",
            "~/bad\x00name",
            "~//outside",
        )
        for value in bad:
            with self.subTest(value=value):
                self.assertTrue(oaplib.parse_runtime_env("OAP_REPO_ROOT=" + value)[1])
                with self.assertRaises(oaplib.ValidationError):
                    oaplib.resolve_home_path(value)
                self.assertTrue(
                    oaplib.parse_runtime_env("OAP_CODING_ARGV_JSON=" + json.dumps([value]))[1]
                )
        for value in ("$HOME/project", "$(id)", "`id`", "~/one;two", "~/one&two", "relative/path"):
            with self.subTest(value=value):
                self.assertTrue(oaplib.parse_runtime_env("OAP_REPO_ROOT=" + value)[1])

    def test_root_safety_checks_original_expanded_ancestors(self):
        with tempfile.TemporaryDirectory(prefix="oap-home-guards-") as directory:
            home = Path(directory)
            (home / "real").mkdir()
            (home / "alias").symlink_to(home / "real", target_is_directory=True)
            (home / "strategy").mkdir()
            (home / "bootstrap").mkdir()
            with patch.object(oaplib.Path, "home", return_value=home):
                before = t.snapshot(directory)
                errors = oaplib.validate_roots(
                    "~/alias/repo", "~/strategy", "~/bootstrap", create_missing=False
                )
                self.assertTrue(any("symlink" in error for error in errors), errors)
                self.assertEqual(before, t.snapshot(directory))
                self.assertTrue(
                    oaplib.validate_roots("~", "~/strategy", "~/bootstrap", create_missing=False)
                )
                self.assertTrue(
                    oaplib.validate_roots(
                        "~/strategy", "~/strategy", "~/bootstrap", create_missing=False
                    )
                )

    def test_home_expansion_preserves_foreign_ownership_refusal(self):
        with tempfile.TemporaryDirectory(prefix="oap-owner-") as directory:
            home = Path(directory)
            for name in ("repo", "strategy", "bootstrap"):
                (home / name).mkdir()
            with (
                patch.object(oaplib.Path, "home", return_value=home),
                patch.object(oaplib, "_owner_ok", return_value=False),
            ):
                errors = oaplib.validate_roots(
                    "~/repo", "~/strategy", "~/bootstrap", create_missing=False
                )
                self.assertTrue(any("foreign-owned" in error for error in errors), errors)

    def test_real_cli_and_fake_client_use_resolved_paths_without_model_calls(self):
        # This owned directory is actually below the current home: no HOME/CODEX_HOME
        # environment override, personal config changes, or foreign fixture cleanup.
        with tempfile.TemporaryDirectory(prefix="oap-portable-", dir=Path.home()) as directory:
            root = Path(directory)
            repo, strategy = root / "repo", root / "strategy"
            repo.mkdir()
            fake = t.install_fake_client(root)
            log = root / "fake.log"
            t.write_runtime_env(
                strategy, repo, activation=True, authority=True, coding_argv=[str(fake)]
            )
            config = strategy / "runtime.env"
            config.write_text(config.read_text().replace(str(Path.home()) + "/", "~/"))
            portable_repo = "~/" + str(repo.relative_to(Path.home()))
            portable_home = "~/" + str(strategy.relative_to(Path.home()))
            rc, out, err, rendered = t.run_cli(
                "oap_launch.py",
                [
                    "coding",
                    "--repo",
                    portable_repo,
                    "--strategic-home",
                    portable_home,
                    "--print-only",
                ],
                cwd=root,
                expect_json=True,
            )
            self.assertEqual(rc, 0, out + err)
            self.assertEqual(rendered["cwd"], str(repo))
            self.assertEqual(rendered["codex_home"], str(strategy / "agent-homes/coding"))
            self.assertEqual(rendered["argv"][0], str(fake))
            self.assertFalse(log.exists(), "print-only must not launch even a fake client")
            # The shared parser's fully resolved argv can execute the owned fake
            # in the requested cwd; this is a contract fixture, not live inference.
            values = oaplib.load_runtime_env(config)
            result = subprocess.run(
                values["OAP_CODING_ARGV_JSON"],
                cwd=repo,
                env={
                    "PATH": os.environ["PATH"],
                    "OAP_FAKE_LOG": str(log),
                    "OAP_ROLE": "CODING",
                    "CODEX_HOME": rendered["codex_home"],
                },
                capture_output=True,
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            record = json.loads(log.read_text())
            self.assertEqual(record["cwd"], str(repo))
            self.assertEqual(record["OAP_ROLE"], "CODING")
            self.assertEqual(record["CODEX_HOME"], rendered["codex_home"])
            for invalid in ("~other/repo", "~/../repo"):
                rc, out, err, _ = t.run_cli(
                    "oap_launch.py",
                    [
                        "coding",
                        "--repo",
                        invalid,
                        "--strategic-home",
                        portable_home,
                        "--print-only",
                    ],
                )
                self.assertNotEqual(rc, 0)
                self.assertNotIn("Traceback", err)

    def test_setup_waits_for_child_chdir_and_cleans_only_its_session_on_timeout(self):
        with tempfile.TemporaryDirectory(prefix="oap-pane-readiness-") as directory:
            root = Path(directory)
            repo, strategy = root / "repo", root / "strategy"
            repo.mkdir()
            strategy.mkdir()
            args = argparse.Namespace(
                repo=str(repo),
                strategic_home=str(strategy),
                socket="fixture-owned",
                print_only=False,
            )
            calls = []
            probes = 0

            def tmux(base, command):
                nonlocal probes
                self.assertEqual(base, ["tmux", "-L", "fixture-owned"])
                calls.append(command)
                if command[0] == "has-session":
                    return 1, "", ""
                if command[0] == "list-panes":
                    probes += 1
                    return (
                        0,
                        (
                            str(root) + "\n" + str(root) + "\n"
                            if probes == 1
                            else str(strategy) + "\n" + str(repo) + "\n"
                        ),
                        "",
                    )
                return 0, "", ""

            with (
                patch.object(oaplib, "run_tmux", side_effect=tmux),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(oap_launch.cmd_setup_tmux(args), 0)
            self.assertEqual(probes, 2)
            self.assertFalse(any(command[0].startswith("kill") for command in calls))
            calls.clear()
            probes = -100
            with (
                patch.object(oaplib, "run_tmux", side_effect=tmux),
                patch.object(oap_launch.time, "monotonic", side_effect=[0, 3]),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                # The first probe still fails: deadline denies success and removes
                # only the newly created session on the selected owned socket.
                probes = 0
                self.assertEqual(oap_launch.cmd_setup_tmux(args), 1)
            self.assertIn(["kill-session", "-t", "oap-setup"], calls)
            self.assertFalse(any(command[0] == "kill-server" for command in calls))


if __name__ == "__main__":
    unittest.main()
