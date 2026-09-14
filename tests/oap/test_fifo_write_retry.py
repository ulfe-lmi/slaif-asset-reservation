"""023-a — deterministic regression tests for the fifo_write EPIPE retry.

The pre-existing CI flake (BrokenPipeError inside fifo_write, oaptestlib,
third occurrence at CI run 34811801450) happens when the writer's open
unblocks on a reader whose bounded receive window then expires BEFORE the
writer's write executes (runner load); the reader closes the read fd and
the write raises EPIPE. The wrapper re-polls, so a full-payload
re-delivery is safe (the torn-down session consumed no wake-up, and
duplicate wake-ups are suppressed state-based).

These tests prove exactly that test-harness contract on real temporary
POSIX FIFOs (no Django/PG, stdlib only):

  (1) a receive-window close between the writer's open and its write is
      retried until the full payload is delivered to the (re)opened
      reader; the writer survives;
  (2) if no reader ever returns, fifo_write raises after the bounded
      deadline (no infinite retry).

The reader mirrors the wrapper's real receive side (fifo_receive opens
O_RDONLY | O_NONBLOCK and polls). The only injected timing is a one-shot
stall of the process's first os.write — the runner stall between open
unblock and write that the flake describes; the EPIPE itself is a
genuine kernel EPIPE on real FIFO descriptors, and the retry logic is
the unpatched fifo_write.
"""

import os
import select
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "oap" / "bin"))

import oaptestlib as t  # noqa: E402


class OneShotWriteStall:
    """Deterministically delays the process's first os.write() call.

    Models the CI-runner stall between the writer's open unblocking and
    its first write executing. The real write then runs against real
    kernel state, so any resulting EPIPE is genuine. Restores os.write
    on exit even on failure.
    """

    def __init__(self, seconds: float):
        self.seconds = seconds
        self._armed = True
        self.consumed = False
        self._real = None

    def __enter__(self):
        self._real = os.write
        os.write = self._stalled
        return self

    def _stalled(self, fd, data, *args):
        if self._armed:
            self._armed = False
            self.consumed = True
            time.sleep(self.seconds)
        return self._real(fd, data, *args)

    def __exit__(self, *exc):
        os.write = self._real
        return False


class FifoWriteRetry(unittest.TestCase):
    def test_retry_delivers_after_receive_window_close(self):
        """Reader window closes after the writer's open unblocked but before
        its write executes; the retry must deliver the full payload to the
        (re)opened reader and the writer must survive."""
        with tempfile.TemporaryDirectory(prefix=t.unique_name("fwr")) as td:
            fifo = t.make_fifo(Path(td) / "c.fifo")
            received: dict = {}

            def reader():
                # (a) open the read end (non-blocking, like fifo_receive):
                #     unblocks the writer's pending open
                fd = os.open(str(fifo), os.O_RDONLY | os.O_NONBLOCK)
                # (b) the receive window expires without reading (the
                #     wrapper's bounded fifo_receive timeout, scaled to ms)
                time.sleep(0.10)
                # (c) close the read end; nothing was read, the session is lost
                os.close(fd)
                # (d) the next receive cycle: reopen and read to EOF. The
                #     sleep lower bound guarantees this reopen starts AFTER
                #     the stalled first attempt has EPIPE'd and closed its
                #     descriptor, so it is a fresh session, not a rejoin of
                #     the lost pipe.
                time.sleep(0.20)
                fd = os.open(str(fifo), os.O_RDONLY | os.O_NONBLOCK)
                data = b""
                while True:
                    r, _, _ = select.select([fd], [], [], 6.0)
                    if not r:
                        received.update(outcome="timeout")
                        return
                    chunk = os.read(fd, 4096)
                    if chunk == b"":
                        received.update(outcome="eof", data=data)
                        return
                    data += chunk

            th = threading.Thread(target=reader, daemon=True)
            th.start()
            exc = None
            t0 = time.monotonic()
            try:
                with OneShotWriteStall(0.15):
                    t.fifo_write(fifo, b"OK", deadline=5.0)
            except Exception as e:  # the writer must survive
                exc = e
            elapsed = time.monotonic() - t0
            th.join(timeout=8)
            self.assertIsNone(exc, f"writer must survive the receive-window close: {exc!r}")
            self.assertEqual(received.get("outcome"), "eof", received)
            self.assertEqual(received.get("data"), b"OK", "full payload, not a partial")
            # delivery happened in the (re)opened session, so the first
            # attempt necessarily EPIPE'd: the retry actually ran
            self.assertGreaterEqual(elapsed, 0.20, "retry must have crossed the close")

    def test_bounded_failure_when_reader_never_returns(self):
        """Reader opens, closes and never reopens: the first attempt EPIPEs
        and the retry must raise after the bounded deadline, not spin."""
        with tempfile.TemporaryDirectory(prefix=t.unique_name("fwr")) as td:
            fifo = t.make_fifo(Path(td) / "c.fifo")

            def reader():
                # opens (unblocking the writer's open), closes, never reopens
                fd = os.open(str(fifo), os.O_RDONLY | os.O_NONBLOCK)
                time.sleep(0.10)
                os.close(fd)

            th = threading.Thread(target=reader, daemon=True)
            th.start()
            stall = OneShotWriteStall(0.15)
            t0 = time.monotonic()
            with self.assertRaises(TimeoutError) as cm:
                with stall:
                    t.fifo_write(fifo, b"OK", deadline=1.5)
            elapsed = time.monotonic() - t0
            th.join(timeout=3)
            msg = str(cm.exception)
            self.assertIn(str(fifo), msg, "message must name the FIFO")
            # the first write attempt actually executed (and EPIPE'd after
            # the reader closed): the retry path was taken, then bounded
            self.assertTrue(stall.consumed, "first write attempt must have executed")
            self.assertGreaterEqual(elapsed, 1.4)
            self.assertLess(elapsed, 4.0)


if __name__ == "__main__":
    unittest.main()
