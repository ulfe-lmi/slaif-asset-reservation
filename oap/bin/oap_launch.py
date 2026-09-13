#!/usr/bin/env python3
"""oap_launch.py — shared launcher logic for coding/strategic roles and tmux modes.

coding       : fresh per round; consumes control FIFO once; launches configured Codex argv
               with private CODEX_HOME; zero model calls while idle; explicit quit.
strategic    : long-lived role from STRATEGIC_HOME with full constitution.
setup-tmux   : isolated owned session, two side-by-side shells (strategy left, coding
               right); works with no model/auth/remote; activates nothing.
oap-tmux     : same topology but gated on doctor operational readiness first.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oaplib  # noqa: E402

CODING_PROMPT = (
    "ROLE=CODING. Follow the repository role router and the exact activated "
    "order under oap/active. Control wake-up was already consumed by the "
    "wrapper. You never merge."
)
STRATEGIC_PROMPT = (
    "ROLE=STRATEGIC. Retain your full strategic constitution during "
    "repository inspection. No active work exists until strategy publishes "
    "one; an absent oap/active pointer means inactive."
)


def _prompt(repo: Path, rel: str, fallback: str) -> str:
    """Tiny role prompt: prefer the versioned oap/prompts file, else the fallback."""
    p = Path(repo) / rel
    if p.is_file() and not p.is_symlink():
        text = p.read_text("utf-8", "replace").strip()
        if text and len(text) <= 2000:
            return text
    return fallback


def _fail(res, code=1):
    print(json.dumps({"ok": False, **res}, indent=1, default=str))
    return code


def _cfg(home: Path):
    envp = home / "runtime.env"
    if not envp.exists():
        return None, ["runtime.env missing"]
    vals, errs = oaplib.parse_runtime_env(envp.read_text("utf-8"))
    return vals, errs


def cmd_coding(args):
    repo, home = Path(args.repo), Path(args.strategic_home)
    role_env = os.environ.get("OAP_ROLE")
    if role_env and role_env != "CODING":
        return _fail(
            {
                "step": "role",
                "error": (
                    f"conflicting OAP_ROLE={role_env}; refusing to launch coding under another role"
                ),
            }
        )
    vals, errs = _cfg(home)
    if errs:
        return _fail({"step": "config", "error": "; ".join(errs[:3])})
    if args.print_only:
        argv = vals.get("OAP_CODING_ARGV_JSON") or []
        print(
            json.dumps(
                {
                    "print_only": True,
                    "role": "CODING",
                    "cwd": str(repo),
                    "codex_home": str(home / "agent-homes" / "coding"),
                    "env": {"OAP_ROLE": "CODING"},
                    "prompt": CODING_PROMPT,
                    "argv": argv or "UNCONFIGURED (operation blocked until qualified)",
                },
                indent=1,
            )
        )
        return 0
    problems = []
    if not vals.get("OAP_ACTIVATION_ENABLED"):
        problems.append("activation disabled")
    if not vals.get("OAP_AUTHORITY_REFERENCE"):
        problems.append("no attributable authority reference")
    if not vals.get("OAP_CODING_ARGV_JSON"):
        problems.append("OAP_CODING_ARGV_JSON not configured")
    if not vals.get("OAP_CODING_MODEL"):
        problems.append("coding model not qualified")
    if problems:
        return _fail(
            {"step": "prerequisites", "error": "operation blocked: " + "; ".join(problems)}, 1
        )
    lease_path = repo / "oap" / "leases" / "coding-wrapper.lease"
    lease_fd = oaplib.acquire_lease(lease_path, owner="coding-wrapper")
    if lease_fd is None:
        return _fail(
            {
                "step": "duplicate",
                "error": "another coding wrapper is already running; refusing duplicate consumer",
            },
            1,
        )
    stop = {"flag": False}

    def _term(signum, frame):
        stop["flag"] = True

    signal.signal(signal.SIGINT, _term)
    signal.signal(signal.SIGTERM, _term)
    consumer_owner = f"coding-wrapper-{os.getpid()}"
    # own the FIFO consumer lease for the whole process lifetime; fifo_receive
    # re-uses it (self-lease) and refuses any other live consumer
    oaplib.acquire_lease(home / "control.fifo.lease", owner=consumer_owner)
    journal = home / "workorders" / "state.json"
    launched = 0

    def _handle(state: dict):
        """Handle one wake-up (live signal or startup recovery).
        Returns 'skip', 'break', or ('fail', message)."""
        nonlocal launched
        oid = state["pointer"].get("id")
        if state["state"] in ("INACTIVE", "ACCEPTED_QUIESCENT") or not oid:
            return "skip"
        if state["state"] == "CORRUPT":
            return ("fail", "corrupt durable state preserved; refusing model invocation")
        # duplicate suppression: same objective already invoked without a new round
        jdata = {"events": []}
        if journal.exists():
            try:
                jdata = json.loads(journal.read_text())
            except ValueError:
                pass
        last = [
            e
            for e in jdata.get("events", [])
            if e.get("order_id") == oid and e.get("kind") == "invoked"
        ]
        report = repo / "oap" / "reports"
        done = (
            any(p.name.startswith(oid + "-") for p in report.glob("*.md"))
            if report.is_dir()
            else False
        )
        if (
            last
            and done
            and not any(
                e.get("kind") == "new_round"
                for e in jdata.get("events", [])
                if e.get("order_id") == oid and e["ts"] > last[-1]["ts"]
            )
        ):
            return "skip"  # duplicate wake-up: durable objective unchanged, suppress
        argv = vals["OAP_CODING_ARGV_JSON"]
        child_env = dict(os.environ)
        child_env["CODEX_HOME"] = str(home / "agent-homes" / "coding")
        child_env["OAP_ROLE"] = "CODING"
        oaplib.ensure_private_dir(str(home / "agent-homes" / "coding"))
        cmd = list(argv)
        if cmd and Path(cmd[0]).name in ("codex",):
            cmd = cmd + [CODING_PROMPT]
        else:
            cmd = cmd + [
                "--oap-prompt",
                _prompt(repo, "oap/prompts/coding-round.md", CODING_PROMPT),
            ]
        jdata.setdefault("events", []).append(
            {"ts": time.time(), "kind": "invoked", "order_id": oid}
        )
        oaplib.ensure_private_dir(str(journal.parent))
        oaplib.atomic_write(journal, json.dumps(jdata, indent=1).encode(), mode=0o600)
        p = subprocess.Popen(cmd, cwd=str(repo), env=child_env)
        launched += 1
        rc = p.wait()
        jdata = json.loads(journal.read_text())
        jdata.setdefault("events", []).append(
            {"ts": time.time(), "kind": "invocation_exited", "order_id": oid, "rc": rc}
        )
        oaplib.atomic_write(journal, json.dumps(jdata, indent=1).encode(), mode=0o600)
        return "break" if args.once else "skip"

    # startup recovery (OP-14): a wake-up already consumed but never reported
    # resumes the SAME objective without waiting for another signal
    pre = oaplib.classify_state(str(repo), str(home), None)
    if pre["state"] == "RUNNING_INTERRUPTED":
        r = _handle(pre)
        if isinstance(r, tuple):
            return _fail({"step": "state", "error": r[1]}, 1)
    try:
        while not stop["flag"]:
            # durable state first; the wake-up is consumed exactly once outside the model
            res = oaplib.fifo_receive(
                home / "control.fifo", timeout=0.5, lease_owner=consumer_owner
            )
            if stop["flag"]:
                break
            if not res["ok"] and res["code"] == 3:
                if args.once:
                    break
                continue
            if not res["ok"]:
                return _fail({"step": "fifo", "error": res["error"]})
            state = oaplib.classify_state(str(repo), str(home), None)
            oid = state["pointer"].get("id")
            if oid:
                # durable consumption evidence BEFORE any model invocation
                oaplib.ensure_private_dir(str(journal.parent))
                jdata = {"events": []}
                if journal.exists():
                    try:
                        jdata = json.loads(journal.read_text())
                    except ValueError:
                        jdata = {"events": []}
                jdata.setdefault("events", []).append(
                    {"ts": time.time(), "kind": "control_consumed", "order_id": oid}
                )
                oaplib.atomic_write(journal, json.dumps(jdata, indent=1).encode(), mode=0o600)
            r = _handle(state)
            if isinstance(r, tuple):
                return _fail({"step": "state", "error": r[1]}, 1)
            if r == "break":
                break
    finally:
        oaplib.release_lease(lease_path, lease_fd)
        oaplib.release_lease(home / "control.fifo.lease")
    print(
        json.dumps(
            {
                "ok": True,
                "role": "CODING",
                "invocations": launched,
                "note": "explicit quit: no automatic resurrection" if stop["flag"] else "finished",
            },
            indent=1,
        )
    )
    return 0


def cmd_strategic(args):
    repo, home = Path(args.repo), Path(args.strategic_home)
    role_env = os.environ.get("OAP_ROLE")
    if role_env and role_env != "STRATEGIC":
        return _fail({"step": "role", "error": f"conflicting OAP_ROLE={role_env}; refusing"})
    vals, errs = _cfg(home)
    if errs:
        return _fail({"step": "config", "error": "; ".join(errs[:3])})
    if args.print_only:
        argv = vals.get("OAP_STRATEGIC_ARGV_JSON") or []
        print(
            json.dumps(
                {
                    "print_only": True,
                    "role": "STRATEGIC",
                    "cwd": str(home),
                    "codex_home": str(home / "agent-homes" / "strategic"),
                    "env": {"OAP_ROLE": "STRATEGIC"},
                    "prompt": STRATEGIC_PROMPT,
                    "argv": argv or "UNCONFIGURED (operation blocked until qualified)",
                },
                indent=1,
            )
        )
        return 0
    problems = []
    if not vals.get("OAP_ACTIVATION_ENABLED"):
        problems.append("activation disabled")
    if not vals.get("OAP_AUTHORITY_REFERENCE"):
        problems.append("no attributable authority reference")
    if not vals.get("OAP_STRATEGIC_ARGV_JSON"):
        problems.append("OAP_STRATEGIC_ARGV_JSON not configured")
    if not vals.get("OAP_STRATEGIC_MODEL"):
        problems.append("strategic model not qualified")
    if problems:
        return _fail(
            {"step": "prerequisites", "error": "operation blocked: " + "; ".join(problems)}, 1
        )
    lease_path = home / "workorders" / "strategic-wrapper.lease"
    lease_fd = oaplib.acquire_lease(lease_path, owner="strategic-wrapper")
    if lease_fd is None:
        return _fail({"step": "duplicate", "error": "strategic wrapper already running"}, 1)
    stop = {"flag": False}

    def _term(signum, frame):
        stop["flag"] = True

    signal.signal(signal.SIGINT, _term)
    signal.signal(signal.SIGTERM, _term)
    argv = vals["OAP_STRATEGIC_ARGV_JSON"]
    child_env = dict(os.environ)
    child_env["CODEX_HOME"] = str(home / "agent-homes" / "strategic")
    child_env["OAP_ROLE"] = "STRATEGIC"
    oaplib.ensure_private_dir(str(home / "agent-homes" / "strategic"))
    cmd = list(argv)
    if cmd and Path(cmd[0]).name == "codex":
        cmd = cmd + [STRATEGIC_PROMPT]
    else:
        cmd = cmd + [
            "--oap-prompt",
            _prompt(repo, "oap/prompts/strategic-start.md", STRATEGIC_PROMPT),
        ]
    try:
        p = subprocess.Popen(cmd, cwd=str(home), env=child_env)
        rc = p.wait()
    finally:
        oaplib.release_lease(lease_path, lease_fd)
    print(
        json.dumps(
            {
                "ok": True,
                "role": "STRATEGIC",
                "rc": rc,
                "note": "logical continuity persists; handoff in workorders/STRATEGIC-HANDOFF.md",
            },
            indent=1,
        )
    )
    return rc if stop["flag"] else 0


def _tmux_argv(socket, session, left_cmd, right_cmd, left_cwd, right_cwd):
    base = ["tmux", "-L", socket]
    return base, session, left_cmd, right_cmd, left_cwd, right_cwd


def cmd_setup_tmux(args):
    repo, home = Path(args.repo), Path(args.strategic_home)
    for d in (repo, home):
        if not d.is_dir():
            return _fail({"step": "roots", "error": f"missing root {d}"})
    socket = args.socket or f"oap-setup-{os.getpid()}"
    session = "oap-setup"
    base = ["tmux", "-L", socket]
    if args.print_only:
        print(
            json.dumps(
                {
                    "print_only": True,
                    "mode": "setup",
                    "socket": socket,
                    "session": session,
                    "left": {"cwd": str(home), "pane": "strategy"},
                    "right": {"cwd": str(repo), "pane": "coding"},
                    "commands": [
                        base
                        + [
                            "new-session",
                            "-d",
                            "-s",
                            session,
                            "-x",
                            "200",
                            "-y",
                            "50",
                            "-c",
                            str(home),
                            "bash",
                        ],
                        base
                        + ["split-window", "-h", "-t", session + ":0", "-c", str(repo), "bash"],
                    ],
                    "note": (
                        "shells only; no operational agents, active order or signal; "
                        "works without model/auth/remote"
                    ),
                },
                indent=1,
            )
        )
        return 0
    rc, out, err = oaplib.run_tmux(base, ["has-session", "-t", session])
    if rc == 0:
        return _fail(
            {
                "step": "session",
                "error": f"session {session} already exists on owned socket; refusing to repurpose",
            },
            1,
        )
    rc, out, err = oaplib.run_tmux(
        base, ["new-session", "-d", "-s", session, "-x", "200", "-y", "50", "-c", str(home), "bash"]
    )
    if rc != 0:
        return _fail({"step": "session", "error": err.strip()[:200]}, 1)
    rc, out, err = oaplib.run_tmux(
        base, ["split-window", "-h", "-t", session + ":0", "-c", str(repo), "bash"]
    )
    if rc != 0:
        oaplib.run_tmux(base, ["kill-session", "-t", session])
        return _fail({"step": "split", "error": err.strip()[:200]}, 1)
    print(
        json.dumps(
            {
                "ok": True,
                "mode": "setup",
                "socket": socket,
                "session": session,
                "left_cwd": str(home),
                "right_cwd": str(repo),
                "note": "login/configure each role independently; nothing is activated",
            },
            indent=1,
        )
    )
    return 0


def cmd_oap_tmux(args):
    # gate: run doctor operational first
    drc = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve().parent / "oap_doctor.py"),
            "--repo",
            str(args.repo),
            "--strategic-home",
            str(args.strategic_home),
            "--level",
            "operational",
            "--json",
        ],
        capture_output=True,
    )
    try:
        doc = json.loads(drc.stdout.decode())
    except ValueError:
        doc = {"gates": {"operational": {"ok": False, "problems": ["doctor unreadable"]}}}
    op = doc.get("gates", {}).get("operational", {"ok": False, "problems": ["missing"]})
    if not op.get("ok"):
        return _fail(
            {
                "step": "gates",
                "error": "operational prerequisites not met: "
                + "; ".join(op.get("problems", [])[:6]),
                "note": "setup mode (launch-setup-tmux.sh) remains available",
            },
            1,
        )
    if args.print_only:
        print(
            json.dumps(
                {
                    "print_only": True,
                    "mode": "oap",
                    "gates": "pass",
                    "note": "would start role wrappers in two side-by-side panes",
                },
                indent=1,
            )
        )
        return 0
    return _fail(
        {
            "step": "unsupported",
            "error": (
                "operational tmux launch requires the wrapper binaries in a qualified environment"
            ),
        },
        1,
    )


def run_tmux_argv(base, extra):
    return oaplib.run_tmux(base, extra)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("coding", "strategic"):
        p = sub.add_parser(name)
        p.add_argument("--repo", required=True)
        p.add_argument("--strategic-home", required=True)
        p.add_argument("--print-only", action="store_true")
        if name == "coding":
            p.add_argument("--once", action="store_true")
    for name in ("setup-tmux", "oap-tmux"):
        p = sub.add_parser(name)
        p.add_argument("--repo", required=True)
        p.add_argument("--strategic-home", required=True)
        p.add_argument("--print-only", action="store_true")
        if name == "setup-tmux":
            p.add_argument("--socket", default=None)
    args = ap.parse_args(argv)
    if args.cmd == "coding":
        return cmd_coding(args)
    if args.cmd == "strategic":
        return cmd_strategic(args)
    if args.cmd == "setup-tmux":
        return cmd_setup_tmux(args)
    return cmd_oap_tmux(args)


if __name__ == "__main__":
    raise SystemExit(main())
