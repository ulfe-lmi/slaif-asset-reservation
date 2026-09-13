"""BA-16/BA-17 — inactive bootstrap and existing operational state."""

import os
import tempfile
import unittest
from pathlib import Path

import oaplib
import oaptestlib as t


class Ba16Inactive(unittest.TestCase):
    def test_ba16_fresh_install_is_inactive(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba16")) as td:
            td = Path(td)
            repo = td / "repo"
            t.make_repo(repo, {"AGENTS.md": b"router\n"})
            home = td / "home"
            home.mkdir()
            t.write_runtime_env(home, repo, activation=False)
            t.make_fifo(home / "control.fifo")
            t.make_fifo(home / "response.fifo")
            (repo / "oap" / "orders").mkdir(parents=True)
            (repo / "oap" / "reports").mkdir(parents=True)
            (repo / "CRITICAL.md").write_bytes(t.make_register([]))
            # no active pointer, no orders, no reports, zero live CRIT entries
            self.assertEqual(oaplib.read_pointer(repo / "oap" / "active")["state"], "ABSENT")
            self.assertEqual(list((repo / "oap" / "orders").glob("*.md")), [])
            self.assertEqual(list((repo / "oap" / "reports").glob("*.md")), [])
            entries, errs = oaplib.parse_register((repo / "CRITICAL.md").read_bytes())
            self.assertEqual(errs, [])
            self.assertEqual(entries, [])
            # no operational signal evidence anywhere
            self.assertFalse((home / "workorders" / "state.json").exists())
            state = oaplib.classify_state(str(repo), str(home))
            self.assertEqual(state["state"], "INACTIVE")

    def test_ba16_empty_or_malformed_pointer_rejected(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba16b")) as td:
            td = Path(td)
            repo = td / "repo"
            (repo / "oap").mkdir(parents=True)
            ptr = repo / "oap" / "active"
            ptr.write_bytes(b"")
            self.assertEqual(oaplib.read_pointer(ptr)["state"], "CORRUPT")
            ptr.write_bytes(b"001-a")  # missing LF
            self.assertEqual(oaplib.read_pointer(ptr)["state"], "CORRUPT")
            ptr.write_bytes(b"001-a\nextra\n")
            self.assertEqual(oaplib.read_pointer(ptr)["state"], "CORRUPT")
            ptr.write_bytes(b"1-a\n")  # bad ID grammar
            self.assertEqual(oaplib.read_pointer(ptr)["state"], "CORRUPT")
            # never treated as inactive: a corrupt pointer must not be silently ignored
            for bad in (b"", b"001-a", b"001-a\nextra\n", b"1-a\n"):
                ptr.write_bytes(bad)
                self.assertNotEqual(oaplib.read_pointer(ptr)["state"], "ABSENT")


class Ba17ExistingState(unittest.TestCase):
    def test_ba17_preexisting_operational_state_preserved(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba17")) as td:
            td = Path(td)
            repo = td / "repo"
            t.make_repo(repo, {"AGENTS.md": b"router\n"})
            head = t.head(repo)
            t.activate_order(repo)
            (repo / "oap" / "reports").mkdir(exist_ok=True)
            (repo / "oap" / "reports" / "001-a-canary.md").write_text(
                f"Implementation head SHA: {head}\nReport publication commit: SELF\n"
            )
            reg = t.make_register([t.make_crit_entry("CRIT-0001")])
            (repo / "CRITICAL.md").write_bytes(reg)
            home = td / "home"
            home.mkdir()
            t.make_fifo(home / "control.fifo")
            t.write_runtime_env(home, repo, activation=True, authority=True)
            # running role: a live lease in oap/leases
            (repo / "oap" / "leases").mkdir(parents=True)
            lease = repo / "oap" / "leases" / "strategic.lease"
            lease.write_text(f'{{"pid": {os.getpid()}, "owner": "strategic"}}')

            seed = b"# CRITICAL - zero-entry seed\n"
            entries = [
                t.file_entry("REPO/CRITICAL.md", seed, kind="seed_if_absent"),
                t.file_entry("REPO/AGENTS.md", b"router\n"),
            ]
            cr = t.make_manifest_root(td, entries)
            boot = td / "boot"
            boot.mkdir()
            rc, out, err, rep = t.run_engine(cr, repo, home, boot, apply=True)
            self.assertEqual(rc, 1, "running role must quiesce before any apply")
            self.assertEqual(rep["result"], "REFUSED_RUNNING_ROLE")
            # state untouched
            self.assertEqual((repo / "CRITICAL.md").read_bytes(), reg)
            self.assertEqual((repo / "oap" / "active").read_text(), "001-a\n")
            self.assertTrue((repo / "oap" / "reports" / "001-a-canary.md").exists())
            lease.unlink()
            rc2, out2, err2, rep2 = t.run_engine(cr, repo, home, boot, apply=True)
            self.assertEqual(rc2, 0, err2)
            self.assertEqual(
                (repo / "CRITICAL.md").read_bytes(),
                reg,
                "pre-existing register preserved, not reseeded",
            )
            self.assertEqual((repo / "oap" / "active").read_text(), "001-a\n")
            # existing FIFOs not recreated as duplicates
            import stat as _stat

            st = os.lstat(str(home / "control.fifo"))
            self.assertTrue(_stat.S_ISFIFO(st.st_mode))
            # recovery classification still sees the live order
            state = oaplib.classify_state(str(repo), str(home))
            self.assertEqual(state["state"], "REPORT_LOCAL")


if __name__ == "__main__":
    unittest.main()
