#!/usr/bin/env python3
"""verify_report.py — OP-09/OP-10 report verification (slim, 015-a).

Exactly three checks:
  1. report_only_changed_path        — the report commit changes ONLY the report path
  2. implementation_head_first_parent — literal implementation head line in the report,
                                         and the report commit's first parent equals it
  3. remote_head_and_pr_identity     — exact remote branch head equals the report commit,
                                         plus PR/branch identity when --pr is given

Structural preconditions (unique valid order, local report, report commit found,
--head match) gate the run: missing local/remote evidence returns BLOCKED, never a
local pass.
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

    def blocked(detail=""):
        res["status"] = "BLOCKED"
        res["blocked"] = oaplib.redact(detail)
        _out(res, args.json)
        return 1

    # ---- preconditions (not counted among the three checks) ----
    head_info = oaplib.git_head(str(repo))
    fmt_len = 64 if head_info["object_format"] == "sha256" else 40
    orders = sorted((repo / "oap" / "orders").glob(oid + "-*.md"))
    if len(orders) != 1:
        res["status"] = "FAIL"
        res["precondition"] = f"pointer ID matches {len(orders)} orders (need exactly 1)"
        _out(res, args.json)
        return 1
    ometa, obody, oerrs = oaplib.parse_order(orders[0].read_bytes(), strict_final=True)
    if oerrs:
        res["status"] = "FAIL"
        res["precondition"] = "order invalid: " + "; ".join(oerrs[:3])
        _out(res, args.json)
        return 1
    rpath = repo / "oap" / "reports" / orders[0].name
    if not rpath.is_file():
        return blocked("no local report")
    rtext = rpath.read_text("utf-8", "replace")
    rlines = rtext.splitlines()
    rc, blobout, _ = oaplib.git(str(repo), "hash-object", str(rpath))
    blob_id = blobout.strip()
    relpath = rpath.relative_to(repo).as_posix()
    rc, out, _ = oaplib.git(
        str(repo), "log", "--format=%H", "--find-object", blob_id, "--", relpath, check=False
    )
    commits = [c for c in out.splitlines() if c]
    if not commits:
        return blocked("no commit carries the report bytes")
    report_commit = commits[0]
    if args.head and args.head != report_commit:
        res["status"] = "FAIL"
        res["precondition"] = f"report commit {report_commit} != expected {args.head}"
        _out(res, args.json)
        return 1

    # ---- check 1: report-only changed path ----
    rc, diff, _ = oaplib.git(
        str(repo), "show", "--name-only", "--format=", report_commit, check=False
    )
    changed = [line for line in diff.splitlines() if line.strip()]
    check("report_only_changed_path", changed == [relpath], f"changed paths: {changed}")

    # ---- check 2: literal implementation head as first parent ----
    m = [line for line in rlines if line.startswith("Implementation head SHA: ")]
    if len(m) != 1:
        check("implementation_head_first_parent", False, "exactly one literal line required")
    else:
        impl = m[0].split("Implementation head SHA: ", 1)[1].strip()
        if (
            len(impl) != fmt_len
            or not oaplib.HEX40.fullmatch(impl)
            and not oaplib.HEX64.fullmatch(impl)
        ):
            check(
                "implementation_head_first_parent",
                False,
                "not a full object ID in {} format".format(head_info["object_format"]),
            )
        else:
            rc, p1, _ = oaplib.git(str(repo), "rev-parse", report_commit + "^", check=False)
            if rc != 0:
                check(
                    "implementation_head_first_parent",
                    False,
                    "report commit is a root commit (no implementation head)",
                )
            elif p1.strip() != impl:
                check(
                    "implementation_head_first_parent",
                    False,
                    f"first parent {p1.strip()} != stated implementation head {impl}",
                )
            else:
                check("implementation_head_first_parent", True, impl)

    # ---- check 3: exact remote head plus PR/branch identity ----
    prior_fail = res["status"] == "FAIL"
    adapter = oaplib.load_remote_adapter(str(repo))
    branch = ometa.get("branch")
    rres = adapter.report_remote(str(repo), oid, ometa)
    if not rres.get("remote_head"):
        check(
            "remote_head_and_pr_identity",
            False,
            "remote branch not verified; local report is NOT completion",
        )
        # missing remote evidence is BLOCKED, never a local pass; an already-failed
        # local check keeps the overall status FAIL
        res["status"] = "FAIL" if prior_fail else "BLOCKED"
    else:
        problems = []
        if rres["remote_head"] != report_commit:
            problems.append(
                "remote head {} differs from report commit {}".format(
                    rres["remote_head"], report_commit
                )
            )
        if args.pr is not None:
            pr = adapter.pr(str(repo), args.pr)
            if not pr:
                problems.append(f"PR {args.pr} not found on remote")
            elif pr.get("branch") != branch:
                problems.append(
                    "PR {} branch {} != order branch {}".format(args.pr, pr.get("branch"), branch)
                )
        else:
            pr = adapter.pr_for_branch(str(repo), branch) if branch else None
            if pr and (pr.get("state") == "merged" or pr.get("merged")):
                problems.append("branch PR is merged; a published round PR must be open")
        if problems:
            check("remote_head_and_pr_identity", False, "; ".join(problems))
        else:
            prinfo = ""
            if args.pr is not None:
                prinfo = f", PR {args.pr} bound"
            check(
                "remote_head_and_pr_identity",
                True,
                "remote head {} at report commit (branch {}){}".format(
                    rres["remote_head"], branch, prinfo
                ),
            )
    if res["status"] == "PASS" and not all(c["ok"] for c in res["checks"].values()):
        res["status"] = "FAIL"
    _out(res, args.json)
    return 0 if res["status"] in ("PASS", "BLOCKED") else 1


def _out(res, as_json):
    if as_json:
        print(json.dumps(res, indent=1, default=str))
    else:
        print("status={}".format(res["status"]))
        for extra in ("precondition", "blocked"):
            if extra in res:
                print(f"  ({extra}) {res[extra]}")
        for name, c in res["checks"].items():
            print(
                "  [{}] {} {}".format(
                    "ok" if c["ok"] else "FAIL", name, c["detail"] if not c["ok"] else ""
                )
            )


if __name__ == "__main__":
    raise SystemExit(main())
