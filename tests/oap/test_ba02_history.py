"""BA-02 — existing app/history preservation.

A fixture with a real application (app code, migrations, lockfile) and a real Git
history: the conversion must change ONLY the governance allowlist, archive the
governing file, and leave application bytes and ancestry untouched.
"""

import tempfile
import unittest
from pathlib import Path

import oaplib
import oaptestlib as t


class Ba02History(unittest.TestCase):
    def test_ba02_app_bytes_and_ancestry_preserved(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba02")) as td:
            td = Path(td)
            repo = td / "repo"
            app_files = {
                "src/app/reservations.py": b"def reserve():\n    return 'ok'\n",
                "src/app/migrations/0001_initial.py": b"MIGRATION = 1\n",
                "src/app/migrations/0002_tokens.py": b"MIGRATION = 2\n",
                "uv.lock": b"lock = 1\n",
                "pyproject.toml": b"[project]\nname = 'app'\n",
            }
            t.make_repo(repo, {**app_files, "AGENTS.md": b"OLD GOVERNING LAW\n"}, "baseline")
            t.commit_files(
                repo, {"src/app/reservations.py": b"def reserve():\n    return 'v2'\n"}, "feature"
            )
            ancestry = t.log_ids(repo)
            self.assertEqual(len(ancestry), 2)

            router = b"# role router (fixture)\n\nCODEX ONLY.\n"
            backup_rel = "REPO/docs/previous/AGENTS.pre-conversion.md"
            entries = [
                t.file_entry(
                    "REPO/AGENTS.md",
                    router,
                    kind="archive_then_copy",
                    pre_sha256=oaplib.sha256_hex(b"OLD GOVERNING LAW\n"),
                    backup=backup_rel,
                ),
                t.file_entry(backup_rel, b"OLD GOVERNING LAW\n"),
                t.file_entry("REPO/oap/README.md", b"# oap (fixture)\n"),
            ]
            cr = t.make_manifest_root(td, entries)
            rc, out, err, rep = t.run_engine(cr, repo, td / "home", td / "boot", apply=True)
            self.assertEqual(rc, 0, err)

            # application bytes byte-identical
            for rel, data in app_files.items():
                if rel == "src/app/reservations.py":
                    continue
                self.assertEqual((repo / rel).read_bytes(), data, f"app bytes changed: {rel}")
            self.assertEqual(
                (repo / "src/app/reservations.py").read_bytes(),
                b"def reserve():\n    return 'v2'\n",
            )
            # ancestry intact
            self.assertEqual(t.log_ids(repo), ancestry)
            # governing file replaced, original archived byte-identically
            self.assertEqual((repo / "AGENTS.md").read_bytes(), router)
            self.assertEqual(
                (repo / "docs/previous/AGENTS.pre-conversion.md").read_bytes(),
                b"OLD GOVERNING LAW\n",
            )
            # only allowlisted governance paths changed in the worktree
            rc, status, _ = t.git.__self__ if False else (0, "", "")
            import subprocess

            st = subprocess.run(
                ["git", "-C", str(repo), "status", "--porcelain", "-uall"],
                capture_output=True,
                env=dict(__import__("os").environ),
            )
            changed = [ln[3:].strip() for ln in st.stdout.decode().splitlines() if ln.strip()]
            allowed = {"AGENTS.md", "docs/previous/AGENTS.pre-conversion.md", "oap/README.md"}
            self.assertEqual(set(changed), allowed, f"unexpected paths changed: {changed}")

    def test_ba02_no_git_destructive_commands(self):
        """The engine never invokes reset/clean/stash/rebase or force-push."""
        import oaplib as _ol

        calls = []
        real_git = _ol.git

        def spy(cwd, *args, **kw):
            calls.append(args)
            return real_git(cwd, *args, **kw)

        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba02b")) as td:
            td = Path(td)
            repo = td / "repo"
            t.make_repo(repo, {"AGENTS.md": b"OLD\n"})
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
            _ol.git = spy
            try:
                rc, out, err, rep = t.run_engine(cr, repo, td / "home", td / "boot", apply=True)
            finally:
                _ol.git = real_git
            self.assertEqual(rc, 0, err)
            banned = {"reset", "clean", "stash", "rebase", "push", "gc", "checkout", "restore"}
            for args in calls:
                self.assertFalse(
                    set(args) & banned, f"destructive/remote git command invoked: {args}"
                )


if __name__ == "__main__":
    unittest.main()
