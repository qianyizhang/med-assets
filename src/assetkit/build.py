"""Build & sync context: recipe execution seam and manifest synchronization."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

from .blobs import inspect_mesh, normalize_path, safe_path, verify
from .errors import AssetKitError
from .registry import AssetRegistry


@dataclass(frozen=True)
class BuildSpec:
    """Deterministic build plan for an Asset Revision's recipe."""

    asset_id: str
    revision_id: str
    owner_dir: str
    recipe_path: str
    command: tuple[str, ...]
    expected_outputs: tuple[str, ...]


@dataclass(frozen=True)
class BuildResult:
    """Outcome of executing (or planning) a BuildSpec."""

    spec: BuildSpec
    status: str  # planned | built | failed
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""
    verified_outputs: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SyncDiff:
    """Observed changes between an assets.json manifest and rebuilt artifacts on disk."""

    manifest_path: str
    updated_exports: tuple[dict[str, Any], ...]
    applied: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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
            cmd = (blender_bin, "--background", "--python", recipe_rel)
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

    verified = []
    for path in spec.expected_outputs:
        chk = verify(repo, path)
        stats = inspect_mesh(repo, path) if path.endswith(".glb") else None
        verified.append(
            {
                "path": chk.path,
                "status": chk.status,
                "sha256": chk.sha256,
                "bytes": chk.bytes,
                "triangles": stats.triangles if stats is not None else None,
            }
        )
    return BuildResult(
        spec=spec,
        status="built",
        returncode=0,
        stdout=out,
        stderr=err,
        verified_outputs=tuple(verified),
    )


def sync_manifest(repo: Path, manifest_rel_path: str, *, apply: bool = False) -> SyncDiff:
    """Refresh sha256, bytes, and GLB triangle counts in a native assets.json from disk."""
    norm = normalize_path(manifest_rel_path)
    manifest = safe_path(repo, norm)
    if not manifest.is_file():
        raise AssetKitError(f"Manifest not found: {norm}")
    doc = json.loads(manifest.read_text(encoding="utf-8"))
    owner_dir = manifest.parent.resolve().relative_to(repo.resolve()).as_posix()

    updates: list[dict[str, Any]] = []
    for asset in doc.get("assets", []):
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
                changes: dict[str, Any] = {}
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
                        {
                            "assetId": asset.get("id"),
                            "revisionId": rev.get("id"),
                            "exportId": exp.get("id"),
                            "path": full_rel,
                            "changes": changes,
                        }
                    )

    if apply and updates:
        manifest.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return SyncDiff(
        manifest_path=norm, updated_exports=tuple(updates), applied=apply and bool(updates)
    )
