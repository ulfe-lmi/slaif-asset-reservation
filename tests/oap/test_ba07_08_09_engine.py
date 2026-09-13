"""BA-07/BA-08/BA-09 — no-write dry run, identical rerun, scoped refresh."""

import tempfile
import unittest
from pathlib import Path

import oaplib
import oaptestlib as t


def _fixture(td: Path, with_register: bool = False):
    repo = td / "repo"
    files = {"AGENTS.md": b"OLD LAW\n", "PLAN.md": b"PLAN\n"}
    if with_register:
        files["CRITICAL.md"] = t.make_register([t.make_crit_entry("CRIT-0001")])
    t.make_repo(repo, files)
    boot = td / "boot"
    boot.mkdir()
    entries = [
        t.file_entry(
            "REPO/AGENTS.md",
            b"ROUTER\n",
            kind="archive_then_copy",
            pre_sha256=oaplib.sha256_hex(b"OLD LAW\n"),
            backup="REPO/docs/previous/AGENTS.md",
        ),
        t.file_entry("REPO/docs/previous/AGENTS.md", b"OLD LAW\n"),
        t.file_entry("REPO/oap/README.md", b"# oap\n"),
    ]
    fifos = [{"rel": "STRATEGIC_HOME/control.fifo"}]
    cr = t.make_manifest_root(td, entries, fifos=fifos)
    return repo, td / "home", boot, cr


class Ba07DryRun(unittest.TestCase):
    def test_ba07_dry_run_zero_writes_including_nonexistent(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba07")) as td:
            td = Path(td)
            repo, home, boot, cr = _fixture(td)
            before_repo = t.snapshot(repo, with_mtime=True)
            # strategic home does not exist yet: dry run must not create it or anything
            rc, out, err, rep = t.run_engine(cr, repo, home, boot, apply=False)
            self.assertEqual(rc, 0, err)
            self.assertEqual(rep["result"], "PLANNED")
            self.assertFalse(home.exists(), "dry run must not create the strategic home")
            self.assertFalse((repo / "oap").exists(), "dry run must not write into the repo")
            self.assertFalse((repo / "docs").exists())
            after_repo = t.snapshot(repo, with_mtime=True)
            self.assertEqual(
                before_repo, after_repo, "dry run changed path/bytes/mode/mtime in the repo"
            )
            # no locks, temp files, journals anywhere in the owned roots
            for base in (repo, boot):
                for p in base.rglob("*"):
                    name = p.name
                    self.assertNotIn(".oap-tmp-", name)
                    self.assertNotIn(".lock", name)
                    self.assertNotEqual(name, "state.json")
            self.assertFalse((td / "content2").parent.joinpath("home").exists())


class Ba08IdenticalRerun(unittest.TestCase):
    def test_ba08_second_apply_is_true_noop(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba08")) as td:
            td = Path(td)
            repo, home, boot, cr = _fixture(td)
            rc, out, err, rep = t.run_engine(cr, repo, home, boot, apply=True)
            self.assertEqual(rc, 0, err)
            snap1 = t.snapshot(td, with_mtime=True)
            fifos = [str(p.relative_to(td)) for p in td.rglob("*.fifo")]
            self.assertEqual(len(fifos), 1)
            rc2, out2, err2, rep2 = t.run_engine(cr, repo, home, boot, apply=True)
            self.assertEqual(rc2, 0, err2)
            snap2 = t.snapshot(td, with_mtime=True)
            self.assertEqual(snap1, snap2, "identical rerun changed bytes/mode/mtime")
            actions = [e["action"] for e in rep2["entries"]]
            for a in actions:
                self.assertIn(
                    a,
                    (
                        "identical",
                        "existing",
                        "preserved-existing",
                        "preserved-private",
                        "recomputed",
                    ),
                    f"unexpected action on rerun: {a}",
                )
            self.assertEqual(len([p for p in td.rglob("*.fifo")]), 1, "no duplicate FIFOs on rerun")
            self.assertEqual(len(list(repo.glob("oap/orders/*.md"))), 0)
            reg = repo / "CRITICAL.md"
            if reg.exists():
                e, errs = oaplib.parse_register(reg.read_bytes())
                self.assertEqual(errs, [])


class Ba09Refresh(unittest.TestCase):
    def test_ba09_scoped_refresh_archives_known_preserves_private(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba09")) as td:
            td = Path(td)
            repo, home, boot, cr = _fixture(td)
            rc, out, err, rep = t.run_engine(cr, repo, home, boot, apply=True)
            self.assertEqual(rc, 0, err)
            gen1_router = (repo / "AGENTS.md").read_bytes()
            # private state that a refresh must preserve
            (home / "runtime.env").write_text("OAP_PROFILE_VERSION=1\n")
            (home / "runtime.env").chmod(0o600)
            (home / "drafts").mkdir(parents=True)
            (home / "drafts" / "015-a-draft.md").write_text("DRAFT\n")
            (home / "logs").mkdir()
            (home / "logs" / "op.log").write_text("log line\n")
            (home / "auth").mkdir()
            (home / "auth" / "session.json").write_text('{"k":"v"}')
            (home / "agent-homes" / "coding").mkdir(parents=True)

            # generation-2 manifest: same router path, NEW candidate bytes,
            # previous_generated records the gen-1 bytes
            new_router = b"ROUTER V2\n"
            entries = [
                t.file_entry("REPO/AGENTS.md", new_router),
                t.file_entry("REPO/oap/README.md", b"# oap\n"),
                t.file_entry("REPO/docs/previous/AGENTS.md", b"OLD LAW\n"),
            ]
            cr2 = t.make_manifest_root(
                td / "gen2",
                entries,
                previous_generated={"REPO/AGENTS.md": oaplib.sha256_hex(gen1_router)},
            )
            # unknown divergent copy: someone edited oap/README.md by hand
            (repo / "oap" / "README.md").write_bytes(b"HAND EDITED\n")
            rc2, out2, err2, rep2 = t.run_engine(cr2, repo, home, boot, refresh=True)
            self.assertEqual(rc2, 1, "unknown divergent copy must block the refresh")
            self.assertEqual((repo / "oap" / "README.md").read_bytes(), b"HAND EDITED\n")
            self.assertEqual(
                (repo / "AGENTS.md").read_bytes(),
                gen1_router,
                "blocked refresh must not partially apply",
            )

            # with the divergent copy removed, refresh archives the gen-1 bytes
            (repo / "oap" / "README.md").write_bytes(b"# oap\n")
            rc3, out3, err3, rep3 = t.run_engine(cr2, repo, home, boot, refresh=True)
            self.assertEqual(rc3, 0, err3)
            self.assertEqual((repo / "AGENTS.md").read_bytes(), new_router)
            # private state preserved
            self.assertEqual((home / "runtime.env").read_text(), "OAP_PROFILE_VERSION=1\n")
            self.assertEqual((home / "drafts" / "015-a-draft.md").read_text(), "DRAFT\n")
            self.assertEqual((home / "logs" / "op.log").read_text(), "log line\n")
            self.assertEqual((home / "auth" / "session.json").read_text(), '{"k":"v"}')
            # git history (live) untouched
            self.assertEqual(len(t.log_ids(repo)), 1)


if __name__ == "__main__":
    unittest.main()
