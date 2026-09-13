"""BA-49/BA-50 — privacy of operational outputs (sentinel redaction) and
owned-only cleanup (foreign files/sessions survive bootstrap operations).
"""

import json
import tempfile
import time
import unittest
from pathlib import Path

import oaplib
import oaptestlib as t

SENT_BEARER = "Bearer abcdef1234567890abcdef1234567890"
SENT_SAR = "sar_ab12cd34ef56_0123456789abcdef"
SENT_URL = "https://user:pass@example.com/x"
SENTINELS = (SENT_BEARER, SENT_SAR, SENT_URL)


class Ba49PrivacyOutputs(unittest.TestCase):
    def test_ba49_redact_unit(self):
        for sentinel in SENTINELS:
            out = oaplib.redact(f"prefix {sentinel} suffix")
            self.assertNotIn(sentinel, out)
            self.assertIn("[REDACTED]", out)
        # clean text passes through unchanged
        self.assertEqual(oaplib.redact("no secrets here"), "no secrets here")

    def _publish_env(self, prefix):
        td = Path(tempfile.mkdtemp(prefix=t.unique_name(prefix)))
        repo = td / "repo"
        head = t.make_repo(repo, {"a.txt": b"a\n"})
        home = td / "home"
        home.mkdir()
        outside = td / "outside"
        outside.mkdir()
        authority = outside / "authority.json"
        authority.write_text(
            json.dumps({"attributed": True, "reference": "fixture-external-record"})
        )
        t.write_runtime_env(home, repo, activation=True, authority=True)
        envp = home / "runtime.env"
        envp.write_text(
            envp.read_text().replace("/abs/attributable-authority.json", str(authority))
        )
        oaplib.ensure_fifo(str(home / "control.fifo"), 0o600)
        remote_file = t.write_remote_state(td, {"refs": {"refs/heads/main": head}})
        return td, repo, head, home, authority, remote_file

    def test_ba49_sentinels_never_leak_into_journal_or_cli(self):
        td, repo, head, home, authority, remote_file = self._publish_env("ba49")
        holder = []
        thr = t.fifo_consumer_thread(home / "control.fifo", holder, timeout=30)
        body = (
            "# 001-a — fixture canary with fixture credentials in the order body\n\n"
            "These fixture-only sentinels must not leak into journal or CLI output:\n\n"
            f"- {SENT_BEARER}\n- {SENT_SAR}\n- {SENT_URL}\n\n"
            "## Deferred human adjudication\n\n- Decision: NONE\n"
        )
        order = t.make_order_file(td, oid="001-a", base_sha=head, body=body)
        rc, out, err, js = t.run_cli(
            "publish_order.py",
            ["--repo", str(repo), "--strategic-home", str(home), "--order", str(order), "--json"],
            env={"OAP_ROLE": "STRATEGIC", "OAP_REMOTE_ADAPTER_FILE": remote_file},
            expect_json=True,
        )
        thr.join(timeout=45)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(js["status"], "PUBLISHED")
        # durable publication happened
        self.assertEqual((repo / "oap" / "active").read_bytes(), b"001-a\n")
        self.assertTrue((repo / "oap" / "orders" / "001-a-canary.md").is_file())
        # 1) journal: no sentinel bytes
        journal = (home / "workorders" / "state.json").read_bytes()
        for s in SENTINELS:
            self.assertNotIn(s.encode(), journal)
        # 2) CLI output: no sentinel
        combined = (out + err).encode()
        for s in SENTINELS:
            self.assertNotIn(s.encode(), combined)
        # 3) the strategic home contains no auth file and no sentinel anywhere
        for p in home.rglob("*"):
            if p.is_file():
                data = p.read_bytes()
                for s in SENTINELS:
                    self.assertNotIn(s.encode(), data, f"leak into {p}")
        self.assertTrue(authority.exists())
        self.assertFalse(
            str(authority).startswith(str(home)),
            "authority reference must stay outside the strategic home",
        )
        # the order artifact itself legitimately carries the ordered bytes
        self.assertIn(SENT_SAR.encode(), (repo / "oap" / "orders" / "001-a-canary.md").read_bytes())


class Ba50OwnedCleanup(unittest.TestCase):
    def setUp(self):
        self.td = Path(tempfile.mkdtemp(prefix=t.unique_name("ba50")))
        self.parent = self.td
        self.foreign_files = []
        for name in ("foreign-sentinel-1.txt", "foreign-sentinel-2.txt"):
            p = self.parent / name
            p.write_bytes((f"foreign {name} do-not-touch").encode())
            self.foreign_files.append(p)
        self.foreign_state = {
            p.name: (p.read_bytes(), p.lstat().st_mtime_ns) for p in self.foreign_files
        }
        self.sockets = []
        if t.TMUX:
            self.foreign_socket = t.tmux_socket()
            self.sockets.append(self.foreign_socket)
            rc, out, err = t.tmux_run(
                self.foreign_socket,
                ["new-session", "-d", "-s", "foreign-keep", "-x", "80", "-y", "24", "sleep", "300"],
            )
            self.assertGreaterEqual(rc, -1)
            self._foreign_session = "foreign-keep"
        else:
            t.record_blocked("BA-50", "tmux not installed; foreign-session part limited")
            self._foreign_session = None

    def tearDown(self):
        for sock in self.sockets:
            t.tmux_run(sock, ["kill-server"])

    def test_ba50_foreign_files_and_session_survive_owned_ops(self):
        # owned roots strictly inside a fresh subdirectory
        area = self.td / "owned-area"
        repo = area / "repo"
        home = area / "home"
        repo.mkdir(parents=True)
        home.mkdir()
        t.write_runtime_env(home, repo, activation=False)

        # 1) engine dry-run (no writes anywhere); bootstrap root is a distinct,
        # non-nested sibling root as the engine requires
        boot = self.td / "bootstrap-root"
        boot.mkdir(exist_ok=True)
        cr = t.make_manifest_root(area, [t.file_entry("REPO/NEW-FILE.md", b"candidate\n")])
        rc, out, err, js = t.run_engine(cr, str(repo), str(home), str(boot))
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(js["result"], "PLANNED")
        self.assertFalse(js["writes_performed"])

        # 2) FIFO framing round-trip on owned FIFOs only
        fifo = home / "owned.fifo"
        oaplib.ensure_fifo(str(fifo), 0o600)
        holder = []
        thr = t.fifo_consumer_thread(fifo, holder, timeout=20)
        time.sleep(0.05)
        sres = oaplib.fifo_send(str(fifo), timeout=15)
        thr.join(timeout=30)
        self.assertTrue(sres["ok"])
        self.assertEqual(holder[0]["code"], 0)

        # 3) owned tmux ops on an owned socket never touch the foreign one
        if t.TMUX:
            own_socket = t.tmux_socket()
            self.sockets.append(own_socket)
            rc, out, err = t.tmux_run(
                own_socket,
                ["new-session", "-d", "-s", "owned-x", "-x", "80", "-y", "24", "sleep", "300"],
            )
            self.assertEqual(rc, 0, err)
            rc, out, err = t.tmux_run(own_socket, ["kill-session", "-t", "owned-x"])
            self.assertEqual(rc, 0, err)

        # verification: foreign bytes, mtimes and session untouched
        for p in self.foreign_files:
            cur = (p.read_bytes(), p.lstat().st_mtime_ns)
            self.assertEqual(cur, self.foreign_state[p.name], f"foreign file touched: {p}")
        listed = sorted(p.name for p in self.parent.iterdir())
        for name in self.foreign_state:
            self.assertIn(name, listed)
        if self._foreign_session:
            rc, out, err = t.tmux_run(
                self.foreign_socket, ["has-session", "-t", self._foreign_session]
            )
            self.assertEqual(rc, 0, f"foreign session killed: {out} {err}")


if __name__ == "__main__":
    unittest.main()
