#!/usr/bin/env python3
"""oap_fifo.py — exact two-byte FIFO transport (OP-05).

send: write exactly ASCII 'OK' (0x4f4b); handles partial writes/EINTR; closes fd.
receive: single-consumer lease; accumulates until EOF; rejects 0/1/>2 bytes, invalid
bytes, missing FIFO, symlinks, wrong owner/mode; finite timeouts.
Exit codes: 0 ok; 3 timeout; 4 framing/type error; 5 ownership/lease; 6 missing FIFO.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oaplib  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("send", "receive"):
        p = sub.add_parser(name)
        p.add_argument("--fifo", required=True)
        p.add_argument("--timeout", type=float, default=10.0)
        if name == "receive":
            p.add_argument("--owner", default="oap-receiver")
    args = ap.parse_args(argv)
    if args.cmd == "send":
        res = oaplib.fifo_send(args.fifo, timeout=args.timeout)
    else:
        res = oaplib.fifo_receive(args.fifo, timeout=args.timeout, lease_owner=args.owner)
    if not res["ok"]:
        print(
            oaplib.redact(json.dumps({"ok": False, "error": res.get("error"), "code": res["code"]}))
        )
        return res["code"]
    print(json.dumps({"ok": True, "code": 0, "bytes": list(res.get("data") or oaplib.OK)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
