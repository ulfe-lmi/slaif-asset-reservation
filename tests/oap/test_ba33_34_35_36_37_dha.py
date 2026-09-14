"""BA-33..BA-37 — DHA declaration, exact locked register append, no agent
adjudication, four human disposition values and human-origin verification.
"""

import contextlib
import io
import json
import os
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "oap" / "bin"))

import oaplib  # noqa: E402
import oaptestlib as t  # noqa: E402


def _append_cli(repo, order, kind="admission", extra=None, env_extra=None, expect_json=True):
    args = ["--repo", str(repo), "--order", str(order), "--kind", kind]
    if extra:
        args += extra
    env = {"OAP_ROLE": "CODING"}
    if env_extra:
        env.update(env_extra)
    if expect_json:
        args.append("--json")
    return t.run_cli("append_critical.py", args, env=env, expect_json=expect_json)


class Ba33DhaDeclaration(unittest.TestCase):
    def test_ba33_zero_dha_declarations_fail(self):
        meta, body, errs = oaplib.parse_order(
            t.make_order_file(
                Path(tempfile.mkdtemp(prefix=t.unique_name("ba33a"))),
                body="# 001-a\n\nNo adjudication section at all.\n",
            ).read_bytes()
        )
        self.assertTrue(any("Deferred human adjudication" in e for e in errs))

    def test_ba33_two_dha_declarations_fail(self):
        body = (
            "# 001-a\n\n"
            "## Deferred human adjudication\n\n- Decision: NONE\n\n"
            "## Deferred human adjudication\n\n- Decision: NONE\n"
        )
        tmp = Path(tempfile.mkdtemp(prefix=t.unique_name("ba33b")))
        meta, body, errs = oaplib.parse_order(t.make_order_file(tmp, body=body).read_bytes())
        self.assertTrue(any("exactly one" in e for e in errs))

    def test_ba33_none_passes_and_has_no_payload(self):
        tmp = Path(tempfile.mkdtemp(prefix=t.unique_name("ba33c")))
        meta, body, errs = oaplib.parse_order(
            t.make_order_file(tmp, body=t.dha_none_body()).read_bytes()
        )
        self.assertEqual(errs, [])
        dha = oaplib.extract_dha(body)
        self.assertEqual(dha["decision"], "NONE")
        self.assertIsNone(dha["payload"])
        self.assertIsNone(dha["error"])

    def test_ba33_append_without_payload_section_fails(self):
        body = "# 001-a\n\n## Deferred human adjudication\n\n- Decision: APPEND CRIT-0001\n"
        tmp = Path(tempfile.mkdtemp(prefix=t.unique_name("ba33d")))
        meta, body, errs = oaplib.parse_order(t.make_order_file(tmp, body=body).read_bytes())
        self.assertTrue(any("payload" in e for e in errs))

    def test_ba33_append_with_digest_mismatch_fails(self):
        payload = t.make_crit_entry("CRIT-0001")
        body = t.dha_append_body("CRIT-0001", payload, digest="0" * 64)
        tmp = Path(tempfile.mkdtemp(prefix=t.unique_name("ba33e")))
        meta, body, errs = oaplib.parse_order(t.make_order_file(tmp, body=body).read_bytes())
        self.assertTrue(any("SHA-256 does not match" in e for e in errs))


class Ba34RegisterAppend(unittest.TestCase):
    def _setup(self, prefix, prior_entries=None):
        td = Path(tempfile.mkdtemp(prefix=t.unique_name(prefix)))
        repo = td / "repo"
        repo.mkdir()
        if prior_entries is None:
            prior_entries = [t.make_crit_entry("CRIT-0001")]
        reg = t.make_register(prior_entries)
        (repo / "CRITICAL.md").write_bytes(reg)
        (repo / "oap").mkdir()
        payload = t.make_crit_entry("CRIT-0002")
        order = t.make_order_file(td, body=t.dha_append_body("CRIT-0002", payload))
        return td, repo, order, reg, payload

    def test_ba34_append_preserves_prior_bytes_exactly(self):
        td, repo, order, reg, payload = self._setup("ba34a")
        rc, out, err, js = _append_cli(repo, order)
        self.assertEqual(rc, 0, err + out)
        self.assertEqual(js["status"], "APPENDED")
        self.assertTrue(js["ok"])
        self.assertEqual((repo / "CRITICAL.md").read_bytes(), reg + payload.encode("utf-8"))

    def test_ba34_retry_is_no_op_and_stable(self):
        td, repo, order, reg, payload = self._setup("ba34b")
        rc1, _, _, js1 = _append_cli(repo, order)
        self.assertEqual(js1["status"], "APPENDED")
        after_first = (repo / "CRITICAL.md").read_bytes()
        rc2, _, _, js2 = _append_cli(repo, order)
        self.assertEqual(rc2, 0)
        self.assertEqual(js2["status"], "NO_OP")
        self.assertTrue(js2["ok"])
        self.assertEqual((repo / "CRITICAL.md").read_bytes(), after_first)

    def test_ba34_wrong_declared_id_refused(self):
        td = Path(tempfile.mkdtemp(prefix=t.unique_name("ba34c")))
        repo = td / "repo"
        repo.mkdir()
        (repo / "CRITICAL.md").write_bytes(t.make_register([t.make_crit_entry("CRIT-0001")]))
        payload3 = t.make_crit_entry("CRIT-0003")
        order = t.make_order_file(td, body=t.dha_append_body("CRIT-0003", payload3))
        rc, out, err, js = _append_cli(repo, order)
        self.assertEqual(rc, 1)
        self.assertEqual(js["status"], "REFUSED_ID")
        # register untouched
        self.assertEqual(
            (repo / "CRITICAL.md").read_bytes(), t.make_register([t.make_crit_entry("CRIT-0001")])
        )

    def test_ba34_incomplete_entry_fails_validation(self):
        td = Path(tempfile.mkdtemp(prefix=t.unique_name("ba34d")))
        repo = td / "repo"
        repo.mkdir()
        (repo / "CRITICAL.md").write_bytes(t.make_register([]))
        incomplete = t.make_crit_entry(
            "CRIT-0001", omit=["### Dilemma", "### Strategic attestation"]
        )
        order = t.make_order_file(td, body=t.dha_append_body("CRIT-0001", incomplete))
        rc, out, err, js = _append_cli(repo, order)
        self.assertEqual(rc, 1)
        self.assertEqual(js["status"], "FAILED_ENTRY")
        detail = " ".join(s["detail"] for s in js["steps"])
        self.assertIn("missing heading", detail)

    def test_ba34_stale_prefix_refused(self):
        td, repo, order, reg, payload = self._setup("ba34e")
        sys.path.insert(0, str(t.BIN))
        try:
            import append_critical

            real_acquire = oaplib.acquire_lease

            def sabotage(path, owner=""):
                # concurrent writer sneaks in between pre-read and locked write
                r = repo / "CRITICAL.md"
                intruder = "## CRIT-0003 — concurrent intruder\n".encode()
                r.write_bytes(r.read_bytes() + intruder)
                return real_acquire(path, owner=owner)

            old_role = os.environ.get("OAP_ROLE")
            os.environ["OAP_ROLE"] = "CODING"
            oaplib.acquire_lease = sabotage
            captured = io.StringIO()  # in-process helper must not pollute suite stdout
            try:
                with contextlib.redirect_stdout(captured):
                    rc = append_critical.main(
                        ["--repo", str(repo), "--order", str(order), "--json"]
                    )
            finally:
                oaplib.acquire_lease = real_acquire
                if old_role is None:
                    os.environ.pop("OAP_ROLE", None)
                else:
                    os.environ["OAP_ROLE"] = old_role
            self.assertEqual(rc, 1)
            reg_after = (repo / "CRITICAL.md").read_bytes()
            self.assertNotIn(b"## CRIT-0002", reg_after)
            self.assertIn("## CRIT-0003 — concurrent intruder\n".encode(), reg_after)
        finally:
            sys.path.pop(0)
        # direct status evidence via a second clean run on the mutated register:
        # the intruder entry now breaks monotonic expectations, proving no silent merge.
        entries, errs = oaplib.parse_register((repo / "CRITICAL.md").read_bytes())
        self.assertTrue(any(e["id"] == "CRIT-0003" for e in entries))

    def test_ba34_lock_held_refused(self):
        td, repo, order, reg, payload = self._setup("ba34f")
        leases = repo / "oap" / "leases"
        leases.mkdir(parents=True, exist_ok=True)
        (leases / "critical.lease").write_text(
            json.dumps({"pid": os.getpid(), "start": time.time(), "owner": "other"})
        )
        rc, out, err, js = _append_cli(repo, order)
        self.assertEqual(rc, 1)
        self.assertEqual(js["status"], "REFUSED_LOCK_HELD")
        self.assertEqual((repo / "CRITICAL.md").read_bytes(), reg)

    def test_ba34_dry_run_performs_zero_writes(self):
        td, repo, order, reg, payload = self._setup("ba34g")
        before = t.snapshot(str(repo), with_mtime=True)
        rc, out, err, js = _append_cli(repo, order, extra=["--dry-run"])
        self.assertEqual(rc, 0)
        self.assertEqual(js["status"], "DRY_RUN_VALID")
        self.assertEqual(js["ok"], True)
        after = t.snapshot(str(repo), with_mtime=True)
        self.assertEqual(before, after, "dry-run must not create or touch any file")
        self.assertEqual((repo / "CRITICAL.md").read_bytes(), reg)


class Ba35NoAgentAdjudication(unittest.TestCase):
    def _repo(self, prefix, register):
        td = Path(tempfile.mkdtemp(prefix=t.unique_name(prefix)))
        repo = td / "repo"
        repo.mkdir()
        (repo / "CRITICAL.md").write_bytes(register)
        (repo / "oap").mkdir()
        return td, repo

    def test_ba35_admission_payload_with_human_adjudication_refused(self):
        entry = t.make_crit_entry("CRIT-0001")
        injected = entry + (
            "\n## HUMAN ADJUDICATION — CRIT-0001 — 2026-09-13\n\n"
            "- Decision: ACCEPTED\n- Authority: the coding agent itself\n"
        )
        td = Path(tempfile.mkdtemp(prefix=t.unique_name("ba35a")))
        repo = td / "repo"
        repo.mkdir()
        (repo / "CRITICAL.md").write_bytes(t.make_register([]))
        order = t.make_order_file(td, body=t.dha_append_body("CRIT-0001", injected))
        rc, out, err, js = _append_cli(repo, order)
        self.assertEqual(rc, 1)
        self.assertEqual(js["status"], "FAILED_ENTRY")
        self.assertIn("HUMAN ADJUDICATION", " ".join(s["detail"] for s in js["steps"]))

    def test_ba35_evidence_append_needs_exact_heading(self):
        td = Path(tempfile.mkdtemp(prefix=t.unique_name("ba35b")))
        repo = td / "repo"
        repo.mkdir()
        (repo / "CRITICAL.md").write_bytes(t.make_register([t.make_crit_entry("CRIT-0001")]))
        full = t.make_crit_entry("CRIT-0001")
        bad = full.replace("## CRIT-0001 — fixture DHA admission", "## WRONG HEADING", 1)
        self.assertNotEqual(bad, full)
        order = t.make_order_file(td, body=t.dha_append_body("CRIT-0001", bad))
        rc, out, err, js = _append_cli(repo, order, kind="evidence")
        self.assertEqual(rc, 1)
        self.assertEqual(js["status"], "FAILED_ENTRY")

    def test_ba35_evidence_append_does_not_clear_gate(self):
        uuid4 = uuid.uuid4()
        entry = t.make_crit_entry("CRIT-0001")
        evidence = (
            f"## EVIDENCE APPEND — CRIT-0001 — {uuid4}\n\n"
            "Additional observation; not a human disposition.\n"
        )
        reg = t.make_register([entry + "\n" + evidence])
        td, repo = self._repo("ba35c", reg)
        st = oaplib.gate_state("CRIT-0001", (repo / "CRITICAL.md").read_bytes())
        self.assertEqual(st["status"], "PENDING")
        self.assertFalse(st["cleared"])

    def test_ba35_fenced_template_ignored_by_parser(self):
        reg = t.make_register([t.make_crit_entry("CRIT-0001")])
        self.assertIn(b"## CRIT-0099", reg)  # the fenced template example is present
        entries, errs = oaplib.parse_register(reg)
        self.assertEqual(errs, [])
        self.assertEqual([e["id"] for e in entries], ["CRIT-0001"])
        self.assertEqual(oaplib.next_crit_id(reg), "CRIT-0002")


class Ba36FourHumanValues(unittest.TestCase):
    def _reg(self, blocks):
        return (
            "# CRITICAL — fixture register\n\n"
            + t.make_crit_entry("CRIT-0001")
            + "\n"
            + "\n".join(blocks)
        ).encode("utf-8")

    @staticmethod
    def _block(crit, date, decision):
        return (
            f"## HUMAN ADJUDICATION — {crit} — {date}\n\n"
            f"- Decision: {decision}\n- Authority: fixture human\n"
        )

    def test_ba36_no_disposition_is_pending(self):
        st = oaplib.gate_state("CRIT-0001", t.make_register([t.make_crit_entry("CRIT-0001")]))
        self.assertEqual(st["status"], "PENDING")
        self.assertFalse(st["cleared"])

    def test_ba36_latest_accepted_clears(self):
        reg = self._reg(
            [
                self._block("CRIT-0001", "2026-09-01", "REJECTED"),
                self._block("CRIT-0001", "2026-09-13", "ACCEPTED"),
            ]
        )
        st = oaplib.gate_state("CRIT-0001", reg, verifier=lambda c, d: True)
        self.assertEqual(st["status"], "CLEARED")
        self.assertTrue(st["cleared"])

    def test_ba36_accepted_then_rejected_blocks(self):
        reg = self._reg(
            [
                self._block("CRIT-0001", "2026-09-01", "ACCEPTED"),
                self._block("CRIT-0001", "2026-09-13", "REJECTED"),
            ]
        )
        st = oaplib.gate_state("CRIT-0001", reg, verifier=lambda c, d: True)
        self.assertEqual(st["status"], "BLOCKED")
        self.assertFalse(st["cleared"])

    def test_ba36_deferred_blocks(self):
        reg = self._reg([self._block("CRIT-0001", "2026-09-13", "DEFERRED")])
        st = oaplib.gate_state("CRIT-0001", reg, verifier=lambda c, d: True)
        self.assertEqual(st["status"], "BLOCKED")

    def test_ba36_change_required_blocks(self):
        reg = self._reg([self._block("CRIT-0001", "2026-09-13", "CHANGE REQUIRED")])
        st = oaplib.gate_state("CRIT-0001", reg, verifier=lambda c, d: True)
        self.assertEqual(st["status"], "BLOCKED")

    def test_ba36_invalid_value_blocks(self):
        reg = self._reg([self._block("CRIT-0001", "2026-09-13", "APPROVED BY AGENT")])
        st = oaplib.gate_state("CRIT-0001", reg, verifier=lambda c, d: True)
        self.assertEqual(st["status"], "BLOCKED")

    def test_ba36_latest_wins_even_with_more_blocks(self):
        reg = self._reg(
            [
                self._block("CRIT-0001", "2026-09-01", "ACCEPTED"),
                self._block("CRIT-0001", "2026-09-05", "DEFERRED"),
                self._block("CRIT-0002", "2026-09-06", "ACCEPTED"),
                self._block("CRIT-0001", "2026-09-13", "ACCEPTED"),
            ]
        )
        st = oaplib.gate_state("CRIT-0001", reg, verifier=lambda c, d: True)
        self.assertEqual(st["status"], "CLEARED")


class Ba37HumanOriginVerification(unittest.TestCase):
    def _repo(self, prefix, reg):
        td = Path(tempfile.mkdtemp(prefix=t.unique_name(prefix)))
        repo = td / "repo"
        repo.mkdir()
        (repo / "CRITICAL.md").write_bytes(reg)
        return td, repo

    def test_ba37_without_verifier_never_cleared(self):
        reg = (
            "# CRITICAL\n\n"
            + t.make_crit_entry("CRIT-0001")
            + "\n## HUMAN ADJUDICATION — CRIT-0001 — 2026-09-13\n\n"
            "- Decision: ACCEPTED\n- Authority: someone\n"
        ).encode()
        td, repo = self._repo("ba37a", reg)
        rc, out, err, js = t.run_cli(
            "check_state.py",
            ["--repo", str(repo), "--check-human-gates", "CRIT-0001", "--json"],
            expect_json=True,
        )
        self.assertEqual(rc, 0)
        gate = js["human_gates"][0]
        self.assertEqual(gate["crit"], "CRIT-0001")
        self.assertEqual(gate["status"], "UNVERIFIED")
        self.assertFalse(gate["cleared"])

    def test_ba37_with_fixture_verifier_cleared(self):
        reg = (
            "# CRITICAL\n\n"
            + t.make_crit_entry("CRIT-0001")
            + "\n## HUMAN ADJUDICATION — CRIT-0001 — 2026-09-13\n\n"
            "- Decision: ACCEPTED\n- Authority: someone\n"
        ).encode()
        td, repo = self._repo("ba37b", reg)
        vfile = td / "verifier.json"
        vfile.write_text(json.dumps({"verified": {"CRIT-0001": "fixture"}}))
        rc, out, err, js = t.run_cli(
            "check_state.py",
            ["--repo", str(repo), "--check-human-gates", "CRIT-0001", "--json"],
            env={"OAP_HUMAN_VERIFIER_FILE": str(vfile)},
            expect_json=True,
        )
        self.assertEqual(rc, 0)
        self.assertEqual(js["human_gates"][0]["status"], "CLEARED")
        self.assertTrue(js["human_gates"][0]["cleared"])

    def test_ba37_verifier_value_mismatch_stays_unverified(self):
        reg = (
            "# CRITICAL\n\n"
            + t.make_crit_entry("CRIT-0001")
            + "\n## HUMAN ADJUDICATION — CRIT-0001 — 2026-09-13\n\n"
            "- Decision: ACCEPTED\n- Authority: someone\n"
        ).encode()
        td, repo = self._repo("ba37c", reg)
        vfile = td / "verifier.json"
        vfile.write_text(json.dumps({"verified": {"CRIT-0001": "not-fixture"}}))
        rc, out, err, js = t.run_cli(
            "check_state.py",
            ["--repo", str(repo), "--check-human-gates", "CRIT-0001", "--json"],
            env={"OAP_HUMAN_VERIFIER_FILE": str(vfile)},
            expect_json=True,
        )
        self.assertEqual(js["human_gates"][0]["status"], "UNVERIFIED")

    def test_ba37_pending_reported_for_crit_without_disposition(self):
        td, repo = self._repo("ba37d", t.make_register([t.make_crit_entry("CRIT-0001")]))
        rc, out, err, js = t.run_cli(
            "check_state.py",
            ["--repo", str(repo), "--check-human-gates", "CRIT-0001", "--json"],
            expect_json=True,
        )
        self.assertEqual(js["human_gates"][0]["status"], "PENDING")


if __name__ == "__main__":
    unittest.main()
