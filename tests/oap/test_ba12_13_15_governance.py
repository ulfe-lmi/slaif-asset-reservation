"""BA-12/BA-13/BA-15 — full vs compact law, coverage and hashes, context budgets.

Runs against the ACTUAL materialized tree (read-only) and against tampered
copies in owned temp roots.
"""

import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import fixture_digests as fd
import oaplib
import oaptestlib as t


def _run_gov(repo, home=None, extra=None):
    args = ["--repo", str(repo), "--json"]
    if home:
        args += ["--strategic-home", str(home)]
    args += extra or []
    return t.run_cli("check_governance.py", args, timeout=60, expect_json=True)


class Ba12FullVsCompact(unittest.TestCase):
    def test_ba12_root_tiny_coding_dense_strategic_distinct(self):
        root = (t.REPO_ROOT / "AGENTS.md").read_bytes()
        coding = (t.REPO_ROOT / "oap" / "coding-instructions" / "AGENTS.md").read_bytes()
        strat = (t.REPO_ROOT / "oap" / "strategic-instructions" / "AGENTS.md").read_bytes()
        self.assertLessEqual(len(root), 2048, "root router must stay tiny")
        self.assertLessEqual(len(coding), 12000)
        self.assertLessEqual(len(strat), 100000)
        self.assertNotEqual(
            oaplib.sha256_hex(coding),
            oaplib.sha256_hex(strat),
            "strategic full source must be genuinely distinct",
        )
        self.assertGreater(
            len(strat), len(coding) // 2, "strategic law should be the fuller document"
        )
        # mandatory transitive graph for coding excludes full sources and register
        compact = (t.REPO_ROOT / "ARCHITECTURE-for-agents.md").read_text("utf-8")
        for full_ref in ("# CRITICAL —", "## CRIT-0001"):
            self.assertNotIn(full_ref, compact, "compact law embeds register content")
        # semantic comparison is recorded, not falsely machine-proved
        dm = (t.REPO_ROOT / "oap" / "governance" / "DISTILLATION-MAP.md").read_text("utf-8")
        self.assertIn("NOT", dm)
        self.assertIn("independent audit", dm.lower().replace("-", " "))

    def test_ba12_coding_read_set_excludes_full_architecture_and_register(self):
        c = (t.REPO_ROOT / "oap" / "coding-instructions" / "AGENTS.md").read_text("utf-8")
        # the dense law references the compact architecture, not the full one
        self.assertIn("ARCHITECTURE-for-agents.md", c)
        m = re.findall(r"ARCHITECTURE\.md\b", c)
        self.assertEqual(m, [], "coding law must not mandate reading the full ARCHITECTURE.md")


class Ba13CoverageHashes(unittest.TestCase):
    def test_ba13_governance_passes_on_materialized_tree(self):
        rc, out, err, js = _run_gov(t.REPO_ROOT)
        self.assertEqual(rc, 0, f"check_governance failed on the materialized tree:\n{out}")
        self.assertTrue(js["ok"], js)
        for name in (
            "projection_source_hash_current",
            "sar_coverage_compact",
            "strategic_clauses_present",
            "coding_clauses_present",
            "byte_budgets",
            "governance_manifest_identities",
            "distillation_map_coverage",
        ):
            self.assertTrue(
                js["checks"][name]["ok"], "{}: {}".format(name, js["checks"][name]["detail"])
            )

    def test_ba13_stale_projection_hash_fails(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba13")) as td:
            td = Path(td)
            repo = td / "repo"
            shutil.copytree(
                t.REPO_ROOT, repo, symlinks=False, ignore=shutil.ignore_patterns(".git", "data")
            )
            compact = repo / "ARCHITECTURE-for-agents.md"
            text = compact.read_text("utf-8")
            # replace the embedded full-architecture sha with a stale one
            sha = fd.ARCH_SHA
            self.assertIn(sha, text)
            stale = "f" * 64
            compact.write_text(text.replace(sha, stale))
            rc, out, err, js = _run_gov(repo)
            self.assertEqual(rc, 1)
            self.assertFalse(js["checks"]["projection_source_hash_current"]["ok"])

    def test_ba13_missing_sar_fails(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba13b")) as td:
            td = Path(td)
            repo = td / "repo"
            shutil.copytree(
                t.REPO_ROOT, repo, symlinks=False, ignore=shutil.ignore_patterns(".git", "data")
            )
            compact = repo / "ARCHITECTURE-for-agents.md"
            text = compact.read_text("utf-8")
            idx = text.find("SAR-038")
            self.assertGreater(idx, 0)
            # remove every line referencing SAR-038 so the compact file no longer
            # advertises the clause at all
            kept = [ln for ln in text.splitlines(keepends=True) if "SAR-038" not in ln]
            assert len(kept) < len(text.splitlines())
            compact.write_text("".join(kept))
            rc, out, err, js = _run_gov(repo)
            self.assertEqual(rc, 1)
            self.assertFalse(js["checks"]["sar_coverage_compact"]["ok"])

    def test_ba13_installed_copy_drift_fails(self):
        home = t.real_strategic_home("BA-13")
        if home is None:
            return
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba13c")) as td:
            td = Path(td)
            h2 = td / "home"
            # FIFOs are not copyable by copytree and are irrelevant to installed-copy identity
            shutil.copytree(home, h2, symlinks=False, ignore=shutil.ignore_patterns("*.fifo"))
            (h2 / "AGENTS.md").write_bytes(
                (t.REPO_ROOT / "oap" / "strategic-instructions" / "AGENTS.md").read_bytes()
                + b"\n# drift\n"
            )
            rc, out, err, js = _run_gov(t.REPO_ROOT, h2)
            self.assertEqual(rc, 1)
            self.assertFalse(js["checks"]["installed_copy_AGENTS.md"]["ok"])

    def test_ba13_expected_hash_alone_cannot_authorize_edits(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba13d")) as td:
            td = Path(td)
            repo = td / "repo"
            shutil.copytree(
                t.REPO_ROOT, repo, symlinks=False, ignore=shutil.ignore_patterns(".git", "data")
            )
            gm = repo / "oap" / "governance" / "MANIFEST.json"
            man = json.loads(gm.read_text())
            name = "AGENTS.md"
            man["identities"][name]["sha256"] = "0" * 64
            gm.write_text(json.dumps(man))
            original = (repo / "AGENTS.md").read_bytes()
            rc, out, err, js = _run_gov(repo)
            self.assertEqual(rc, 1)
            self.assertFalse(js["checks"]["governance_manifest_identities"]["ok"])
            self.assertEqual(
                (repo / "AGENTS.md").read_bytes(), original, "the file itself must remain untouched"
            )


class Ba15Budgets(unittest.TestCase):
    def test_ba15_exact_bytes_match_budget_doc(self):
        doc = (t.REPO_ROOT / "oap" / "governance" / "CONTEXT-BUDGET.md").read_text("utf-8")
        self.assertIn("UNMEASURED", doc, "tokens must stay UNMEASURED")
        total = 0
        for m in re.finditer(
            r"`(AGENTS\.md|oap/coding-instructions/AGENTS\.md|"
            r"ARCHITECTURE-for-agents\.md|OAP-COMMUNICATION-coding-agent\.md|"
            r"oap/coding-instructions/(?:SECURITY-CORE|TESTING-CORE)\.md)`\s*\|\s*(\d+)",
            doc,
        ):
            rel, size = m.group(1), int(m.group(2))
            actual = (t.REPO_ROOT / rel).read_bytes()
            self.assertEqual(len(actual), size, f"budget doc bytes stale for {rel}")
            total += size
        mtotal = re.search(r"\*\*Total \(excluding order/code\)\*\*\s*\|\s*\*\*(\d+)\*\*", doc)
        self.assertEqual(int(mtotal.group(1)), total)
        self.assertLessEqual(total, 50000)

    def test_ba15_ceiling_overflow_fails(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba15")) as td:
            td = Path(td)
            repo = td / "repo"
            shutil.copytree(
                t.REPO_ROOT, repo, symlinks=False, ignore=shutil.ignore_patterns(".git", "data")
            )
            router = repo / "AGENTS.md"
            router.write_bytes(router.read_bytes() + b"x" * 4000)
            rc, out, err, js = _run_gov(repo)
            self.assertEqual(rc, 1)
            self.assertFalse(js["checks"]["byte_budgets"]["ok"])


if __name__ == "__main__":
    unittest.main()
