"""BA-06 — dirty/untracked work.

A known touched (dirty) file that the candidate wants to replace blocks the
replacement and is left byte-identical; unrelated dirty/untracked bytes survive;
no reset/clean/stash command is ever invoked.
"""

import subprocess
import tempfile
import unittest
from pathlib import Path

import oaplib
import oaptestlib as t


class Ba06Dirty(unittest.TestCase):
    def test_ba06_dirty_touched_file_blocks_replacement(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba06")) as td:
            td = Path(td)
            repo = td / "repo"
            t.make_repo(repo, {"AGENTS.md": b"COMMITTED\n", "OTHER.md": b"other\n"})
            dirty_bytes = b"COMMITTED\n+unrelated local edit\n"
            (repo / "AGENTS.md").write_bytes(dirty_bytes)
            (repo / "untracked-note.txt").write_bytes(b"keep me\n")
            entries = [
                t.file_entry(
                    "REPO/AGENTS.md",
                    b"NEW CANDIDATE\n",
                    kind="archive_then_copy",
                    pre_sha256=oaplib.sha256_hex(b"COMMITTED\n"),
                    backup="REPO/docs/previous/AGENTS.md",
                )
            ]
            cr = t.make_manifest_root(
                td, entries + [t.file_entry("REPO/docs/previous/AGENTS.md", b"COMMITTED\n")]
            )
            boot = td / "boot"
            boot.mkdir(parents=True, exist_ok=True)
            rc, out, err, rep = t.run_engine(cr, repo, td / "home", boot, apply=True)
            self.assertEqual(rc, 1, "dirty touched file must block the replacement")
            self.assertEqual(
                (repo / "AGENTS.md").read_bytes(), dirty_bytes, "dirty bytes must remain untouched"
            )
            self.assertEqual((repo / "untracked-note.txt").read_bytes(), b"keep me\n")
            self.assertEqual(
                subprocess.run(
                    ["git", "-C", str(repo), "stash", "list"], capture_output=True
                ).stdout,
                b"",
            )

    def test_ba06_unrelated_dirty_and_untracked_preserved_on_apply(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba06b")) as td:
            td = Path(td)
            repo = td / "repo"
            t.make_repo(repo, {"AGENTS.md": b"COMMITTED\n", "UNTOUCHED.md": b"committed clean\n"})
            (repo / "UNTOUCHED.md").write_bytes(b"committed clean\n+dirty but unrelated\n")
            (repo / "scratch.txt").write_bytes(b"untracked\n")
            entries = [
                t.file_entry(
                    "REPO/AGENTS.md",
                    b"NEW CANDIDATE\n",
                    kind="archive_then_copy",
                    pre_sha256=oaplib.sha256_hex(b"COMMITTED\n"),
                    backup="REPO/docs/previous/AGENTS.md",
                )
            ]
            cr = t.make_manifest_root(
                td, entries + [t.file_entry("REPO/docs/previous/AGENTS.md", b"COMMITTED\n")]
            )
            boot = td / "boot"
            boot.mkdir()
            rc, out, err, rep = t.run_engine(cr, repo, td / "home", boot, apply=True)
            self.assertEqual(rc, 0, err)
            self.assertEqual((repo / "AGENTS.md").read_bytes(), b"NEW CANDIDATE\n")
            self.assertEqual(
                (repo / "UNTOUCHED.md").read_bytes(), b"committed clean\n+dirty but unrelated\n"
            )
            self.assertEqual((repo / "scratch.txt").read_bytes(), b"untracked\n")


if __name__ == "__main__":
    unittest.main()
