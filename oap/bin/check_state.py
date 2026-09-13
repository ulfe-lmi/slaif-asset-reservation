#!/usr/bin/env python3
"""check_state.py — pointer/order/report/PR/remote/recovery state. Read-only.

--check-human-gates CRIT-0001[,CRIT-0002,...] evaluates latest attributable
dispositions (structural only; provenance verifier injectable for tests).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oaplib  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--strategic-home", default=None)
    ap.add_argument("--check-human-gates", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    repo = Path(args.repo)
    adapter = oaplib.load_remote_adapter(str(repo))
    state = oaplib.classify_state(str(repo), args.strategic_home, adapter)
    out = {
        "repo": str(repo),
        "state": state["state"],
        "detail": state["detail"],
        "pointer": state["pointer"],
        "test_mode_adapter": oaplib.remote_adapter_is_test_mode(),
    }
    if state.get("order"):
        o = state["order"]
        out["order"] = {
            "id": o["id"],
            "path": o["path"],
            "round": o["meta"]["round"],
            "pr_mode": o["meta"]["pr_mode"],
            "pr_number": o["meta"]["pr_number"],
            "branch": o["meta"]["branch"],
            "state": o["meta"]["state"],
        }
        if state["state"] in ("ACTIVE_PENDING", "RUNNING_INTERRUPTED", "REPORT_LOCAL"):
            pr = None
            if o["meta"].get("pr_number") is not None:
                pr = adapter.pr(str(repo), o["meta"]["pr_number"])
            out["remote"] = {
                "pr": pr,
                "note": "fixture adapter evidence; operational API unconfigured returns PENDING",
            }
    if args.check_human_gates:
        reg = repo / "CRITICAL.md"
        data = reg.read_bytes() if reg.exists() else b""
        verifier = None
        envf = os.environ.get("OAP_HUMAN_VERIFIER_FILE")
        if envf:
            vinfo = json.loads(Path(envf).read_text())

            def verifier(crit, disp):
                return crit in (vinfo.get("verified") or {}) and (
                    vinfo["verified"][crit] == "fixture"
                )

        gates = []
        for cid in [c.strip() for c in args.check_human_gates.split(",") if c.strip()]:
            gates.append(oaplib.gate_state(cid, data, verifier))
        out["human_gates"] = gates
    if args.json:
        print(json.dumps(out, indent=1, default=str))
    else:
        print("state={} detail={}".format(out["state"], out["detail"]))
        if "order" in out:
            o = out["order"]
            print(
                "order={} round={} pr={} branch={}".format(
                    o["id"], o["round"], o["pr_number"], o["branch"]
                )
            )
        for g in out.get("human_gates", []):
            print("gate {}: {} ({})".format(g["crit"], g["status"], g["detail"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
