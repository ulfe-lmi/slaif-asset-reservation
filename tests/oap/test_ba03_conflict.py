"""BA-03 — plan/architecture/register conflicts.

An existing approved root PLAN.md / ARCHITECTURE.md / CRITICAL.md is preserved:
a different candidate is a conflict, never a silent replacement, and the register
seed never reseeds over live entries.
"""

import tempfile
import unittest
from pathlib import Path

import oaplib
import oaptestlib as t


class Ba03Conflict(unittest.TestCase):
    def test_ba03_existing_plan_architecture_preserved_on_conflict(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba03")) as td:
            td = Path(td)
            repo = td / "repo"
            plan_old = b"# APPROVED PLAN (locally accepted)\n"
            arch_old = b"# ACCEPTED ARCHITECTURE\n"
            t.make_repo(repo, {"PLAN.md": plan_old, "ARCHITECTURE.md": arch_old})
            entries = [
                t.file_entry("REPO/PLAN.md", b"# CANDIDATE PLAN (different)\n"),
                t.file_entry("REPO/ARCHITECTURE.md", b"# CANDIDATE ARCH (different)\n"),
            ]
            cr = t.make_manifest_root(td, entries)
            rc, out, err, rep = t.run_engine(cr, repo, td / "home", td / "boot", apply=True)
            self.assertEqual(rc, 1, "conflict must stop the run")
            self.assertEqual(rep["result"], "CONFLICTS")
            self.assertEqual((repo / "PLAN.md").read_bytes(), plan_old)
            self.assertEqual((repo / "ARCHITECTURE.md").read_bytes(), arch_old)

    def test_ba03_register_never_reseeded(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba03b")) as td:
            td = Path(td)
            repo = td / "repo"
            live = t.make_register([t.make_crit_entry("CRIT-0001")])
            t.make_repo(repo, {"CRITICAL.md": live})
            seed = b"# CRITICAL - zero-entry seed\n"
            entries = [t.file_entry("REPO/CRITICAL.md", seed, kind="seed_if_absent")]
            cr = t.make_manifest_root(td, entries)
            rc, out, err, rep = t.run_engine(cr, repo, td / "home", td / "boot", apply=True)
            self.assertEqual(rc, 0, err)
            self.assertEqual(
                (repo / "CRITICAL.md").read_bytes(),
                live,
                "live register must be preserved byte-for-byte",
            )
            entries2, errs2 = oaplib.parse_register(live)
            self.assertEqual(errs2, [])
            self.assertEqual([e["id"] for e in entries2], ["CRIT-0001"])

    def test_ba03_seed_applies_only_when_absent(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba03c")) as td:
            td = Path(td)
            repo = td / "repo"
            t.make_repo(repo, {"APP.txt": b"x\n"})
            seed = b"# CRITICAL - zero-entry seed\n"
            entries = [t.file_entry("REPO/CRITICAL.md", seed, kind="seed_if_absent")]
            cr = t.make_manifest_root(td, entries)
            rc, out, err, rep = t.run_engine(cr, repo, td / "home", td / "boot", apply=True)
            self.assertEqual(rc, 0, err)
            self.assertEqual((repo / "CRITICAL.md").read_bytes(), seed)
            # second run: preserved, no rewrite
            rc2, out2, err2, rep2 = t.run_engine(cr, repo, td / "home", td / "boot", apply=True)
            self.assertEqual(rc2, 0, err2)
            self.assertEqual((repo / "CRITICAL.md").read_bytes(), seed)


if __name__ == "__main__":
    unittest.main()
