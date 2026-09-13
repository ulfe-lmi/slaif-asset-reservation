"""BA-14 — candidate vs accepted.

A governance-changing fixture PR is checked against the accepted base with the
ordered scope: out-of-scope changes fail, and the candidate cannot grant itself
merge or activation.
"""

import tempfile
import unittest
from pathlib import Path

import oaptestlib as t


class Ba14Scope(unittest.TestCase):
    def _fixture(self, td: Path):
        repo = td / "repo"
        t.make_repo(
            repo,
            {
                "AGENTS.md": b"router\n",
                "SECURITY.md": b"security\n",
                "oap/strategic-instructions/AGENTS.md": b"strategy law\n",
                "uv.lock": b"lock\n",
            },
            "accepted base",
        )
        base = t.head(repo)
        return repo, base

    def test_ba14_in_scope_candidate_passes(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba14")) as td:
            td = Path(td)
            repo, base = self._fixture(td)
            t.commit_files(
                repo,
                {
                    "oap/strategic-instructions/AGENTS.md": b"strategy law v2\n",
                    "AGENTS.md": b"router v2\n",
                },
                "candidate",
            )
            rc, out, err, js = t.run_cli(
                "check_governance.py",
                [
                    "--repo",
                    str(repo),
                    "--json",
                    "--accepted-base",
                    base,
                    "--scope",
                    "oap/strategic-instructions/,AGENTS.md",
                ],
                timeout=60,
                expect_json=True,
            )
            self.assertEqual(rc, 0, out)
            self.assertTrue(js["checks"]["candidate_scope_vs_accepted"]["ok"])

    def test_ba14_out_of_scope_candidate_fails(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba14b")) as td:
            td = Path(td)
            repo, base = self._fixture(td)
            t.commit_files(
                repo,
                {
                    "oap/strategic-instructions/AGENTS.md": b"strategy law v2\n",
                    "SECURITY.md": b"security TAMPERED\n",
                },
                "candidate",
            )
            rc, out, err, js = t.run_cli(
                "check_governance.py",
                [
                    "--repo",
                    str(repo),
                    "--json",
                    "--accepted-base",
                    base,
                    "--scope",
                    "oap/strategic-instructions/",
                ],
                timeout=60,
                expect_json=True,
            )
            self.assertEqual(rc, 1)
            self.assertFalse(js["checks"]["candidate_scope_vs_accepted"]["ok"])
            self.assertIn("SECURITY.md", js["checks"]["candidate_scope_vs_accepted"]["detail"])

    def test_ba14_candidate_cannot_self_activate(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba14c")) as td:
            td = Path(td)
            repo, base = self._fixture(td)
            home = td / "home"
            home.mkdir()
            # activation disabled in config: publishing a candidate order is blocked
            t.write_runtime_env(home, repo, activation=False, authority=True)
            order = t.make_order_file(td, base_sha=base)
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
                env={"OAP_ROLE": "STRATEGIC"},
                timeout=30,
                expect_json=True,
            )
            self.assertNotEqual(rc, 0)
            self.assertEqual(
                js["status"], "BLOCKED_INACTIVE", "a candidate order cannot grant itself activation"
            )
            # and with activation on but no attributable authority, still blocked
            t.write_runtime_env(home, repo, activation=True, authority=False)
            rc2, out2, err2, js2 = t.run_cli(
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
                env={"OAP_ROLE": "STRATEGIC"},
                timeout=30,
                expect_json=True,
            )
            self.assertNotEqual(rc2, 0)
            self.assertEqual(js2["status"], "BLOCKED_AUTHORITY")


if __name__ == "__main__":
    unittest.main()
