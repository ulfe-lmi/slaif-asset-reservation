"""BA-24/BA-25 — FIFO framing and ownership on real temporary FIFOs."""

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "oap" / "bin"))

import oaplib  # noqa: E402
import oaptestlib as t  # noqa: E402


class Ba24Framing(unittest.TestCase):
    def _one(self, send_fn, timeout=8.0):
        td = tempfile.TemporaryDirectory(prefix=t.unique_name("ba24"))
        try:
            fifo = t.make_fifo(Path(td.name) / "c.fifo")
            holder = []
            th = t.fifo_consumer_thread(fifo, holder, timeout=timeout)
            time.sleep(0.15)  # let the reader open
            send_fn(fifo)
            th.join(timeout=timeout + 5)
            self.assertFalse(th.is_alive(), "consumer did not finish")
            return holder[0]
        finally:
            td.cleanup()

    def test_ba24_exact_ok(self):
        res = self._one(lambda f: t.fifo_write(f, b"OK"))
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["data"], b"OK")

    def test_ba24_fragmented_write(self):
        res = self._one(lambda f: t.fifo_write(f, b"OK", fragment=True))
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["data"], b"OK")

    def test_ba24_empty_bytes(self):
        res = self._one(lambda f: t.fifo_write(f, b""))
        self.assertFalse(res["ok"])
        self.assertEqual(res["code"], 4)

    def test_ba24_one_byte(self):
        res = self._one(lambda f: t.fifo_write(f, b"O"))
        self.assertFalse(res["ok"])
        self.assertEqual(res["code"], 4)

    def test_ba24_extra_bytes(self):
        res = self._one(lambda f: t.fifo_write(f, b"OKX"))
        self.assertFalse(res["ok"])
        self.assertIn("more than two", res["error"])

    def test_ba24_invalid_bytes(self):
        res = self._one(lambda f: t.fifo_write(f, b"XX"))
        self.assertFalse(res["ok"])
        self.assertIn("invalid framing", res["error"])

    def test_ba24_finite_timeouts(self):
        td = tempfile.TemporaryDirectory(prefix=t.unique_name("ba24t"))
        try:
            fifo = t.make_fifo(Path(td.name) / "c.fifo")
            # sender without a reader: bounded timeout, code 3
            t0 = time.monotonic()
            res = oaplib.fifo_send(str(fifo), timeout=1.0)
            self.assertFalse(res["ok"])
            self.assertEqual(res["code"], 3)
            self.assertLess(time.monotonic() - t0, 5.0)
            # receiver without a sender: bounded timeout, code 3
            holder = []
            th = t.fifo_consumer_thread(fifo, holder, timeout=1.0)
            th.join(timeout=10)
            self.assertFalse(th.is_alive())
            self.assertEqual(holder[0]["code"], 3)
        finally:
            td.cleanup()


class Ba25Ownership(unittest.TestCase):
    def test_ba25_symlink_and_regular_file_refused(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba25")) as td:
            td = Path(td)
            real = t.make_fifo(td / "real.fifo")
            link = td / "link.fifo"
            os.symlink(str(real), str(link))
            res = oaplib.fifo_send(str(link), timeout=1.0)
            self.assertFalse(res["ok"])
            self.assertIn("symlink", res["error"])
            res2 = oaplib.fifo_receive(str(link), timeout=1.0)
            self.assertFalse(res2["ok"])
            regular = td / "plain.fifo"
            regular.write_bytes(b"OK")
            res3 = oaplib.fifo_send(str(regular), timeout=1.0)
            self.assertFalse(res3["ok"])
            self.assertIn("not a FIFO", res3["error"])

    def test_ba25_mode_must_be_0600(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba25b")) as td:
            td = Path(td)
            fifo = t.make_fifo(td / "c.fifo")
            os.chmod(str(fifo), 0o644)
            res = oaplib.fifo_send(str(fifo), timeout=1.0)
            self.assertFalse(res["ok"])
            self.assertIn("0600", res["error"])
            os.chmod(str(fifo), 0o600)
            holder = []
            th = t.fifo_consumer_thread(fifo, holder, timeout=5.0)
            time.sleep(0.15)
            t.fifo_write(fifo, b"OK")
            th.join(timeout=10)
            self.assertTrue(holder[0]["ok"])

    def test_ba25_multiple_consumers_rejected(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba25c")) as td:
            td = Path(td)
            fifo = t.make_fifo(td / "c.fifo")
            holder1 = []
            th1 = t.fifo_consumer_thread(fifo, holder1, timeout=6.0, owner="first")
            time.sleep(0.4)  # first consumer owns the lease now
            res2 = oaplib.fifo_receive(str(fifo), timeout=3.0, lease_owner="second")
            self.assertFalse(res2["ok"])
            self.assertIn("another consumer", res2["error"])
            t.fifo_write(fifo, b"OK")
            th1.join(timeout=10)
            self.assertTrue(holder1[0]["ok"])
            # lease released afterwards: a new consumer may proceed
            holder3 = []
            th3 = t.fifo_consumer_thread(fifo, holder3, timeout=5.0, owner="third")
            time.sleep(0.15)
            t.fifo_write(fifo, b"OK")
            th3.join(timeout=10)
            self.assertTrue(holder3[0]["ok"])

    def test_ba25_sender_closes_descriptor(self):
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba25d")) as td:
            td = Path(td)
            fifo = t.make_fifo(td / "c.fifo")
            holder = []
            th = t.fifo_consumer_thread(fifo, holder, timeout=5.0)
            time.sleep(0.15)
            opened, closed = [], []
            real_open, real_close = os.open, os.close

            def spy_open(path, flags, *a, **k):
                fd = real_open(path, flags, *a, **k)
                if os.fspath(path) == str(fifo):
                    opened.append(fd)
                return fd

            def spy_close(fd):
                if fd in opened:
                    closed.append(fd)
                return real_close(fd)

            os.open, os.close = spy_open, spy_close
            try:
                res = oaplib.fifo_send(str(fifo), timeout=5.0)
            finally:
                os.open, os.close = real_open, real_close
            self.assertTrue(res["ok"])
            self.assertEqual(
                sorted(opened), sorted(closed), "sender must close every descriptor it opened"
            )
            th.join(timeout=10)
            self.assertTrue(holder[0]["ok"])

    def test_ba25_no_dummy_writer_masks_eof(self):
        """A second writer appending after the first closes is a NEW message;
        a concurrent second writer concatenates into invalid framing."""
        with tempfile.TemporaryDirectory(prefix=t.unique_name("ba25e")) as td:
            td = Path(td)
            fifo = t.make_fifo(td / "c.fifo")
            holder = []
            th = t.fifo_consumer_thread(fifo, holder, timeout=6.0)
            time.sleep(0.15)
            # two senders race: bytes concatenate to OKOK -> framing error
            t.fifo_write(fifo, b"OKOK")
            th.join(timeout=10)
            self.assertFalse(holder[0]["ok"])
            self.assertIn("more than two", holder[0]["error"])
            # sequential messages: each sender closes -> clean EOF per message
            holder2 = []
            th2 = t.fifo_consumer_thread(fifo, holder2, timeout=5.0)
            time.sleep(0.15)
            t.fifo_write(fifo, b"OK")
            th2.join(timeout=10)
            self.assertTrue(holder2[0]["ok"])
            self.assertEqual(holder2[0]["data"], b"OK")


if __name__ == "__main__":
    unittest.main()
