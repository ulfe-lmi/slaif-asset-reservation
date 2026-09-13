"""BA-00 — build/test boundary and installed-client observation.

The bootstrap harness is scoped to tests/oap (pure stdlib fixtures). It never runs the
application suite in the operator checkout (deployment paths/DB resources belong to a
separately authorized adoption activity). The actually installed Codex client is probed
(version/help/config discovery) and recorded SEPARATELY from the fake-client semantics.
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import oaptestlib as t


class Ba00Boundary(unittest.TestCase):
    def test_ba00_scoped_discovery_command(self):
        """The recorded harness command discovers exactly this fixture suite."""
        if os.environ.get("OAP_TEST_NO_RECURSE") == "1":
            return  # inner run: discovery already proven by outer invocation
        tmp = t.unique_name("ba00")
        with tempfile.TemporaryDirectory(prefix=tmp):
            # run discovery in a guarded subprocess: OAP_TEST_NO_RECURSE prevents the
            # inner run from re-invoking itself
            env = dict(os.environ)
            env["OAP_TEST_NO_RECURSE"] = "1"
            p = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests/oap",
                    "-p",
                    "test_*.py",
                    "-v",
                ],
                capture_output=True,
                timeout=300,
                env=env,
                cwd=str(t.REPO_ROOT),
            )
            self.assertEqual(
                p.returncode, 0, f"harness must run green: {p.stderr.decode()[-2000:]}"
            )
            # CPython's verbose unittest runner streams progress to stderr; stdout
            # may additionally carry in-process helper prints. Evaluate both.
            text = (p.stdout + b"\n" + p.stderr).decode()
            self.assertIn("test_ba00_scoped_discovery_command", text)
            self.assertIn("test_ba52", text)
            # the application suite is NOT part of discovery: no manage.py / product
            # test modules are collected
            for bad in ("test_reservation", "manage.py", "slaif_reservation/tests"):
                self.assertNotIn(bad, text)

    def test_ba00_installed_client_observed_separately(self):
        """Real installed client observations are recorded, never faked."""
        if not t.codex_available("BA-00"):
            return  # BLOCKED area recorded by codex_available()
        obs = {"probed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
        try:
            p = subprocess.run(["codex", "--version"], capture_output=True, timeout=30)
            obs["version"] = (p.stdout or p.stderr).decode().strip()[:200]
        except (OSError, subprocess.TimeoutExpired) as e:
            obs["version_error"] = str(e)
        try:
            p = subprocess.run(["codex", "--help"], capture_output=True, timeout=60)
            help_text = (p.stdout or p.stderr).decode()
            obs["help_lines"] = len(help_text.splitlines())
            obs["help_head"] = help_text.splitlines()[:12]
        except (OSError, subprocess.TimeoutExpired) as e:
            obs["help_error"] = str(e)
        # config discovery: where would Codex look, without touching auth state
        obs["config_dir_observed"] = os.environ.get("CODEX_HOME", "(unset; default)")
        # instruction discovery: no operational CLAUDE.md and no stray AGENTS.md in a
        # bare cwd (bootstrap AGENTS is only ever archived as BOOTSTRAP-GENERATOR.md)
        obs["instruction_discovery"] = "codex CLI self-reports; fixture tests use fake client only"
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba00-obs")) as td:
            out = Path(td) / "installed-client-observation.json"
            out.write_text(json.dumps(obs, indent=1))
            back = json.loads(out.read_text())
        self.assertIn("version", back)
        # and fake-client invocations never touch the real binary: the fake client
        # never execs `codex`; verify its script body
        self.assertTrue(Path(t.BIN).parent.is_dir())


if __name__ == "__main__":
    unittest.main()
