"""Canonical records fill missing pins and verify the exact native export."""

from __future__ import annotations

import hashlib
import json
import struct
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from typer.testing import CliRunner

from assetkit import (
    AssetKitError,
    ExportRef,
    PortExpectation,
    apply_record_sync,
    check_port,
    plan_record_sync,
)
from assetkit.cli import app

OWNER = "models/example"
RECORD = f"{OWNER}/asset.record.json"
PAYLOAD = f"{OWNER}/liver.glb"
ASSET = "anatomy:example:liver"
REF = ExportRef(asset=ASSET, revision="r01", export="teaching")
TARGET = f"{ASSET}@r01:teaching"
FRAME = {
    "convention": "glb-y-up-m",
    "units": "m",
    "axes": ["right-handed", "Y-up"],
    "evidence": f"{OWNER}/frame.md",
}


@pytest.fixture
def package(tmp_path: Path) -> tuple[Path, dict, bytes]:
    owner = tmp_path / OWNER
    owner.mkdir(parents=True)
    (owner / "frame.md").write_text("Unregistered glTF coordinate frame.\n")
    (owner / "recipe.py").write_text("# Replay the pinned source here.\n")
    gltf = {
        "asset": {"version": "2.0"},
        "nodes": [{"name": "Capsule", "mesh": 0}, {"mesh": 0}],
        "meshes": [{"primitives": [{"indices": 0}]}],
        "accessors": [{"count": 3, "componentType": 5123, "type": "SCALAR"}],
    }
    chunk = json.dumps(gltf).encode()
    chunk += b" " * (-len(chunk) % 4)
    raw = struct.pack("<4sIIII", b"glTF", 2, 20 + len(chunk), len(chunk), 0x4E4F534A) + chunk
    (tmp_path / PAYLOAD).write_bytes(raw)
    record = {
        "schemaVersion": 1,
        "assetId": ASSET,
        "status": "provisional",
        "owner": OWNER,
        "sources": [
            {"sourceId": "source:example", "license": "CC0", "url": "https://example.com/source"}
        ],
        "parts": [{"partId": "capsule", "selectors": ["Capsule"]}],
        "revisions": [
            {
                "revisionId": "r01",
                "status": "provisional",
                "frame": FRAME,
                "recipe": "recipe.py",
                "sourceIds": ["source:example"],
                "exports": [{"id": "teaching", "path": PAYLOAD, "partIds": ["capsule"]}],
            }
        ],
        "exports": [{"path": PAYLOAD}],
        "uses": [],
    }
    (tmp_path / RECORD).write_text(json.dumps(record))
    return tmp_path, record, raw


def _pin(tmp: Path, record: dict, raw: bytes) -> PortExpectation:
    exp = record["revisions"][0]["exports"][0]
    digest = hashlib.sha256(raw).hexdigest()
    exp.update(sha256=digest, bytes=len(raw), triangles=2)
    record["exports"][0].update(sha256=digest, bytes=len(raw))
    (tmp / RECORD).write_text(json.dumps(record))
    return PortExpectation(
        ref=REF,
        record=RECORD,
        path=PAYLOAD,
        sha256=digest,
        bytes=len(raw),
        triangles=2,
        selectors=("Capsule",),
    )


def test_sync_applies_reviewed_token_once_even_with_concurrent_writers(package) -> None:
    tmp, _, raw = package
    manifest = tmp / RECORD
    original = manifest.read_bytes()
    consumer_path = tmp / "lesson/consumer.json"
    consumer_path.parent.mkdir()
    consumer_path.write_text(
        json.dumps({"consumers": [{"id": "lesson:data", "pins": [REF.to_dict()]}]})
    )
    cli = CliRunner()
    args = ["--repo", str(tmp), "sync", RECORD]
    dry = cli.invoke(app, args)
    assert dry.exit_code == 0, dry.output
    plan = json.loads(dry.output)
    assert plan["recordSha256"] == hashlib.sha256(original).hexdigest()
    updates = plan["updatedExports"]
    assert updates[0]["changes"]["triangles"] == {"before": None, "after": 2}
    assert updates[1]["changes"]["bytes"]["after"] == len(raw)
    reader = plan["affectedReaders"][0]["consumers"][0]
    assert reader["ownerPath"] == "lesson/consumer.json"
    assert reader["pins"][0]["exportId"] == REF.export
    assert manifest.read_bytes() == original

    token = plan["planToken"]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(apply_record_sync, tmp, RECORD, token) for _ in range(2)]
        assert sorted(future.result().applied for future in futures) == [False, True]
    written = manifest.read_bytes()
    assert written != original
    repeated = cli.invoke(app, [*args, "--apply", "--expect-plan", token])
    assert repeated.exit_code == 0, repeated.output
    assert json.loads(repeated.output)["updatedExports"] == []
    assert manifest.read_bytes() == written


@pytest.mark.parametrize(
    "changed", ["manifest", "payload", "recipe", "removed-payload", "frame-evidence"]
)
def test_stale_plan_preserves_original_record(package, changed: str) -> None:
    tmp, _, _ = package
    plan = plan_record_sync(tmp, RECORD)
    assert plan.plan_token is not None
    manifest = tmp / RECORD
    match changed:
        case "manifest":
            manifest.write_bytes(manifest.read_bytes() + b"\n")
        case "payload":
            (tmp / PAYLOAD).write_bytes(b"replacement")
        case "recipe":
            (tmp / OWNER / "recipe.py").write_text("# Different input.\n")
        case "removed-payload":
            (tmp / PAYLOAD).unlink()
        case "frame-evidence":
            (tmp / OWNER / "frame.md").write_text("Different frame documentation.\n")
    before = manifest.read_bytes()
    with pytest.raises(AssetKitError, match="Stale sync plan"):
        apply_record_sync(tmp, RECORD, plan.plan_token)
    assert manifest.read_bytes() == before


@pytest.mark.parametrize("field", ["sha256", "bytes", "triangles"])
def test_sync_rejects_disagreeing_declarations(package, field: str) -> None:
    tmp, record, raw = package
    _pin(tmp, record, raw)
    record["exports"][0][field] = "f" * 64 if field == "sha256" else 1000
    manifest = tmp / RECORD
    manifest.write_text(json.dumps(record))
    before = manifest.read_bytes()
    with pytest.raises(AssetKitError, match="Inconsistent duplicate export declaration"):
        plan_record_sync(tmp, RECORD)
    assert manifest.read_bytes() == before


def test_sync_never_replaces_a_pin_and_rejects_unpinned_lfs(package) -> None:
    tmp, record, raw = package
    expected = _pin(tmp, record, raw)
    path = tmp / PAYLOAD
    path.write_bytes(raw + b"changed")
    before = (tmp / RECORD).read_bytes()
    with pytest.raises(AssetKitError, match="Conflicting SHA-256 or byte count"):
        plan_record_sync(tmp, RECORD)
    assert (tmp / RECORD).read_bytes() == before

    path.write_text(
        "version https://git-lfs.github.com/spec/v1\n"
        f"oid sha256:{expected.sha256}\nsize {expected.bytes}\n"
    )
    assert plan_record_sync(tmp, RECORD).updated_exports == ()
    for row in (record["exports"][0], record["revisions"][0]["exports"][0]):
        del row["bytes"]
    (tmp / RECORD).write_text(json.dumps(record))
    with pytest.raises(AssetKitError, match="Hydrated bytes required"):
        plan_record_sync(tmp, RECORD)


def test_port_rejects_synthetic_selector_wrong_frame_and_bad_independent_pin(package) -> None:
    tmp, record, raw = package
    expected = _pin(tmp, record, raw)
    result = check_port(tmp, expected)
    assert result.mesh is not None and result.mesh.node_names == ("Capsule",)
    assert result.export.frame is not None and result.export.frame.convention == "glb-y-up-m"

    different_pin = expected.model_copy(update={"bytes": 10})
    with pytest.raises(AssetKitError, match="independent pin"):
        check_port(tmp, different_pin)

    record["parts"][0]["selectors"].append("node_1")
    _pin(tmp, record, raw)
    with pytest.raises(AssetKitError, match="Missing or ambiguous selectors"):
        check_port(tmp, expected)

    record["parts"][0]["selectors"] = ["Capsule"]
    record["revisions"][0]["frame"] = {"convention": "unverified-frame"}
    _pin(tmp, record, raw)
    with pytest.raises(AssetKitError, match="missing frame evidence"):
        check_port(tmp, expected)

    record["unresolved"] = ["Missing evidence for r01 source orientation."]
    record["revisions"][0]["frame"]["unresolved"] = record["unresolved"][0]
    _pin(tmp, record, raw)
    frame = check_port(tmp, expected).export.frame
    assert frame is not None and frame.convention == "unverified-frame"


def test_check_port_rejects_a_malformed_pointer(package) -> None:
    tmp, record, raw = package
    expected = _pin(tmp, record, raw)
    path = tmp / PAYLOAD
    pointer = (
        "version https://git-lfs.github.com/spec/v1\n"
        f"oid sha256:{expected.sha256}\nsize {expected.bytes}\n"
    )
    path.write_text(pointer)
    assert check_port(tmp, expected, allow_lfs_pointer=True).identity.status == "pointer-match"
    with pytest.raises(AssetKitError, match="Hydrated bytes required"):
        check_port(tmp, expected)
    path.write_text(pointer + "unexpected trailing bytes\n")
    with pytest.raises(AssetKitError, match="invalid-pointer"):
        check_port(tmp, expected, allow_lfs_pointer=True)


def test_portable_recipe_binds_both_declared_pins_and_rechecks_source_on_apply(package) -> None:
    tmp, record, raw = package
    original = b"original source bytes"
    source = {
        "path": f"{OWNER}/source.glb",
        "sha256": hashlib.sha256(original).hexdigest(),
        "bytes": len(original),
    }
    source_file = tmp / source["path"]
    source_file.write_bytes(original)
    record["sources"][0].update(source)
    record["revisions"][0]["recipe"] = "recipe.json"
    recipe_file = tmp / OWNER / "recipe.json"
    recipe = {
        "operation": "normal-i8",
        "source": source,
        "output": {"path": PAYLOAD, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)},
    }
    recipe_file.write_text(json.dumps(recipe))
    manifest = tmp / RECORD
    manifest.write_text(json.dumps(record))
    before = manifest.read_bytes()

    plan = plan_record_sync(tmp, RECORD)
    assert plan.plan_token is not None
    source_file.write_bytes(b"mutated source bytes")
    with pytest.raises(AssetKitError, match="Stale sync plan"):
        apply_record_sync(tmp, RECORD, plan.plan_token)
    assert manifest.read_bytes() == before

    source_file.write_bytes(original)
    expected = _pin(tmp, record, raw)
    source_file.write_text(
        "version https://git-lfs.github.com/spec/v1\n"
        f"oid sha256:{source['sha256']}\nsize {source['bytes']}\n"
    )
    with pytest.raises(AssetKitError, match="Hydrated bytes required for recipe input"):
        check_port(tmp, expected)
    assert check_port(tmp, expected, allow_lfs_pointer=True).found
    source_file.write_bytes(original)

    sibling = f"{OWNER}/sibling.glb"
    (tmp / sibling).write_bytes(original)
    recipe["source"]["path"] = sibling
    recipe_file.write_text(json.dumps(recipe))
    with pytest.raises(AssetKitError, match="Portable recipe source differs"):
        check_port(tmp, expected)

    recipe["source"]["path"] = f"{OWNER}/source.glb"
    recipe["output"]["path"] = sibling
    recipe_file.write_text(json.dumps(recipe))
    with pytest.raises(AssetKitError, match="Portable recipe output differs"):
        check_port(tmp, expected)


def test_port_rejects_false_source_and_coordinate_evidence(package) -> None:
    tmp, record, raw = package
    source = record["sources"][0]
    source["license"] = True
    expected = _pin(tmp, record, raw)
    with pytest.raises(AssetKitError, match="invalid rights declaration"):
        check_port(tmp, expected)
    source["license"] = "CC0"
    del source["url"]
    _pin(tmp, record, raw)
    with pytest.raises(AssetKitError, match="Missing source locator"):
        check_port(tmp, expected)
    source["doi"] = "10.example/annotated-recipe"
    record["revisions"][0]["frame"] = {**FRAME, "axes": ["left-handed", "Z-up"]}
    _pin(tmp, record, raw)
    with pytest.raises(AssetKitError, match="Axes contradict"):
        check_port(tmp, expected)


def test_atomic_replace_failure_preserves_record_and_cleans_temporary_file(
    package, monkeypatch: pytest.MonkeyPatch
) -> None:
    tmp, _, _ = package
    manifest = tmp / RECORD
    original = manifest.read_bytes()
    files = set(manifest.parent.iterdir())
    plan = plan_record_sync(tmp, RECORD)
    assert plan.plan_token is not None

    def fail_replace(*args) -> None:
        raise OSError("simulated rename failure")

    monkeypatch.setattr("assetkit.build.os.replace", fail_replace)
    with pytest.raises(OSError, match="simulated rename failure"):
        apply_record_sync(tmp, RECORD, plan.plan_token)
    assert manifest.read_bytes() == original
    assert set(manifest.parent.iterdir()) == files
