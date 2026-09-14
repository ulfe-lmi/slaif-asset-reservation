"""015-a round-trip canary — the simplified round, end to end, on a fixture repo.

Proves on a fixture repo with explicit fake remote/client adapters and a real
temporary POSIX FIFO (finite timeouts throughout):

  (a) publish dry-run performs zero writes
  (b) real publication creates the immutable order, then the exact ID+LF pointer
  (c) one control OK consumes exactly one wake-up and launches exactly one fresh
      coding context
  (d) the (fake) coding round commits order/pointer bytes, opens the PR before
      report composition, and appends a report-only commit whose literal
      implementation head is the first parent
  (e) verify_report passes (exactly the three slim checks)
  (f) check_state traces PUBLISHED -> REPORT_PUBLISHED -> inactive after pointer
      clear
  (g) a duplicate wake-up reconciles and suppresses a second launch
"""

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "oap" / "bin"))

import oaplib  # noqa: E402
import oaptestlib as t  # noqa: E402


def _wait(predicate, timeout: float = 15.0, interval: float = 0.1):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False


class RoundTripCanary(unittest.TestCase):
    def test_roundtrip_canary(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("canary")) as td:
            td = Path(td)
            repo = td / "repo"
            head0 = t.make_repo(repo, {"AGENTS.md": b"router\n"}, "baseline")
            home = td / "home"
            (home / "agent-homes" / "coding").mkdir(parents=True)
            fake = t.install_fake_client(td)
            t.write_runtime_env(
                home,
                repo,
                activation=True,
                authority=True,
                coding_argv=[str(fake)],
                model="fixture-model",
            )
            control = t.make_fifo(home / "control.fifo")  # real temp POSIX FIFO
            fake_log = td / "fake-codex.jsonl"
            remote_state = {
                "refs": {"refs/heads/main": head0},
                "prs": [],
                "next_pr_number": 50,
            }
            remote_file = t.write_remote_state(td, remote_state)
            env = {"OAP_ROLE": "STRATEGIC", "OAP_REMOTE_ADAPTER_FILE": remote_file}
            order = t.make_order_file(td, oid="001-a", base_sha=head0)
            oid = "001-a"
            branch = "oap/001-a"

            def publish_cli(dry: bool, recover: bool = False, json_out: bool = True):
                args = [
                    "--repo",
                    str(repo),
                    "--strategic-home",
                    str(home),
                    "--order",
                    str(order),
                ]
                if dry:
                    args.append("--dry-run")
                if recover:
                    args.append("--recover")
                if json_out:
                    args.append("--json")
                return t.run_cli(
                    "publish_order.py", args, env=env, timeout=40, expect_json=json_out
                )

            # ---------------- (a) dry-run: zero writes ----------------
            before = t.snapshot(str(repo)) | {
                f"home/{k}": v for k, v in t.snapshot(str(home)).items()
            }
            rc, out, err, js = publish_cli(dry=True)
            self.assertEqual(rc, 0, out + err)
            self.assertEqual(js["status"], "DRY_RUN_VALID")
            after = t.snapshot(str(repo)) | {
                f"home/{k}": v for k, v in t.snapshot(str(home)).items()
            }
            self.assertEqual(before, after, "dry-run must perform zero writes")
            self.assertFalse((repo / "oap" / "active").exists())

            # ---------------- (b) real publication: order, then pointer ----------------
            consumer = []
            thr = t.fifo_consumer_thread(control, consumer, timeout=30)
            time.sleep(0.2)  # let the reader open
            rc, out, err, js = publish_cli(dry=False)
            self.assertEqual(rc, 0, out + err)
            self.assertEqual(js["status"], "PUBLISHED")
            thr.join(timeout=10)
            self.assertFalse(thr.is_alive(), "signal consumer did not finish")
            dest = repo / "oap" / "orders" / "001-a-canary.md"
            self.assertEqual(dest.read_bytes(), order.read_bytes(), "order bytes immutable")
            self.assertEqual(
                (repo / "oap" / "active").read_bytes(), b"001-a\n", "pointer is exactly ID+LF"
            )
            journal = json.loads((home / "workorders" / "state.json").read_text())
            kinds = [e["kind"] for e in journal["events"]]
            self.assertIn("order_written", kinds)
            self.assertIn("signaled", kinds)
            self.assertLess(kinds.index("order_written"), kinds.index("signaled"))
            self.assertTrue(consumer and consumer[0]["ok"], "control OK received")
            self.assertEqual(consumer[0]["data"], b"OK", "exactly the two ASCII OK bytes")
            # the PUBLISHED state is visible to check_state
            st = oaplib.classify_state(str(repo), str(home), oaplib.FixtureRemote(remote_state))
            self.assertEqual(st["state"], "ACTIVE_PENDING", st)

            # ---------------- (c) one control OK -> exactly one fresh context ----------------
            wrapper = subprocess.Popen(
                [
                    sys.executable,
                    str(t.BIN / "oap_launch.py"),
                    "coding",
                    "--repo",
                    str(repo),
                    "--strategic-home",
                    str(home),
                ],
                env={**os.environ, "OAP_FAKE_LOG": str(fake_log)},
                cwd=str(repo),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                self.assertTrue(
                    _wait(lambda: len(t.read_fake_log(fake_log)) == 0, timeout=3.0),
                    "wrapper came up idle without invoking",
                )
                t.fifo_write(control)  # exactly one control OK
                self.assertTrue(
                    _wait(lambda: len(t.read_fake_log(fake_log)) >= 1),
                    "wake-up must launch exactly one fresh coding context",
                )
                self.assertTrue(
                    _wait(
                        lambda: "invocation_exited"
                        in (home / "workorders" / "state.json").read_text()
                    ),
                    "invocation did not exit",
                )
                recs = t.read_fake_log(fake_log)
                self.assertEqual(len(recs), 1, "exactly one invocation")
                self.assertEqual(recs[0]["OAP_ROLE"], "CODING")
                self.assertEqual(recs[0]["cwd"], os.path.realpath(str(repo)))
                self.assertEqual(
                    recs[0]["CODEX_HOME"], os.path.realpath(str(home / "agent-homes" / "coding"))
                )
                self.assertIn("already consumed", recs[0]["argv"][-1])
                j = json.loads((home / "workorders" / "state.json").read_text())
                kinds = [e["kind"] for e in j["events"]]
                self.assertIn("control_consumed", kinds)
                self.assertLess(kinds.index("control_consumed"), kinds.index("invoked"))
            finally:
                wrapper.send_signal(signal.SIGTERM)
                try:
                    wout, werr = wrapper.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    wrapper.kill()
                    wout, werr = wrapper.communicate()
            self.assertNotIn("Traceback", werr.decode(), "clean wrapper exit")

            # ---------------- (d) fake coding round: commit, PR, report ----------------
            t.git(repo, "add", "-A")  # order + pointer bytes
            t.git(repo, "commit", "-q", "-m", "implementation: order and pointer bytes")
            impl_head = t.head(repo)
            # PR identity BEFORE report composition
            adapter = oaplib.FixtureRemote(remote_state)
            pr = adapter.create_pr(str(repo), branch, "round-trip canary")
            self.assertIsNotNone(pr)
            pr_number = pr["number"]
            report_name = "oap/reports/001-a-canary.md"
            report_text = (
                "# Final report 001-a-canary (fixture)\n\n"
                f"Order digest: {oaplib.sha256_hex(dest.read_bytes())}\n"
                f"Implementation head SHA: {impl_head}\n"
                "Report publication commit: SELF\n\n"
                "## Implementation head CI\n"
                "quality/test/container observed at the implementation head (fixture).\n\n"
                "## Report head CI\n"
                "NOT YET OBSERVED AT AUTHORING\n"
            )
            (repo / report_name).parent.mkdir(parents=True, exist_ok=True)
            (repo / report_name).write_text(report_text)
            t.git(repo, "add", report_name)  # report-only commit
            t.git(repo, "commit", "-q", "-m", "report only")
            report_commit = t.head(repo)
            self.assertEqual(t.git(repo, "rev-parse", report_commit + "^"), impl_head)
            # remote now carries the branch head at the report commit, PR still open
            remote_state["refs"][branch] = report_commit
            remote_state["refs"]["refs/heads/" + branch] = report_commit
            Path(remote_file).write_text(json.dumps(remote_state))

            # ---------------- (e) verify_report: exactly three checks, PASS ----------------
            rc, out, err, js = t.run_cli(
                "verify_report.py",
                [
                    "--repo",
                    str(repo),
                    "--id",
                    oid,
                    "--pr",
                    str(pr_number),
                    "--head",
                    report_commit,
                    "--json",
                ],
                env={"OAP_REMOTE_ADAPTER_FILE": remote_file},
                timeout=40,
                expect_json=True,
            )
            self.assertEqual(js["status"], "PASS", js)
            self.assertEqual(
                sorted(js["checks"]),
                [
                    "implementation_head_first_parent",
                    "remote_head_and_pr_identity",
                    "report_only_changed_path",
                ],
            )
            self.assertTrue(all(c["ok"] for c in js["checks"].values()), js)

            # ---------------- (f) state trace (part 1): REPORT_PUBLISHED ----------------
            st = oaplib.classify_state(str(repo), str(home), oaplib.FixtureRemote(remote_state))
            self.assertEqual(st["state"], "REPORT_PUBLISHED", st)

            # ---------------- (g) duplicate wake-up: reconcile, suppress ----------------
            wrapper2 = subprocess.Popen(
                [
                    sys.executable,
                    str(t.BIN / "oap_launch.py"),
                    "coding",
                    "--repo",
                    str(repo),
                    "--strategic-home",
                    str(home),
                ],
                env={**os.environ, "OAP_FAKE_LOG": str(fake_log)},
                cwd=str(repo),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                self.assertTrue(_wait(lambda: True, timeout=1.5))  # wrapper settles
                t.fifo_write(control)
                t.fifo_write(control)  # duplicate wake-ups
                self.assertTrue(_wait(lambda: True, timeout=3.0))  # let them reconcile
                self.assertEqual(
                    len(t.read_fake_log(fake_log)),
                    1,
                    "duplicate wake-ups must not launch a second context",
                )
                self.assertEqual((repo / "oap" / "active").read_bytes(), b"001-a\n")
            finally:
                wrapper2.send_signal(signal.SIGTERM)
                try:
                    _, werr2 = wrapper2.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    wrapper2.kill()
                    _, werr2 = wrapper2.communicate()
            self.assertNotIn("Traceback", werr2.decode(), "clean wrapper exit")

            # ---------------- (f) state trace (part 2): pointer clear -> INACTIVE --------
            (repo / "oap" / "active").unlink()
            st = oaplib.classify_state(str(repo), str(home), oaplib.FixtureRemote(remote_state))
            self.assertEqual(st["state"], "INACTIVE", st)
            rc, out, err, _ = t.run_cli(
                "check_state.py", ["--repo", str(repo), "--strategic-home", str(home)]
            )
            self.assertEqual(rc, 0, out + err)
            self.assertIn("state=INACTIVE", out)
