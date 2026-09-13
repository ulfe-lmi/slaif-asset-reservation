#!/usr/bin/env python3
"""publish_order.py — OP-03/OP-04 two recoverable publication writes.

Validates the FINAL order fully before any write; dry-run performs ZERO writes.
Real publication: private publication lock -> order file (fsync file+dir) -> journal ->
pointer (atomic, ID+LF, fsync dir) -> journal -> control FIFO OK (bounded timeout).
Signal failure => PUBLISHED_NOT_SIGNALED (order+pointer remain durable).
Only the STRATEGIC role may publish; activation must be enabled with an attributable
reference; a test-mode remote adapter is explicit (never default).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oaplib  # noqa: E402

EXIT_SIGNAL_LOST = 2


def _journal(home: Path, event: dict):
    j = home / "workorders" / "state.json"
    oaplib.ensure_private_dir(str(j.parent))
    data = {"events": []}
    if j.exists():
        try:
            data = json.loads(j.read_text())
        except ValueError:
            raise oaplib.ConflictError("private journal unparseable; reconcile manually") from None
    data.setdefault("events", []).append({"ts": time.time(), **event})
    oaplib.atomic_write(j, json.dumps(data, indent=1).encode(), mode=0o600)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--strategic-home", required=True)
    ap.add_argument("--order", required=True, help="path to the order file (draft or final)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--recover", action="store_true")
    ap.add_argument("--signal-timeout", type=float, default=15.0)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    repo = Path(args.repo)
    home = Path(args.strategic_home)
    res = {"ok": False, "status": None, "steps": [], "role": os.environ.get("OAP_ROLE")}

    def step(name, ok, detail=""):
        res["steps"].append({"step": name, "ok": ok, "detail": oaplib.redact(detail)})
        if not ok:
            res["status"] = "FAILED_VALIDATION" if res["status"] is None else res["status"]

    # role guard
    if os.environ.get("OAP_ROLE") != "STRATEGIC":
        res["status"] = "REFUSED_ROLE"
        step(
            "role",
            False,
            "OAP_ROLE must be STRATEGIC (got {!r})".format(os.environ.get("OAP_ROLE")),
        )
        _out(res, args.json)
        return 1
    step("role", True)
    # activation guard (config is data, not authority)
    envp = home / "runtime.env"
    vals, env_errs = (
        oaplib.parse_runtime_env(envp.read_text("utf-8"))
        if envp.exists()
        else ({}, ["runtime.env missing"])
    )
    if env_errs:
        res["status"] = "REFUSED_CONFIG"
        step("config", False, "; ".join(env_errs[:3]))
        _out(res, args.json)
        return 1
    step("config", True)
    if not vals.get("OAP_ACTIVATION_ENABLED"):
        res["status"] = "BLOCKED_INACTIVE"
        step("activation", False, "OAP_ACTIVATION_ENABLED is false; bootstrap stays inactive")
        _out(res, args.json)
        return 1
    if not vals.get("OAP_AUTHORITY_REFERENCE"):
        res["status"] = "BLOCKED_AUTHORITY"
        step("authority", False, "no attributable authority reference")
        _out(res, args.json)
        return 1
    step("activation", True)
    step("authority", True)
    # order validation
    opath = Path(args.order)
    if not opath.is_file():
        res["status"] = "FAILED_VALIDATION"
        step("order_file", False, "missing")
        _out(res, args.json)
        return 1
    data = opath.read_bytes()
    meta, body, errs = oaplib.parse_order(data, strict_final=True)
    if errs:
        res["status"] = "FAILED_VALIDATION"
        step("order_schema", False, "; ".join(errs[:5]))
        _out(res, args.json)
        return 1
    step("order_schema", True, "id={}".format(meta["id"]))
    if (
        meta.get("repo") != vals.get("OAP_REMOTE_REPOSITORY")
        and meta.get("repo") != "ulfe-lmi/slaif-asset-reservation"
    ):
        step(
            "order_repo",
            False,
            "order repo {!r} does not match configured remote".format(meta.get("repo")),
        )
        _out(res, args.json)
        return 1
    step("order_repo", True)
    oid = meta["id"]
    slug = meta["slug"]
    orders_dir = repo / "oap" / "orders"
    dest = orders_dir / (f"{oid}-{slug}.md")
    journal = home / "workorders" / "state.json"
    jdata = {"events": []}
    if journal.exists():
        try:
            jdata = json.loads(journal.read_text())
        except ValueError:
            jdata = {"events": []}
    events = jdata.get("events", [])
    # current active expectation
    ptr = oaplib.read_pointer(repo / "oap" / "active")
    if ptr["state"] == "CORRUPT":
        res["status"] = "REFUSED_CORRUPT_POINTER"
        step("pointer_state", False, ptr["error"])
        _out(res, args.json)
        return 1
    step("pointer_state", True, ptr["state"])
    # remote reconciliation (read-only; fixture adapter explicit)
    adapter = oaplib.load_remote_adapter(str(repo))
    rhead = adapter.remote_head(str(repo), "refs/heads/" + meta["base_branch"])
    if not rhead.get("ok"):
        step(
            "remote_reconcile",
            False,
            "remote base head unavailable: {} (BLOCKED, not a local pass)".format(
                rhead.get("error")
            ),
        )
        _out(res, args.json)
        return 1
    step("remote_reconcile", True, "remote {}={}".format(meta["base_branch"], rhead["head"]))
    # PR identity
    if meta["pr_number"] is None:
        existing = adapter.pr_for_branch(str(repo), meta["branch"])
        if existing:
            if existing.get("merged") or existing.get("state") == "merged":
                step(
                    "pr_identity",
                    False,
                    (
                        "branch {} already belongs to MERGED historical PR {}; a new objective "
                        "needs a new branch, historical PRs are never reused".format(
                            meta["branch"], existing.get("number")
                        )
                    ),
                )
                _out(res, args.json)
                return 1
            step(
                "pr_identity",
                False,
                "round a but branch already has open PR {}; order must bind it "
                "(REUSE, not new)".format(existing.get("number")),
            )
            _out(res, args.json)
            return 1
        step("pr_identity", True, "no PR yet for branch (CREATE_OR_RESUME)")
    else:
        pr = adapter.pr(str(repo), meta["pr_number"])
        if not pr:
            step("pr_identity", False, "PR {} not found".format(meta["pr_number"]))
            _out(res, args.json)
            return 1
        if pr.get("branch") != meta["branch"]:
            step("pr_identity", False, "PR branch mismatch")
            _out(res, args.json)
            return 1
        if meta["round"] == "a" and (pr.get("merged") or pr.get("state") == "merged"):
            step(
                "pr_identity",
                False,
                "round a cannot bind merged historical PR {}".format(meta["pr_number"]),
            )
            _out(res, args.json)
            return 1
        step("pr_identity", True, "PR {} bound".format(meta["pr_number"]))
    # recovery semantics
    last_events = [e for e in events if e.get("order_id") == oid]
    if dest.exists():
        cur = dest.read_bytes()
        if cur == data:
            jpending = [
                e for e in last_events if e.get("kind") == "order_written" and not e.get("signaled")
            ]
            if not jpending:
                step(
                    "existing",
                    False,
                    "order already fully published; historical order cannot be reactivated",
                )
                res["status"] = "REFUSED_ALREADY_PUBLISHED"
                _out(res, args.json)
                return 1
            if ptr["id"] == oid:
                step("signal_retry", False, "retried by the wrapper")
                step(
                    "existing",
                    False,
                    "pointer already set; signal may be retried by wrapper, not re-published",
                )
                res["status"] = "REFUSED_ALREADY_PUBLISHED"
                _out(res, args.json)
                return 1
            if not args.recover:
                step("existing", False, "unresolved publication exists; use --recover")
                res["status"] = "REFUSED_USE_RECOVER"
                _out(res, args.json)
                return 1
            step("recover", True, "completing identical unresolved publication")
        else:
            step("existing", False, "order path occupied by different bytes; replacement forbidden")
            res["status"] = "REFUSED_MISMATCH"
            _out(res, args.json)
            return 1
    # transition legality
    obj, rnd = oaplib.split_id(oid)
    if rnd == "a" and meta["previous_round"] is not None:
        step("transition", False, "round a must not have previous_round")
        _out(res, args.json)
        return 1
    if rnd != "a":
        prev = meta["previous_round"]
        pobj, prnd = oaplib.split_id(prev or "")
        if pobj != obj or prnd != oaplib.prev_round(rnd):
            step(
                "transition",
                False,
                "previous_round must be the immediately preceding round of the same objective",
            )
            _out(res, args.json)
            return 1
    step("transition", True)
    if args.dry_run:
        res["ok"] = True
        res["status"] = "DRY_RUN_VALID"
        step("dry_run", True, "zero writes performed")
        _out(res, args.json)
        return 0
    # ---- real publication (writes) ----
    lock_fd = oaplib.acquire_lease(repo / "oap" / "leases" / "publication.lease", owner="publisher")
    if lock_fd is None:
        res["status"] = "REFUSED_LOCK_HELD"
        step("lock", False, "another publisher holds the publication lock")
        _out(res, args.json)
        return 1
    step("lock", True)
    try:
        oaplib.ensure_dir(str(orders_dir))
        oaplib.atomic_write(dest, data, mode=0o644, expect_absent=True)
        _journal(
            home,
            {
                "kind": "order_written",
                "order_id": oid,
                "path": str(dest),
                "sha256": oaplib.sha256_hex(data),
            },
        )
        step("order_file", True, "written+fsynced")
        if ptr["id"] is not None and ptr["id"] != oid:
            step(
                "pointer",
                False,
                "active pointer names {}; concurrent objective must quiesce first".format(
                    ptr["id"]
                ),
            )
            res["status"] = "FAILED_POINTER_CONFLICT"
            _out(res, args.json)
            return 1
        oaplib.write_pointer_atomic(repo / "oap" / "active", oid)
        step("pointer", True, f"active={oid}+LF")
        signaled = False
        try:
            sres = oaplib.fifo_send(home / "control.fifo", timeout=args.signal_timeout)
            signaled = sres.get("ok", False)
        except Exception as e:
            sres = {"ok": False, "error": str(e)}
        if signaled:
            _journal(home, {"kind": "signaled", "order_id": oid})
            step("signal", True)
            res["ok"] = True
            res["status"] = "PUBLISHED"
        else:
            _journal(
                home,
                {
                    "kind": "published_not_signaled",
                    "order_id": oid,
                    "detail": sres.get("error", "signal failed"),
                },
            )
            step("signal", False, sres.get("error", "signal failed"))
            res["status"] = "PUBLISHED_NOT_SIGNALED"
            res["ok"] = False
            _out(res, args.json)
            return EXIT_SIGNAL_LOST
        _out(res, args.json)
        return 0
    finally:
        oaplib.release_lease(repo / "oap" / "leases" / "publication.lease", lock_fd)


def _out(res, as_json):
    if as_json:
        print(json.dumps(res, indent=1, default=str))
    else:
        print("status={}".format(res["status"]))
        for s in res["steps"]:
            print("  [{}] {} {}".format("ok" if s["ok"] else "FAIL", s["step"], s["detail"]))


if __name__ == "__main__":
    raise SystemExit(main())
