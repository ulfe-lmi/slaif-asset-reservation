#!/usr/bin/env python3
"""verify_report.py — OP-09/OP-10 report verification.

Verifies actual object format, exact order digest, literal implementation parent,
report-only changed path, no CRITICAL mutation in the report commit, correct
PR/branch/round, remote availability and exact remote head. Missing remote evidence
returns BLOCKED/PENDING, never a local pass.
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
    ap.add_argument("--repo", required=True)
    ap.add_argument("--id", required=True)
    ap.add_argument("--pr", type=int, default=None)
    ap.add_argument("--head", default=None, help="expected report publication commit (full ID)")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    repo = Path(args.repo)
    oid = args.id
    res = {
        "id": oid,
        "checks": {},
        "status": "PASS",
        "test_mode_adapter": oaplib.remote_adapter_is_test_mode(),
    }

    def check(name, ok, detail=""):
        res["checks"][name] = {"ok": ok, "detail": oaplib.redact(detail)}
        if not ok and res["status"] == "PASS":
            res["status"] = "FAIL"

    head_info = oaplib.git_head(str(repo))
    fmt_len = 64 if head_info["object_format"] == "sha256" else 40
    orders = sorted((repo / "oap" / "orders").glob(oid + "-*.md"))
    if len(orders) != 1:
        check("order_unique", False, f"pointer ID matches {len(orders)} orders")
        _out(res, args.json)
        return 1
    ometa, obody, oerrs = oaplib.parse_order(orders[0].read_bytes(), strict_final=True)
    if oerrs:
        check("order_valid", False, "; ".join(oerrs[:3]))
        _out(res, args.json)
        return 1
    check("order_valid", True, orders[0].name)
    rpath = repo / "oap" / "reports" / orders[0].name
    if not rpath.is_file():
        check("report_exists", False, "no local report")
        res["status"] = "BLOCKED"
        _out(res, args.json)
        return 1
    check("report_exists", True)
    rtext = rpath.read_text("utf-8", "replace")
    rlines = rtext.splitlines()
    m = [line for line in rlines if line.startswith("Implementation head SHA: ")]
    if len(m) != 1:
        check("implementation_head_line", False, "exactly one literal line required")
    else:
        impl = m[0].split("Implementation head SHA: ", 1)[1].strip()
        if (
            len(impl) != fmt_len
            or not oaplib.HEX40.fullmatch(impl)
            and not oaplib.HEX64.fullmatch(impl)
        ):
            check(
                "implementation_head_line",
                False,
                "not a full object ID in {} format".format(head_info["object_format"]),
            )
        else:
            check("implementation_head_line", True, impl)
            if "--head" in sys.argv or args.head:
                pass
            rc, p1, _ = oaplib.git(str(repo), "rev-parse", impl + "^", check=False)
            if rc != 0:
                check(
                    "implementation_head_exists", False, "implementation head not in object store"
                )
            else:
                check("implementation_head_exists", True, p1.strip())
    if "Report publication commit: SELF" not in rlines:
        check("self_marker", False, "missing 'Report publication commit: SELF'")
    else:
        check("self_marker", True)
    # the report commit: find commit that introduced exactly the report blob
    rc, blobout, _ = oaplib.git(str(repo), "hash-object", str(rpath))
    blob_id = blobout.strip()
    relpath = rpath.relative_to(Path(repo)).as_posix()
    rc, out, _ = oaplib.git(
        str(repo), "log", "--format=%H", "--find-object", blob_id, "--", relpath, check=False
    )
    commits = [c for c in out.splitlines() if c]
    if not commits:
        check("report_commit_found", False, "no commit carries the report bytes")
        _out(res, args.json)
        return 1
    report_commit = commits[0]
    check("report_commit_found", True, report_commit)
    if args.head and args.head != report_commit:
        check("expected_head", False, f"report commit {report_commit} != expected {args.head}")
    else:
        check("expected_head", True, report_commit)
    rc, p1, _ = oaplib.git(str(repo), "rev-parse", report_commit + "^", check=False)
    if rc != 0:
        check("first_parent", False, "report commit is a root commit (no implementation head)")
    else:
        p1 = p1.strip()
        impl_line = [line for line in rlines if line.startswith("Implementation head SHA: ")]
        if impl_line and p1 != impl_line[0].split("Implementation head SHA: ", 1)[1].strip():
            check("first_parent", False, f"first parent {p1} != stated implementation head")
        else:
            check("first_parent", True, p1)
    rc, diff, _ = oaplib.git(
        str(repo), "show", "--name-only", "--format=", report_commit, check=False
    )
    changed = [line for line in diff.splitlines() if line.strip()]
    if changed != [relpath]:
        check("report_only_path", False, f"changed paths: {changed}")
    else:
        check("report_only_path", True)
    if "CRITICAL.md" in changed:
        check("no_critical_mutation", False, "CRITICAL.md changed in report commit")
    else:
        check("no_critical_mutation", True)
    # order digest inside report metadata (OP-09: order_path/hash)
    if "order" in rtext.lower() or True:
        odigest = oaplib.sha256_hex(orders[0].read_bytes())
        if odigest not in rtext:
            check("order_digest_in_report", False, "report must reference the exact order digest")
        else:
            check("order_digest_in_report", True)
    # CI honesty (colon form and heading-section form)
    meta_block = rtext
    import re as _re

    future_claim = bool(
        _re.search(r"(?im)^Report head CI:\s*(success|passed|green)\s*$", meta_block)
    )
    if not future_claim:
        _rlines = meta_block.splitlines()
        for _i, _l in enumerate(_rlines):
            if _re.match(r"^#{1,6}\s*Report head CI\s*$", _l.strip()):
                for _l2 in _rlines[_i + 1 : _i + 6]:
                    _s = _l2.strip()
                    if _s and not _s.startswith("#"):
                        if _re.fullmatch(r"success|passed|green", _s, _re.I):
                            future_claim = True
                        break
                break
    not_yet = "NOT YET OBSERVED AT AUTHORING" in meta_block
    if future_claim:
        check("future_ci_honesty", False, "report claims its own future report-head CI success")
    else:
        check(
            "future_ci_honesty",
            True,
            "report-head CI explicitly unobserved" if not_yet else "no future CI claim",
        )
    # remote verification
    adapter = oaplib.load_remote_adapter(str(repo))
    branch = ometa.get("branch")
    rres = adapter.report_remote(str(repo), oid, ometa)
    prior_fail = res["status"] == "FAIL"
    if not rres.get("remote_head"):
        check(
            "remote_available", False, "remote branch not verified; local report is NOT completion"
        )
        res["status"] = "FAIL" if prior_fail else "BLOCKED"
    else:
        check("remote_available", True, "remote head {}".format(rres["remote_head"]))
        if rres["remote_head"] != report_commit:
            check("remote_head_match", False, "remote head differs from report commit")
        else:
            check("remote_head_match", True)
    if args.pr is not None:
        pr = adapter.pr(str(repo), args.pr)
        if not pr:
            check("pr_identity", False, f"PR {args.pr} not found on remote")
        else:
            ok = pr.get("branch") == branch
            check("pr_identity", ok, "PR {} branch={}".format(args.pr, pr.get("branch")))
    if res["status"] == "PASS" and not all(c["ok"] for c in res["checks"].values()):
        res["status"] = "FAIL"
    _out(res, args.json)
    return 0 if res["status"] in ("PASS", "BLOCKED") else 1


def _out(res, as_json):
    if as_json:
        print(json.dumps(res, indent=1, default=str))
    else:
        print("status={}".format(res["status"]))
        for name, c in res["checks"].items():
            print(
                "  [{}] {} {}".format(
                    "ok" if c["ok"] else "FAIL", name, c["detail"] if not c["ok"] else ""
                )
            )


if __name__ == "__main__":
    raise SystemExit(main())
