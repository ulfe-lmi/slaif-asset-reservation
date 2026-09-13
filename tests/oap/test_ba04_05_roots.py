"""BA-04/BA-05 — path identity/nesting and ownership/parent safety."""

import os
import tempfile
import unittest
from pathlib import Path

import oaplib
import oaptestlib as t


class Ba04Roots(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix=t.unique_name("ba04"))
        self.td = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _base(self):
        self.repo = self.td / "repo"
        self.home = self.td / "home"
        self.boot = self.td / "boot"
        for p in (self.repo, self.boot):
            p.mkdir(parents=True, exist_ok=True)

    def test_ba04_identical_nested_rootfs_fail(self):
        self._base()
        self.assertTrue(
            any("identical" in e for e in oaplib.validate_roots(self.repo, self.repo, self.boot))
        )
        self.assertTrue(
            any(
                "nested" in e
                for e in oaplib.validate_roots(self.repo, self.repo / "child", self.boot)
            )
        )
        self.assertTrue(
            any("filesystem root" in e for e in oaplib.validate_roots("/", self.home, self.boot))
        )

    def test_ba04_regular_file_target_fails(self):
        self._base()
        f = self.td / "notadir"
        f.write_bytes(b"file")
        errs = oaplib.validate_roots(self.repo, f, self.boot)
        self.assertTrue(any("not a directory" in e for e in errs), errs)

    def test_ba04_symlink_root_fails(self):
        self._base()
        real = self.td / "real-home"
        real.mkdir()
        link = self.td / "link-home"
        os.symlink(str(real), str(link))
        errs = oaplib.validate_roots(self.repo, link, self.boot)
        self.assertTrue(any("symlink" in e for e in errs), errs)

    def test_ba04_spaces_unicode_and_worktree_file_succeed(self):
        self._base()
        pretty = self.td / "répo ünicode (x)"
        pretty.mkdir()
        t.make_repo(pretty, {"a.txt": b"1\n"})
        errs = oaplib.validate_roots(pretty, self.td / "home2", self.boot)
        self.assertEqual(errs, [], errs)
        # git worktree: .git is a FILE, roots must still validate
        wt = self.td / "wt"
        t.git(pretty, "worktree", "add", "-q", str(wt), "-b", "wt-branch")
        self.assertTrue((wt / ".git").is_file())
        errs2 = oaplib.validate_roots(wt, self.td / "home3", self.boot)
        self.assertEqual(errs2, [], errs2)
        self.assertEqual(oaplib.git_head(str(wt))["head"][:7], t.head(str(pretty))[:7])


class Ba05Ownership(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix=t.unique_name("ba05"))
        self.td = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_ba05_foreign_owner_refused(self):
        """A foreign-owned existing root directory is refused (lstat spoofed)."""
        repo = self.td / "repo"
        repo.mkdir()
        boot = self.td / "boot"
        boot.mkdir()
        me = os.getuid()
        real_lstat = os.lstat

        def fake_lstat(p, *a, **k):
            st = real_lstat(p, *a, **k)
            if Path(os.fspath(p)).name == "repo":
                st2 = real_lstat(p)
                lst = list(st2)
                lst[4] = me + 1  # st_uid: foreign owner
                return os.stat_result(lst)
            return st

        os.lstat = fake_lstat
        try:
            errs = oaplib.validate_roots(repo, self.td / "home", boot)
        finally:
            os.lstat = real_lstat
        self.assertTrue(any("foreign-owned" in e for e in errs), errs)

    def test_ba05_symlink_parent_escape_refused_no_fallback(self):
        """A symlinked staging subtree cannot write outside the owned root."""
        outside = self.td / "outside"
        outside.mkdir()
        repo = self.td / "repo"
        repo.mkdir()
        t.make_repo(repo, {"AGENTS.md": b"OLD\n"})
        boot = self.td / "boot"
        boot.mkdir()
        # strategic home parent is a symlink pointing outside the owned tree
        home_parent_link = self.td / "hlink"
        os.symlink(str(self.td / "outside"), str(home_parent_link))
        home = home_parent_link / "home"
        entries = [t.file_entry("STRATEGIC_HOME/AGENTS.md", b"STRAT\n")]
        cr = t.make_manifest_root(self.td, entries)
        rc, out, err, rep = t.run_engine(cr, repo, home, boot, apply=True)
        # refused at root validation OR at the safe write boundary: no writes outside
        if rc == 0:
            self.fail("symlink-parent strategic home must be refused")
        self.assertFalse(
            (outside / "home" / "AGENTS.md").exists()
            or (self.td / "outside" / "AGENTS.md").exists(),
            "no fallback write may escape the owned root",
        )
        self.assertEqual((repo / "AGENTS.md").read_bytes(), b"OLD\n")

    def test_ba05_no_broad_chmod_and_no_secret_reading(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba05c")) as td:
            td = Path(td)
            repo = td / "repo"
            t.make_repo(
                repo, {"AGENTS.md": b"OLD\n", "secret.env": b"SECRET_TOKEN=supersecretvalue\n"}
            )
            boot = td / "boot"
            boot.mkdir()
            entries = [
                t.file_entry(
                    "REPO/AGENTS.md",
                    b"NEW\n",
                    kind="archive_then_copy",
                    pre_sha256=oaplib.sha256_hex(b"OLD\n"),
                    backup="REPO/docs/previous/AGENTS.md",
                )
            ]
            cr = t.make_manifest_root(
                td, entries + [t.file_entry("REPO/docs/previous/AGENTS.md", b"OLD\n")]
            )
            before = t.snapshot(repo)
            rc, out, err, rep = t.run_engine(cr, repo, td / "home", boot, apply=True)
            self.assertEqual(rc, 0, err)
            after = t.snapshot(repo)
            # unrelated file: bytes AND mode untouched
            self.assertEqual(after["secret.env"], before["secret.env"])
            self.assertEqual(after["secret.env"][0], 0o644)
            # secret bytes never appear in any written governance output
            written = b""
            for p in repo.rglob("*"):
                if p.is_file() and p.name != "secret.env":
                    written += p.read_bytes()
            self.assertNotIn(b"SECRET_TOKEN=supersecretvalue", written)


if __name__ == "__main__":
    unittest.main()
