"""BA-01 — immutable inputs.

Copies of the source prompt / OAP manual / old architecture are byte-locked:
SHA-256 (and Git blob identity where the source was a Git object) is verified
against build-time injected constants, and a deliberate one-byte mutation of the
staged input fails BEFORE any target write happens.
"""

import hashlib
import tempfile
import unittest
from pathlib import Path

import fixture_digests as fd
import oaplib
import oaptestlib as t

INPUTS_DIR = t.REPO_ROOT / "docs" / "bootstrap" / fd.GEN / "inputs"


class Ba01Inputs(unittest.TestCase):
    def _require_inputs(self):
        if not INPUTS_DIR.is_dir():
            self.fail(f"input snapshots not materialized at {INPUTS_DIR}")

    def test_ba01_input_digests_match_constants(self):
        self._require_inputs()
        for name, expected in fd.INPUT_DIGESTS.items():
            p = INPUTS_DIR / name
            self.assertTrue(p.is_file(), f"missing input snapshot: {name}")
            actual = hashlib.sha256(p.read_bytes()).hexdigest()
            self.assertEqual(actual, expected, f"input snapshot drifted: {name}")

    def test_ba01_generator_archived_under_non_discovered_name(self):
        self._require_inputs()
        gen = t.REPO_ROOT / "docs" / "bootstrap" / fd.GEN / "BOOTSTRAP-GENERATOR.md"
        self.assertTrue(gen.is_file(), "BOOTSTRAP-GENERATOR.md missing")
        expected = fd.INPUT_DIGESTS["bootstrap-generator-prompt.md"]
        self.assertEqual(hashlib.sha256(gen.read_bytes()).hexdigest(), expected)
        # no operational AGENTS basename anywhere under the archive
        for p in (t.REPO_ROOT / "docs" / "bootstrap").rglob("*"):
            if p.is_file() and p.name in ("AGENTS.md", "CLAUDE.md"):
                self.fail(f"discovered instruction basename in archive: {p}")

    def test_ba01_old_architecture_git_blob_identity(self):
        self._require_inputs()
        # the archived original architecture must hash to the recorded Git blob
        prev = t.REPO_ROOT / "docs" / "bootstrap" / fd.GEN / "previous" / "docs-architecture.md"
        if prev.is_file():
            self.assertEqual(oaplib.git_blob_id(prev.read_bytes()), fd.BLOB_IDS["docs_arch"])
        # and the compatibility pointer now lives at docs/architecture.md
        ptr = (t.REPO_ROOT / "docs" / "architecture.md").read_text("utf-8")
        self.assertIn(fd.BLOB_IDS["docs_arch"], ptr)

    def test_ba01_one_byte_mutation_fails_before_target_writes(self):
        """A corrupted staged input refuses the run and writes nothing."""
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba01")) as td:
            td = Path(td)
            repo = td / "repo"
            home = td / "home"
            boot = td / "boot"
            repo.mkdir()
            t.make_repo(repo, {"APP.txt": b"product bytes\n"})
            # staged copy of a real input snapshot with its digest locked in the manifest
            src_name = "CRITICAL.md"
            src = INPUTS_DIR / src_name
            self._require_inputs()
            data = src.read_bytes()
            entries = [t.file_entry("REPO/CRITICAL.md", data)]
            cr = t.make_manifest_root(td, entries)
            rc, out, err, rep = t.run_engine(cr, repo, home, boot, apply=True)
            self.assertEqual(rc, 0, err)
            self.assertEqual((repo / "CRITICAL.md").read_bytes(), data)
            # deliberate one-byte mutation of the staged content
            corrupted = data[:-1] + bytes([data[-1] ^ 0x01])
            (cr / "REPO" / "CRITICAL.md").write_bytes(corrupted)
            (repo / "CRITICAL.md").unlink()
            rc2, out2, err2, rep2 = t.run_engine(cr, repo, home, boot, apply=True)
            self.assertNotEqual(rc2, 0, "corrupted staged input must fail the run")
            self.assertTrue(
                (repo / "CRITICAL.md").exists() is False,
                "no target write may happen after an input mutation",
            )
            self.assertIn("mismatch", (out2 + err2).lower())


if __name__ == "__main__":
    unittest.main()
