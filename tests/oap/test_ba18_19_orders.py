"""BA-18/BA-19 — FINAL order schema and ID/round transitions."""

import json
import tempfile
import unittest
from pathlib import Path

import oaplib
import oaptestlib as t


def parse_full(meta: dict, body: str):
    text = f"<!-- OAP-META\n{json.dumps(meta, indent=1)}\n-->\n{body}"
    return oaplib.parse_order(text.encode("utf-8"), strict_final=True)


class Ba18Schema(unittest.TestCase):
    def test_ba18_valid_order_passes(self):
        meta = t.order_meta(base_sha="a" * 40)
        _, _, errs = parse_full(meta, t.dha_none_body())
        self.assertEqual(errs, [])

    def test_ba18_missing_fields_rejected(self):
        base = t.order_meta(base_sha="a" * 40)
        cases = {
            "provenance": ([], "provenance"),
            "requirements": ([], "requirements"),
            "base_sha": ("", "base_sha"),
            "issue_number": (0, "issue_number"),
            "pr_mode": ("MERGE_NOW", "pr_mode"),
            "governance_revision": ("nothex", "governance_revision"),
            "source_hashes": ({"PLAN.md": "abc"}, "source_hashes"),
            "allowed_paths": ([], "allowed_paths"),
        }
        for name, (val, key) in cases.items():
            m = dict(base)
            m[key] = val
            _, _, errs = parse_full(m, t.dha_none_body())
            self.assertTrue(errs, f"missing/invalid {name} must reject")

    def test_ba18_dha_required_and_none_default(self):
        meta = t.order_meta(base_sha="a" * 40)
        no_dha = "# order\n\nno adjudication section\n"
        _, _, errs = parse_full(meta, no_dha)
        self.assertTrue(any("Deferred human adjudication" in e for e in errs))
        two_dha = t.dha_none_body() + "## Deferred human adjudication\n\n- Decision: NONE\n"
        _, _, errs2 = parse_full(meta, two_dha)
        self.assertTrue(any("exactly one" in e for e in errs2))

    def test_ba18_genuine_unresolved_rejected_fenced_ok(self):
        meta = t.order_meta(base_sha="a" * 40)
        bad = t.dha_none_body() + "\nThe branch is TBD.\n"
        _, _, errs = parse_full(meta, bad)
        self.assertTrue(any("unresolved" in e.lower() for e in errs), errs)
        # a QUOTED test example placeholder inside a fence must not fail a valid order
        fenced = (
            t.dha_none_body()
            + "\nExample (quoted, not live):\n\n```\nassert TODO == None  # test example\n```\n"
        )
        _, _, errs2 = parse_full(meta, fenced)
        self.assertEqual(errs2, [])

    def test_ba18_round_a_requires_create_or_resume(self):
        m = t.order_meta(
            oid="002-b", pr_mode="CREATE_OR_RESUME", previous_round="002-a", base_sha="a" * 40
        )
        _, _, errs = parse_full(m, t.dha_none_body("002-b"))
        self.assertTrue(any("AMEND" in e for e in errs))
        m2 = t.order_meta(oid="002-a", pr_mode="AMEND", base_sha="a" * 40)
        _, _, errs2 = parse_full(m2, t.dha_none_body())
        self.assertTrue(any("CREATE_OR_RESUME" in e for e in errs2))


class Ba19Ids(unittest.TestCase):
    def test_ba19_round_progression(self):
        self.assertEqual(oaplib.next_round("a"), "b")
        self.assertEqual(oaplib.next_round("y"), "z")
        self.assertEqual(oaplib.next_round("z"), "aa")
        self.assertEqual(oaplib.next_round("az"), "ba")
        self.assertIsNone(oaplib.next_round("zz"))
        self.assertEqual(oaplib.prev_round("b"), "a")
        self.assertEqual(oaplib.prev_round("aa"), "z")
        self.assertIsNone(oaplib.prev_round("a"))

    def test_ba19_id_grammar(self):
        for good in ("001-a", "150-z", "999-az", "015-aa", "001-zz"):
            self.assertTrue(oaplib.valid_id(good), good)
        for bad in ("1-a", "001-", "001-A", "001-abc", "00a-a", "01-a", ""):
            self.assertFalse(oaplib.valid_id(bad), bad)

    def test_ba19_duplicate_ids_corrupt_state(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba19")) as td:
            td = Path(td)
            repo = td / "repo"
            t.make_repo(repo, {"AGENTS.md": b"r\n"})
            t.activate_order(repo)
            orders = repo / "oap" / "orders"
            first = list(orders.glob("001-a-*.md"))[0]
            (orders / "001-a-other.md").write_bytes(first.read_bytes())
            state = oaplib.classify_state(str(repo))
            self.assertEqual(state["state"], "CORRUPT")
            self.assertIn("exactly 1", state["detail"])

    def test_ba19_illegal_round_jump_refused(self):
        m = t.order_meta(oid="003-c", pr_mode="AMEND", previous_round="003-a", base_sha="a" * 40)
        m["pr_number"] = 12
        _, _, errs = parse_full(m, t.dha_none_body("003-c"))
        self.assertEqual(errs, [])  # schema-level: c follows b; publish enforces the jump
        # publish-time transition check: previous_round must be the immediately
        # preceding round (b), not a
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba19b")) as td:
            td = Path(td)
            repo = td / "repo"
            t.make_repo(repo, {"AGENTS.md": b"r\n"})
            head = t.head(repo)
            m2 = t.order_meta(
                oid="003-c",
                pr_mode="AMEND",
                previous_round="003-a",
                base_sha=head,
                pr_number=12,
                branch="oap/003-a",
            )
            body = t.dha_none_body("003-c")
            order = t.make_order_file(td, meta=m2, body=body)
            home = td / "home"
            home.mkdir()
            t.write_runtime_env(home, repo, activation=True, authority=True)
            remote = t.write_remote_state(
                td,
                {
                    "refs": {"refs/heads/main": head},
                    "prs": [
                        {"number": 12, "branch": "oap/003-a", "state": "open", "merged": False}
                    ],
                },
            )
            rc, out, err, js = t.run_cli(
                "publish_order.py",
                [
                    "--repo",
                    str(repo),
                    "--strategic-home",
                    str(home),
                    "--order",
                    str(order),
                    "--dry-run",
                    "--json",
                ],
                env={"OAP_ROLE": "STRATEGIC", "OAP_REMOTE_ADAPTER_FILE": remote},
                timeout=30,
                expect_json=True,
            )
            self.assertNotEqual(rc, 0)
            steps = {s["step"]: s for s in js["steps"]}
            self.assertFalse(
                steps["transition"]["ok"],
                "jump from a to c must be refused: {}".format(js["status"]),
            )

    def test_ba19_same_objective_new_pr_refused(self):
        # a correction round (b) on a NEW PR is schema-invalid (must AMEND the PR)
        m = t.order_meta(
            oid="004-b", pr_mode="CREATE_OR_RESUME", previous_round="004-a", base_sha="a" * 40
        )
        _, _, errs = parse_full(m, t.dha_none_body("004-b"))
        self.assertTrue(any("AMEND" in e for e in errs), errs)


if __name__ == "__main__":
    unittest.main()
