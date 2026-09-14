"""BA-46..BA-48 — ICA structural scope/matrix, freshness/independence, and
post-remediation closed-queue rules. Structural PASS never claims independence.
"""

import json
import tempfile
import unittest
from pathlib import Path

import oaptestlib as t

REQUIREMENTS = [
    {"id": "SAR-001", "title": "One reservation authority"},
    {"id": "SAR-002", "title": "Product boundaries"},
    {"id": "SAR-003", "title": "Domain model integrity"},
    {"id": "SAR-004", "title": "Time semantics"},
    {"id": "SAR-005", "title": "Audit trail"},
]


def _valid_request(arch_sha, revision_line="Merged product revision: pending"):
    rows = "\n".join(
        "- {} — IMPLEMENTED (fixture row; negative path named; enforcing path named)".format(
            r["id"]
        )
        for r in REQUIREMENTS
    )
    return (
        "# ICA request — fixture\n\n"
        "Human scope: fixture milestone M-CONVERSION, attributed to the human requester.\n\n"
        f"Architecture digest (full): {arch_sha}\n\n"
        f"{revision_line}\n\n"
        f"{rows}\n\n"
        "Classification vocabulary used: IMPLEMENTED / PARTIAL / ABSENT / UNPROVEN.\n"
        "Negative paths are named per row; unknowns are recorded, not guessed.\n\n"
        "Auditor: pending (unresolved; no identity prefilled in a request draft)\n"
        "Independence: this structural check is not proof of independence; it is structural "
        "validation only.\n"
    )


def _valid_report(arch_sha):
    rows = "\n".join(
        "- {} — UNPROVEN (fixture report row; negative path named)".format(r["id"])
        for r in REQUIREMENTS
    )
    return (
        "# ICA report — fixture\n\n"
        "Human scope: fixture milestone M-CONVERSION, attributed to the human requester.\n\n"
        f"Architecture digest (full): {arch_sha}\n\n"
        "Merged product revision: 0123456789abcdef0123456789abcdef01234567\n\n"
        f"{rows}\n\n"
        "## Findings\n\n"
        "No fabricated confidence. Failed/skipped/not-run/blocked checks stated separately.\n\n"
        "Auditor: fixture auditor context (provenance recorded separately)\n"
        "Independence: structural validation only; this report is not proof of independence.\n"
        "Human milestone judgment is NOT granted by this report.\n"
    )


class IcaBase(unittest.TestCase):
    def setUp(self):
        self.td = Path(tempfile.mkdtemp(prefix=t.unique_name("ba46")))
        self.repo = self.td / "repo"
        self.repo.mkdir()
        self.arch_bytes = ("# full architecture fixture\n" * 10).encode()
        (self.repo / "ARCHITECTURE.md").write_bytes(self.arch_bytes)
        self.arch_sha = t.oaplib.sha256_hex(self.arch_bytes)
        self.req_file = self.td / "requirements.json"
        self.req_file.write_text(json.dumps(REQUIREMENTS))

    def _run(self, text, kind="request"):
        f = self.td / (f"ica-{kind}.md")
        f.write_text(text)
        return t.run_cli(
            "check_ica.py",
            [
                "--repo",
                str(self.repo),
                "--file",
                str(f),
                "--kind",
                kind,
                "--requirements-json",
                str(self.req_file),
                "--json",
            ],
            expect_json=True,
        )


class Ba46ScopeAndMatrix(IcaBase):
    def test_ba46_valid_request_passes_structural_only(self):
        rc, out, err, js = self._run(_valid_request(self.arch_sha))
        self.assertEqual(rc, 0, out + err)
        self.assertTrue(js["ok"])
        # the human-facing label is structural-only and never claims independence
        f = self.td / "ica-request.md"
        rc2, out2, err2, _ = t.run_cli(
            "check_ica.py",
            [
                "--repo",
                str(self.repo),
                "--file",
                str(f),
                "--kind",
                "request",
                "--requirements-json",
                str(self.req_file),
            ],
        )
        self.assertEqual(rc2, 0)
        self.assertIn("result=PASS-STRUCTURAL-ONLY", out2)

    def test_ba46_missing_human_scope_fails(self):
        text = _valid_request(self.arch_sha).replace("Human scope:", "Scope:")
        rc, out, err, js = self._run(text)
        self.assertEqual(rc, 1)
        self.assertFalse(js["checks"]["human_scope"]["ok"])

    def test_ba46_missing_architecture_hash_fails(self):
        text = _valid_request(self.arch_sha).replace(self.arch_sha, "no digest here")
        rc, out, err, js = self._run(text)
        self.assertEqual(rc, 1)
        self.assertFalse(js["checks"]["architecture_hash"]["ok"])

    def test_ba46_stale_architecture_hash_fails(self):
        stale = "f" * 64
        text = _valid_request(stale)
        rc, out, err, js = self._run(text)
        self.assertEqual(rc, 1)
        self.assertFalse(js["checks"]["architecture_hash_current"]["ok"])

    def test_ba46_missing_sar_rows_fail(self):
        # drop the SAR-003 row entirely
        lines = [
            line for line in _valid_request(self.arch_sha).splitlines() if "SAR-003" not in line
        ]
        rc, out, err, js = self._run("\n".join(lines))
        self.assertEqual(rc, 1)
        self.assertFalse(js["checks"]["requirement_matrix_complete"]["ok"])
        self.assertIn("SAR-003", js["checks"]["requirement_matrix_complete"]["detail"])

    def test_ba46_missing_revision_fails(self):
        text = _valid_request(self.arch_sha).replace(
            "Merged product revision: pending", "revision status: unknown-ish"
        )
        rc, out, err, js = self._run(text)
        self.assertEqual(rc, 1)
        self.assertFalse(js["checks"]["exact_revision"]["ok"])

    def test_ba46_no_classification_vocabulary_fails(self):
        text = (
            _valid_request(self.arch_sha)
            .replace("IMPLEMENTED", "DONE")
            .replace("PARTIAL", "PARTLY")
            .replace("ABSENT", "MISSING")
            .replace("UNPROVEN", "UNPROOF")
        )
        rc, out, err, js = self._run(text)
        self.assertEqual(rc, 1)
        self.assertFalse(js["checks"]["classifications_present"]["ok"])

    def test_ba46_no_negative_paths_fails(self):
        text = (
            _valid_request(self.arch_sha)
            .replace("negative", "counterfactual-ish")
            .replace("Negative", "Counterfactual-ish")
        )
        rc, out, err, js = self._run(text)
        self.assertEqual(rc, 1)
        self.assertFalse(js["checks"]["negative_paths"]["ok"])

    def test_ba46_no_auditor_or_independence_fails(self):
        text = _valid_request(self.arch_sha).replace("Auditor:", "Reviewer:")
        rc, out, err, js = self._run(text)
        self.assertEqual(rc, 1)
        self.assertFalse(js["checks"]["auditor_provenance"]["ok"])

    def test_ba46_prefilled_result_pass_fails(self):
        text = _valid_request(self.arch_sha) + "\nResult: PASS\n"
        rc, out, err, js = self._run(text)
        self.assertEqual(rc, 1)
        self.assertFalse(js["checks"]["no_prefilled_success"]["ok"])


class Ba47FreshnessIndependence(IcaBase):
    def test_ba47_report_requires_findings(self):
        text = _valid_report(self.arch_sha).replace("## Findings", "## Conclusions")
        rc, out, err, js = self._run(text, kind="report")
        self.assertEqual(rc, 1)
        self.assertFalse(js["checks"]["findings_section"]["ok"])

    def test_ba47_valid_report_passes_structural_only(self):
        rc, out, err, js = self._run(_valid_report(self.arch_sha), kind="report")
        self.assertEqual(rc, 0, out + err)
        self.assertTrue(js["ok"])

    def test_ba47_stale_revision_hash_fails(self):
        text = _valid_report("e" * 64)
        rc, out, err, js = self._run(text, kind="report")
        self.assertEqual(rc, 1)
        self.assertFalse(js["checks"]["architecture_hash_current"]["ok"])

    def test_ba47_independence_disclaimer_required(self):
        text = (
            _valid_report(self.arch_sha)
            .replace(
                "Independence: structural validation only; this report is not proof of "
                "independence.",
                "Autonomy: the context believes it is separate.",
            )
            .replace("not-run", "nr")
            .replace("NOT granted", "never granted")
        )
        rc, out, err, js = self._run(text, kind="report")
        self.assertEqual(rc, 1)
        self.assertFalse(js["checks"]["structural_only_disclaimer"]["ok"])


class Ba48PostRemediation(IcaBase):
    def test_ba48_closed_queue_without_full_matrix_fails(self):
        text = (
            "# ICA report — fixture closed queue\n\n"
            "Human scope: fixture milestone after remediation.\n\n"
            f"Architecture digest (full): {self.arch_sha}\n\n"
            "Merged product revision: 0123456789abcdef0123456789abcdef01234567\n\n"
            "Issue queue closed. Matrix rows:\n\n"
            "- SAR-001 — UNPROVEN (negative path named)\n"
            "- SAR-002 — UNPROVEN (negative path named)\n\n"
            "## Findings\n\nNo new findings.\n\n"
            "Auditor: fixture auditor context\n"
            "Independence: structural validation only; not proof of independence.\n"
        )
        rc, out, err, js = self._run(text, kind="report")
        self.assertEqual(rc, 1)
        missing = js["checks"]["requirement_matrix_complete"]["detail"]
        for rid in ("SAR-003", "SAR-004", "SAR-005"):
            self.assertIn(rid, missing)

    def test_ba48_report_template_mentions_human_milestone_judgment(self):
        tpl = t.REPO_ROOT / "docs" / "audit" / "ICA-REPORT-TEMPLATE.md"
        if not tpl.is_file():
            t.record_blocked("BA-48", "ICA report template not present")
            self.skipTest("ICA report template absent")
        text = tpl.read_text("utf-8", "replace")
        self.assertIn("milestone", text.lower())
        self.assertIn("human", text.lower())
        self.assertIn("acceptance", text.lower())


if __name__ == "__main__":
    unittest.main()
