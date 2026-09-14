#!/usr/bin/env python3
"""Materialization engine for the Concentrated OAP two-workspace bootstrap.

Manifest-owned, scoped, atomic writes. Default is DRY RUN (zero writes).
Modes: --dry-run (default) | --apply | --refresh (apply of known previous generated
versions with backups; unknown divergent copies stay conflicts).
"""

from __future__ import annotations

import argparse
import json
import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oaplib  # noqa: E402

MANIFEST_NAME = ".oap-materialization.json"


def load_manifest(content_root: Path):
    mp = content_root / MANIFEST_NAME
    man = json.loads(mp.read_text())
    man["_content_root"] = str(content_root)
    for entry in man.get("files", []):
        src = content_root / entry["rel"]
        if not src.is_file():
            raise oaplib.OAPError("manifest content missing: {}".format(entry["rel"]))
        if (
            entry.get("content_sha256")
            and oaplib.sha256_hex(src.read_bytes()) != entry["content_sha256"]
        ):
            raise oaplib.OAPError("manifest content hash mismatch: {}".format(entry["rel"]))
    return man


def root_of(rel: str, repo_root: str, strategic_home: str) -> str:
    if rel == "REPO":
        return str(Path(repo_root))
    if rel == "STRATEGIC_HOME":
        return str(Path(strategic_home))
    if rel.startswith("REPO/"):
        return str(Path(repo_root) / rel[len("REPO/") :])
    if rel.startswith("STRATEGIC_HOME/"):
        return str(Path(strategic_home) / rel[len("STRATEGIC_HOME/") :])
    raise oaplib.OAPError(f"unknown manifest root: {rel}")


def git_state(repo_root: str) -> dict:
    head = oaplib.git_head(repo_root)
    # --no-optional-locks: a read-only bootstrap must not refresh/rewrite the
    # git index (it would perturb .git mtimes in a no-write dry run)
    rc, out, _ = oaplib.git(repo_root, "--no-optional-locks", "status", "--porcelain=v1", "-uall")
    dirty = [ln[3:].strip() for ln in out.splitlines() if ln.strip()]
    rc2, wt, _ = oaplib.git(repo_root, "rev-parse", "--show-toplevel")
    rc3, fmt, _ = oaplib.git(repo_root, "rev-parse", "--git-common-dir")
    gitdir = oaplib.canonical(repo_root, ".git") if False else str(Path(repo_root) / ".git")
    is_worktree_file = Path(gitdir).is_file()
    return {
        "head": head["head"],
        "object_format": head["object_format"],
        "dirty": dirty,
        "worktree": wt.strip(),
        "git_dir_is_file": is_worktree_file,
    }


def running_role_detected(repo_root: str) -> list:
    found = []
    leases = Path(repo_root) / "oap" / "leases"
    if leases.is_dir():
        for lf in leases.iterdir():
            try:
                info = json.loads(lf.read_text())
                if oaplib.pid_alive(int(info.get("pid", -1))):
                    found.append(str(lf))
            except (ValueError, OSError):
                found.append(str(lf) + " (unparseable)")
    return found


def plan(man, repo_root: str, strategic_home: str, mode: str):
    """Compute the full plan. Returns (entries, conflicts, notes)."""
    entries = []
    conflicts = []
    notes = []
    for entry in man.get("files", []):
        rel = entry["rel"]
        target = root_of(rel, repo_root, strategic_home)
        content = (Path(man["_content_root"]) / rel).read_bytes()
        tpath = Path(target)
        kind = entry.get("kind", "copy")
        st = tpath.lstat() if tpath.exists() or tpath.is_symlink() else None
        cur = tpath.read_bytes() if (st is not None and stat.S_ISREG(st.st_mode)) else None
        rec = {
            "rel": rel,
            "target": target,
            "content_sha256": oaplib.sha256_hex(content),
            "bytes": len(content),
        }
        if kind == "archive_then_copy":
            pre = entry.get("pre_sha256")
            backup = entry.get("backup")
            if st is None:
                rec["action"] = "created"
            elif cur == content:
                rec["action"] = "identical"
                if backup and not Path(root_of(backup, repo_root, strategic_home)).exists():
                    rec["archive_pending"] = True
            elif pre and oaplib.sha256_hex(cur) == pre:
                rec["action"] = "replace"
                rec["backup"] = backup
            else:
                rec["action"] = "conflict"
                rec["reason"] = (
                    "existing file matches neither the expected pre-bytes nor the "
                    "candidate; preserved untouched"
                )
                conflicts.append(rec)
        elif kind == "seed_if_absent":
            if st is None:
                rec["action"] = "created"
            else:
                rec["action"] = "preserved-existing"
                if cur != content:
                    rec["note"] = (
                        "existing register differs from candidate seed; "
                        "preserved byte-for-byte (seed not applied)"
                    )
                    notes.append(rec["note"])
        elif kind == "create_if_absent":
            if st is None:
                rec["action"] = "created"
            else:
                rec["action"] = "preserved-private"
        else:  # copy
            if st is None:
                rec["action"] = "created"
            elif cur == content:
                rec["action"] = "identical"
            else:
                prev = (man.get("previous_generated") or {}).get(rel)
                if mode in ("apply", "refresh") and prev and oaplib.sha256_hex(cur) == prev:
                    rec["action"] = "replace"
                    rec["backup"] = entry.get("backup")
                else:
                    rec["action"] = "conflict"
                    rec["reason"] = (
                        "existing file is not the candidate nor a known previous generated "
                        "version; preserved untouched"
                    )
                    conflicts.append(rec)
        entries.append(rec)
    for d in man.get("dirs", []):
        target = root_of(d["rel"], repo_root, strategic_home)
        rec = {
            "rel": d["rel"],
            "target": target,
            "action": "existing" if Path(target).exists() else "created",
            "dir": True,
            "mode": oct(d.get("mode", 0o755)),
        }
        entries.append(rec)
    for f in man.get("fifos", []):
        target = root_of(f["rel"], repo_root, strategic_home)
        p = Path(target)
        if p.exists():
            rec = {"rel": f["rel"], "target": target, "action": "existing", "fifo": True}
        else:
            rec = {"rel": f["rel"], "target": target, "action": "created", "fifo": True}
        entries.append(rec)
    if man.get("manifest_sha256"):
        entries.append(
            {
                "rel": "REPO/MANIFEST.sha256",
                "target": str(Path(repo_root) / "MANIFEST.sha256"),
                "action": "recomputed"
                if (Path(repo_root) / "MANIFEST.sha256").exists()
                else "created",
                "special": "manifest",
            }
        )
    return entries, conflicts, notes


def compute_manifest_sha256(repo_root: str, spec: dict, generated=None):
    """Recompute MANIFEST.sha256: existing listed paths with current digests + the
    generation's own public generated paths. Dynamic state stays out (exclusion
    list). When `generated` is given, the file universe is exactly that list plus
    previously listed lines — the destination is never globbed, so runtime
    artifacts (e.g. __pycache__) can never enter the static manifest."""
    root = Path(repo_root)
    exclude_prefix = spec.get("exclude_prefixes", [])
    exclude_exact = set(spec.get("exclude_exact", []))
    listed = {}
    mpath = root / "MANIFEST.sha256"
    if mpath.exists():
        for line in mpath.read_text().splitlines():
            if not line.strip():
                continue
            digest, path = line.split("  ", 1)
            rel = path[2:] if path.startswith("./") else path
            if "__pycache__" in rel.split("/") or rel.endswith(".pyc"):
                continue  # volatile bytecode can never be a static manifest entry
            listed[path] = digest
    files = set()
    if generated is not None:
        for g in generated:
            rel = "./" + g
            if rel == "./MANIFEST.sha256":
                continue
            files.add(rel)
    else:
        for p in root.rglob("*"):
            rel = "./" + p.relative_to(root).as_posix()
            if rel == "./MANIFEST.sha256" or p.is_symlink():
                continue
            if not p.is_file():
                continue
            if "__pycache__" in rel.split("/") or rel.endswith(".pyc"):
                continue
            if any(rel.startswith(pre) or ("./" + pre) == rel for pre in exclude_prefix):
                continue
            if rel in exclude_exact or p.relative_to(root).as_posix() in exclude_exact:
                continue
            if rel == "./.git" or rel.startswith("./.git/"):
                continue
            files.add(rel)
    merged = {}
    for path in sorted(set(listed) | files):
        rel = path[2:] if path.startswith("./") else path
        p = root / rel
        if p.is_file() and not p.is_symlink():
            merged[path] = oaplib.sha256_hex(p.read_bytes())
        elif path in listed and not p.exists():
            merged[path] = listed[path]  # tracked elsewhere; keep line (should not happen)
    lines = [f"{d}  {p}" for p, d in sorted(merged.items())]
    return "\n".join(lines) + "\n"


def apply(man, repo_root: str, strategic_home: str, mode: str, plan_entries, conflicts, notes):
    applied = []
    for rec in plan_entries:
        if rec.get("dir") or rec.get("fifo") or rec.get("special"):
            if rec.get("dir"):
                res = (
                    oaplib.ensure_private_dir(rec["target"])
                    if rec.get("mode") == "0o700"
                    else oaplib.ensure_dir(rec["target"], 0o755)
                )
                rec["result"] = res
                applied.append(rec)
            elif rec.get("fifo"):
                rec["result"] = oaplib.ensure_fifo(rec["target"], 0o600)
                applied.append(rec)
            continue
        if rec["action"] == "conflict":
            continue
        if rec["action"] in ("identical", "preserved-existing", "preserved-private"):
            if rec.get("archive_pending"):
                btarget = root_of(rec.get("backup"), repo_root, strategic_home)
                oaplib.atomic_write(
                    btarget,
                    (Path(man["_content_root"]) / rec["rel"]).read_bytes(),
                    expect_absent=True,
                )
            applied.append(rec)
            continue
        if rec["action"] == "recomputed":
            continue
        data = (Path(man["_content_root"]) / rec["rel"]).read_bytes()
        target = Path(rec["target"])
        entry = next((e for e in man.get("files", []) if e["rel"] == rec["rel"]), {})
        kind = entry.get("kind", "copy")
        mode = entry.get("mode") or (
            0o600
            if rec["rel"].endswith((".env", ".fifo")) or "agent-homes" in rec["rel"]
            else 0o644
        )
        expect = None
        # capture the OLD bytes before any write; the backup must never contain new bytes
        old = target.read_bytes() if (target.exists() and not target.is_symlink()) else None
        if kind == "archive_then_copy" and old is not None:
            expect = old  # re-verify expected pre-identity at write time
        if kind == "seed_if_absent":
            res = oaplib.atomic_write(target, data, mode=mode, expect_absent=True)
        else:
            res = oaplib.atomic_write(target, data, mode=mode, expect=expect)
        if rec.get("backup") and old is not None:
            btarget = Path(root_of(rec["backup"], repo_root, strategic_home))
            if not btarget.exists():
                oaplib.atomic_write(
                    btarget, expect if expect is not None else old, expect_absent=True
                )
        rec["result"] = res
        applied.append(rec)
    # MANIFEST.sha256 recompute (after all scoped writes); universe = manifest-owned
    # generated repo files + previously listed lines (never a destination glob)
    if man.get("manifest_sha256"):
        gen = [
            f["rel"][len("REPO/") :]
            for f in man.get("files", [])
            if f.get("rel", "").startswith("REPO/")
        ]
        text = compute_manifest_sha256(repo_root, man["manifest_sha256"], generated=gen)
        oaplib.atomic_write(Path(repo_root) / "MANIFEST.sha256", text.encode(), mode=0o644)
        for rec in plan_entries:
            if rec.get("special") == "manifest":
                rec["result"] = "written"
    return applied


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--content-root", required=True, help="staged content tree with .oap-materialization.json"
    )
    ap.add_argument("--repo", required=True, help="REPO_ROOT canonical path")
    ap.add_argument("--strategic-home", required=True, help="STRATEGIC_HOME canonical path")
    ap.add_argument(
        "--bootstrap-root", default=None, help="BOOTSTRAP_ROOT (third, non-nested root)"
    )
    ap.add_argument("--apply", action="store_true", help="perform scoped writes")
    ap.add_argument(
        "--refresh",
        action="store_true",
        help="apply known-previous-generation refresh with backups",
    )
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)
    mode = "refresh" if args.refresh else ("apply" if args.apply else "dry-run")
    if args.apply and args.refresh:
        print("use --apply or --refresh, not both", file=sys.stderr)
        return 2
    try:
        man = load_manifest(Path(args.content_root).resolve())
    except oaplib.OAPError as e:
        _emit(
            {
                "mode": mode,
                "generation": None,
                "roots": {},
                "root_errors": [],
                "git": None,
                "running_roles": None,
                "entries": [],
                "conflicts": [],
                "notes": [],
                "writes_performed": False,
                "result": "REFUSED",
                "errors": [str(e)],
            },
            args.json,
        )
        return 1
    errs = oaplib.validate_roots(
        args.repo,
        args.strategic_home,
        args.bootstrap_root or str(Path(args.content_root).parent),
        create_missing=True,
    )
    report = {
        "mode": mode,
        "generation": man.get("generation"),
        "roots": {
            "repo": oaplib.canonical(args.repo),
            "strategic": oaplib.canonical(args.strategic_home),
        },
        "root_errors": errs,
        "git": None,
        "running_roles": None,
        "entries": [],
        "conflicts": [],
        "notes": [],
        "writes_performed": False,
    }
    if errs:
        report["result"] = "REFUSED"
        _emit(report, args.json)
        return 1
    if mode in ("apply", "refresh"):
        running = running_role_detected(args.repo)
        report["running_roles"] = running
        if running:
            report["result"] = "REFUSED_RUNNING_ROLE"
            report["notes"].append("running role lease detected; quiesce before applying")
            _emit(report, args.json)
            return 1
    gstate = git_state(args.repo)
    report["git"] = gstate
    entries, conflicts, notes = plan(man, args.repo, args.strategic_home, mode)
    # Note: dirty-touched protection is enforced by plan() byte-identity rules
    # (a worktree file matching neither the candidate nor its recorded pre/previous
    # identity is a conflict). A replace whose current bytes match a recorded identity
    # is authorized even when HEAD differs (refresh of a never-committed generation).
    report["entries"] = entries
    report["conflicts"] = conflicts
    report["notes"] = notes
    if conflicts:
        report["result"] = "CONFLICTS"
        if mode in ("apply", "refresh"):
            _emit(report, args.json)
            return 1
    if mode == "dry-run":
        report["result"] = "PLANNED"
        report["would_write"] = [
            e["rel"] for e in entries if e["action"] in ("created", "replace", "recomputed")
        ]
    else:
        apply(man, args.repo, args.strategic_home, mode, entries, conflicts, notes)
        report["writes_performed"] = True
        report["result"] = "APPLIED"
    _emit(report, args.json)
    return 0


def _emit(report, as_json):
    if as_json:
        print(json.dumps(report, indent=1, default=str))
        return
    print(
        "mode={} generation={} result={}".format(
            report["mode"], report["generation"], report["result"]
        )
    )
    if report["root_errors"]:
        for e in report["root_errors"]:
            print(f"ROOT-ERROR: {e}")
    if report.get("git"):
        g = report["git"]
        print(f"git head={g['head']} dirty={len(g['dirty'])} worktree_file={g['git_dir_is_file']}")
    for e in report["entries"]:
        extra = ""
        if e.get("result"):
            extra = " -> {}".format(e["result"])
        if e.get("reason"):
            extra += " [{}]".format(e["reason"])
        if e.get("note"):
            extra += " ({})".format(e["note"])
        print(f"{e['action']:<9} {e['rel']}{extra}")
    for n in report["notes"]:
        print(f"NOTE: {n}")


if __name__ == "__main__":
    raise SystemExit(main())
