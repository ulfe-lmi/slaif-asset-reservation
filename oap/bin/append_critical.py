#!/usr/bin/env python3
"""append_critical.py — OP-12 exact locked register append.

admission: only the next monotonic CRIT ID, complete entry, all-five attestation,
strategy-authorized exact bytes with matching declared digest and trusted prior
register prefix. evidence: separate exact ordered bytes headed EVIDENCE APPEND.
Refuses HUMAN ADJUDICATION content. Retries are NO_OP when the exact payload already
exists at the authorized position. Atomic replace preserves all prior bytes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oaplib  # noqa: E402

REQUIRED_ENTRY_HEADINGS = [
    "### Dilemma",
    "### Decision taken",
    "### Reasoning",
    "### Alternatives considered",
    "### Strongest argument that this decision is wrong",
    "### Assumptions",
    "### Failure mode and blast radius",
    "### Mitigations and evidence",
    "### Reversibility and rollback",
    "### Safe autonomous continuation",
    "### Exact human gate",
    "### Exact question for the human adjudicator",
    "### Strategic attestation",
    "### Human disposition",
    "### Resolution",
]


def validate_entry(payload: bytes, kind: str, expected_id: str = None):
    errs = []
    text = payload.decode("utf-8", "replace")
    if not text.startswith("## CRIT-") and kind == "admission":
        errs.append("payload must start with a CRIT entry heading")
    if kind == "admission":
        m = re.match(r"## (CRIT-[0-9]{4}) — \S", text)
        if not m:
            errs.append("entry heading malformed")
        else:
            if expected_id and m.group(1) != expected_id:
                errs.append(f"entry ID {m.group(1)} is not the expected next ID {expected_id}")
        if "ALL FIVE CRITICAL-ENTRY CONDITIONS SATISFIED" not in text:
            errs.append("missing all-five attestation")
        if "Introduced by:**" not in text:
            errs.append("missing 'Introduced by' (actual PR and objective)")
        else:
            ib = re.search(r"Introduced by:\*\*\s*(.+)", text)
            if ib and ("TBD" in ib.group(1) or "TODO" in ib.group(1) or "<actual" in ib.group(1)):
                errs.append("placeholder in 'Introduced by'")
        for h in REQUIRED_ENTRY_HEADINGS:
            if h not in text:
                errs.append(f"missing heading: {h}")
        if re.search(r"(?m)^- \*\*Status:\*\* OPEN", text) is None:
            errs.append("status line missing or not OPEN")
        for bad in ("<actual PR", "TBD", "TODO", "FIXME"):
            if bad in text:
                errs.append(f"placeholder present: {bad}")
    if "HUMAN ADJUDICATION" in text and kind == "admission":
        errs.append("admission payload must not contain HUMAN ADJUDICATION content")
    if kind == "evidence" and not re.match(
        r"## EVIDENCE APPEND — CRIT-[0-9]{4} — [0-9a-f-]{36}\s*$",
        text.splitlines()[0] if text.splitlines() else "",
        re.M,
    ):
        errs.append("evidence payload must use the EVIDENCE APPEND heading")
    if kind == "evidence" and "HUMAN ADJUDICATION" in text:
        errs.append("evidence append must not contain HUMAN ADJUDICATION content")
    return errs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=oaplib.argument_path, required=True)
    ap.add_argument("--order", type=oaplib.argument_path, required=True)
    ap.add_argument("--kind", choices=("admission", "evidence"), default="admission")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    repo = Path(args.repo)
    res = {"ok": False, "status": None, "steps": []}

    def step(name, ok, detail=""):
        res["steps"].append({"step": name, "ok": ok, "detail": oaplib.redact(detail)})

    role = __import__("os").environ.get("OAP_ROLE")
    if role not in ("CODING", "STRATEGIC"):
        res["status"] = "REFUSED_ROLE"
        step(
            "role",
            False,
            f"OAP_ROLE must be CODING (append) or STRATEGIC (authoring); got {role!r}",
        )
        _out(res, args.json)
        return 1
    step("role", True, role)
    opath = Path(args.order)
    if not opath.is_file():
        res["status"] = "FAILED_VALIDATION"
        step("order", False, "missing")
        _out(res, args.json)
        return 1
    meta, body, errs = oaplib.parse_order(opath.read_bytes(), strict_final=True)
    if errs:
        res["status"] = "FAILED_VALIDATION"
        step("order_schema", False, "; ".join(errs[:4]))
        _out(res, args.json)
        return 1
    step("order_schema", True, meta["id"])
    dha = oaplib.extract_dha(body)
    if dha["error"]:
        res["status"] = "FAILED_VALIDATION"
        step("dha", False, dha["error"])
        _out(res, args.json)
        return 1
    if args.kind == "admission" and (
        not dha["decision"].startswith("APPEND") or dha["payload"] is None
    ):
        res["status"] = "REFUSED_NO_APPEND"
        step("dha", False, "order does not declare an APPEND with exact payload")
        _out(res, args.json)
        return 1
    reg = repo / "CRITICAL.md"
    prior = reg.read_bytes() if reg.exists() else b""
    entries, rerrs = oaplib.parse_register(prior)
    if rerrs:
        res["status"] = "REFUSED_REGISTER"
        step("register", False, "; ".join(rerrs[:3]))
        _out(res, args.json)
        return 1
    step("register", True, f"{len(entries)} live entries")
    if args.kind == "admission":
        declared = dha["decision"].split(":", 1)[1]
        payload = dha["payload"]
        expected_id = oaplib.next_crit_id(prior)
    else:
        # evidence payload: fenced block in body under '## Exact CRITICAL payload'
        declared = None
        expected_id = None
        m = re.search(r"## Exact CRITICAL payload\s*\n```text\s*\n(.*?)\n```", body, re.S)
        if not m:
            res["status"] = "FAILED_VALIDATION"
            step("payload", False, "no fenced evidence payload")
            _out(res, args.json)
            return 1
        payload = (m.group(1) + "\n").encode("utf-8")
    # idempotent retry: the exact payload is already the trailing live entry
    if oaplib.payload_at(prior, payload):
        verrs = validate_entry(payload, args.kind, declared)
        if verrs:
            res["status"] = "FAILED_ENTRY"
            step("retry", False, "trailing entry does not validate: " + "; ".join(verrs[:3]))
            _out(res, args.json)
            return 1
        res["ok"] = True
        res["status"] = "NO_OP"
        step("retry", True, "exact payload already present at authorized position")
        _out(res, args.json)
        return 0
    if args.kind == "admission":
        if expected_id and declared != expected_id:
            res["status"] = "REFUSED_ID"
            step(
                "id",
                False,
                f"order declares {declared} but next monotonic ID is {expected_id}",
            )
            _out(res, args.json)
            return 1
        step("id", True, expected_id)
    verrs = validate_entry(payload, args.kind, expected_id)
    if verrs:
        res["status"] = "FAILED_ENTRY"
        step("entry", False, "; ".join(verrs[:4]))
        _out(res, args.json)
        return 1
    step("entry", True)
    new = prior + payload
    if args.dry_run:
        res["ok"] = True
        res["status"] = "DRY_RUN_VALID"
        step("dry_run", True, f"zero writes; new register would be {len(new)} bytes")
        _out(res, args.json)
        return 0
    lock_fd = oaplib.acquire_lease(
        repo / "oap" / "leases" / "critical.lease", owner="append_critical"
    )
    if lock_fd is None:
        res["status"] = "REFUSED_LOCK_HELD"
        step("lock", False, "concurrent append holds the register lock")
        _out(res, args.json)
        return 1
    step("lock", True)
    try:
        prior2 = reg.read_bytes() if reg.exists() else b""
        if prior2 != prior:
            res["status"] = "REFUSED_STALE_PREFIX"
            step("prefix", False, "register changed under us; trusted prior prefix broken")
            _out(res, args.json)
            return 1
        step("prefix", True, f"prior bytes preserved ({len(prior2)})")
        oaplib.atomic_write(reg, new, mode=0o644, expect=prior)
        step("append", True, "atomic replace done")
        res["ok"] = True
        res["status"] = "APPENDED"
    finally:
        oaplib.release_lease(repo / "oap" / "leases" / "critical.lease", lock_fd)
    _out(res, args.json)
    return 0


def _out(res, as_json):
    if as_json:
        print(json.dumps(res, indent=1, default=str))
    else:
        print("status={}".format(res["status"]))
        for s in res["steps"]:
            print("  [{}] {} {}".format("ok" if s["ok"] else "FAIL", s["step"], s["detail"]))


if __name__ == "__main__":
    raise SystemExit(main())
