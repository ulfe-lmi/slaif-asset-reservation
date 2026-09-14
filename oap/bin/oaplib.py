#!/usr/bin/env python3
"""Shared stdlib library for the Concentrated OAP helpers (SLAIF existing-repo profile).

Standard library only. No model calls, no network writes. Read-only remote operations
are `git ls-remote` when a caller explicitly asks for remote reconciliation, and the two
fixed read-only `gh` templates (`gh pr view`, `gh pr list`) for PR identity; tests inject
an explicit fixture adapter instead (OAP_REMOTE_ADAPTER_FILE).
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import select
import stat
import subprocess
import time
from pathlib import Path

# ---------------------------------------------------------------------- errors


class OAPError(Exception):
    """Bounded, redactable failure."""


class ConflictError(OAPError):
    """Existing state conflicts with an expected identity; nothing was replaced."""


class ValidationError(OAPError):
    """Input violates a schema/grammar/contract."""


class RefusedError(OAPError):
    """Operation refused (role, authority, ownership, type)."""


STATUSES = ("PASSED", "FAILED", "SKIPPED", "NOT RUN", "BLOCKED", "PENDING", "MISSING")

# ---------------------------------------------------------------------- hashing


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path) -> str:
    return sha256_hex(Path(path).read_bytes())


def git_blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\x00" % len(data) + data).hexdigest()


def read_file(path) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


# ---------------------------------------------------------------------- IDs / rounds

ID_RE = re.compile(r"^[0-9]{3}-[a-z]{1,2}$")
OBJECTIVE_RE = re.compile(r"^([0-9]{3})-([a-z]{1,2})$")


def valid_id(s) -> bool:
    return (
        isinstance(s, str)
        and ID_RE.fullmatch(s) is not None
        and round_value(s.split("-", 1)[1]) is not None
    )


def round_value(r: str):
    """Numeric progression value: a=1 .. z=26, aa=27 .. zz=702; None if invalid."""
    if not isinstance(r, str) or not re.fullmatch(r"[a-z]{1,2}", r):
        return None
    if len(r) == 1:
        return ord(r) - 96
    v = (ord(r[0]) - 96) * 26 + (ord(r[1]) - 96)
    return v if 27 <= v <= 702 else None


def next_round(r: str):
    v = round_value(r)
    if v is None or v >= 702:
        return None
    v += 1
    if v <= 26:
        return chr(96 + v)
    first = (v - 27) // 26 + 1
    second = (v - 27) % 26 + 1
    return chr(96 + first) + chr(96 + second)


def prev_round(r: str):
    v = round_value(r)
    if v is None or v <= 1:
        return None
    v -= 1
    if v <= 26:
        return chr(96 + v)
    first = (v - 27) // 26 + 1
    second = (v - 27) % 26 + 1
    return chr(96 + first) + chr(96 + second)


def split_id(i: str):
    m = OBJECTIVE_RE.fullmatch(i or "")
    return (int(m.group(1)), m.group(2)) if m else (None, None)


# ---------------------------------------------------------------------- path safety


def canonical(p) -> str:
    return os.path.realpath(os.fspath(p))


def _owner_ok(st: os.stat_result, allow_root_owned: bool = True) -> bool:
    me = os.getuid()
    if st.st_uid == me:
        return True
    if not allow_root_owned or st.st_uid != 0:
        return False
    mode = st.st_mode
    if (mode & 0o022) == 0:
        return True
    # standard sticky world-writable temporary directories (/tmp, /var/tmp)
    return stat.S_ISDIR(mode) and (mode & 0o1777) == 0o1777


def validate_roots(repo_root, strategic_home, bootstrap_root, create_missing=True) -> list:
    """Return a list of error strings; empty means the three roots are safe and usable.

    Every canonical root must be (or be creatable as) a real directory; symlink roots and
    symlink/file/foreign-owned ancestors are refused; identical or nested roots are refused.
    Ancestor safety is checked on the ORIGINAL (unresolved) path, because a symlinked
    staging parent resolves away and would otherwise be invisible.
    """
    errs = []
    roots = {
        "repo": os.fspath(repo_root),
        "strategic": os.fspath(strategic_home),
        "bootstrap": os.fspath(bootstrap_root),
    }
    canon = {}
    for name, p in roots.items():
        if not p:
            errs.append(f"{name} root empty")
            continue
        if Path(p).is_symlink():
            errs.append(f"{name} root is a symlink: {p}")
            continue
        cp = canonical(p)
        if cp == "/":
            errs.append(f"{name} root is filesystem root")
            continue
        if Path(cp).exists() and not Path(cp).is_dir():
            errs.append(f"{name} root is not a directory: {p}")
            continue
        canon[name] = cp
    for name in sorted(canon):
        raw = os.path.abspath(roots[name])
        cp = canon[name]
        # the existing root itself (resolved identity)
        try:
            st = os.lstat(cp)
        except OSError:
            st = None
        if st is not None:
            if not _owner_ok(st):
                errs.append(f"{name} root is foreign-owned: {cp}")
            if not stat.S_ISDIR(st.st_mode):
                errs.append(f"{name} root is not a directory: {cp}")
        else:
            if not create_missing:
                errs.append(f"{name} root missing and creation not requested: {cp}")
        # walk the ORIGINAL path from its parent up to /: symlink/file/foreign ancestors
        probe = Path(raw).parent
        while True:
            try:
                if probe.is_symlink():
                    errs.append(f"{name} root has symlink ancestor: {probe}")
                    break
            except OSError:
                break
            if probe.exists() and not probe.is_dir():
                errs.append(f"{name} root ancestor is a regular file: {probe}")
                break
            try:
                ast = probe.lstat()
            except OSError:
                ast = None
            if ast is not None and not _owner_ok(ast):
                errs.append(f"{name} root has foreign-owned ancestor: {probe}")
                break
            if not probe.exists():
                break  # nothing further above an absent parent to verify here
            if probe == probe.parent:
                break
            probe = probe.parent
        if st is None and create_missing:
            par = Path(raw).parent
            try:
                if par.exists() and not os.access(str(par), os.W_OK):
                    errs.append(f"{name} root parent not writable: {par}")
            except OSError:
                pass
    names = sorted(canon)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = canon[names[i]], canon[names[j]]
            if a == b:
                errs.append(f"roots {names[i]} and {names[j]} are identical: {a}")
            elif a + "/" in b + "/" or b + "/" in a + "/":
                errs.append(f"roots {names[i]} and {names[j]} are nested")
    return errs


def safe_child(base: str, rel: str) -> str:
    base_c = canonical(base)
    target = canonical(os.path.join(base_c, rel))
    if target != base_c and not target.startswith(base_c + os.sep):
        raise RefusedError(f"path escapes root: {rel}")
    return target


def ensure_dir(path, mode: int = 0o755) -> str:
    """Create a directory (and missing parents, safely). Returns 'created'/'existing'."""
    p = Path(path)
    if p.exists():
        if p.is_symlink() or not p.is_dir():
            raise ConflictError(f"expected directory: {path}")
        return "existing"
    parent = p.parent
    if not parent.exists():
        ensure_dir(str(parent))
    if parent.is_symlink():
        raise RefusedError(f"unsafe symlink parent: {parent}")
    try:
        p.mkdir(mode=mode)
    except FileExistsError:
        if not p.is_dir() or p.is_symlink():
            raise ConflictError(f"expected directory: {path}") from None
        return "existing"
    return "created"


def ensure_private_dir(path) -> str:
    """Manifest-owned private directory: 0700 whether created or already present
    (parent chains created by file writes default to 0755 and must be tightened)."""
    p = Path(path)
    res = ensure_dir(str(p), mode=0o700)
    os.chmod(p, 0o700)
    return res


def fsync_dir(path) -> None:
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_write(
    path, data: bytes, mode: int = 0o644, expect: bytes | None = None, expect_absent: bool = False
) -> str:
    """Atomically install `data` at `path` with an expected-identity check.

    expect=None  -> no prior-identity constraint (still refuses symlinks)
    expect=bytes -> the file, if present, must byte-equal these (else ConflictError)
    Returns 'created' | 'replaced' | 'identical'. Identical reruns perform no write and
    preserve metadata.
    """
    p = Path(path)
    if p.is_symlink():
        raise RefusedError(f"refusing to write through symlink: {path}")
    if p.exists():
        if not p.is_file():
            raise ConflictError(f"expected regular file: {path}")
        cur = p.read_bytes()
        if cur == data:
            return "identical"
        if expect_absent:
            raise ConflictError(f"file unexpectedly exists: {path}")
        if expect is not None and cur != expect:
            raise ConflictError(f"identity mismatch (not the expected previous bytes): {path}")
    parent = p.parent
    ensure_dir(str(parent))
    if parent.is_symlink():
        raise RefusedError(f"unsafe symlink parent: {parent}")
    tmp = p.with_name(p.name + f".oap-tmp-{os.getpid()}")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(str(tmp), str(p))
    except BaseException:
        try:
            os.unlink(str(tmp))
        except OSError:
            pass
        raise
    fsync_dir(str(parent))
    st = p.stat()
    want = stat.S_IMODE(mode)
    if stat.S_IMODE(st.st_mode) != want:
        os.chmod(p, want)
    return "created" if not p.exists() else "replaced"


def ensure_fifo(path, mode: int = 0o600) -> str:
    p = Path(path)
    if p.is_symlink():
        raise RefusedError(f"refusing symlink fifo: {path}")
    if p.exists():
        st = p.lstat()
        if not stat.S_ISFIFO(st.st_mode):
            raise ConflictError(f"expected FIFO: {path}")
        if st.st_uid != os.getuid():
            raise RefusedError(f"foreign-owned FIFO: {path}")
        return "existing"
    ensure_dir(str(p.parent), mode=0o700)
    os.mkfifo(str(p), mode)
    os.chmod(p, mode)
    return "created"


def snapshot_tree(root) -> dict:
    out = {}
    r = Path(root)
    if not r.exists():
        return out
    for p in sorted(r.rglob("*")):
        if p.is_symlink():
            out[p.relative_to(r).as_posix()] = ("symlink",)
            continue
        if p.is_dir():
            continue
        st = p.stat()
        out[p.relative_to(r).as_posix()] = (
            st.st_size,
            stat.S_IMODE(st.st_mode),
            st.st_mtime_ns,
            sha256_hex(p.read_bytes()),
        )
    return out


# ---------------------------------------------------------------------- pointer


def read_pointer(path) -> dict:
    p = Path(path)
    if not p.exists():
        return {"state": "ABSENT", "id": None, "error": None}
    if p.is_symlink() or not p.is_file():
        return {"state": "CORRUPT", "id": None, "error": "pointer is not a regular file"}
    data = p.read_bytes()
    if data == b"":
        return {"state": "CORRUPT", "id": None, "error": "empty pointer"}
    if not data.endswith(b"\n") or data.count(b"\n") != 1:
        return {"state": "CORRUPT", "id": None, "error": "pointer is not exactly ID+LF"}
    oid = data[:-1].decode("utf-8", "replace")
    if not valid_id(oid):
        return {"state": "CORRUPT", "id": None, "error": f"pointer ID invalid: {oid!r}"}
    return {"state": "ACTIVE", "id": oid, "error": None}


def write_pointer_atomic(path, oid: str) -> str:
    if not valid_id(oid):
        raise ValidationError(f"invalid pointer ID: {oid!r}")
    return atomic_write(path, (oid + "\n").encode("utf-8"), mode=0o644, expect_absent=False)


# ---------------------------------------------------------------------- orders

META_OPEN = "<!-- OAP-META\n"
META_CLOSE = "\n-->"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")

# Slim final order schema (015-a): exactly nine meta fields plus the DHA body
# declaration = ten fields. Published superset orders (e.g. the 25-field
# generation-1 orders) remain valid: unknown extra keys pass through unvalidated.
ORDER_SLIM = {
    "id": str,
    "round": str,
    "base_sha": str,
    "issue_number": int,
    "branch": str,
    "pr_mode": str,
    "previous_round": (str, type(None)),
    "allowed_paths": list,
    "forbidden_resources": list,
}

# Normalized display values for slim orders, so protected consumers that read
# superseded keys (e.g. check_state.py) keep working. These are NOT enforced
# schema fields.
ORDER_NORM_DEFAULTS = {"pr_number": None, "state": "FINAL"}


def _full_hex(v) -> bool:
    return isinstance(v, str) and bool(HEX40.fullmatch(v) or HEX64.fullmatch(v))


def parse_order(data: bytes, strict_final: bool = False):
    """Parse an OAP order. Returns (meta, body, errors).

    Slim schema: the nine ORDER_SLIM meta fields plus exactly one DHA body
    declaration. Extra superset keys (generation-1 25-field orders) are accepted
    and passed through unchanged; a superset 'state' key must be FINAL when
    strict_final is set.
    """
    errs = []
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None, "", ["order is not valid UTF-8"]
    if "\r" in text:
        errs.append("order must use LF line endings")
    if not text.startswith(META_OPEN):
        errs.append("missing leading OAP-META block")
        return None, text, errs
    end = text.find(META_CLOSE, len(META_OPEN))
    if end < 0:
        return None, text, errs + ["unterminated OAP-META block"]
    meta_text = text[len(META_OPEN) : end]
    body = text[end + len(META_CLOSE) :]
    try:
        meta = json.loads(meta_text)
        if not isinstance(meta, dict):
            raise ValueError("meta not an object")
    except (ValueError, TypeError) as e:
        return None, body, errs + [f"OAP-META is not valid JSON: {e.__class__.__name__}"]
    for key, _typ in ORDER_SLIM.items():
        if key not in meta:
            errs.append(f"meta missing key: {key}")
    if not errs:
        for key, typ in ORDER_SLIM.items():
            if not isinstance(meta[key], typ) or (typ is int and isinstance(meta[key], bool)):
                errs.append(f"meta {key} has wrong type")
        if errs:
            return meta, body, errs
        if not valid_id(meta["id"]):
            errs.append("bad ID grammar: {!r}".format(meta["id"]))
        elif meta["id"].split("-", 1)[1] != meta["round"]:
            errs.append("ID round part must equal round")
        if not _full_hex(meta["base_sha"]):
            errs.append("base_sha must be a full object ID")
        if not isinstance(meta["issue_number"], int) or meta["issue_number"] <= 0:
            errs.append("issue_number must be a positive integer")
        if not (isinstance(meta["branch"], str) and meta["branch"].strip()):
            errs.append("branch must be a nonempty string")
        if meta["pr_mode"] not in ("CREATE_OR_RESUME", "AMEND"):
            errs.append("pr_mode invalid")
        if meta["round"] == "a":
            if meta["pr_mode"] != "CREATE_OR_RESUME":
                errs.append("round a requires pr_mode CREATE_OR_RESUME")
            if meta["previous_round"] is not None:
                errs.append("round a must have previous_round null")
        else:
            if meta["pr_mode"] != "AMEND":
                errs.append("correction rounds require pr_mode AMEND")
            if not isinstance(meta["previous_round"], str) or not valid_id(meta["previous_round"]):
                errs.append("previous_round must be a valid ID")
        if (
            not isinstance(meta["allowed_paths"], list)
            or not meta["allowed_paths"]
            or not all(isinstance(x, str) and x for x in meta["allowed_paths"])
        ):
            errs.append("allowed_paths must be a nonempty list of paths")
        if not isinstance(meta["forbidden_resources"], list) or not all(
            isinstance(x, str) for x in meta["forbidden_resources"]
        ):
            errs.append("forbidden_resources must be a list of strings")
        if strict_final and meta.get("state") is not None and meta["state"] != "FINAL":
            errs.append(
                "order state must be FINAL for publication (found {!r})".format(meta["state"])
            )
        dha = extract_dha(body)
        if dha["error"]:
            errs.append(dha["error"])
        unres = unresolved_finalization(body)
        if unres:
            errs.append("genuine unresolved finalization field(s): {}".format(", ".join(unres[:5])))
    # normalized display values for superseded keys (not part of the slim schema)
    for key, default in ORDER_NORM_DEFAULTS.items():
        meta.setdefault(key, default)
    return meta, body, errs


DHA_HEADER = "## Deferred human adjudication"
DHA_NONE = "- Decision: NONE"
DHA_APPEND_RE = re.compile(r"^- Decision: APPEND (CRIT-[0-9]{4})\s*$")
UNRESOLVED_RES = re.compile(r"(?i)\b(TODO|TBD)\b|<unknown|UNRESOLVED_METADATA|FIXME")


def _strip_fenced(text: str) -> list:
    """Return list of (line, in_fence) for body scanning; fences are ``` or ~~~."""
    out = []
    fence = None
    for line in text.splitlines():
        stripped = line.lstrip()
        if fence is None and (stripped.startswith("```") or stripped.startswith("~~~")):
            fence = stripped[:3]
            out.append((line, True))
            continue
        if fence is not None:
            out.append((line, True))
            if stripped.startswith(fence):
                fence = None
            continue
        out.append((line, False))
    return out


def unresolved_finalization(body: str) -> list:
    """Genuine unresolved fields outside code fences and inline backtick literals."""
    found = []
    for line, in_fence in _strip_fenced(body):
        if in_fence:
            continue
        no_inline = re.sub(r"`[^`]*`", "", line)
        if UNRESOLVED_RES.search(no_inline):
            found.append(line.strip()[:80])
    return found


def extract_dha(body: str) -> dict:
    """Exactly one DHA declaration; returns decision + APPEND payload details."""
    headers = [i for i, ln in enumerate(body.splitlines()) if ln.strip() == DHA_HEADER]
    if len(headers) != 1:
        return {
            "decision": None,
            "error": (
                "expected exactly one '## Deferred human adjudication' "
                f"declaration (found {len(headers)})"
            ),
        }
    lines = body.splitlines()
    start = headers[0] + 1
    decision = None
    for ln in lines[start:]:
        s = ln.strip()
        if not s:
            continue
        if s.startswith("#"):
            break
        if s == DHA_NONE:
            if decision is not None:
                return {"decision": None, "error": "multiple DHA decision lines"}
            decision = "NONE"
        m = DHA_APPEND_RE.fullmatch(s)
        if m:
            if decision is not None:
                return {"decision": None, "error": "multiple DHA decision lines"}
            decision = "APPEND:" + m.group(1)
        break
    if decision is None:
        return {"decision": None, "error": "DHA declaration has no decision line"}
    if decision == "NONE":
        return {"decision": "NONE", "payload": None, "error": None}
    # find the exact payload section after the DHA header
    sec = re.search(r"## Exact CRITICAL payload\s*\n", body)
    if not sec:
        return {
            "decision": decision,
            "payload": None,
            "error": "APPEND requires '## Exact CRITICAL payload' section",
        }
    rest = body[sec.end() :]
    fence = re.match(r"```text\s*\n", rest)
    if not fence:
        return {
            "decision": decision,
            "payload": None,
            "error": "payload must be a fenced text block",
        }
    rest = rest[fence.end() :]
    close = rest.find("\n```")
    if close < 0:
        return {"decision": decision, "payload": None, "error": "unterminated payload fence"}
    payload = rest[: close + 1].encode("utf-8")  # includes final LF
    if not payload.endswith(b"\n"):
        return {"decision": decision, "payload": None, "error": "payload must end with LF"}
    tail = rest[close + 4 :]
    sha_line = re.search(r"^Payload SHA-256:\s*([0-9a-f]{64})\s*$", tail, flags=re.M)
    if not sha_line:
        return {"decision": decision, "payload": None, "error": "missing 'Payload SHA-256:' line"}
    if sha_line.group(1) != sha256_hex(payload):
        return {
            "decision": decision,
            "payload": payload,
            "error": "payload SHA-256 does not match payload bytes",
        }
    if "ALL FIVE CRITICAL-ENTRY CONDITIONS SATISFIED" not in payload.decode("utf-8", "replace"):
        return {
            "decision": decision,
            "payload": payload,
            "error": "missing all-five attestation in payload",
        }
    return {"decision": decision, "payload": payload, "error": None}


# ---------------------------------------------------------------------- register

CRIT_HEAD = re.compile(r"^## (CRIT-[0-9]{4}) — ", re.M)
EVIDENCE_HEAD = re.compile(r"^## EVIDENCE APPEND — (CRIT-[0-9]{4}) — [0-9a-f-]{36}\s*$", re.M)
HUMAN_HEAD = re.compile(r"^## HUMAN ADJUDICATION — (CRIT-[0-9]{4}) — \d{4}-\d{2}-\d{2}\s*$", re.M)
HUMAN_VALUES = ("ACCEPTED", "REJECTED", "CHANGE REQUIRED", "DEFERRED")


def _top_level_lines(text: str):
    for line, in_fence in _strip_fenced(text):
        if not in_fence:
            yield line


def parse_register(data: bytes):
    """Parse live CRITICAL entries (fenced templates ignored). Returns entries, errors."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return [], ["register not UTF-8"]
    entries = []
    errs = []
    seen = set()
    # line-based so fenced blocks are excluded
    pos = 0
    lines = text.splitlines()
    fence = None
    for i, line in enumerate(lines):
        st = line.lstrip()
        if fence is None and (st.startswith("```") or st.startswith("~~~")):
            fence = st[:3]
            continue
        if fence is not None:
            if st.startswith(fence):
                fence = None
            continue
        m = CRIT_HEAD.match(line)
        if m:
            cid = m.group(1)
            if cid in seen:
                errs.append(f"duplicate CRIT ID: {cid}")
            seen.add(cid)
            entries.append({"id": cid, "line": i, "start": pos})
            pos = None
    if entries:
        ids = [e["id"] for e in entries]
        nums = [int(i.split("-")[1]) for i in ids]
        if nums != list(range(1, len(nums) + 1)):
            errs.append("CRIT IDs are not monotonic from CRIT-0001")
    return entries, errs


def next_crit_id(data: bytes):
    entries, errs = parse_register(data)
    if errs:
        return None
    return f"CRIT-{len(entries) + 1:04d}"


def payload_at(data: bytes, payload: bytes) -> bool:
    """True when the exact full payload already exists as the trailing live entry."""
    return (
        data.endswith(payload)
        and b"\n## " in data[: -len(payload)]
        or (data == payload and payload.startswith(b"## CRIT-"))
    )


def parse_dispositions(data: bytes) -> dict:
    """Structural parse of human adjudication blocks. Verification is external."""
    text = data.decode("utf-8", "replace")
    out = {}
    fence = None
    lines = text.splitlines()
    cur = None
    for line in lines:
        st = line.lstrip()
        if fence is None and (st.startswith("```") or st.startswith("~~~")):
            fence = st[:3]
            continue
        if fence is not None:
            if st.startswith(fence):
                fence = None
            continue
        m = HUMAN_HEAD.match(line)
        if m:
            cur = m.group(1)
            out.setdefault(cur, []).append(
                {"value": None, "authority": None, "conditions": None, "evidence": None}
            )
            continue
        if cur:
            mv = re.match(r"^- Decision:\s*(.+?)\s*$", line)
            if mv:
                out[cur][-1]["value"] = mv.group(1)
            ma = re.match(r"^- Authority:\s*(.+?)\s*$", line)
            if ma:
                out[cur][-1]["authority"] = ma.group(1)
            mc = re.match(r"^- Conditions or required follow-up:\s*(.*)$", line)
            if mc:
                out[cur][-1]["conditions"] = mc.group(1).strip()
            me = re.match(r"^- Evidence/reference:\s*(.*)$", line)
            if me:
                out[cur][-1]["evidence"] = me.group(1).strip()
            if line.startswith("## "):
                cur = None
    return out


def gate_state(crit_id: str, data: bytes, verifier=None) -> dict:
    """Latest attributable disposition semantics. verifier(crit, disp)->bool (test injection)."""
    disps = parse_dispositions(data).get(crit_id, [])
    if not disps:
        return {
            "crit": crit_id,
            "cleared": False,
            "status": "PENDING",
            "detail": "no human disposition recorded",
        }
    last = disps[-1]
    if last["value"] not in HUMAN_VALUES:
        return {
            "crit": crit_id,
            "cleared": False,
            "status": "BLOCKED",
            "detail": "invalid disposition value {!r}".format(last["value"]),
        }
    verified = bool(verifier) and verifier(crit_id, last)
    if not verified:
        return {
            "crit": crit_id,
            "cleared": False,
            "status": "UNVERIFIED",
            "detail": "latest disposition {} lacks verified human provenance".format(last["value"]),
        }
    if last["value"] != "ACCEPTED":
        return {
            "crit": crit_id,
            "cleared": False,
            "status": "BLOCKED",
            "detail": "latest attributable disposition is {}".format(last["value"]),
        }
    return {
        "crit": crit_id,
        "cleared": True,
        "status": "CLEARED",
        "detail": "latest attributable ACCEPTED",
    }


# ---------------------------------------------------------------------- runtime.env

ENV_KEYS = {
    "OAP_PROFILE_VERSION": "int",
    "OAP_REPO_ROOT": "path",
    "OAP_STRATEGIC_HOME": "path",
    "OAP_REMOTE_REPOSITORY": "str",
    "OAP_BASE_BRANCH": "str",
    "OAP_ACCEPTED_GOVERNANCE_REVISION": "hex",
    "OAP_ACTIVATION_ENABLED": "bool",
    "OAP_DEVELOPMENT_MERGE_ENABLED": "bool",
    "OAP_AUTHORITY_REFERENCE": "path",
    "OAP_TARGET_MILESTONE": "str",
    "OAP_APPROVED_RUNTIME_REFERENCE": "path",
    "OAP_CODING_CLIENT": "str",
    "OAP_STRATEGIC_CLIENT": "str",
    "OAP_CODING_MODEL": "str",
    "OAP_STRATEGIC_MODEL": "str",
    "OAP_AUDIT_MODEL": "str",
    "OAP_PROVIDER": "str",
    "OAP_CLIENT_QUALIFICATION_REFERENCE": "path",
    "OAP_CODING_ARGV_JSON": "jsonlist",
    "OAP_STRATEGIC_ARGV_JSON": "jsonlist",
    "OAP_CODING_HOME": "path",
    "OAP_STRATEGIC_HOME_CONFIG": "path",
}


def parse_runtime_env(text: str):
    """Strict allowlisted parser. Never evaluates. Returns (values, errors)."""
    values = {}
    errs = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "$" in line or "`" in line or "\\" in line or ";" in line or "&" in line:
            errs.append(f"line {n}: interpolation/command-substitution characters are not data")
            continue
        if "=" not in line:
            errs.append(f"line {n}: not KEY=VALUE")
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        if key not in ENV_KEYS:
            errs.append(f"line {n}: key not allowlisted: {key}")
            continue
        if key in values:
            errs.append(f"line {n}: duplicate key: {key}")
            continue
        kind = ENV_KEYS[key]
        if kind == "bool":
            if val not in ("true", "false"):
                errs.append(f"line {n}: invalid boolean: {val!r}")
                continue
            values[key] = val == "true"
        elif kind == "int":
            if not val.isdigit():
                errs.append(f"line {n}: invalid integer: {val!r}")
                continue
            values[key] = int(val)
        elif kind == "hex":
            if val and not _full_hex(val):
                errs.append(f"line {n}: invalid object ID: {val!r}")
                continue
            values[key] = val
        elif kind == "jsonlist":
            try:
                v = json.loads(val)
                if not isinstance(v, list) or not all(isinstance(x, str) and x for x in v):
                    raise ValueError
            except ValueError:
                errs.append(f"line {n}: argv JSON must be a list of strings")
                continue
            for tok in v:
                if "$" in tok or "`" in tok or ";" in tok:
                    errs.append(f"line {n}: argv tokens must be plain strings")
            values[key] = v
        elif kind == "path":
            if val and not val.startswith("/"):
                errs.append(f"line {n}: path must be absolute or empty")
                continue
            values[key] = val
        else:
            values[key] = val
    return values, errs


def load_runtime_env(path) -> dict:
    values, errs = parse_runtime_env(Path(path).read_text("utf-8"))
    if errs:
        raise ValidationError("runtime.env errors: " + "; ".join(errs[:5]))
    return values


# ---------------------------------------------------------------------- FIFO

OK = b"OK"


def _fifo_owner_mode_ok(path, kind: str):
    st = os.lstat(path)
    if not stat.S_ISFIFO(st.st_mode):
        return "not a FIFO"
    if st.st_uid != os.getuid():
        return "foreign-owned FIFO"
    if st.st_mode & 0o077:
        return f"FIFO mode must be 0600 (found {stat.S_IMODE(st.st_mode):o})"
    return None


def fifo_send(path, timeout: float = 10.0) -> dict:
    """Send exactly OK. Handles partial write/EINTR; closes descriptor."""
    if os.path.islink(path):
        return {"ok": False, "error": "refusing symlink fifo", "code": 5}
    if not os.path.exists(path):
        return {"ok": False, "error": "missing FIFO", "code": 6}
    err = _fifo_owner_mode_ok(path, "send")
    if err:
        return {"ok": False, "error": err, "code": 5}
    deadline = time.monotonic() + timeout
    fd = None
    while True:
        try:
            fd = os.open(path, os.O_WRONLY | os.O_NONBLOCK)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                return {"ok": False, "error": "timeout waiting for reader", "code": 3}
            time.sleep(0.02)
        except OSError as e:
            if e.errno == errno.ENXIO:
                # FIFO with no connected reader yet: retry until the deadline
                if time.monotonic() >= deadline:
                    return {"ok": False, "error": "timeout waiting for reader", "code": 3}
                time.sleep(0.02)
                continue
            return {"ok": False, "error": f"open failed: {e.strerror}", "code": 4}
    buf = OK
    try:
        while buf:
            try:
                n = os.write(fd, buf)
                buf = buf[n:]
            except BlockingIOError:
                pass
            except InterruptedError:
                continue
            if buf and time.monotonic() >= deadline:
                return {"ok": False, "error": "timeout during write", "code": 3}
            if buf:
                time.sleep(0.01)
        return {"ok": True, "code": 0}
    finally:
        os.close(fd)


def fifo_receive(path, timeout: float = 5.0, lease_owner: str = "") -> dict:
    """Single-consumer receive of exactly OK; accumulates until EOF."""
    if os.path.islink(path):
        return {"ok": False, "error": "refusing symlink fifo", "code": 5, "data": None}
    if not os.path.exists(path):
        return {"ok": False, "error": "missing FIFO", "code": 6, "data": None}
    err = _fifo_owner_mode_ok(path, "receive")
    if err:
        return {"ok": False, "error": err, "code": 5, "data": None}
    lease = Path(str(path) + ".lease")
    lease_fd = None
    self_lease = False
    try:
        lease_fd = os.open(str(lease), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.write(
            lease_fd,
            json.dumps({"pid": os.getpid(), "start": time.time(), "owner": lease_owner}).encode(),
        )
    except FileExistsError:
        try:
            _self_info = json.loads(lease.read_text())
        except (ValueError, OSError):
            _self_info = {}
        if (
            lease_owner
            and _self_info.get("pid") == os.getpid()
            and _self_info.get("owner") == lease_owner
        ):
            self_lease = True
            lease_fd = None
        if not self_lease:
            try:
                info = json.loads(lease.read_text())
            except (ValueError, OSError):
                return {
                    "ok": False,
                    "error": "corrupt lease; reconcile manually",
                    "code": 5,
                    "data": None,
                }
            alive = True
            try:
                os.kill(int(info.get("pid", -1)), 0)
            except (ProcessLookupError, ValueError, TypeError):
                alive = False
            except PermissionError:
                alive = True
            if alive:
                return {
                    "ok": False,
                    "error": "another consumer holds the FIFO lease",
                    "code": 5,
                    "data": None,
                }
            try:
                os.unlink(str(lease))
            except OSError:
                return {"ok": False, "error": "stale lease not removable", "code": 5, "data": None}
            try:
                lease_fd = os.open(str(lease), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                os.write(
                    lease_fd,
                    json.dumps(
                        {"pid": os.getpid(), "start": time.time(), "owner": lease_owner}
                    ).encode(),
                )
            except FileExistsError:
                return {"ok": False, "error": "lease race lost", "code": 5, "data": None}
    try:
        # ONE read descriptor for the whole receive: a FIFO only reports EOF to
        # the fd that was open while the writer was connected, so the fd must
        # survive across polls. select readiness implies a writer is/was present;
        # a fresh fd with no writer never becomes readable.
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        except OSError as e:
            return {"ok": False, "error": f"open failed: {e.strerror}", "code": 4, "data": None}
        deadline = time.monotonic() + timeout
        data = b""
        try:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return {
                        "ok": False,
                        "error": "timeout before EOF",
                        "code": 3,
                        "data": data or None,
                    }
                r, _, _ = select.select([fd], [], [], max(0.0, remaining))
                if not r:
                    continue
                try:
                    chunk = os.read(fd, 4096)
                except BlockingIOError:
                    chunk = None
                except InterruptedError:
                    chunk = None
                if chunk == b"":
                    break  # all writers closed: clean EOF
                if chunk:
                    data += chunk
                    if len(data) > 2:
                        return {
                            "ok": False,
                            "error": "more than two bytes",
                            "code": 4,
                            "data": data,
                        }
        finally:
            os.close(fd)
        if data == OK:
            return {"ok": True, "code": 0, "data": data}
        if data == b"":
            return {"ok": False, "error": "zero bytes before EOF", "code": 4, "data": None}
        return {"ok": False, "error": f"invalid framing ({data!r})", "code": 4, "data": data}
    finally:
        if lease_fd is not None and not self_lease:
            os.close(lease_fd)
        if not self_lease:
            try:
                os.unlink(str(lease))
            except FileNotFoundError:
                pass


# ---------------------------------------------------------------------- git


def git(cwd, *args, timeout: float = 30.0, check: bool = False):
    try:
        p = subprocess.run(
            ["git", "-C", str(cwd)] + list(args), capture_output=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        raise OAPError("git timed out: {}".format(" ".join(args[:3]))) from None
    if check and p.returncode != 0:
        raise OAPError(
            "git {} failed: {}".format(
                " ".join(args[:3]), p.stderr.decode("utf-8", "replace")[:300]
            )
        )
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def git_head(cwd) -> dict:
    rc, out, _ = git(cwd, "rev-parse", "HEAD", check=False)
    if rc != 0:
        return {"head": None, "object_format": "sha1"}
    rc2, fmt, _ = git(cwd, "rev-parse", "--show-object-format")
    fmt = fmt.strip() or "sha1"
    return {"head": out.strip(), "object_format": fmt}


def git_remote_head(cwd, remote: str, ref: str, timeout: float = 20.0) -> dict:
    """Read-only ls-remote for one ref. Network failure -> BLOCKED, never a local pass."""
    rc, out, err = git(cwd, "ls-remote", remote, ref, timeout=timeout)
    if rc != 0:
        return {"ok": False, "head": None, "error": (err or "ls-remote failed").strip()[:200]}
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) == 2 and parts[1].strip() == ref:
            return {"ok": True, "head": parts[0].strip(), "error": None}
    return {"ok": False, "head": None, "error": f"ref not found: {ref}"}


# ---------------------------------------------------------------------- gh (read-only PR identity)

GH_PR_VIEW_FIELDS = "number,headRefName,headRefOid,state,mergedAt"
GH_PR_LIST_FIELDS = "number,headRefName,state,mergedAt"


def gh_owner_name(repo_root: str):
    """Parse owner/name from `git remote get-url origin` (read-only).

    Returns (owner_name, None) or (None, short factual reason).
    """
    rc, out, _ = git(repo_root, "remote", "get-url", "origin", timeout=20.0, check=False)
    if rc != 0:
        return None, "origin remote not configured"
    url = out.strip()
    if not url:
        return None, "origin remote URL empty"
    path = url
    if "://" in path:
        path = path.split("://", 1)[1]
        if "/" not in path:
            return None, "cannot parse owner/name from origin URL"
        path = path.split("/", 1)[1]
    elif path.count(":") == 1 and "@" in path.split(":", 1)[0]:
        path = path.split(":", 1)[1]
    path = path.strip("/")
    if path.endswith(".git"):
        path = path[: -len(".git")]
    parts = [part for part in path.split("/") if part]
    if len(parts) < 2:
        return None, "cannot parse owner/name from origin URL"
    return "/".join(parts[-2:]), None


def gh_readonly(repo_root: str, args: list, timeout: float = 30.0):
    """Run one READ-ONLY gh query; `args` must be a fixed read-only template.

    Returns (parsed JSON, None) or (None, short factual reason). Missing gh, non-zero
    exit, timeout or unparsable output never fabricate an identity.
    """
    owner_name, why = gh_owner_name(repo_root)
    if owner_name is None:
        return None, why
    try:
        p = subprocess.run(
            ["gh"] + list(args) + ["--repo", owner_name],
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=timeout,
        )
    except FileNotFoundError:
        return None, "gh executable not found"
    except OSError as e:
        return None, f"gh could not be executed: {e.strerror or e.__class__.__name__}"
    except subprocess.TimeoutExpired:
        return None, "gh timed out"
    if p.returncode != 0:
        return None, f"gh exited with code {p.returncode}"
    try:
        return json.loads(p.stdout.decode("utf-8", "replace")), None
    except ValueError:
        return None, "gh output not parseable as JSON"


def gh_pr_identity(obj, require_head: bool):
    """Map one gh PR JSON object to the FixtureRemote dict shape.

    Returns None when a required field is missing or mistyped; the caller reports
    unknown, never a fabricated value.
    """
    if not isinstance(obj, dict):
        return None
    for key in ("number", "headRefName", "state", "mergedAt"):
        if key not in obj:
            return None
    if require_head and "headRefOid" not in obj:
        return None
    try:
        number = int(obj["number"])
    except (TypeError, ValueError):
        return None
    branch = obj["headRefName"]
    state_raw = obj["state"]
    merged_at = obj["mergedAt"]
    if not isinstance(branch, str) or not branch:
        return None
    if not isinstance(state_raw, str) or not state_raw:
        return None
    if merged_at is not None and not isinstance(merged_at, str):
        return None
    head = obj.get("headRefOid")
    if require_head and (not isinstance(head, str) or not head):
        return None
    merged = merged_at is not None or state_raw.upper() == "MERGED"
    if merged:
        state = "merged"
    elif state_raw.upper() == "OPEN":
        state = "open"
    else:
        state = "closed"
    return {
        "number": number,
        "branch": branch,
        "head": head if isinstance(head, str) and head else None,
        "state": state,
        "merged": merged,
    }


# ---------------------------------------------------------------------- locks / leases


def acquire_lease(path, owner: str = ""):
    """Acquire an exclusive lease file. Returns fd or None (with existing owner)."""
    p = Path(path)
    ensure_dir(str(p.parent))
    try:
        fd = os.open(str(p), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        try:
            info = json.loads(p.read_text())
            try:
                os.kill(int(info.get("pid", -1)), 0)
                return None
            except (ProcessLookupError, ValueError, TypeError):
                pass
            except PermissionError:
                return None
        except Exception:
            return None
        try:
            os.unlink(str(p))
        except OSError:
            return None
        try:
            fd = os.open(str(p), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            return None
    os.write(fd, json.dumps({"pid": os.getpid(), "start": time.time(), "owner": owner}).encode())
    return fd


def release_lease(path, fd=None) -> None:
    if fd is not None:
        try:
            os.close(fd)
        except OSError:
            pass
    try:
        os.unlink(str(path))
    except FileNotFoundError:
        pass


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


# ---------------------------------------------------------------------- redaction

REDACT_PATTERNS = [
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{8,}"),
    re.compile(r"\bsar_[0-9a-f]{8,}_[A-Za-z0-9]{16,}\b"),
    re.compile(r"(?i)([a-z][a-z0-9+.\-]*://)[^/\s:@]+:[^@\s]+@"),
    re.compile(r"(?i)(secret[_-]?key|password|passwd|api[_-]?key|token)\s*[=:]\s*\S+"),
]


def redact(text: str) -> str:
    out = text
    for pat in REDACT_PATTERNS:
        out = pat.sub(lambda m: m.group(0)[:4] + "[REDACTED]" if m.lastindex else "[REDACTED]", out)
    return out


# ---------------------------------------------------------------------- state machine


def classify_state(repo_root, strategic_home=None, remote_adapter=None) -> dict:
    """OP-14 recovery classification from durable state. No mutation."""
    repo = Path(repo_root)
    ptr = read_pointer(repo / "oap" / "active")
    out = {"pointer": ptr, "state": "INACTIVE", "detail": "no active pointer", "order": None}
    if ptr["state"] == "CORRUPT":
        out["state"] = "CORRUPT"
        out["detail"] = ptr["error"]
        return out
    if ptr["state"] == "ABSENT":
        return out
    oid = ptr["id"]
    orders_dir = repo / "oap" / "orders"
    matches = [p for p in orders_dir.glob("*.md")] if orders_dir.is_dir() else []
    named = [p for p in matches if p.name.startswith(oid + "-")]
    if len(named) != 1:
        out["state"] = "CORRUPT"
        out["detail"] = f"pointer ID matches {len(named)} orders (need exactly 1)"
        return out
    order_path = named[0]
    meta, body, errs = parse_order(order_path.read_bytes())
    if errs:
        out["state"] = "CORRUPT"
        out["detail"] = "active order failed validation: " + errs[0]
        return out
    out["order"] = {"id": oid, "path": str(order_path), "meta": meta, "errors": []}
    report = repo / "oap" / "reports" / order_path.name
    journal = None
    if strategic_home:
        jp = Path(strategic_home) / "workorders" / "state.json"
        if jp.exists():
            try:
                journal = json.loads(jp.read_text())
            except ValueError:
                journal = {"unparseable": True}
    if journal and isinstance(journal, dict) and journal.get("unparseable"):
        out["state"] = "CORRUPT"
        out["detail"] = "private journal unparseable"
        return out
    events = (journal or {}).get("events", [])
    last_for = [e for e in events if e.get("order_id") == oid]
    if report.exists():
        out["state"] = "REPORT_LOCAL"
        out["detail"] = "local report present; remote verification required"
        if remote_adapter is not None:
            res = remote_adapter.report_remote(str(repo), oid, meta)
            if res.get("remote_head"):
                out["state"] = "REPORT_PUBLISHED"
                out["detail"] = "report verified on remote; lost response routes to strategy review"
        merged = (journal or {}).get("merged", {})
        if merged.get(oid):
            contradicted = False
            if remote_adapter is not None and out["order"]["meta"].get("branch"):
                pr = remote_adapter.pr_for_branch(str(repo), out["order"]["meta"]["branch"])
                if pr and not pr.get("merged"):
                    contradicted = True
            if contradicted:
                out["state"] = "REPORT_PUBLISHED"
                out["detail"] = (
                    "private journal claims merged but the remote PR for the branch "
                    "is still open; remote state wins, reconcile before acceptance"
                )
                return out
            out["state"] = "ACCEPTED_QUIESCENT"
            out["detail"] = "merged/accepted; pointer quiescent, not executable"
        return out
    consumed = any(e.get("kind") == "control_consumed" for e in last_for)
    invoked = any(e.get("kind") == "invoked" for e in last_for)
    if consumed and not invoked:
        out["state"] = "RUNNING_INTERRUPTED"
        out["detail"] = "control consumed without report; resume same ID/branch/PR"
        return out
    out["state"] = "ACTIVE_PENDING"
    out["detail"] = "valid final order is active; awaiting wake-up/invocation"
    return out


def round_frozen(repo_root, oid: str, remote_adapter=None) -> dict:
    """BA-32: a completed round cannot be mutated; next suffix on the same PR."""
    repo = Path(repo_root)
    orders = sorted((repo / "oap" / "orders").glob(oid + "-*.md"))
    if not orders:
        return {"frozen": False, "reason": "no order found"}
    meta, _, errs = parse_order(orders[0].read_bytes())
    if errs:
        return {"frozen": False, "reason": "order invalid: " + errs[0]}
    report = repo / "oap" / "reports" / orders[0].name
    if report.exists():
        return {
            "frozen": True,
            "reason": f"report published for {oid}; corrections use next suffix on the same PR",
            "next_round": next_round(meta["round"]),
            "same_pr": meta.get("pr_number"),
        }
    return {"frozen": False, "reason": "no report yet"}


# ---------------------------------------------------------------------- merge gate

REQUIRED_CI = ("quality", "test", "security", "container")
PASS_STATES = {"success"}
BAD_STATES = {"pending", "missing", "skipped", "cancelled", "unexecuted", "unknown", "failure"}


def evaluate_merge_gate(
    order_meta: dict,
    checks: dict,
    remote: dict,
    side_effects: dict,
    delegation: dict,
    head: str,
    reviewed_head: str,
) -> dict:
    """OP-11 evaluation. checks: {job: {"state":..., "head":...}} for the reviewed head."""
    problems = []
    if delegation.get("enabled") is not True or not delegation.get("attributable_reference"):
        problems.append("development-merge delegation not active/attributable")
    if not side_effects.get("checked"):
        problems.append("merge side effects not checked")
    if side_effects.get("d2_detected"):
        problems.append("D2 side effect detected on merge; delegated merge refused")
    if head != reviewed_head:
        problems.append("reviewed head changed; re-review required")
    for job in REQUIRED_CI:
        c = checks.get(job)
        if not c:
            problems.append(f"required check missing: {job}")
            continue
        if c.get("head") not in (reviewed_head, None) and c.get("head") != head:
            problems.append(f"check {job} not at reviewed head")
            continue
        if c.get("state") not in PASS_STATES:
            problems.append("check {} state {} is not success".format(job, c.get("state")))
    if order_meta.get("decision_class") == "D2_PREPARATION":
        problems.append("order is D2_PREPARATION; boundary actions need human authorization")
    if problems:
        return {"decision": "BLOCKED", "problems": problems}
    return {"decision": "REVIEW_PERMITTED", "problems": []}


# ---------------------------------------------------------------------- remote adapter


class FixtureRemote:
    """Explicit test-mode remote adapter. State loaded from a JSON file; never default."""

    def __init__(self, state: dict):
        self.state = state
        self.calls = []

    def _record(self, name, **kw):
        self.calls.append({"call": name, **kw})

    def remote_head(self, repo_root, ref):
        self._record("remote_head", ref=ref)
        heads = self.state.get("refs", {})
        if ref in heads:
            return {"ok": True, "head": heads[ref], "error": None}
        return {"ok": False, "head": None, "error": "ref not found in fixture"}

    def pr(self, repo_root, number):
        self._record("pr", number=number)
        for p in self.state.get("prs", []):
            if p.get("number") == number:
                return dict(p)
        return None

    def pr_for_branch(self, repo_root, branch):
        self._record("pr_for_branch", branch=branch)
        for p in self.state.get("prs", []):
            if p.get("branch") == branch:
                return dict(p)
        return None

    def create_pr(self, repo_root, branch, title):
        self._record("create_pr", branch=branch)
        if self.state.get("create_pr_blocked"):
            return None
        number = self.state.get("next_pr_number") or 1000
        self.state.setdefault("prs", []).append(
            {
                "number": number,
                "branch": branch,
                "state": "open",
                "head": self.state.get("refs", {}).get("main"),
                "created_at": time.time(),
                "merged": False,
                "title": title,
            }
        )
        self.state["next_pr_number"] = number + 1
        self.state["refs"][branch] = self.state.get("refs", {}).get("main")
        return {"number": number, "branch": branch, "state": "open"}

    def checks(self, head):
        self._record("checks", head=head)
        out = {}
        for job, spec in (self.state.get("checks") or {}).items():
            out[job] = {"state": spec.get("state", "missing"), "head": spec.get("head")}
        return out

    def report_remote(self, repo_root, oid, meta):
        self._record("report_remote", oid=oid)
        branch = meta.get("branch")
        pr = self.pr_for_branch(repo_root, branch) if branch else None
        refs = self.state.get("refs", {})
        head = None
        if branch:
            head = refs.get(branch) or refs.get("refs/heads/" + branch)
        if pr and pr.get("state") == "open" and head:
            return {"remote_head": head, "pr": pr["number"]}
        return {"remote_head": None, "pr": None}

    def mark_merged(self, number, head=None):
        for p in self.state.get("prs", []):
            if p.get("number") == number:
                p["state"] = "merged"
                p["merged"] = True
                if head:
                    p["head"] = head
                if p.get("branch") in self.state.get("refs", {}):
                    pass
        return True


def load_remote_adapter(repo_root):
    """Default adapter: read-only git ls-remote plus read-only gh PR identity.
    Fixture adapter only via explicit env file (test mode)."""
    env_file = os.environ.get("OAP_REMOTE_ADAPTER_FILE")
    if env_file:
        return FixtureRemote(json.loads(Path(env_file).read_text()))

    class GitRemote:
        def remote_head(self, repo_root, ref):
            return git_remote_head(repo_root, "origin", ref)

        def pr(self, repo_root, number):
            if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
                return {"unknown": True, "reason": "PR number must be a positive integer"}
            data, why = gh_readonly(
                repo_root,
                ["pr", "view", str(number), "--json", GH_PR_VIEW_FIELDS],
            )
            if why is not None:
                return {"unknown": True, "reason": why}
            mapped = gh_pr_identity(data, require_head=True)
            if mapped is None:
                return {"unknown": True, "reason": "gh PR view output missing required fields"}
            return mapped

        def pr_for_branch(self, repo_root, branch):
            data, why = gh_readonly(
                repo_root,
                ["pr", "list", "--state", "all", "--json", GH_PR_LIST_FIELDS],
            )
            if why is not None:
                return {"unknown": True, "reason": why}
            if not isinstance(data, list):
                return {"unknown": True, "reason": "gh PR list output is not a JSON list"}
            best = None
            rank = {"open": 0, "merged": 1, "closed": 2}
            for entry in data:
                if not isinstance(entry, dict) or entry.get("headRefName") != branch:
                    continue
                mapped = gh_pr_identity(entry, require_head=False)
                if mapped is None:
                    return {"unknown": True, "reason": "gh PR entry for branch missing fields"}
                if best is None or rank.get(mapped["state"], 3) < rank.get(best["state"], 3):
                    best = mapped
            return best

        def create_pr(self, repo_root, branch, title):
            raise RefusedError("PR creation requires separately authorized operational access")

        def checks(self, head):
            return {}

        def report_remote(self, repo_root, oid, meta):
            branch = meta.get("branch")
            if not branch:
                return {"remote_head": None, "pr": None}
            res = git_remote_head(repo_root, "origin", "refs/heads/" + branch)
            return {"remote_head": res.get("head"), "pr": None}

        def mark_merged(self, number, head=None):
            raise RefusedError("operational adapter cannot mutate remote state")

    return GitRemote()


def remote_adapter_is_test_mode() -> bool:
    return bool(os.environ.get("OAP_REMOTE_ADAPTER_FILE"))


def run_tmux(base: list, extra: list, timeout: float = 15.0):
    """Run a tmux command on an isolated -L socket. base includes ['tmux','-L',socket]."""
    try:
        p = subprocess.run(list(base) + list(extra), capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 124, "", "tmux timed out"
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")
