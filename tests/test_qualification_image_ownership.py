"""Construction-bound image ownership; fake contracts and real warm-cache proof."""

from __future__ import annotations

import os
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path

import pytest
from tests import test_branding as branding


def _default_clock():
    """Coarse wall-referenced logical clock (1-second tick, exact value)."""
    return float(int(time.time()))


class _LogicalTime:
    """Scoped stand-in for the branding module's ``time`` reference.

    Only ``time`` is logical; every other attribute delegates to the real
    module, so the separate real Docker warm-cache test keeps real time.
    """

    def __init__(self, clock):
        self._clock = clock

    def time(self):
        return self._clock()

    def __getattr__(self, name):
        return getattr(time, name)


def simulated_build(monkeypatch, tmp_path, *, fault=None, clock=None, legacy_wall_mtime=False):
    """Fake construction sharing one controlled logical clock with the helper.

    ``clock`` supplies both the helper's sampled start (via the branding
    module's ``time.time``) and the IID file timestamp, so a successful
    simulated build is deterministically fresh instead of racing two
    uncoordinated real clocks (CI run 39062814291, head f6eca5b).  With
    ``legacy_wall_mtime=True`` the IID file keeps a plain wall-clock
    timestamp pinned at fixture setup while the helper uses the logical
    clock, reproducing the pre-fix fixture for skew regression evidence.
    """
    owner = branding._OwnedDocker("test-owner")
    image_id = "sha256:" + "a" * 64
    image = {
        "Id": image_id,
        "Config": {"Labels": {branding.OWNER_LABEL: owner.nonce}},
        "Created": "2000-01-01T00:00:00Z",
        "RepoTags": [],
    }
    removed = []
    foreign = {}
    wall_reference = time.time()
    active_clock = clock if clock is not None else _default_clock

    def inspect(kind, reference):
        if reference in foreign:
            return foreign[reference]
        return image if reference == image_id and image_id not in removed else None

    def run(command, **kwargs):
        if command[1] == "build":
            assert "--tag" not in command, "construction must not overwrite racing foreign tags"
            output = Path(command[command.index("--iidfile") + 1])
            if fault == "early-failure":
                return subprocess.CompletedProcess(command, 1, "", "failed before output")
            if fault == "symlink":
                target = tmp_path / "foreign-output"
                target.write_text(image_id)
                output.symlink_to(target)
            else:
                output.write_text("invalid" if fault == "malformed" else image_id)
                if legacy_wall_mtime:
                    os.utime(output, (wall_reference, wall_reference))
                else:
                    stamp = active_clock()
                    os.utime(output, (stamp, stamp))
            if fault == "stale":
                os.utime(output, (1, 1))
            if fault == "wrong-id":
                image["Id"] = "sha256:" + "b" * 64
            if fault == "wrong-nonce":
                image["Config"]["Labels"][branding.OWNER_LABEL] = "foreign"
            if fault == "missing-created":
                image["Created"] = None
            if fault == "naive-created":
                image["Created"] = "2000-01-01T00:00:00"
            if fault == "named-image":
                image["RepoTags"] = ["foreign:test"]
            if fault == "race":
                foreign["reserved:test"] = {"Id": "foreign-image", "Created": image["Created"]}
            return subprocess.CompletedProcess(command, 0, "", "")
        assert command == ["docker", "image", "rm", image_id]
        removed.append(command[-1])
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(owner, "inspect", inspect)
    monkeypatch.setattr(branding, "_run", run)
    monkeypatch.setattr(branding, "time", _LogicalTime(active_clock))
    return owner, image_id, image, removed, foreign


def test_cached_created_requires_actual_construction_proof(monkeypatch, tmp_path):
    owner, image_id, image, removed, _ = simulated_build(monkeypatch, tmp_path)
    with pytest.raises(AssertionError, match="construction proof"):
        owner.remember("image", image_id)
    assert owner.build_image("reserved:test", tmp_path) == image_id
    owner.remember("image", image_id)
    assert owner.objects[("image", image_id)] == (owner.nonce, image["Created"])
    owner.cleanup()
    assert removed == [image_id]


def test_skewed_clock_rejects_legacy_fixture_and_accepts_fixed_fixture(monkeypatch, tmp_path):
    """Deterministic clock-skew regression for the fake construction fixture.

    The pre-fix fixture left the IID file with a plain wall-clock timestamp
    while the helper sampled ``time.time()`` just before the fake build; on
    uncoordinated clocks a fresh output measured 36-350 microseconds behind
    wall and was misclassified stale (CI run 39062814291, head f6eca5b,
    attempts 1-2).  Under one deliberately skewed logical clock (wall + 1 s):

    1. a legacy wall-timestamped output is refused as stale; its timestamp is
       pinned to the real wall at fixture setup, so the skew is provable with
       no sleeps, tolerances or probability loops;
    2. the fixed fixture, stamped from the same logical clock, satisfies the
       full positive construction contract and exact cleanup receipt.
    """

    def skewed():
        return time.time() + 1.0

    owner, _, _, removed, _ = simulated_build(
        monkeypatch, tmp_path, clock=skewed, legacy_wall_mtime=True
    )
    with pytest.raises(AssertionError, match="stale image construction output"):
        owner.build_image("reserved:test", tmp_path)
    owner.cleanup()
    assert owner.objects == {} and removed == []

    owner, image_id, image, removed, _ = simulated_build(monkeypatch, tmp_path, clock=skewed)
    assert owner.build_image("reserved:test", tmp_path) == image_id
    owner.remember("image", image_id)
    assert owner.objects[("image", image_id)] == (owner.nonce, image["Created"])
    owner.cleanup()
    assert removed == [image_id]


@pytest.mark.parametrize(
    "fault",
    [
        "early-failure",
        "malformed",
        "stale",
        "symlink",
        "wrong-id",
        "wrong-nonce",
        "missing-created",
        "naive-created",
        "named-image",
    ],
)
def test_unproven_image_is_not_adopted_or_deleted(monkeypatch, tmp_path, fault):
    owner, _, _, removed, _ = simulated_build(monkeypatch, tmp_path, fault=fault)
    with pytest.raises((AssertionError, OSError, ValueError)):
        owner.build_image("reserved:test", tmp_path)
    owner.cleanup()
    assert owner.objects == {} and removed == []


def test_foreign_tag_race_cleans_only_constructed_id(monkeypatch, tmp_path):
    owner, image_id, _, removed, foreign = simulated_build(monkeypatch, tmp_path, fault="race")
    with pytest.raises(AssertionError, match="already exists"):
        owner.build_image("reserved:test", tmp_path)
    owner.cleanup()
    assert removed == [image_id] and foreign["reserved:test"]["Id"] == "foreign-image"


def test_preexisting_name_is_refused_before_build(monkeypatch, tmp_path):
    owner, _, _, removed, foreign = simulated_build(monkeypatch, tmp_path)
    foreign["reserved:test"] = {"Id": "preexisting-foreign"}
    with pytest.raises(AssertionError, match="already exists"):
        owner.build_image("reserved:test", tmp_path)
    owner.cleanup()
    assert removed == [] and owner.objects == {}


def test_failure_after_construction_uses_exact_receipt(monkeypatch, tmp_path):
    owner, image_id, _, removed, _ = simulated_build(monkeypatch, tmp_path)
    with pytest.raises(RuntimeError, match="later qualification"):
        try:
            owner.build_image("reserved:test", tmp_path)
            raise RuntimeError("later qualification")
        finally:
            owner.cleanup()
    assert removed == [image_id]


def test_image_changed_created_receipt_refuses_cleanup(monkeypatch, tmp_path):
    owner, _, image, removed, _ = simulated_build(monkeypatch, tmp_path)
    owner.build_image("reserved:test", tmp_path)
    image["Created"] = "2001-01-01T00:00:00Z"
    with pytest.raises(AssertionError, match="changed ownership receipt"):
        owner.cleanup()
    assert removed == []


def test_later_foreign_named_reference_is_never_deleted(monkeypatch, tmp_path):
    owner, _, image, removed, _ = simulated_build(monkeypatch, tmp_path)
    owner.build_image("reserved:test", tmp_path)
    image["RepoTags"] = ["foreign:test"]
    with pytest.raises(AssertionError, match="changed ownership receipt"):
        owner.cleanup()
    assert removed == []


def test_real_warm_cache_repeat_and_post_build_failure_cleanup(tmp_path):
    if not branding._docker_available():
        pytest.skip("local Docker prerequisite missing")
    context = tmp_path / "context"
    context.mkdir()
    (context / "Dockerfile").write_text("FROM scratch\nCOPY payload /payload\n")
    (context / "payload").write_text("Owned warm-cache qualification\n")
    owners = []
    images = []
    created = []
    try:
        for index in range(2):
            owner = branding._OwnedDocker(uuid.uuid4().hex)
            owners.append(owner)
            reserved = f"sar-receipt-{owner.nonce}:test"
            image_id = owner.build_image(reserved, context, timeout=120)
            image = owner.inspect("image", image_id)
            assert image and image["Config"]["Labels"][branding.OWNER_LABEL] == owner.nonce
            assert owner.inspect("image", reserved) is None
            images.append(image_id)
            created.append(image["Created"])
            if index == 0:
                time.sleep(2)
            else:
                assert (
                    datetime.fromisoformat(image["Created"].replace("Z", "+00:00")) < owner.started
                )
                # A real post-build failure still has its receipt before any
                # app startup or later assertion can fail.
                with pytest.raises(RuntimeError, match="owned post-build"):
                    try:
                        raise RuntimeError("owned post-build")
                    finally:
                        owner.cleanup()
                assert owner.inspect("image", image_id) is None
        assert images[0] != images[1] and created[0] == created[1]
    finally:
        for owner in owners:
            owner.cleanup()
        for owner, image_id in zip(owners, images, strict=True):
            assert owner.inspect("image", image_id) is None
