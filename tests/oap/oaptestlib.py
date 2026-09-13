"""Shared fixture library for the tests/oap harness. Stdlib only.

Isolation rules (BA-50): every test works inside its own TemporaryDirectory
root; git repos, FIFOs, tmux sockets and processes are created and destroyed by
owner identity only. Nothing outside the owned roots is touched.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BIN = REPO_ROOT / "oap" / "bin"
if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))

import oaplib  # noqa: E402

REPO_ID = "ulfe-lmi/slaif-asset-reservation"
GIT_ENV = {
    "GIT_AUTHOR_NAME": "OAP Test",
    "GIT_AUTHOR_EMAIL": "oap-test@example.invalid",
    "GIT_COMMITTER_NAME": "OAP Test",
    "GIT_COMMITTER_EMAIL": "oap-test@example.invalid",
}

# ---------------------------------------------------------------- BLOCKED areas
# External prerequisites that cannot exist in every environment (installed Codex
# CLI, real strategic home) are recorded here as explicit BLOCKED areas, never
# silently skipped. The receipt carries the recorded list.
BLOCKED_AREAS: list = []


def record_blocked(case: str, reason: str) -> None:
    entry = {"case": case, "reason": reason, "pid": os.getpid()}
    if entry not in BLOCKED_AREAS:
        BLOCKED_AREAS.append(entry)
    print(f"[BLOCKED] {case}: {reason}", flush=True)


def real_strategic_home(case: str):
    """The real materialized strategic home, or None with a recorded BLOCKED area."""
    home = Path(
        os.environ.get(
            "OAP_TEST_STRATEGIC_HOME", "/home/ubuntu/codex-supervision/slaif-asset-reservation"
        )
    )
    if not home.is_dir():
        record_blocked(case, f"real strategic home not present in this environment: {home}")
        return None
    return home


def codex_available(case: str) -> bool:
    try:
        p = subprocess.run(["codex", "--version"], capture_output=True, timeout=20)
        if p.returncode == 0:
            return True
    except (OSError, subprocess.TimeoutExpired):
        pass
    record_blocked(case, "installed Codex CLI not runnable in this environment")
    return False


# ---------------------------------------------------------------- git fixtures


def git(cwd, *args, timeout: float = 30.0) -> str:
    env = dict(os.environ)
    env.update(GIT_ENV)
    p = subprocess.run(
        ["git", "-C", str(cwd)] + list(args), capture_output=True, timeout=timeout, env=env
    )
    if p.returncode != 0:
        raise RuntimeError(
            "git {} failed: {}".format(args, p.stderr.decode("utf-8", "replace")[:300])
        )
    return p.stdout.decode().strip()


def make_repo(root, files: dict, msg: str = "baseline") -> str:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for rel, data in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    git(root, "init", "-q", "-b", "main")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", msg)
    return git(root, "rev-parse", "HEAD")


def commit_files(root, files: dict, msg: str = "change") -> str:
    for rel, data in files.items():
        p = Path(root) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", msg)
    return git(root, "rev-parse", "HEAD")


def head(root) -> str:
    return git(root, "rev-parse", "HEAD")


def log_ids(root) -> list:
    return git(root, "log", "--format=%H").splitlines()


# ---------------------------------------------------------------- CLI runner


def run_cli(
    name: str,
    args: list,
    env: dict = None,
    cwd=None,
    timeout: float = 90.0,
    expect_json: bool = False,
):
    cmd = [sys.executable, str(BIN / name)] + [str(a) for a in args]
    e = dict(os.environ)
    e.update(env or {})
    p = subprocess.run(
        cmd, capture_output=True, timeout=timeout, env=e, cwd=str(cwd) if cwd else None
    )
    out = p.stdout.decode("utf-8", "replace")
    err = p.stderr.decode("utf-8", "replace")
    js = None
    if expect_json:
        js = json.loads(out)
    return p.returncode, out, err, js


# ---------------------------------------------------------------- fake client

FAKE_CLIENT = r"""#!/usr/bin/env bash
# fixture-only fake Codex client: records the invocation, never invokes a model
LOG="${OAP_FAKE_LOG:?OAP_FAKE_LOG required}"
python3 - "$LOG" "$@" <<'PY'
import json, os, sys
rec = {
    "argv": sys.argv[2:],
    "cwd": os.getcwd(),
    "CODEX_HOME": os.environ.get("CODEX_HOME", ""),
    "OAP_ROLE": os.environ.get("OAP_ROLE", ""),
}
with open(sys.argv[1], "a", encoding="utf-8") as fh:
    fh.write(json.dumps(rec) + "\n")
PY
sleep "${OAP_FAKE_SLEEP:-0.1}"
exit "${OAP_FAKE_EXIT:-0}"
"""


def install_fake_client(tmp: Path) -> Path:
    p = tmp / "fake-codex"
    p.write_text(FAKE_CLIENT)
    p.chmod(0o755)
    return p


def read_fake_log(log_path: Path) -> list:
    if not log_path.exists():
        return []
    return [json.loads(ln) for ln in log_path.read_text().splitlines() if ln.strip()]


# ---------------------------------------------------------------- runtime.env


def write_runtime_env(
    home: Path,
    repo: Path,
    activation: bool = False,
    authority: bool = False,
    coding_argv: list = None,
    strategic_argv: list = None,
    model: str = "",
    extra: dict = None,
) -> Path:
    lines = [
        "OAP_PROFILE_VERSION=1",
        f"OAP_REPO_ROOT={repo}",
        f"OAP_STRATEGIC_HOME={home}",
        f"OAP_REMOTE_REPOSITORY={REPO_ID}",
        "OAP_BASE_BRANCH=main",
        "OAP_ACCEPTED_GOVERNANCE_REVISION=",
        "OAP_ACTIVATION_ENABLED=%s" % ("true" if activation else "false"),
        "OAP_DEVELOPMENT_MERGE_ENABLED=false",
        "OAP_AUTHORITY_REFERENCE=%s" % ("/abs/attributable-authority.json" if authority else ""),
        "OAP_TARGET_MILESTONE=",
        "OAP_APPROVED_RUNTIME_REFERENCE=",
        "OAP_CODING_CLIENT=codex",
        "OAP_STRATEGIC_CLIENT=codex",
        f"OAP_CODING_MODEL={model}",
        f"OAP_STRATEGIC_MODEL={model}",
        "OAP_AUDIT_MODEL=",
        "OAP_PROVIDER=",
        "OAP_CLIENT_QUALIFICATION_REFERENCE=",
        f"OAP_CODING_ARGV_JSON={json.dumps(coding_argv or [])}",
        f"OAP_STRATEGIC_ARGV_JSON={json.dumps(strategic_argv or [])}",
        "OAP_CODING_HOME=",
        "OAP_STRATEGIC_HOME_CONFIG=",
    ]
    for k, v in (extra or {}).items():
        lines.append(f"{k}={v}")
    p = Path(home) / "runtime.env"
    Path(home).mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines) + "\n")
    p.chmod(0o600)
    return p


# ---------------------------------------------------------------- orders


def order_meta(
    oid: str = "001-a",
    slug: str = "canary",
    base_sha: str = None,
    branch: str = None,
    pr_number: int = None,
    pr_mode: str = None,
    state: str = "FINAL",
    previous_round: str = None,
    issue_number: int = 1,
    repo: str = REPO_ID,
    reqs: list = None,
    prov: list = None,
    allowed: list = None,
    tests: list = None,
    decision: str = "D0",
    target_gate: str = "M-CONVERSION",
    gov: str = "0" * 40,
    **over,
):
    n, rnd = oid.split("-")
    meta = {
        "schema_version": 1,
        "kind": "order",
        "id": oid,
        "objective": int(n),
        "round": rnd,
        "slug": slug,
        "state": state,
        "repo": repo,
        "base_branch": "main",
        "base_sha": base_sha or "0" * 40,
        "issue_number": issue_number,
        "branch": branch or (f"oap/{oid}"),
        "pr_mode": pr_mode or ("CREATE_OR_RESUME" if rnd == "a" else "AMEND"),
        "pr_number": pr_number,
        "previous_round": previous_round,
        "provenance": prov
        or [
            {"marker": "H", "source": "fixture human request", "section_or_evidence": "fixture"},
            {"marker": "I", "source": "fixture inspection", "section_or_evidence": "fixture HEAD"},
        ],
        "requirements": reqs or ["SAR-001"],
        "governance_revision": gov,
        "source_hashes": {"PLAN.md": "0" * 64},
        "allowed_paths": allowed or ["oap/WORKFLOW-CANARY.md"],
        "forbidden_resources": ["deployment", "credentials"],
        "decision_class": decision,
        "expected_report_path": f"oap/reports/{oid}-{slug}.md",
        "tests": tests or ["python3 -m unittest discover -s tests/oap -p 'test_*.py' -v"],
        "target_gate": target_gate,
    }
    meta.update(over)
    return meta


def dha_none_body(oid: str = "001-a") -> str:
    return (
        f"# {oid} — fixture canary\n\n"
        "Implement exactly the ordered path with fixture evidence only.\n\n"
        "## Deferred human adjudication\n\n"
        "- Decision: NONE\n"
    )


def make_order_file(
    tmp: Path,
    oid: str = "001-a",
    base_sha: str = None,
    body: str = None,
    meta: dict = None,
    name: str = None,
) -> Path:
    m = meta or order_meta(oid=oid, base_sha=base_sha)
    b = body if body is not None else dha_none_body(oid)
    text = f"<!-- OAP-META\n{json.dumps(m, indent=1)}\n-->\n{b}"
    p = Path(tmp) / (name or ("{}-{}-order.md".format(oid, m["slug"])))
    p.write_text(text)
    return p


REQUIRED_HEADINGS = [
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


def make_crit_entry(
    crit_id: str = "CRIT-0001",
    intro: str = "PR 28 / objective 001-a",
    omit: list = None,
    extra_text: str = "",
) -> str:
    omit = omit or []
    lines = [
        f"## {crit_id} — fixture DHA admission",
        "",
        "- **Status:** OPEN",
        "",
        f"Introduced by:** {intro}",
        "",
    ]
    for h in REQUIRED_HEADINGS:
        if h in omit:
            continue
        lines.append(h)
        lines.append(f"Fixture {h} detail (no placeholder fields).")
        lines.append("")
    lines.append("Strategic attestation: ALL FIVE CRITICAL-ENTRY CONDITIONS SATISFIED.")
    lines.append(extra_text)
    return "\n".join(lines).rstrip("\n") + "\n"


def dha_append_body(
    crit_id: str = "CRIT-0001", payload: str = None, digest: str = None, oid: str = "001-a"
) -> str:
    payload = payload if payload is not None else make_crit_entry(crit_id)
    pb = payload.encode("utf-8")
    digest = digest or oaplib.sha256_hex(pb)
    return (
        f"# {oid} — fixture DHA round\n\n"
        "Ordered register admission with exact bytes.\n\n"
        "## Deferred human adjudication\n\n"
        f"- Decision: APPEND {crit_id}\n\n"
        "## Exact CRITICAL payload\n"
        "```text\n"
        f"{payload}```\n"
        "\n"
        f"Payload SHA-256: {digest}\n"
    )


def make_register(entries: list) -> bytes:
    """entries: list of raw entry texts (starting with '## CRIT-')."""
    base = (
        "# CRITICAL — DHA register (fixture)\n\n"
        "Append-only. Fenced templates below are examples, not live entries.\n\n"
        "```text\n## CRIT-0099 — fenced template example (ignored)\n```\n\n"
    )
    return (base + "\n".join(entries)).encode("utf-8")


def activate_order(
    repo: Path, oid: str = "001-a", slug: str = "canary", branch: str = None, pr_number: int = None
) -> dict:
    """Durable fixture state: valid FINAL order file + exact-ID pointer."""
    repo = Path(repo)
    meta = order_meta(
        oid=oid,
        slug=slug,
        base_sha=head(repo),
        branch=branch or (f"oap/{oid}"),
        pr_number=pr_number,
    )
    body = dha_none_body(oid)
    text = f"<!-- OAP-META\n{json.dumps(meta, indent=1)}\n-->\n{body}"
    orders = repo / "oap" / "orders"
    orders.mkdir(parents=True, exist_ok=True)
    (orders / (f"{oid}-{slug}.md")).write_text(text)
    (repo / "oap" / "active").write_text(oid + "\n")
    return meta


# ---------------------------------------------------------------- materialization


def file_entry(
    rel: str,
    data: bytes,
    kind: str = None,
    pre_sha256: str = None,
    backup: str = None,
    mode: int = None,
) -> dict:
    e = {"rel": rel, "content_sha256": oaplib.sha256_hex(data), "bytes": data}
    if kind:
        e["kind"] = kind
    if pre_sha256:
        e["pre_sha256"] = pre_sha256
    if backup:
        e["backup"] = backup
    if mode:
        e["mode"] = mode
    return e


def _sha256(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


def make_manifest_root(
    tmp: Path,
    entries: list,
    dirs: list = None,
    fifos: list = None,
    manifest_sha256: dict = None,
    previous_generated: dict = None,
) -> Path:
    cr = Path(tmp) / "content2"
    for e in entries:
        p = cr / e["rel"]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(e.get("bytes", b""))
    serializable = []
    for e in entries:
        f = {k: v for k, v in e.items() if k != "bytes"}
        f["content_sha256"] = f.get("content_sha256") or _sha256(e.get("bytes", b""))
        serializable.append(f)
    man = {
        "schema_version": 1,
        "generation": "1",
        "files": serializable,
        "dirs": dirs or [],
        "fifos": fifos or [],
    }
    if manifest_sha256:
        man["manifest_sha256"] = manifest_sha256
    if previous_generated:
        man["previous_generated"] = previous_generated
    (cr / ".oap-materialization.json").write_text(json.dumps(man, indent=1))
    return cr


def run_engine(
    content_root,
    repo,
    home,
    bootstrap,
    apply: bool = False,
    refresh: bool = False,
    timeout: float = 90.0,
):
    args = [
        "--content-root",
        str(content_root),
        "--repo",
        str(repo),
        "--strategic-home",
        str(home),
        "--bootstrap-root",
        str(bootstrap),
    ]
    if refresh:
        args.append("--refresh")
    elif apply:
        args.append("--apply")
    args.append("--json")
    return run_cli("oap_materialize.py", args, timeout=timeout, expect_json=True)


# ---------------------------------------------------------------- snapshots


def snapshot(path, with_mtime: bool = False) -> dict:
    out = {}
    p = Path(path)
    if not p.exists():
        return out
    for f in sorted(p.rglob("*")):
        key = str(f.relative_to(p))
        if f.is_symlink():
            out[key] = ("symlink", os.readlink(str(f)))
        elif f.is_dir():
            continue
        else:
            st = f.lstat()
            if stat.S_ISFIFO(st.st_mode):
                out[key] = ("fifo",)
                continue
            val = (stat.S_IMODE(st.st_mode), f.read_bytes())
            if with_mtime:
                val = val + (st.st_mtime_ns,)
            out[key] = val
    return out


def snapshot_new_paths(before: dict, after: dict) -> list:
    return sorted(set(after) - set(before))


# ---------------------------------------------------------------- fifos / threads


def make_fifo(path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    oaplib.ensure_fifo(str(path), 0o600)
    return path


def fifo_consumer_thread(fifo_path, holder: list, timeout: float = 30.0, owner: str = ""):
    def run():
        holder.append(
            oaplib.fifo_receive(
                str(fifo_path), timeout=timeout, lease_owner=owner or f"test-{os.getpid()}"
            )
        )

    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t


def fifo_write(fifo_path: Path, data: bytes = b"OK", fragment: bool = False) -> None:
    fd = os.open(str(fifo_path), os.O_WRONLY)
    try:
        if fragment and data:
            os.write(fd, data[:1])
            time.sleep(0.05)
            os.write(fd, data[1:])
        else:
            while data:
                n = os.write(fd, data)
                data = data[n:]
    finally:
        os.close(fd)


def unique_name(prefix: str) -> str:
    return f"{prefix}-{os.getpid()}-{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------- tmux


def shutil_which(name: str):
    for d in os.environ.get("PATH", "").split(os.pathsep):
        p = Path(d) / name
        if p.is_file() and os.access(str(p), os.X_OK):
            return str(p)
    return None


TMUX = shutil_which("tmux")


def tmux_socket() -> str:
    return unique_name("oaptmx")


def tmux_run(socket: str, extra: list, timeout: float = 20.0):
    if not TMUX:
        return 127, "", "tmux not installed"
    p = subprocess.run([TMUX, "-L", socket] + list(extra), capture_output=True, timeout=timeout)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


# ---------------------------------------------------------------- remote fixture


def write_remote_state(tmp: Path, state: dict) -> str:
    p = Path(tmp) / (f"remote-{uuid.uuid4().hex[:6]}.json")
    p.write_text(json.dumps(state))
    return str(p)
