#!/usr/bin/env python3
"""check_governance.py — source/projection/installed-copy identity and coverage.

Checks: canonical sources exist; compact architecture embeds the current full
architecture SHA; S-01..S-24 referenced by coding law; C-01..C-16 present; all SAR IDs
in compact architecture and ICA matrix; byte budgets; strategic installed copies equal
versioned sources; installed identities match governance MANIFEST; accepted-vs-candidate
diff scope (with --accepted-base).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oaplib  # noqa: E402

BUDGETS = {
    "AGENTS.md": 2048,
    "oap/coding-instructions/AGENTS.md": 12000,
    "ARCHITECTURE-for-agents.md": 20000,
    "OAP-COMMUNICATION-coding-agent.md": 10000,
}
ROUTINE_TOTAL = 50000


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--strategic-home", default=None)
    ap.add_argument(
        "--accepted-base", default=None, help="git revision of accepted base for diff-scope check"
    )
    ap.add_argument(
        "--scope", default=None, help="comma-separated allowed changed paths for candidate review"
    )
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    repo = Path(args.repo)
    res = {"repo": str(repo), "checks": {}, "ok": True}
    review_mode = bool(args.accepted_base)

    def check(name, ok, detail=""):
        res["checks"][name] = {"ok": ok, "detail": detail}
        if not ok:
            res["ok"] = False

    def absent(name, what):
        # a scoped diff review (--accepted-base) only reviews what the candidate
        # carries; whole-tree identity belongs to the materialized-tree review
        if review_mode:
            check(name, True, what + " absent in candidate; not reviewed")
        else:
            check(name, False, what + " missing")

    full = repo / "ARCHITECTURE.md"
    compact = repo / "ARCHITECTURE-for-agents.md"
    if not full.is_file():
        absent("canonical_architecture_present", "root ARCHITECTURE.md")
    elif not compact.is_file():
        absent("canonical_architecture_present", "compact ARCHITECTURE-for-agents.md")
    else:
        full_b = full.read_bytes()
        compact_b = compact.read_bytes()
        sha = oaplib.sha256_hex(full_b)
        check("canonical_architecture_present", True, f"full={len(full_b)} bytes sha256={sha}")
        check(
            "projection_source_hash_current",
            sha in compact_b.decode("utf-8", "replace"),
            "compact must embed the exact full-architecture SHA-256",
        )
        ids = re.findall(r"\*\*SAR-(\d{3})[^*]*\*\*|### SAR-(\d{3})", compact_b.decode("utf-8"))
        found = {a or b for a, b in ids}
        missing = [f"SAR-{i:03d}" for i in range(1, 39) if f"{i:03d}" not in found]
        check("sar_coverage_compact", not missing, f"missing: {missing}")
        matrix = repo / "oap" / "audit" / "ICA-REQUIREMENT-MATRIX-TEMPLATE.md"
        if matrix.is_file():
            mtxt = matrix.read_text("utf-8", "replace")
            mmissing = [f"SAR-{i:03d}" for i in range(1, 39) if f"SAR-{i:03d}" not in mtxt]
            check("sar_coverage_ica_matrix", not mmissing, f"missing: {mmissing}")
    # clause coverage
    coding = repo / "oap" / "coding-instructions" / "AGENTS.md"
    strat_src = repo / "oap" / "strategic-instructions" / "AGENTS.md"
    if coding.is_file() and strat_src.is_file():
        c = coding.read_text("utf-8", "replace")
        s = strat_src.read_text("utf-8", "replace")
        smissing = [i for i in range(1, 25) if f"S-{i:02d}" not in s]
        srefs = [i for i in range(1, 25) if f"S-{i:02d}" not in c]
        cmissing = [i for i in range(1, 17) if f"C-{i:02d}" not in c]
        check("strategic_clauses_present", not smissing, f"missing in strategic source: {smissing}")
        check(
            "strategic_to_coding_reference",
            not srefs,
            f"strategic clause IDs not referenced by coding law: {srefs}",
        )
        check("coding_clauses_present", not cmissing, f"missing coding clauses: {cmissing}")
    # budgets
    sizes = {}
    for rel in list(BUDGETS) + [
        "oap/coding-instructions/SECURITY-CORE.md",
        "oap/coding-instructions/TESTING-CORE.md",
    ]:
        p = repo / rel
        if p.is_file():
            sizes[rel] = len(p.read_bytes())
        else:
            if not review_mode:
                check("budget_file_present", False, f"missing {rel}")
    if not sizes and review_mode:
        check("budget_file_present", True, "no budget files present in candidate; not reviewed")
    over = {k: (sizes.get(k), v) for k, v in BUDGETS.items() if sizes.get(k, 0) > v}
    check("byte_budgets", not over, f"over ceiling: {over}")
    check(
        "routine_total_budget",
        sum(sizes.values()) <= ROUTINE_TOTAL,
        f"total {sum(sizes.values())} > {ROUTINE_TOTAL}",
    )
    budget_doc = repo / "oap" / "governance" / "CONTEXT-BUDGET.md"
    if budget_doc.is_file():
        bt = budget_doc.read_text("utf-8", "replace")
        check(
            "budget_tokens_unmeasured_honest",
            "UNMEASURED" in bt,
            "token provenance must state UNMEASURED without a qualified tokenizer",
        )
    # distillation map coverage
    dm = repo / "oap" / "governance" / "DISTILLATION-MAP.md"
    if dm.is_file():
        dt = dm.read_text("utf-8", "replace")
        dmiss = [i for i in range(1, 25) if f"S-{i:02d}" not in dt]
        check("distillation_map_coverage", not dmiss, f"missing: {dmiss}")
    else:
        absent("distillation_map_coverage", "DISTILLATION-MAP.md")
    # installed copies
    if args.strategic_home:
        home = Path(args.strategic_home)
        pairs = [
            ("AGENTS.md", "oap/strategic-instructions/AGENTS.md"),
            (
                "OAP-COMMUNICATION-strategic.md",
                "oap/strategic-instructions/OAP-COMMUNICATION-strategic.md",
            ),
            (
                "strategic_model_init_material.md",
                "oap/strategic-instructions/strategic_model_init_material.md",
            ),
            ("INITIAL-ROADMAP.md", "oap/strategic-instructions/INITIAL-ROADMAP.md"),
        ]
        for dst, src_rel in pairs:
            d, s = home / dst, repo / src_rel
            if not d.is_file() or not s.is_file():
                check(f"installed_copy_{dst}", False, "missing copy")
            else:
                ok = oaplib.sha256_hex(d.read_bytes()) == oaplib.sha256_hex(s.read_bytes())
                check(
                    f"installed_copy_{dst}",
                    ok,
                    "byte-identical to versioned source" if ok else "drift from versioned source",
                )
    # governance manifest identity
    gm = repo / "oap" / "governance" / "MANIFEST.json"
    if gm.is_file():
        try:
            manifest = json.loads(gm.read_text())
            ids = manifest.get("identities", {})
            bad = []
            for name, meta in ids.items():
                p = repo / name
                if not p.is_file():
                    bad.append(name + " (missing)")
                elif oaplib.sha256_hex(p.read_bytes()) != meta.get("sha256"):
                    bad.append(name + " (hash drift)")
            check("governance_manifest_identities", not bad, f"drift: {bad}")
        except ValueError:
            check("governance_manifest_identities", False, "MANIFEST.json unparseable")
    else:
        absent("governance_manifest_identities", "governance MANIFEST.json")
    # candidate vs accepted scope
    if args.accepted_base:
        rc, out, err = oaplib.git(str(repo), "diff", "--name-only", args.accepted_base, "HEAD")
        if rc != 0:
            rc, out, err = oaplib.git(str(repo), "diff", "--name-only", args.accepted_base)
        changed = [line for line in out.splitlines() if line.strip()]
        scope = [s.strip() for s in (args.scope or "").split(",") if s.strip()]
        if scope:
            allowed = []
            for c in changed:
                if any(c == s or c.startswith(s.rstrip("/") + "/") for s in scope):
                    allowed.append(c)
            outside = [c for c in changed if c not in allowed]
            check(
                "candidate_scope_vs_accepted",
                not outside,
                f"changes outside ordered governance scope: {outside[:10]}",
            )
        else:
            check("candidate_scope_vs_accepted", False, "--scope required with --accepted-base")
    if args.json:
        print(json.dumps(res, indent=1, default=str))
    else:
        for name, c in res["checks"].items():
            print(f"{name:<38} {'OK' if c['ok'] else 'FAIL'} {c['detail'] if not c['ok'] else ''}")
        print(f"RESULT: {'PASS' if res['ok'] else 'FAIL'}")
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
