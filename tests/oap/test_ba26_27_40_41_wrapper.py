"""BA-26/BA-27/BA-40/BA-41 — wrapper invocation discipline, duplicate
notifications, quit/duplicate process, consumed-signal crash recovery."""

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


def start_wrapper(
    td: Path, repo: Path, home: Path, extra: list = None, env: dict = None, cwd: Path = None
):
    log = td / f"fake-{os.getpid()}.jsonl"
    p = subprocess.Popen(
        [
            sys.executable,
            str(t.BIN / "oap_launch.py"),
            "coding",
            "--repo",
            str(repo),
            "--strategic-home",
            str(home),
        ]
        + (extra or []),
        env={**os.environ, "OAP_FAKE_LOG": str(log), **(env or {})},
        cwd=str(cwd or repo),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return p, log


class WrapperFixture:
    def __init__(self, td: Path, oid: str = "001-a"):
        self.td = td
        self.repo = td / "repo"
        self.head = t.make_repo(self.repo, {"AGENTS.md": b"router\n"})
        self.fake = t.install_fake_client(td)
        self.home = td / "home"
        (self.home / "agent-homes" / "coding").mkdir(parents=True)
        t.write_runtime_env(
            self.home,
            self.repo,
            activation=True,
            authority=True,
            coding_argv=[str(self.fake)],
            model="fixture-model",
        )
        t.make_fifo(self.home / "control.fifo")
        self.oid = oid
        t.activate_order(self.repo, oid=oid)


class Ba26ZeroIdle(unittest.TestCase):
    def test_ba26_zero_model_calls_while_idle(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba26")) as td:
            td = Path(td)
            fx = WrapperFixture(td)
            p, log = start_wrapper(td, fx.repo, fx.home)
            try:
                time.sleep(2.0)  # idle: no signal at all
                self.assertEqual(t.read_fake_log(log), [], "no model call while idle")
                # one valid control wakes exactly one fresh invocation
                t.fifo_write(fx.home / "control.fifo")
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    if len(t.read_fake_log(log)) >= 1:
                        break
                    time.sleep(0.1)
                recs = t.read_fake_log(log)
                self.assertEqual(len(recs), 1, "exactly one invocation")
                self.assertEqual(recs[0]["cwd"], os.path.realpath(str(fx.repo)))
                prompt = recs[0]["argv"][-1]
                self.assertIn("already consumed", prompt)
                # the model is never asked to wait on the FIFO itself
                self.assertNotIn("control.fifo", prompt)
                self.assertNotIn("wait for", prompt)
            finally:
                p.send_signal(signal.SIGTERM)
                try:
                    out, err = p.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    p.kill()
                    out, err = p.communicate()
            # clean exit on SIGTERM: wrapper handled it (no traceback)
            self.assertNotIn("Traceback", err.decode())

    def test_ba26_consumption_journalized(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba26b")) as td:
            td = Path(td)
            fx = WrapperFixture(td)
            p, log = start_wrapper(td, fx.repo, fx.home)
            try:
                time.sleep(0.7)
                t.fifo_write(fx.home / "control.fifo")
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    j = fx.home / "workorders" / "state.json"
                    if j.exists() and "control_consumed" in j.read_text():
                        break
                    time.sleep(0.1)
                j = json.loads((fx.home / "workorders" / "state.json").read_text())
                kinds = [e["kind"] for e in j["events"]]
                self.assertIn("control_consumed", kinds)
                self.assertIn("invoked", kinds)
                self.assertLess(kinds.index("control_consumed"), kinds.index("invoked"))
            finally:
                p.send_signal(signal.SIGTERM)
                try:
                    p.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.communicate()


class Ba27Duplicate(unittest.TestCase):
    def test_ba27_extra_wakeups_do_not_reimplement(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba27")) as td:
            td = Path(td)
            fx = WrapperFixture(td)
            p, log = start_wrapper(td, fx.repo, fx.home)
            try:
                time.sleep(0.7)
                t.fifo_write(fx.home / "control.fifo")
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    if len(t.read_fake_log(log)) >= 1:
                        break
                    time.sleep(0.1)
                # let the invocation finish, then spam extra wake-ups while the
                # objective is published (report present, invocation journaled)
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    j = fx.home / "workorders" / "state.json"
                    if j.exists() and "invocation_exited" in j.read_text():
                        break
                    time.sleep(0.1)
                (fx.repo / "oap" / "reports").mkdir(exist_ok=True)
                (fx.repo / "oap" / "reports" / "001-a-canary.md").write_text(
                    f"Implementation head SHA: {fx.head}\nReport publication commit: SELF\n"
                )
                for _ in range(3):
                    t.fifo_write(fx.home / "control.fifo")
                    time.sleep(0.4)
                time.sleep(1.0)
                recs = t.read_fake_log(log)
                self.assertEqual(
                    len(recs), 1, f"duplicate wake-ups must not re-invoke: {len(recs)}"
                )
                self.assertEqual(
                    (fx.repo / "oap" / "active").read_text(),
                    "001-a\n",
                    "same durable objective remains selected",
                )
            finally:
                p.send_signal(signal.SIGTERM)
                try:
                    p.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.communicate()


class Ba40QuitDuplicate(unittest.TestCase):
    def test_ba40_sigint_sigterm_quit_without_restart(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba40")) as td:
            td = Path(td)
            fx = WrapperFixture(td)
            # unrelated process + unrelated tmux session must survive
            sleeper = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
            sock = t.tmux_socket()
            rc, out, err = t.tmux_run(sock, ["new-session", "-d", "-s", "unrelated", "sleep 30"])
            self.assertEqual(rc, 0, err)
            try:
                p, log = start_wrapper(td, fx.repo, fx.home)
                time.sleep(0.7)
                p.send_signal(signal.SIGINT)
                out, err = p.communicate(timeout=10)
                self.assertNotIn("Traceback", err.decode())
                self.assertEqual(len(t.read_fake_log(log)), 0, "no invocation, no restart")
                # second wrapper: SIGTERM
                p2, log2 = start_wrapper(td, fx.repo, fx.home)
                time.sleep(0.7)
                p2.send_signal(signal.SIGTERM)
                out2, err2 = p2.communicate(timeout=10)
                self.assertNotIn("Traceback", err2.decode())
                self.assertEqual(len(t.read_fake_log(log2)), 0)
            finally:
                rc2, _, _ = t.tmux_run(sock, ["kill-server"])
                sleeper.kill()
                sleeper.wait(timeout=10)

    def test_ba40_duplicate_consumer_blocked(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba40b")) as td:
            td = Path(td)
            fx = WrapperFixture(td)
            p1, log1 = start_wrapper(td, fx.repo, fx.home)
            time.sleep(1.0)  # first wrapper owns the FIFO consumer lease
            try:
                # a second raw consumer must be refused while the wrapper is up
                res = oaplib.fifo_receive(
                    str(fx.home / "control.fifo"), timeout=2.0, lease_owner="intruder"
                )
                self.assertFalse(res["ok"])
                self.assertIn("another consumer", res["error"])
                # a second wrapper process is also refused (duplicate lease)
                lease = fx.repo / "oap" / "leases" / "coding-wrapper.lease"
                self.assertTrue(lease.exists())
                p2, log2 = start_wrapper(td, fx.repo, fx.home, env={})
                time.sleep(1.5)
                out2, err2 = p2.communicate(timeout=10)
                self.assertIn("duplicate", out2.decode())
                self.assertEqual(len(t.read_fake_log(log2)), 0)
            finally:
                p1.send_signal(signal.SIGTERM)
                try:
                    p1.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    p1.kill()


class Ba41ConsumedCrash(unittest.TestCase):
    def test_ba41_consumed_without_report_recovers_same_objective(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba41")) as td:
            td = Path(td)
            fx = WrapperFixture(td)
            # simulate: wake-up consumed, process died before the report
            jpath = fx.home / "workorders" / "state.json"
            jpath.parent.mkdir(parents=True, exist_ok=True)
            jpath.write_text(
                json.dumps(
                    {
                        "events": [
                            {"ts": time.time(), "kind": "control_consumed", "order_id": "001-a"}
                        ]
                    }
                )
            )
            state = oaplib.classify_state(str(fx.repo), str(fx.home))
            self.assertEqual(state["state"], "RUNNING_INTERRUPTED")
            self.assertIn("resume same ID/branch/PR", state["detail"])
            # a restarted wrapper resumes the SAME objective (no new task, no fake accept)
            p, log = start_wrapper(td, fx.repo, fx.home)
            try:
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    if len(t.read_fake_log(log)) >= 1:
                        break
                    time.sleep(0.1)
                recs = t.read_fake_log(log)
                self.assertEqual(len(recs), 1, "resume re-invokes the same objective")
                j = json.loads(jpath.read_text())
                events = j["events"]
                self.assertEqual(
                    [e["order_id"] for e in events if e["kind"] == "invoked"], ["001-a"]
                )
                self.assertFalse(
                    any(e.get("kind") in ("merged", "accepted") for e in events),
                    "crash must not be falsely marked accepted",
                )
                # no second objective was invented
                self.assertEqual(len(list((fx.repo / "oap" / "orders").glob("*.md"))), 1)
                self.assertEqual((fx.repo / "oap" / "active").read_text(), "001-a\n")
            finally:
                p.send_signal(signal.SIGTERM)
                try:
                    p.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.communicate()


if __name__ == "__main__":
    unittest.main()
