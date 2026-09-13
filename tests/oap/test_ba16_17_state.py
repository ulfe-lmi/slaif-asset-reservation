"""BA-16/BA-17 — inactive state and pointer sanity (015-a slim round)."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "oap" / "bin"))

import oaplib  # noqa: E402
import oaptestlib as t  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
