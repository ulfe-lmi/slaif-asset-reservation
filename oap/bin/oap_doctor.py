#!/usr/bin/env python3
"""doctor.sh / oap_doctor.py — readiness in separate dimensions.

structural : inventory, modes, FIFOs, inactive state, no active order
setup      : tmux/codex availability, role homes, parseable runtime.env (activation may be off)
operational: activation enabled + attributable reference, qualified argv/models,
             accepted governance identity, merge side effects, no test adapters
adoption   : conversion adoption state (WO0014 reserved, human-merged)
Missing credentials never prevent the setup shells.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oaplib  # noqa: E402


def _cmd(bin_name):
    try:
        p = subprocess.run([bin_name, "--version"], capture_output=True, timeout=10)
        return (
            (p.stdout or p.stderr).decode("utf-8", "replace").splitlines()[0][:80]
            if (p.stdout or p.stderr)
            else "unavailable"
        )
    except Exception:
        return "unavailable"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--strategic-home", required=True)
    ap.add_argument(
        "--level", choices=("structural", "setup", "operational", "adoption", "all"), default="all"
    )
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
        "oap/COMPLETENESS.md",
        "oap/coding-instructions/AGENTS.md",
        "oap/strategic-instructions/AGENTS.md",
        "oap/governance/MANIFEST.json",
        "oap/governance/DISTILLATION-MAP.md",
        "oap/governance/CONTEXT-BUDGET.md",
        "oap/bootstrap-sources.lock.json",
    ]
    for rel in required_repo:
        if not (repo / rel).exists():
            struct["ok"] = False
            struct["problems"].append(f"missing repo file: {rel}")
    ptr = oaplib.read_pointer(repo / "oap" / "active")
    struct["pointer"] = ptr
    if ptr["state"] != "ABSENT":
        struct["ok"] = False
        struct["problems"].append(
            "active pointer present at structural check: {}".format(ptr["state"])
        )
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
            if not __import__("stat").S_ISFIFO(st.st_mode) or st.st_mode & 0o077:
                struct["ok"] = False
                struct["problems"].append(f"fifo {rel} wrong type/mode")
        elif rel == "runtime.env" and p.lstat().st_mode & 0o077:
            struct["ok"] = False
            struct["problems"].append("runtime.env must be mode 0600")
    out["gates"]["structural"] = struct
    # ---------------- setup
    setup = {"ok": True, "problems": [], "codex": _cmd("codex"), "tmux": _cmd("tmux")}
    if setup["codex"] == "unavailable":
        setup["ok"] = False
        setup["problems"].append("codex CLI not found")
    if setup["tmux"] == "unavailable":
        setup["ok"] = False
        setup["problems"].append("tmux not found")
    for rel in ("agent-homes/coding", "agent-homes/strategic"):
        p = home / rel
        if not p.is_dir():
            setup["ok"] = False
            setup["problems"].append(f"missing role home: {rel}")
        elif p.lstat().st_mode & 0o077:
            setup["problems"].append(f"role home {rel} should be 0700")
    envp = home / "runtime.env"
    if envp.exists():
        try:
            vals, env_errs = oaplib.parse_runtime_env(envp.read_text("utf-8"))
            setup["env_errors"] = env_errs
            if env_errs:
                setup["ok"] = False
                setup["problems"].extend(env_errs[:5])
            setup["activation_enabled"] = vals.get("OAP_ACTIVATION_ENABLED", False)
        except Exception as e:
            setup["ok"] = False
            setup["problems"].append(f"runtime.env unreadable: {e}")
    out["gates"]["setup"] = setup
    # ---------------- operational
    op = {"ok": False, "problems": []}
    if oaplib.remote_adapter_is_test_mode():
        op["problems"].append(
            "TEST remote adapter present; operational mode refuses fixture adapters"
        )
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
    if not vals.get("OAP_ACCEPTED_GOVERNANCE_REVISION"):
        op["problems"].append("no accepted governance revision")
    if not vals.get("OAP_TARGET_MILESTONE"):
        op["problems"].append("no target milestone selected")
    if ptr["state"] != "ABSENT":
        op["problems"].append("active order present; reconcile before a new operational session")
    op["ok"] = not op["problems"]
    out["gates"]["operational"] = op
    # ---------------- adoption
    a14 = repo / "docs" / "decisions" / "0014-concentrated-oap-workflow-conversion.md"
    adoption = {
        "ok": a14.exists(),
        "note": (
            "ADR 0014 present; adoption is the one-time human-governed WO0014 session; "
            "adoption PR remains human-merged; bootstrap never self-approves"
        )
        if a14.exists()
        else "ADR 0014 missing; conversion candidate incomplete",
    }
    out["gates"]["adoption"] = adoption
    out["result"] = (
        "PASS" if all(out["gates"][k]["ok"] for k in ("structural", "setup")) else "NEEDS ATTENTION"
    )
    if args.json:
        print(json.dumps(out, indent=1, default=str))
    else:
        for name in ("structural", "setup", "operational", "adoption"):
            if args.level not in ("all", name):
                continue
            g = out["gates"][name]
            print("[{}] {}".format(name, "OK" if g["ok"] else "BLOCKED"))
            for p in g.get("problems", []):
                print(f"   - {oaplib.redact(p)}")
    return 0 if out["gates"]["structural"]["ok"] and out["gates"]["setup"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
