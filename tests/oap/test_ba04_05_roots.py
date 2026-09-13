"""BA-04/BA-05 — path identity/nesting and ownership/parent safety of the
validate_roots guard (shared oaplib; the materialization engine that consumed it
was archived in 015-a)."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "oap" / "bin"))

import oaplib  # noqa: E402
import oaptestlib as t  # noqa: E402


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
            st = real_lstat(p)
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
        """A symlinked staging parent resolves away; the guard must refuse it."""
        real_parent = self.td / "real-parent"
        real_parent.mkdir()
        link_parent = self.td / "link-parent"
        os.symlink(str(real_parent), str(link_parent))
        repo = self.td / "repo"
        repo.mkdir()
        boot = self.td / "boot"
        boot.mkdir()
        home = link_parent / "home-under-symlink"
        home.mkdir()
        errs = oaplib.validate_roots(repo, home, boot)
        self.assertTrue(any("symlink ancestor" in e for e in errs), errs)
        # no fallback to the resolved path: the error must name the ORIGINAL path
        self.assertTrue(any(str(link_parent) in e for e in errs), errs)


if __name__ == "__main__":
    unittest.main()
