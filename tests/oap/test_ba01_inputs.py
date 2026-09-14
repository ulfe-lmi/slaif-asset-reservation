"""BA-01 — immutable inputs.

Copies of the source prompt / OAP manual / old architecture are byte-locked:
SHA-256 (and Git blob identity where the source was a Git object) is verified
against build-time injected constants. The archived snapshots under
docs/bootstrap/1/ are historical evidence, not live governance.
"""

import hashlib
import sys
import unittest
from pathlib import Path

import fixture_digests as fd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "oap" / "bin"))

import oaplib  # noqa: E402
import oaptestlib as t  # noqa: E402

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


if __name__ == "__main__":
    unittest.main()
