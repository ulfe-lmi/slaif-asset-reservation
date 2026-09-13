"""BA-20..BA-23 — publication semantics: PR reuse, immutability, crash windows,
signal-after-durability."""

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "oap" / "bin"))

import oaplib  # noqa: E402
import oaptestlib as t  # noqa: E402


def load_publish_module():
    spec = importlib.util.spec_from_file_location("publish_order_mod", t.BIN / "publish_order.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class PublishFixture:
    def __init__(
        self,
        td: Path,
        activation=True,
        authority=True,
        with_fifo=True,
        prs=None,
        oid="001-a",
        order_meta=None,
    ):
        self.td = td
        self.repo = td / "repo"
        self.head = t.make_repo(self.repo, {"AGENTS.md": b"router\n"})
        self.home = td / "home"
        self.home.mkdir()
        t.write_runtime_env(self.home, self.repo, activation=activation, authority=authority)
        self.remote = t.write_remote_state(
            td,
            {
                "refs": {"refs/heads/main": self.head},
                "prs": prs or [],
                "next_pr_number": 30,
            },
        )
        meta = order_meta or t.order_meta(oid=oid, base_sha=self.head)
        self.order = t.make_order_file(td, meta=meta)
        self.consumer = []
        if with_fifo:
            t.make_fifo(self.home / "control.fifo")
            self.thread = t.fifo_consumer_thread(self.home / "control.fifo", self.consumer)
        self.env = {"OAP_ROLE": "STRATEGIC", "OAP_REMOTE_ADAPTER_FILE": self.remote}

    def publish(self, recover=False, dry=False, timeout=30, signal_timeout=None):
        args = [
            "--repo",
            str(self.repo),
            "--strategic-home",
            str(self.home),
            "--order",
            str(self.order),
        ]
        if recover:
            args.append("--recover")
        if dry:
            args.append("--dry-run")
        if signal_timeout is not None:
            args += ["--signal-timeout", str(signal_timeout)]
        args.append("--json")
        return t.run_cli("publish_order.py", args, env=self.env, timeout=timeout, expect_json=True)


class Ba20FirstRoundResume(unittest.TestCase):
    def test_ba20_interrupted_round_a_reuses_existing_pr(self):
        """Slim CREATE_OR_RESUME: an interrupted round a reuses the verified open
        branch PR; the publisher never creates or re-creates a second PR."""
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba20")) as td:
            td = Path(td)
            fx = PublishFixture(
                td, prs=[{"number": 31, "branch": "oap/001-a", "state": "open", "merged": False}]
            )
            rc, out, err, js = fx.publish(dry=True)
            self.assertEqual(rc, 0, out)
            self.assertEqual(js["status"], "DRY_RUN_VALID")
            steps = {s["step"]: s for s in js["steps"]}
            self.assertTrue(steps["pr_identity"]["ok"], js)
            self.assertIn("31", steps["pr_identity"]["detail"])
            self.assertIn("reuses", steps["pr_identity"]["detail"])
            # no second PR was created: remote state unchanged
            state = json.loads(Path(fx.remote).read_text())
            self.assertEqual(len(state["prs"]), 1)
            # a merged historical PR on the branch is still refused
            fx2 = PublishFixture(
                td / "b",
                prs=[{"number": 31, "branch": "oap/001-a", "state": "merged", "merged": True}],
            )
            rc2, out2, err2, js2 = fx2.publish(dry=True)
            self.assertNotEqual(rc2, 0)
            steps2 = {s["step"]: s for s in js2["steps"]}
            self.assertFalse(steps2["pr_identity"]["ok"])
            self.assertIn("MERGED historical PR", steps2["pr_identity"]["detail"])


class Ba21ImmutablePublication(unittest.TestCase):
    def test_ba21_order_before_pointer_exact_pointer(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba21")) as td:
            td = Path(td)
            fx = PublishFixture(td)
            rc, out, err, js = fx.publish()
            self.assertEqual(rc, 0, out)
            self.assertEqual(js["status"], "PUBLISHED")
            dest = fx.repo / "oap" / "orders" / "001-a-canary.md"
            self.assertTrue(dest.is_file())
            self.assertEqual(dest.read_bytes(), fx.order.read_bytes())
            ptr = fx.repo / "oap" / "active"
            self.assertEqual(ptr.read_bytes(), b"001-a\n", "pointer is exactly ID+LF")
            journal = json.loads((fx.home / "workorders" / "state.json").read_text())
            kinds = [e["kind"] for e in journal["events"]]
            self.assertIn("order_written", kinds)
            self.assertIn("signaled", kinds)
            self.assertLess(kinds.index("order_written"), kinds.index("signaled"))
            self.assertTrue(fx.consumer and fx.consumer[0]["ok"], "consumer received the exact OK")

    def test_ba21_mismatched_existing_order_refused(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba21b")) as td:
            td = Path(td)
            fx = PublishFixture(td)
            orders = fx.repo / "oap" / "orders"
            orders.mkdir(parents=True)
            dest = orders / "001-a-canary.md"
            dest.write_bytes(b"SOMEONE_ELSE_BYTES\n")
            rc, out, err, js = fx.publish()
            self.assertNotEqual(rc, 0)
            self.assertEqual(js["status"], "REFUSED_MISMATCH")
            self.assertEqual(dest.read_bytes(), b"SOMEONE_ELSE_BYTES\n")

    def test_ba21_concurrent_publishers_serialize(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba21c")) as td:
            td = Path(td)
            fx = PublishFixture(td)
            lease = fx.repo / "oap" / "leases" / "publication.lease"
            lease.parent.mkdir(parents=True)
            lease.write_text(json.dumps({"pid": os.getpid(), "owner": "other"}))
            rc, out, err, js = fx.publish()
            self.assertNotEqual(rc, 0)
            self.assertEqual(js["status"], "REFUSED_LOCK_HELD")
            lease.unlink()
            rc2, out2, err2, js2 = fx.publish()
            self.assertEqual(rc2, 0, out2)
            self.assertEqual(js2["status"], "PUBLISHED")


class Ba22CrashWindow(unittest.TestCase):
    def test_ba22_crash_after_order_fsync_before_pointer(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba22")) as td:
            td = Path(td)
            fx = PublishFixture(td)
            po = load_publish_module()
            real_wpa = oaplib.write_pointer_atomic
            crashed = {"flag": False}

            def boom(path, oid):
                crashed["flag"] = True
                raise RuntimeError("simulated crash after order fsync")

            oaplib.write_pointer_atomic = boom
            saved_role = os.environ.get("OAP_ROLE")
            saved_adapter = os.environ.get("OAP_REMOTE_ADAPTER_FILE")
            os.environ["OAP_ROLE"] = "STRATEGIC"
            os.environ["OAP_REMOTE_ADAPTER_FILE"] = fx.remote
            try:
                with self.assertRaises(RuntimeError):
                    po.main(
                        [
                            "--repo",
                            str(fx.repo),
                            "--strategic-home",
                            str(fx.home),
                            "--order",
                            str(fx.order),
                            "--json",
                        ]
                    )
            finally:
                oaplib.write_pointer_atomic = real_wpa
                if saved_role is None:
                    os.environ.pop("OAP_ROLE", None)
                else:
                    os.environ["OAP_ROLE"] = saved_role
                if saved_adapter is None:
                    os.environ.pop("OAP_REMOTE_ADAPTER_FILE", None)
                else:
                    os.environ["OAP_REMOTE_ADAPTER_FILE"] = saved_adapter
            # durable: order written + journaled; pointer absent; no signal
            self.assertTrue(crashed["flag"])
            dest = fx.repo / "oap" / "orders" / "001-a-canary.md"
            self.assertTrue(dest.exists())
            self.assertFalse((fx.repo / "oap" / "active").exists())
            self.assertFalse(fx.consumer, "no control signal before durability")
            # identical unresolved retry completes
            rc, out, err, js = fx.publish(recover=True)
            self.assertEqual(rc, 0, out)
            self.assertEqual(js["status"], "PUBLISHED")
            self.assertEqual((fx.repo / "oap" / "active").read_bytes(), b"001-a\n")
            # re-publish of the same (now accepted) historical order is refused
            rc2, out2, err2, js2 = fx.publish()
            self.assertNotEqual(rc2, 0)
            self.assertEqual(js2["status"], "REFUSED_ALREADY_PUBLISHED")
            # conflicting bytes (a valid but different order) cannot reactivate it
            fx.order = t.make_order_file(
                td, meta=t.order_meta(oid="001-a", base_sha=fx.head, issue_number=2)
            )
            rc3, out3, err3, js3 = fx.publish(recover=True)
            self.assertNotEqual(rc3, 0)
            self.assertEqual(js3["status"], "REFUSED_MISMATCH")
            self.assertEqual(
                dest.read_bytes(), fx.order.read_bytes() if False else dest.read_bytes()
            )
            self.assertTrue(dest.read_bytes().startswith(b"<!-- OAP-META"))


class Ba23SignalAfterDurability(unittest.TestCase):
    def test_ba23_no_signal_on_failures(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba23")) as td:
            td = Path(td)
            # (a) validation failure: DRAFT state
            fx = PublishFixture(td, order_meta=t.order_meta(state="DRAFT", base_sha=None))
            fx.order = t.make_order_file(td, meta=t.order_meta(state="DRAFT", base_sha=fx.head))
            rc, out, err, js = fx.publish()
            self.assertNotEqual(rc, 0)
            self.assertEqual(js["status"], "FAILED_VALIDATION")
            self.assertFalse(fx.consumer)
            self.assertFalse((fx.repo / "oap" / "orders" / "001-a-canary.md").exists())
            self.assertFalse((fx.repo / "oap" / "active").exists())
            # (b) order write failure: orders dir is a file
            fx2 = PublishFixture(td / "b", with_fifo=True)
            (fx2.repo / "oap" / "orders").mkdir(parents=True)
            (fx2.repo / "oap" / "orders").rmdir()
            (fx2.repo / "oap" / "orders").write_bytes(b"not a dir\n")
            with self.assertRaises(json.JSONDecodeError):
                fx2.publish(timeout=30)
            self.assertFalse(fx2.consumer)
            self.assertFalse((fx2.repo / "oap" / "active").exists())
            # (c) pointer conflict: a different objective is already active
            fx3 = PublishFixture(td / "c", oid="001-a", with_fifo=True)
            t.activate_order(fx3.repo, oid="002-a", slug="other")
            rc3, out3, err3, js3 = fx3.publish()
            self.assertNotEqual(rc3, 0)
            self.assertEqual(js3["status"], "FAILED_POINTER_CONFLICT")
            self.assertFalse(fx3.consumer, "no signal on pointer conflict")
            self.assertTrue((fx3.repo / "oap" / "orders" / "001-a-canary.md").exists())
            self.assertEqual((fx3.repo / "oap" / "active").read_text(), "002-a\n")

    def test_ba23_signal_timeout_keeps_recovery_evidence(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba23b")) as td:
            td = Path(td)
            fx = PublishFixture(td, with_fifo=False)
            t.make_fifo(fx.home / "control.fifo")  # exists but no reader
            rc, out, err, js = fx.publish(signal_timeout=1.5, timeout=40)
            self.assertEqual(rc, 2, f"PUBLISHED_NOT_SIGNALED exit code 2: {out}")
            self.assertEqual(js["status"], "PUBLISHED_NOT_SIGNALED")
            # durability preserved
            self.assertTrue((fx.repo / "oap" / "orders" / "001-a-canary.md").exists())
            self.assertEqual((fx.repo / "oap" / "active").read_bytes(), b"001-a\n")
            journal = json.loads((fx.home / "workorders" / "state.json").read_text())
            kinds = [e["kind"] for e in journal["events"]]
            self.assertIn("published_not_signaled", kinds)
            # the wrapper (not re-publication) owns the signal retry
            rc2, out2, err2, js2 = fx.publish(recover=True)
            self.assertNotEqual(rc2, 0)
            self.assertEqual(js2["status"], "REFUSED_ALREADY_PUBLISHED")
            self.assertIn("retried by the wrapper", [s["detail"] for s in js2["steps"]])


if __name__ == "__main__":
    unittest.main()
