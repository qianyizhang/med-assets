"""Canonical package record synchronization and strict acceptance of a native port."""

from __future__ import annotations

import json
import math
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from med_assets.artifacts import claim_identity, source_path, unique_keys
from pydantic import Field, ValidationError

from .blobs import HEX64, BlobRef, MeshStats, inspect_mesh_bytes, read_verified, safe_path, verify
from .delivery import ImpactResult
from .errors import AssetKitError
from .models import AssetModel
from .registry import MANIFEST_VERSION, CoordinateFrame, ExportRef, VoxelGrid
from .workspace import ShowAssetResult, ShowExportView, Workspace

_SEGMENT = r"[a-z0-9]+(?:-[a-z0-9]+)*"
_ASSET_ID = re.compile(rf"{_SEGMENT}:{_SEGMENT}:{_SEGMENT}")
_ID = re.compile(_SEGMENT)
_RECORD = "asset.record.json"


@dataclass(frozen=True)
class RecordExport:
    revision_id: str | None
    export_id: str | None
    path: str
    row: dict[str, Any]
    selectors: tuple[str, ...] = ()
    frame: CoordinateFrame | None = None

    @property
    def is_voxel_mesh(self) -> bool:
        return (
            self.path.endswith(".mesh")
            and self.frame is not None
            and self.frame.convention == "voxel-index"
        )


@dataclass(frozen=True)
class AssetRecord:
    path: str
    raw: bytes
    doc: dict[str, Any]
    exports: tuple[RecordExport, ...]
    inputs: tuple[BlobRef, ...]
    recipe_inputs: tuple[BlobRef, ...]


class PortExpectation(AssetModel):
    """Identity drawn from an independent package assignment, recipe, or delivery pin."""

    ref: ExportRef
    record: str
    path: str
    sha256: str
    bytes: int = Field(ge=0)
    triangles: int | None = Field(default=None, ge=0)
    selectors: tuple[str, ...] = ()


class PortCheck(AssetModel):
    """Verified native owner, selected export, and exact indexed readers."""

    found: bool = True
    record: str
    ref: ExportRef
    export: ShowExportView
    identity: BlobRef
    mesh: MeshStats | None = None
    impact: ImpactResult
    inputs: tuple[BlobRef, ...]


def _rows(owner: dict[str, Any], key: str) -> list[dict[str, Any]]:
    values = owner.get(key, [])
    if not isinstance(values, list) or not all(isinstance(row, dict) for row in values):
        raise AssetKitError(f"Expected a list of objects for {key}")
    return values


def _claim_path(row: dict[str, Any]) -> str:
    path = row.get("path")
    if not isinstance(path, str):
        raise AssetKitError("Expected a repository-relative path in the artifact declaration")
    return source_path(path)


def _unique_text(values: object, context: str) -> tuple[str, ...]:
    if not isinstance(values, list) or any(
        not isinstance(value, str) or not value.strip() for value in values
    ):
        raise AssetKitError(f"Expected a list of non-empty strings for {context}")
    if len(set(values)) != len(values):
        raise AssetKitError(f"Duplicate value in {context}")
    return tuple(values)


def _identity_claim(row: dict[str, Any], path: str) -> tuple[str | None, int | None]:
    digest, size = row.get("sha256"), row.get("bytes")
    if "sha256" in row and (not isinstance(digest, str) or not HEX64.fullmatch(digest)):
        raise AssetKitError(f"Invalid SHA-256 in declaration for {path}")
    if "bytes" in row and (type(size) is not int or size < 0):
        raise AssetKitError(f"Invalid byte count in declaration for {path}")
    return digest, size


def _observe(
    repo: Path,
    path: str,
    row: dict[str, Any],
) -> BlobRef:
    digest, size = _identity_claim(row, path)
    observed = verify(repo, path, digest, size)
    if observed.status == "mismatch":
        raise AssetKitError(f"Conflicting SHA-256 or byte count for {path}")
    if observed.status in {"missing", "invalid-pointer"}:
        raise AssetKitError(f"Cannot verify {path}: {observed.status}")
    if observed.status in {"pointer", "pointer-match"} and (digest is None or size is None):
        raise AssetKitError(f"Hydrated bytes required for initial identity registration: {path}")
    return observed


def _frame(raw: object, unresolved: tuple[str, ...], context: str) -> CoordinateFrame:
    try:
        frame = CoordinateFrame.model_validate(raw)
    except ValidationError as exc:
        raise AssetKitError(f"Invalid coordinate frame for {context}: {exc}") from exc
    if frame.convention == "unverified-frame":
        if not frame.unresolved or frame.unresolved not in unresolved:
            raise AssetKitError(
                f"Name the missing frame evidence for {context} in the record's unresolved list"
            )
        return frame
    expected_units = "BU" if frame.convention == "blender-z-up-bu" else "m"
    if frame.convention != "voxel-index" and (
        frame.units != expected_units
        or not frame.axes
        or any(not axis.strip() for axis in frame.axes)
    ):
        raise AssetKitError(f"Declare {expected_units} units and axes for {context}")
    up = {"glb-y-up-m": "Y-up", "blender-z-up-m": "Z-up", "blender-z-up-bu": "Z-up"}.get(
        frame.convention
    )
    if up:
        axes = set(frame.axes)
        other_up = {"X-up", "Y-up", "Z-up"} - {up}
        if not {"right-handed", up} <= axes or axes & ({"left-handed"} | other_up):
            raise AssetKitError(f"Axes contradict the {frame.convention} convention for {context}")
    if frame.convention == "voxel-index" and frame.units not in (None, "voxel"):
        raise AssetKitError(f"Declare voxel index units for {context}")
    if not frame.evidence and frame.convention != "voxel-index":
        raise AssetKitError(f"Declare coordinate evidence for {context}")
    return frame


def _check_voxel_grid(row: dict[str, Any], frame: CoordinateFrame, context: str) -> None:
    if frame.convention != "voxel-index":
        if "voxelGrid" in row:
            raise AssetKitError(
                f"Voxel grid conflicts with the coordinate convention for {context}"
            )
        return
    raw = row.get("voxelGrid")
    if not isinstance(raw, dict) or not {"case", "shape", "rasMmFromVoxel"} <= raw.keys():
        raise AssetKitError(f"Missing voxel grid case, shape, or affine for {context}")
    try:
        grid = VoxelGrid.model_validate(raw)
    except ValidationError as exc:
        raise AssetKitError(f"Invalid case, shape, or affine for {context}: {exc}") from exc
    if any(type(item) is not int for item in raw["shape"]) or any(
        type(value) not in (int, float)
        for affine_row in raw["rasMmFromVoxel"]
        for value in affine_row
    ):
        raise AssetKitError(f"Invalid voxel grid shape or affine values for {context}")
    a, b, c, bottom = grid.ras_mm_from_voxel
    determinant = (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )
    if (
        not grid.case.strip()
        or bottom != (0, 0, 0, 1)
        or not math.isfinite(determinant)
        or determinant == 0
    ):
        raise AssetKitError(f"Invalid voxel grid case or affine for {context}")


def _index_rows(
    rows: list[dict[str, Any]], id_key: str, *, stable_segment: bool = False
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = row.get(id_key)
        if (
            not isinstance(key, str)
            or not key.strip()
            or (stable_segment and not _ID.fullmatch(key))
        ):
            raise AssetKitError(f"Invalid or missing {id_key}: {key!r}")
        if key in indexed:
            raise AssetKitError(f"Duplicate {id_key}: {key}")
        indexed[key] = row
    return indexed


def _recipe_path(repo: Path, owner: Path, recipe: str) -> str:
    exact = source_path(recipe)
    if safe_path(repo, exact).is_file():
        return exact
    return (owner / exact).as_posix()


def _verify_edition_recipe(
    repo: Path,
    recipe: BlobRef,
    sources: list[dict[str, Any]],
    exports: list[dict[str, Any]],
) -> tuple[BlobRef, ...]:
    """Bind the maintained portable recipe's source and output declarations."""
    if not recipe.path.endswith(".json"):
        return ()
    assert recipe.sha256 is not None and recipe.bytes is not None
    raw = read_verified(repo, recipe.path, recipe.sha256, recipe.bytes)
    doc = json.loads(raw, object_pairs_hook=unique_keys)
    if not isinstance(doc, dict) or "operation" not in doc:
        return ()
    if not isinstance(doc.get("operation"), str) or not doc["operation"].strip():
        raise AssetKitError(f"Invalid portable recipe operation in {recipe.path}")
    source, output = doc.get("source"), doc.get("output")
    if not isinstance(source, dict) or not isinstance(output, dict):
        raise AssetKitError(f"Missing portable recipe source or output pin in {recipe.path}")
    source_file, output_file = _claim_path(source), _claim_path(output)
    if not {"sha256", "bytes"} <= source.keys() or not {"sha256", "bytes"} <= output.keys():
        raise AssetKitError(f"Incomplete portable recipe input or output pin in {recipe.path}")
    source_pin, output_pin = claim_identity(source), claim_identity(output)
    if not any(
        (row.get("path"), row.get("sha256"), row.get("bytes")) == (source_file, *source_pin)
        for row in sources
    ):
        raise AssetKitError(
            f"Portable recipe source differs from declared revision sources: {recipe.path}"
        )
    declared_output = next((row for row in exports if row.get("path") == output_file), None)
    if declared_output is None or any(
        field in declared_output and declared_output[field] != value
        for field, value in zip(("sha256", "bytes"), output_pin, strict=True)
    ):
        raise AssetKitError(
            f"Portable recipe output differs from declared revision exports: {recipe.path}"
        )
    return _observe(repo, source_file, source), _observe(repo, output_file, output)


def _check_source(row: dict[str, Any], unresolved: tuple[str, ...]) -> None:
    source_id = row["sourceId"]
    reason = row.get("unresolved")
    explicit_gap = isinstance(reason, str) and reason in unresolved
    if not any(
        isinstance(value := row.get(field), str) and value.strip()
        for field in ("path", "url", "doi")
    ) and not (_rows(row, "evidence") or explicit_gap):
        raise AssetKitError(f"Missing source locator or unresolved source evidence for {source_id}")
    license = row.get("license")
    if ("license" in row and (not isinstance(license, str) or not license.strip())) or (
        license is None and not explicit_gap
    ):
        raise AssetKitError(f"Missing or invalid rights declaration for {source_id}")
    if "path" not in row:
        _identity_claim(row, source_id)


def _read_record(repo: Path, path: str) -> tuple[bytes, dict[str, Any]]:
    if Path(source_path(path)).name != _RECORD:
        raise AssetKitError(f"Expected a package-owned {_RECORD}: {path}")
    record_file = safe_path(repo, path)
    if not record_file.is_file():
        raise AssetKitError(f"Missing canonical owner record: {path}")
    raw = record_file.read_bytes()
    doc = json.loads(raw, object_pairs_hook=unique_keys)
    if (
        not isinstance(doc, dict)
        or type(doc.get("schemaVersion")) is not int
        or doc["schemaVersion"] != MANIFEST_VERSION
        or not isinstance(doc.get("assetId"), str)
        or not _ASSET_ID.fullmatch(doc["assetId"])
    ):
        raise AssetKitError(f"Expected AssetKit schema v1 and a three-segment assetId in {path}")
    return raw, doc


def load_record(repo: Path, path: str, *, strict: bool) -> AssetRecord:
    """Read a record losslessly for sync, or enforce the batch contract for registration."""
    raw, doc = _read_record(repo, path)
    owner = Path(path).parent
    asset_id = doc["assetId"]
    if strict and (doc.get("owner") != owner.as_posix() or doc.get("status") != "provisional"):
        raise AssetKitError(f"Expected the canonical owner and provisional status in {path}")

    sources = _index_rows(_rows(doc, "sources"), "sourceId")
    parts = _index_rows(_rows(doc, "parts"), "partId", stable_segment=strict)
    unresolved = _unique_text(doc.get("unresolved", []), f"{path} unresolved")
    dependencies: list[tuple[str, dict[str, Any]]] = []
    verified_recipes: list[BlobRef] = []
    exports: list[RecordExport] = []
    all_revisions = _index_rows(_rows(doc, "revisions"), "revisionId", stable_segment=strict)
    if not all_revisions:
        raise AssetKitError(f"No declared revisions in {path}")

    for row in (*sources.values(), *_rows(doc, "artifacts")):
        if "path" in row:
            dependencies.append((_claim_path(row), row))
        for evidence in _rows(row, "evidence"):
            dependencies.append((_claim_path(evidence), evidence))

    for revision_id, rev in all_revisions.items():
        context = f"{asset_id}@{revision_id}"
        if strict and rev.get("status") != "provisional":
            raise AssetKitError(f"Expected provisional revision {context}")
        if strict and not (rev.get("recipe") or rev.get("recipeEvidence")):
            raise AssetKitError(f"Missing recipe or replay evidence for {context}")
        if "recipeEvidence" in rev:
            evidence = rev["recipeEvidence"]
            if not isinstance(evidence, dict):
                raise AssetKitError(f"Invalid recipe evidence for {context}")
            dependencies.append((_claim_path(evidence), evidence))

        source_ids = _unique_text(rev.get("sourceIds", []), f"{context} sourceIds")
        if set(source_ids) - sources.keys() or (strict and not source_ids):
            raise AssetKitError(f"Missing or unknown source declarations on {context}")
        rev_sources = [sources[sid] for sid in source_ids]
        if strict:
            for source in rev_sources:
                _check_source(source, unresolved)
        if strict or "frame" in rev:
            rev_frame = _frame(rev.get("frame"), unresolved, context)
            if rev_frame.evidence:
                dependencies.append((source_path(rev_frame.evidence), {}))
        else:
            rev_frame = None

        export_rows = _rows(rev, "exports")
        if strict:
            _index_rows(export_rows, "id", stable_segment=True)
        elif len({row["id"] for row in export_rows if "id" in row}) != sum(
            "id" in row for row in export_rows
        ):
            raise AssetKitError(f"Duplicate export id for {context}")
        if not export_rows:
            raise AssetKitError(f"No declared exports for {context}")
        if "recipe" in rev:
            recipe = _observe(repo, _recipe_path(repo, owner, rev["recipe"]), {})
            verified_recipes.append(recipe)
            verified_recipes.extend(_verify_edition_recipe(repo, recipe, rev_sources, export_rows))
        seen_paths: set[str] = set()
        for row in export_rows:
            export_path = _claim_path(row)
            if export_path in seen_paths:
                raise AssetKitError(f"Duplicate export path in {context}: {export_path}")
            seen_paths.add(export_path)
            frame = None
            selectors: tuple[str, ...] = ()
            if strict:
                part_ids = _unique_text(row.get("partIds", []), f"{context} partIds")
                if set(part_ids) - parts.keys():
                    raise AssetKitError(f"Unknown part declaration for {export_path}")
                selectors = tuple(
                    selector
                    for part_id in part_ids
                    for selector in _unique_text(
                        parts[part_id].get("selectors", []), f"{part_id} selectors"
                    )
                )
            if "frame" in row:
                frame = _frame(row["frame"], unresolved, export_path)
                if frame.evidence:
                    dependencies.append((source_path(frame.evidence), {}))
            else:
                frame = rev_frame
            if frame is not None:
                _check_voxel_grid(row, frame, export_path)
            exports.append(
                RecordExport(revision_id, row.get("id"), export_path, row, selectors, frame)
            )

    for row in _rows(doc, "exports"):
        exports.append(RecordExport(None, row.get("id"), _claim_path(row), row))

    claims: dict[str, dict[str, Any]] = {}
    inventory_paths: set[str] = set()
    for entry in exports:
        if entry.revision_id is None:
            if entry.path in inventory_paths:
                raise AssetKitError(f"Duplicate inventory export {entry.path}")
            inventory_paths.add(entry.path)
        merged = claims.setdefault(entry.path, {})
        _identity_claim(entry.row, entry.path)
        for key in ("sha256", "bytes", "triangles"):
            if key not in entry.row:
                continue
            value = entry.row[key]
            if key == "triangles" and (type(value) is not int or value < 0):
                raise AssetKitError(f"Invalid triangles declaration for {entry.path}")
            if key in merged and merged[key] != value:
                raise AssetKitError(
                    f"Inconsistent duplicate export declaration for {entry.path}: {key}"
                )
            merged[key] = value

    inputs = [_observe(repo, p, row) for p, row in claims.items()]
    inputs.extend(_observe(repo, p, row) for p, row in dependencies)
    inputs.extend(verified_recipes)
    return AssetRecord(path, raw, doc, tuple(exports), tuple(inputs), tuple(verified_recipes))


def export_mesh(repo: Path, observed: BlobRef, *, voxel_mesh: bool = False) -> MeshStats | None:
    """Check declared statistics against the same hydrated bytes as the verified identity."""
    if observed.status not in {"hydrated", "verified"} or not (
        observed.path.lower().endswith(".glb") or voxel_mesh
    ):
        return None
    assert observed.sha256 is not None and observed.bytes is not None
    raw = read_verified(repo, observed.path, observed.sha256, observed.bytes)
    if voxel_mesh and observed.path.endswith(".mesh") and len(raw) >= 8:
        vertices, faces = struct.unpack_from("<2I", raw)
        if vertices and faces and len(raw) == 8 + 12 * (vertices + faces):
            return MeshStats(bytes=len(raw), triangles=faces, node_names=(), node_triangles={})
        raise AssetKitError(f"Invalid voxel mesh: {observed.path}")
    try:
        result = inspect_mesh_bytes(raw)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError) as exc:
        raise AssetKitError(f"Cannot inspect hydrated mesh: {observed.path}") from exc
    if result is None:
        raise AssetKitError(f"Cannot inspect hydrated mesh: {observed.path}")
    return result


def check_port(
    repo: Path, expected: PortExpectation, *, allow_lfs_pointer: bool = False
) -> PortCheck:
    """Require exact native ownership, pinned bytes, and the new registration contract."""
    record = load_record(repo, expected.record, strict=True)
    ref = expected.ref
    key = f"{ref.asset}@{ref.revision}:{ref.export}"
    ws = Workspace.load(repo, include_legacy_adapters=False)
    shown = ws.show(key)
    if (
        not isinstance(shown, ShowAssetResult)
        or shown.asset.id != ref.asset
        or shown.asset.source_manifest != expected.record
    ):
        raise AssetKitError(f"Native owner does not match {expected.record} for {key}")

    selected = next(
        (
            entry
            for entry in record.exports
            if (entry.revision_id, entry.export_id) == (ref.revision, ref.export)
        ),
        None,
    )
    if selected is None:
        raise AssetKitError(f"Missing exact revision and export declaration for {key}")
    shown_export = next(
        export
        for revision in shown.revisions
        if revision.id == ref.revision
        for export in revision.exports
        if export.id == ref.export
    )
    pin = expected.path, expected.sha256, expected.bytes
    if (selected.path, *_identity_claim(selected.row, selected.path)) != pin or (
        shown_export.path,
        shown_export.sha256,
        shown_export.bytes,
    ) != pin:
        raise AssetKitError(f"Declared export identity differs from the independent pin for {key}")

    for use in _rows(record.doc, "uses"):
        if use.get("status") != "provisional":
            raise AssetKitError(f"New adoption must be provisional in {expected.record}")
    missing_selectors = set(expected.selectors) - set(selected.selectors)
    if missing_selectors:
        raise AssetKitError(f"Missing required selectors for {key}: {sorted(missing_selectors)}")
    declared_triangles = selected.row.get("triangles")
    if expected.triangles is not None and declared_triangles != expected.triangles:
        raise AssetKitError(f"Declared triangle count differs from the independent pin for {key}")

    observed = _observe(repo, selected.path, selected.row)
    mesh = None
    if observed.status == "pointer-match":
        if not allow_lfs_pointer:
            raise AssetKitError(f"Hydrated bytes required for {key}")
    else:
        mesh = export_mesh(repo, observed, voxel_mesh=selected.is_voxel_mesh)
        if (selected.selectors or declared_triangles is not None) and mesh is None:
            raise AssetKitError(f"Cannot verify claimed mesh statistics or selectors for {key}")
        if mesh is not None:
            if declared_triangles is not None and declared_triangles != mesh.triangles:
                raise AssetKitError(f"Hydrated triangle count differs for {key}")
            missing = {name for name in selected.selectors if mesh.node_names.count(name) != 1}
            if missing:
                raise AssetKitError(f"Missing or ambiguous selectors for {key}: {sorted(missing)}")

    if not allow_lfs_pointer:
        for recipe_input in record.recipe_inputs:
            if recipe_input.status == "pointer-match":
                raise AssetKitError(
                    f"Hydrated bytes required for recipe input: {recipe_input.path}"
                )
    if _read_record(repo, expected.record)[0] != record.raw:
        raise AssetKitError(f"Owner record changed during acceptance for {key}")
    return PortCheck(
        record=expected.record,
        ref=ref,
        export=shown_export,
        identity=observed,
        mesh=mesh,
        impact=ws.impact(key),
        inputs=record.inputs,
    )
