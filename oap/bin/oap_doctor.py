#!/usr/bin/env python3
"""doctor.sh / oap_doctor.py — readiness in separate dimensions (slim, 015-a).

structural : inventory, modes, FIFOs, pointer sanity, no foreign/conflicting state
operational: activation enabled + attributable reference, qualified argv/models,
             target milestone, no test adapters, merge side effects (delegation must
             stay disabled while not evidenced), qualified audit model
The governance-identity, setup and adoption dimensions were removed in 015-a.
"""

from __future__ import annotations

import argparse
import json
import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oaplib  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=oaplib.argument_path, required=True)
    ap.add_argument("--strategic-home", type=oaplib.argument_path, required=True)
    ap.add_argument("--level", choices=("structural", "operational", "all"), default="all")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    repo = Path(args.repo)
    home = Path(args.strategic_home)
    out = {
        "repo": oaplib.canonical(str(repo)),
        "strategic_home": oaplib.canonical(str(home)),
        "gates": {},
    }
    # ---------------- structural
    struct = {"ok": True, "problems": []}
    required_repo = [
        "AGENTS.md",
        "oap/README.md",
        "oap/RECOVERY.md",
        "oap/coding-instructions/AGENTS.md",
        "oap/strategic-instructions/AGENTS.md",
    ]
    for rel in required_repo:
        if not (repo / rel).exists():
            struct["ok"] = False
            struct["problems"].append(f"missing repo file: {rel}")
    ptr = oaplib.read_pointer(repo / "oap" / "active")
    struct["pointer"] = ptr
    if ptr["state"] == "CORRUPT":
        struct["ok"] = False
        struct["problems"].append("pointer sanity failed: {}".format(ptr["error"]))
    elif ptr["state"] == "ACTIVE":
        orders = (
            [p.name for p in (repo / "oap" / "orders").glob(ptr["id"] + "-*.md")]
            if (repo / "oap" / "orders").is_dir()
            else []
        )
        if len(orders) != 1:
            struct["ok"] = False
            struct["problems"].append(f"active pointer names {len(orders)} orders (need exactly 1)")
    orders = (
        [p.name for p in (repo / "oap" / "orders").glob("*.md")]
        if (repo / "oap" / "orders").is_dir()
        else []
    )
    reports = (
        [p.name for p in (repo / "oap" / "reports").glob("*.md")]
        if (repo / "oap" / "reports").is_dir()
        else []
    )
    struct["orders"] = orders
    struct["reports"] = reports
    # reports must bind a published order (no fabricated execution state)
    for rname in reports:
        if not any(o == rname for o in orders):
            struct["ok"] = False
            struct["problems"].append(f"report without matching order: {rname}")
    reg = repo / "CRITICAL.md"
    if reg.exists():
        entries, errs = oaplib.parse_register(reg.read_bytes())
        struct["critical_entries"] = [e["id"] for e in entries]
        struct["critical_errors"] = errs
        if errs:
            struct["ok"] = False
    for rel, _need in (("control.fifo", True), ("response.fifo", True), ("runtime.env", True)):
        p = home / rel
        if not p.exists():
            struct["ok"] = False
            struct["problems"].append(f"missing strategic home file: {rel}")
        elif rel.endswith(".fifo"):
            st = p.lstat()
            if not stat.S_ISFIFO(st.st_mode) or st.st_mode & 0o077:
                struct["ok"] = False
                struct["problems"].append(f"fifo {rel} wrong type/mode")
        elif rel == "runtime.env" and p.lstat().st_mode & 0o077:
            struct["ok"] = False
            struct["problems"].append("runtime.env must be mode 0600")
    out["gates"]["structural"] = struct
    # ---------------- operational
    op = {"ok": False, "problems": []}
    if oaplib.remote_adapter_is_test_mode():
        op["problems"].append(
            "TEST remote adapter present; operational mode refuses fixture adapters"
        )
    envp = home / "runtime.env"
    vals, env_errs = (
        oaplib.parse_runtime_env(envp.read_text("utf-8"))
        if envp.exists()
        else ({}, ["runtime.env missing"])
    )
    if env_errs:
        op["problems"].extend(env_errs[:5])
    if not vals.get("OAP_ACTIVATION_ENABLED"):
        op["problems"].append("OAP_ACTIVATION_ENABLED is not true")
    if not vals.get("OAP_AUTHORITY_REFERENCE"):
        op["problems"].append("no attributable authority reference recorded")
    for k in ("OAP_CODING_ARGV_JSON", "OAP_STRATEGIC_ARGV_JSON"):
        if not vals.get(k):
            op["problems"].append(f"{k} not configured")
    for k in ("OAP_CODING_MODEL", "OAP_STRATEGIC_MODEL"):
        if not vals.get(k):
            op["problems"].append(f"{k} not qualified")
    if not vals.get("OAP_AUDIT_MODEL"):
        op["problems"].append("OAP_AUDIT_MODEL not qualified; ICA audit model unqualified")
    if not vals.get("OAP_TARGET_MILESTONE"):
        op["problems"].append("no target milestone selected")
    if vals.get("OAP_DEVELOPMENT_MERGE_ENABLED"):
        op["problems"].append(
            "OAP_DEVELOPMENT_MERGE_ENABLED is true but merge side effects are not "
            "evidenced; development-merge delegation must stay disabled"
        )
    if ptr["state"] != "ABSENT":
        op["problems"].append("active order present; reconcile before a new operational session")
    op["ok"] = not op["problems"]
    out["gates"]["operational"] = op
    out["result"] = "PASS" if out["gates"]["structural"]["ok"] and op["ok"] else "NEEDS ATTENTION"
    if args.json:
        print(json.dumps(out, indent=1, default=str))
    else:
        for name in ("structural", "operational"):
            if args.level not in ("all", name):
                continue
            g = out["gates"][name]
            print("[{}] {}".format(name, "OK" if g["ok"] else "BLOCKED"))
            for p in g.get("problems", []):
                print(f"   - {oaplib.redact(p)}")
    return 0 if out["gates"]["structural"]["ok"] and op["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
