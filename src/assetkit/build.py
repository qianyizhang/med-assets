"""Build & sync context: recipe execution seam and manifest synchronization."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Literal, Protocol

from .blobs import BlobRef, BlobStatus, MeshStats, inspect_mesh, normalize_path, safe_path, verify
from .delivery import ImpactResult
from .errors import AssetKitError
from .models import AssetModel
from .records import AssetRecord, export_mesh, load_record
from .registry import MANIFEST_VERSION, AssetRegistry
from .workspace import Workspace


class BuildSpec(AssetModel):
    """Deterministic build plan for an Asset Revision's recipe."""

    asset_id: str
    revision_id: str
    owner_dir: str
    recipe_path: str
    command: tuple[str, ...]
    expected_outputs: tuple[str, ...]


class VerifiedOutput(AssetModel):
    """Post-build verification result for a single expected output."""

    path: str
    status: BlobStatus
    sha256: str | None = None
    bytes: int | None = None
    triangles: int | None = None


class BuildResult(AssetModel):
    """Outcome of executing (or planning) a BuildSpec."""

    spec: BuildSpec
    status: Literal["planned", "built", "failed"]
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""
    verified_outputs: tuple[VerifiedOutput, ...] = ()


class SyncExportChange(AssetModel):
    """Before/after field changes observed for one export during manifest sync."""

    asset_id: str | None = None
    revision_id: str | None = None
    export_id: str | None = None
    path: str
    changes: dict[str, dict[str, Any]]


class SyncDiff(AssetModel):
    """Observed changes and the preconditions for a canonical record sync."""

    manifest_path: str
    updated_exports: tuple[SyncExportChange, ...]
    applied: bool
    record_sha256: str | None = None
    inputs: tuple[BlobRef, ...] = ()
    affected_readers: tuple[ImpactResult, ...] = ()
    plan_token: str | None = None


class BuildRunner(Protocol):
    """Seam for executing package recipes (subprocess, Blender, or test fake)."""

    def run(self, repo: Path, spec: BuildSpec) -> tuple[int, str, str]: ...


class SubprocessRunner:
    """Default runner executing recipe commands in the repository root."""

    def run(self, repo: Path, spec: BuildSpec) -> tuple[int, str, str]:
        proc = subprocess.run(
            list(spec.command),
            cwd=repo,
            text=True,
            capture_output=True,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr


def plan_build(
    repo: Path,
    registry: AssetRegistry,
    asset_id: str,
    revision_id: str,
    *,
    blender_bin: str = "blender",
) -> BuildSpec:
    """Construct a reproducible BuildSpec for an Asset Revision."""
    asset = registry.get(asset_id)
    if asset is None:
        raise AssetKitError(f"Unknown asset '{asset_id}'")
    rev = next((r for r in asset.revisions if r.id == revision_id), None)
    if rev is None:
        raise AssetKitError(f"Unknown revision '{revision_id}' on asset '{asset_id}'")
    if not rev.recipe:
        raise AssetKitError(f"Revision {asset_id}@{revision_id} declares no recipe")

    recipe_rel = (
        rev.recipe
        if (repo / rev.recipe).exists()
        else normalize_path(f"{asset.owner_dir}/{rev.recipe}")
    )
    recipe_file = safe_path(repo, recipe_rel)
    if not recipe_file.is_file():
        raise AssetKitError(f"Recipe not found: {recipe_rel}")

    if recipe_rel.endswith(".py"):
        text = recipe_file.read_text(encoding="utf-8", errors="ignore")
        if "import bpy" in text or "from bpy" in text:
            cmd = (blender_bin, "--background", "--python-exit-code", "1", "--python", recipe_rel)
        else:
            cmd = (sys.executable, recipe_rel)
    else:
        raise AssetKitError(f"Unsupported recipe type: {recipe_rel}")

    return BuildSpec(
        asset_id=asset.id,
        revision_id=rev.id,
        owner_dir=asset.owner_dir,
        recipe_path=recipe_rel,
        command=cmd,
        expected_outputs=tuple(e.path for e in rev.exports),
    )


def run_build(
    repo: Path,
    spec: BuildSpec,
    *,
    apply: bool = False,
    runner: BuildRunner | None = None,
) -> BuildResult:
    """Dry-run by default; when apply=True executes via BuildRunner and verifies outputs."""
    if not apply:
        return BuildResult(spec=spec, status="planned")
    active_runner = runner or SubprocessRunner()
    code, out, err = active_runner.run(repo, spec)
    if code != 0:
        return BuildResult(spec=spec, status="failed", returncode=code, stdout=out, stderr=err)

    verified: list[VerifiedOutput] = []
    for path in spec.expected_outputs:
        chk = verify(repo, path)
        stats = inspect_mesh(repo, path) if path.endswith(".glb") else None
        verified.append(
            VerifiedOutput(
                path=chk.path,
                status=chk.status,
                sha256=chk.sha256,
                bytes=chk.bytes,
                triangles=stats.triangles if stats is not None else None,
            )
        )
    return BuildResult(
        spec=spec,
        status="built" if all(output.status == "hydrated" for output in verified) else "failed",
        returncode=0,
        stdout=out,
        stderr=err,
        verified_outputs=tuple(verified),
    )


def _sync_payload(record: AssetRecord) -> bytes:
    return (json.dumps(record.doc, ensure_ascii=False, indent=2) + "\n").encode()


def _sync_precondition(record: AssetRecord, raw: bytes) -> str:
    token = hashlib.sha256(record.path.encode() + b"\0" + raw)
    for identity in record.inputs:
        observation = (
            identity.path,
            identity.sha256,
            identity.bytes,
            identity.status in {"hydrated", "verified"},
        )
        token.update(b"\0" + json.dumps(observation, ensure_ascii=False).encode())
    return token.hexdigest()


def _record_sync(repo: Path, record: AssetRecord) -> SyncDiff:
    observed = {identity.path: identity for identity in reversed(record.inputs)}
    changes: list[SyncExportChange] = []
    meshes: dict[str, MeshStats | None] = {}
    for export in record.exports:
        blob = observed[export.path]
        if blob.status == "pointer-match" and not {"sha256", "bytes"} <= export.row.keys():
            raise AssetKitError(
                f"Hydrated bytes required for initial identity registration: {export.path}"
            )
        if export.path not in meshes:
            meshes[export.path] = export_mesh(repo, blob)
        mesh = meshes[export.path]
        fields: dict[str, str | int | None] = {"sha256": blob.sha256, "bytes": blob.bytes}
        if mesh is not None:
            if "triangles" in export.row and export.row["triangles"] != mesh.triangles:
                raise AssetKitError(f"Conflicting triangle count for {export.path}")
            if export.revision_id is not None:
                fields["triangles"] = mesh.triangles
        updates: dict[str, dict[str, Any]] = {}
        for field, value in fields.items():
            if field not in export.row:
                updates[field] = {"before": None, "after": value}
                export.row[field] = value
        if updates:
            changes.append(
                SyncExportChange(
                    asset_id=record.doc["assetId"],
                    revision_id=export.revision_id,
                    export_id=export.export_id,
                    path=export.path,
                    changes=updates,
                )
            )

    readers: tuple[ImpactResult, ...] = ()
    if changes:
        ws = Workspace.load(repo)
        paths = dict.fromkeys(change.path for change in changes)
        readers = tuple(ws.impact(path) for path in paths)
    before = _sync_precondition(record, record.raw)
    after = _sync_precondition(record, _sync_payload(record)) if changes else before
    return SyncDiff(
        manifest_path=record.path,
        updated_exports=tuple(changes),
        applied=False,
        record_sha256=hashlib.sha256(record.raw).hexdigest(),
        inputs=record.inputs,
        affected_readers=readers,
        plan_token=f"{before}.{after}",
    )


def plan_record_sync(repo: Path, record_path: str) -> SyncDiff:
    """Observe the exact current record and inputs and preview any missing metadata."""
    return _record_sync(repo, load_record(repo, record_path, strict=False))


def apply_record_sync(repo: Path, record_path: str, plan_token: str) -> SyncDiff:
    """Apply a previously planned update, serializing writers in the owner directory."""
    destination = safe_path(repo, record_path)
    # The directory inode survives record replacement and needs no persistent lock file.
    directory = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY)
    staged: Path | None = None
    try:
        fcntl.flock(directory, fcntl.LOCK_EX)
        try:
            record = load_record(repo, record_path, strict=False)
            current = _record_sync(repo, record)
        except (AssetKitError, OSError, ValueError) as exc:
            raise AssetKitError(f"Stale sync plan for {record_path}: {exc}") from exc
        if not current.updated_exports:
            before, separator, after = plan_token.partition(".")
            if separator and len(before) == 64 and after == _sync_precondition(record, record.raw):
                return current
        if current.plan_token != plan_token:
            raise AssetKitError(f"Stale sync plan for {record_path}")
        with NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
            staged = Path(stream.name)
            stream.write(_sync_payload(record))
            os.fchmod(stream.fileno(), stat.S_IMODE(destination.stat().st_mode))
            stream.flush()
            os.fsync(stream.fileno())
        # Recheck after preparation so a failed update leaves the original untouched.
        try:
            latest = load_record(repo, record_path, strict=False)
        except (AssetKitError, OSError, ValueError) as exc:
            raise AssetKitError(f"Stale sync plan for {record_path}: {exc}") from exc
        if latest.raw != record.raw or latest.inputs != record.inputs:
            raise AssetKitError(f"Stale sync plan for {record_path}")
        os.replace(staged, destination)
        return current.model_copy(update={"applied": True})
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)
        os.close(directory)


def sync_manifest(
    repo: Path,
    manifest_rel_path: str,
    *,
    apply: bool = False,
    expect_plan: str | None = None,
) -> SyncDiff:
    """Sync a canonical package record or the supported assets.json metadata fixture."""
    if Path(manifest_rel_path).name == "asset.record.json":
        if expect_plan is not None:
            if not apply:
                raise AssetKitError("A sync plan token requires --apply")
            return apply_record_sync(repo, manifest_rel_path, expect_plan)
        plan = plan_record_sync(repo, manifest_rel_path)
        if apply:
            assert plan.plan_token is not None
            return apply_record_sync(repo, manifest_rel_path, plan.plan_token)
        return plan
    if expect_plan is not None:
        raise AssetKitError("Sync plan tokens are available for asset.record.json")
    return _sync_legacy_manifest(repo, manifest_rel_path, apply=apply)


def _sync_legacy_manifest(repo: Path, manifest_rel_path: str, *, apply: bool) -> SyncDiff:
    """Refresh the historic metadata fixture's hashes and GLB stats."""
    norm = normalize_path(manifest_rel_path)
    manifest = safe_path(repo, norm)
    if not manifest.is_file():
        raise AssetKitError(f"Manifest not found: {norm}")
    doc = json.loads(manifest.read_text(encoding="utf-8"))
    if (
        not isinstance(doc, dict)
        or doc.get("schemaVersion") != MANIFEST_VERSION
        or not isinstance(doc.get("assets"), list)
    ):
        raise AssetKitError(f"Expected an AssetKit assets.json manifest: {norm}")
    owner_dir = manifest.parent.resolve().relative_to(repo.resolve()).as_posix()

    updates: list[SyncExportChange] = []
    for asset in doc["assets"]:
        for rev in asset.get("revisions", []):
            for exp in rev.get("exports", []):
                raw_path = exp["path"]
                full_rel = (
                    raw_path
                    if (repo / raw_path).exists()
                    else normalize_path(f"{owner_dir}/{raw_path}")
                )
                chk = verify(repo, full_rel)
                if chk.status not in {"hydrated", "verified", "pointer", "pointer-match"}:
                    continue
                stats = (
                    inspect_mesh(repo, full_rel)
                    if full_rel.endswith(".glb") and chk.status in {"hydrated", "verified"}
                    else None
                )
                changes: dict[str, dict[str, Any]] = {}
                if chk.sha256 and exp.get("sha256") != chk.sha256:
                    changes["sha256"] = {"before": exp.get("sha256"), "after": chk.sha256}
                    exp["sha256"] = chk.sha256
                if chk.bytes is not None and exp.get("bytes") != chk.bytes:
                    changes["bytes"] = {"before": exp.get("bytes"), "after": chk.bytes}
                    exp["bytes"] = chk.bytes
                if stats is not None and exp.get("triangles") != stats.triangles:
                    changes["triangles"] = {
                        "before": exp.get("triangles"),
                        "after": stats.triangles,
                    }
                    exp["triangles"] = stats.triangles
                if changes:
                    updates.append(
                        SyncExportChange(
                            asset_id=asset.get("id"),
                            revision_id=rev.get("id"),
                            export_id=exp.get("id"),
                            path=full_rel,
                            changes=changes,
                        )
                    )

    if apply and updates:
        manifest.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return SyncDiff(
        manifest_path=norm, updated_exports=tuple(updates), applied=apply and bool(updates)
    )
