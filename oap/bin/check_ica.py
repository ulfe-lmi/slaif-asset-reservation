#!/usr/bin/env python3
"""check_ica.py — structural validation of ICA requests/reports.

Required: human target scope, full architecture hash, exact merged revision, complete
requirement matrix (all applicable SAR rows with classification/enforcing path/
evidence/negative path), auditor provenance, independence statement. Structural
validation NEVER proves independence, correctness or milestone closure.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oaplib  # noqa: E402

CLASSIFICATIONS = ("IMPLEMENTED", "PARTIAL", "ABSENT", "UNPROVEN")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--file", required=True, help="ICA request or report file")
    ap.add_argument("--kind", choices=("request", "report"), default="request")
    ap.add_argument("--requirements-json", default=None, help="SAR inventory to cross-check")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    repo = Path(args.repo)
    f = Path(args.file)
    res = {"file": str(f), "kind": args.kind, "checks": {}, "ok": True}

    def check(name, ok, detail=""):
        res["checks"][name] = {"ok": ok, "detail": detail}
        if not ok:
            res["ok"] = False

    if not f.is_file():
        check("exists", False, "missing")
        _out(res, args.json)
        return 1
    text = f.read_text("utf-8", "replace")
    check(
        "human_scope",
        bool(re.search(r"(?im)^Human scope", text) or "human scope" in text.lower()),
        "attributable human target scope required",
    )
    arch = repo / "ARCHITECTURE.md"
    if arch.is_file():
        cur = oaplib.sha256_hex(arch.read_bytes())
        has_hash = bool(re.search(r"\b[0-9a-f]{64}\b", text))
        check("architecture_hash", has_hash, "full architecture digest required")
        if has_hash and cur not in text:
            check(
                "architecture_hash_current",
                False,
                f"stale: current full-architecture digest {cur} not referenced",
            )
        else:
            check("architecture_hash_current", True)
    else:
        check("architecture_hash", False, "no canonical ARCHITECTURE.md to bind")
    rev_ok = bool(
        re.search(r"(?im)^(Merged product revision|exact merged revision|Audited revision)", text)
    )
    rev_line = re.search(r"(?im)^(?:Merged product revision|Audited revision):\s*(\S+)", text)
    if not rev_ok:
        check("exact_revision", False, "exact merged revision field required")
    elif rev_line and rev_line.group(1).lower() in ("pending", "unresolved", "<actual", "tbd"):
        check("exact_revision", True, "explicitly unresolved (request draft)")
    else:
        check("exact_revision", True)
    if args.requirements_json:
        rows = json.loads(Path(args.requirements_json).read_text())
        missing = [r["id"] for r in rows if r["id"] not in text]
        check("requirement_matrix_complete", not missing, f"missing SAR rows: {missing}")
    else:
        ids = set(re.findall(r"SAR-[0-9]{3}", text))
        check("requirement_matrix_present", len(ids) >= 10, f"{len(ids)} SAR IDs referenced")
    cls_found = [c for c in CLASSIFICATIONS if c in text]
    check(
        "classifications_present",
        len(cls_found) >= 1,
        "IMPLEMENTED/PARTIAL/ABSENT/UNPROVEN vocabulary required",
    )
    check(
        "auditor_provenance",
        bool(re.search(r"(?im)Auditor", text) and bool(re.search(r"(?im)Independence", text))),
        "auditor/context provenance and independence statement required",
    )
    check("negative_paths", "negative" in text.lower(), "negative paths must be named")
    if args.kind == "request":
        check(
            "no_prefilled_success",
            not re.search(r"(?im)^Result:\s*PASS", text),
            "request must not prefill a passing result",
        )
        if re.search(r"(?im)^Auditor:\s*(?!.*pending|.*<|.*unresolved)", text) and not re.search(
            r"(?im)pending|unresolved|TBD", text, re.I
        ):
            m = re.search(r"(?im)^Auditor:\s*(.+)$", text)
            check(
                "auditor_unfilled_in_request",
                "pending" in (m.group(1) if m else "").lower()
                or "<" in (m.group(1) if m else "")
                or "unresolved" in (m.group(1) if m else "").lower(),
                "request drafts must not populate an auditor identity",
            )
    else:
        check(
            "findings_section",
            "findings" in text.lower(),
            "findings/contrary evidence required in report",
        )
    check(
        "structural_only_disclaimer",
        "independence" in text.lower() and ("not" in text.lower()),
        "must state structural validation is not proof of independence",
    )
    _out(res, args.json)
    return 0 if res["ok"] else 1


def _out(res, as_json):
    if as_json:
        print(json.dumps(res, indent=1, default=str))
    else:
        print("result=%s" % ("PASS-STRUCTURAL-ONLY" if res["ok"] else "FAIL"))
        for name, c in res["checks"].items():
            print(
                "  [{}] {} {}".format(
                    "ok" if c["ok"] else "FAIL", name, c["detail"] if not c["ok"] else ""
                )
            )


if __name__ == "__main__":
    raise SystemExit(main())
