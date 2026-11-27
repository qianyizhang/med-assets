"""Supply / authoring context: AssetRegistry, Asset aggregates, and per-part Provenance."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, FiniteFloat, PositiveInt

from .blobs import inspect_mesh, normalize_path, safe_path, verify
from .discovery import SKIP_DIRS, manifests
from .errors import AssetKitError
from .models import AssetModel
from .vocab import ConceptGraph

ASSET_KINDS = frozenset({"model", "assembly", "diagram", "rig", "generator", "detail"})
REVISION_STATUSES = frozenset({"provisional", "active", "deprecated", "retired"})
REGISTRATION_STATES = frozenset(
    {"native", "registered", "fitted", "illustrative", "synthetic", "unknown"}
)
MODEL_EXTS = frozenset({".glb", ".gltf", ".blend", ".svg", ".obj", ".stl"})
MANIFEST_VERSION = 1


class ExportRef(AssetModel):
    """An exact export identity declared by a downstream owner."""

    asset: str
    revision: str
    export: str


class RecordExportRef(ExportRef):
    """An exact export reference with its package record for targeted reads."""

    record: str


class VoxelGrid(AssetModel):
    """Voxel-index coordinates with a case-bound affine into RAS millimetres."""

    case: str
    shape: tuple[PositiveInt, PositiveInt, PositiveInt]
    ras_mm_from_voxel: tuple[
        tuple[FiniteFloat, FiniteFloat, FiniteFloat, FiniteFloat],
        tuple[FiniteFloat, FiniteFloat, FiniteFloat, FiniteFloat],
        tuple[FiniteFloat, FiniteFloat, FiniteFloat, FiniteFloat],
        tuple[FiniteFloat, FiniteFloat, FiniteFloat, FiniteFloat],
    ]


FrameConvention = Literal[
    "glb-y-up-m", "voxel-index", "blender-z-up-m", "tool-probe-m", "unverified-frame"
]


class CoordinateFrame(AssetModel):
    """Convention of stored coordinates, with independent documentation of placement."""

    convention: FrameConvention
    units: str | None = None
    axes: tuple[str, ...] = ()
    evidence: str | None = None
    unresolved: str | None = None


class SpatialFrame(AssetModel):
    """Coordinate system, units, axes, and source-to-export transform metadata."""

    units: str | None = None
    axes: tuple[str, ...] = ()
    laterality: str | None = None
    source_frame: str | None = None
    frame: str | None = None
    transform: tuple[float, ...] | None = None
    transform_evidence: str | None = None

    def validate_invariants(self, context: str) -> None:
        if self.transform is not None and len(self.transform) != 16:
            raise AssetKitError(f"Transform matrix must have 16 values in {context}")


class Provenance(AssetModel):
    """Source, subject, spatial frame, and registration honesty record."""

    source: str | None = None
    subject: str | None = None
    license: str | None = None
    registration: str = "unknown"
    registration_note: str | None = None
    spatial: SpatialFrame | None = None
    derived_from: str | None = None
    limits: tuple[str, ...] = ()

    def validate_invariants(self, context: str) -> None:
        if self.registration not in REGISTRATION_STATES:
            raise AssetKitError(f"Invalid registration '{self.registration}' in {context}")
        if self.spatial is not None:
            self.spatial.validate_invariants(context)


class Part(AssetModel):
    """An addressable sub-structure inside an Export."""

    id: str
    label: str
    selectors: tuple[str, ...] = ()
    concepts: tuple[str, ...] = ()
    kind: str = "mesh-node"
    selectable: bool = True
    context_only: bool = False
    bytes: int | None = None
    triangles: int | None = None
    provenance: Provenance | None = None

    def validate_invariants(self, context: str) -> None:
        if not self.id.strip():
            raise AssetKitError(f"Part requires non-empty id in {context}")
        if self.selectable and self.context_only:
            raise AssetKitError(
                f"Part '{self.id}' in {context} cannot be both selectable and context_only"
            )
        if self.bytes is not None and self.bytes < 0:
            raise AssetKitError(f"Negative bytes on part '{self.id}' in {context}")
        if self.triangles is not None and self.triangles < 0:
            raise AssetKitError(f"Negative triangles on part '{self.id}' in {context}")
        if self.provenance is not None:
            self.provenance.validate_invariants(f"{context}:part:{self.id}")


class Export(AssetModel):
    """A concrete deliverable payload produced by a Revision."""

    id: str
    path: str
    format: str
    role: str = "teaching-mesh"
    variant: str = "normal"
    sha256: str | None = None
    bytes: int | None = None
    triangles: int | None = None
    storage_status: str = "unverified"
    parts: tuple[Part, ...] = ()
    voxel_grid: VoxelGrid | None = None
    frame: CoordinateFrame | None = None

    def validate_invariants(self, context: str) -> None:
        if not self.id.strip() or not self.path.strip():
            raise AssetKitError(f"Export requires non-empty id and path in {context}")
        if self.bytes is not None and self.bytes < 0:
            raise AssetKitError(f"Negative export bytes on '{self.id}' in {context}")
        if self.triangles is not None and self.triangles < 0:
            raise AssetKitError(f"Negative export triangles on '{self.id}' in {context}")
        seen: set[str] = set()
        for part in self.parts:
            if part.id in seen:
                raise AssetKitError(f"Duplicate part id '{part.id}' in {context}:{self.id}")
            seen.add(part.id)
            part.validate_invariants(f"{context}:{self.id}")


class Revision(AssetModel):
    """An immutable iteration of an Asset."""

    id: str
    status: str = "provisional"
    recipe: str | None = None
    provenance: Provenance = Field(default_factory=Provenance)
    capabilities: tuple[str, ...] = ()
    exports: tuple[Export, ...] = ()
    frame: CoordinateFrame | None = None

    def validate_invariants(self, asset_id: str) -> None:
        if not self.id.strip():
            raise AssetKitError(f"Revision requires non-empty id in asset '{asset_id}'")
        if self.status not in REVISION_STATUSES:
            raise AssetKitError(f"Invalid revision status '{self.status}' in {asset_id}@{self.id}")
        self.provenance.validate_invariants(f"{asset_id}@{self.id}")
        seen: set[str] = set()
        for exp in self.exports:
            if exp.id in seen:
                raise AssetKitError(f"Duplicate export id '{exp.id}' in {asset_id}@{self.id}")
            seen.add(exp.id)
            exp.validate_invariants(f"{asset_id}@{self.id}")


class Asset(AssetModel):
    """An independently maintained reusable work (authoring unit)."""

    id: str
    title: str
    kind: str
    owner_dir: str
    families: tuple[str, ...] = ()
    concepts: tuple[str, ...] = ()
    revisions: tuple[Revision, ...] = ()
    source_manifest: str | None = None
    unresolved: tuple[str, ...] = ()
    status: str | None = None

    def validate_invariants(self) -> None:
        if not self.id.strip() or not self.owner_dir.strip():
            raise AssetKitError(f"Asset requires non-empty id and owner_dir: {self}")
        if self.kind not in ASSET_KINDS:
            raise AssetKitError(f"Invalid asset kind '{self.kind}' on '{self.id}'")
        seen: set[str] = set()
        for rev in self.revisions:
            if rev.id in seen:
                raise AssetKitError(f"Duplicate revision '{rev.id}' on asset '{self.id}'")
            seen.add(rev.id)
            rev.validate_invariants(self.id)


@dataclass(frozen=True)
class AssetRegistry:
    """Owns all maintained Assets, Revisions, Exports, and Parts."""

    assets: tuple[Asset, ...] = ()

    @classmethod
    def load(
        cls,
        repo: Path,
        *,
        include_legacy_adapters: bool = True,
        inspect_glbs: bool = False,
    ) -> AssetRegistry:
        root = repo.resolve()
        assets, covered_dirs = _load_native_assets(root, inspect_glbs=inspect_glbs)
        manifest_dirs = covered_dirs.copy()
        existing_ids = {a.id for a in assets}
        record_assets = _load_asset_records(
            root, covered_dirs, existing_ids, inspect_glbs=inspect_glbs
        )
        assets.extend(record_assets)
        if include_legacy_adapters:
            atlas = _project_body_atlas(root, covered_dirs, inspect_glbs=inspect_glbs)
            for item in atlas:
                existing_ids.add(item.id)
            assets.extend(atlas)
            export_paths = {
                export.path
                for asset in assets
                for revision in asset.revisions
                for export in revision.exports
            }
            assets.extend(
                _project_directory_packages(
                    root, manifest_dirs, existing_ids, export_paths, inspect_glbs=inspect_glbs
                )
            )
        return cls(assets=tuple(assets))

    @classmethod
    def load_records(cls, repo: Path, paths: Iterable[str]) -> AssetRegistry:
        """Resolve explicit package records without discovering or inspecting other assets."""
        paths = tuple(dict.fromkeys(paths))
        records = tuple(safe_path(repo, path) for path in paths)
        if any(path.name != "asset.record.json" for path in records):
            raise AssetKitError("Expected package-owned asset.record.json paths")
        assets = _load_asset_records(
            repo.resolve(), set(), set(), inspect_glbs=False, record_paths=records
        )
        return cls(assets=tuple(assets))

    def validate(self, vocab: ConceptGraph | None = None) -> list[str]:
        warnings: list[str] = []
        known_concepts = vocab.ids if vocab is not None else set()
        seen: set[str] = set()
        for asset in self.assets:
            if asset.id in seen:
                raise AssetKitError(f"Duplicate asset id '{asset.id}'")
            seen.add(asset.id)
            asset.validate_invariants()
            if known_concepts:
                for cid in asset.concepts:
                    if cid not in known_concepts:
                        warnings.append(f"Asset '{asset.id}' references undeclared concept '{cid}'")
        return warnings

    def get(self, asset_id: str) -> Asset | None:
        return next((a for a in self.assets if a.id == asset_id), None)

    def resolve_export(
        self, asset_id: str, revision_id: str, export_id: str
    ) -> tuple[Asset, Revision, Export] | None:
        asset = self.get(asset_id)
        if asset is None:
            return None
        rev = next((r for r in asset.revisions if r.id == revision_id), None)
        if rev is None:
            return None
        exp = next((e for e in rev.exports if e.id == export_id), None)
        if exp is None:
            return None
        return (asset, rev, exp)

    def require_record_export(self, ref: RecordExportRef) -> tuple[Asset, Revision, Export]:
        """Resolve an export and require the package record named by its reader."""
        key = f"{ref.asset}@{ref.revision}:{ref.export}"
        resolved = self.resolve_export(ref.asset, ref.revision, ref.export)
        if resolved is None:
            raise AssetKitError(f"Unknown package export: {key}")
        if resolved[0].source_manifest != normalize_path(ref.record):
            raise AssetKitError(f"Package export {key} is outside its declared record {ref.record}")
        return resolved

    def require_voxel_export(self, ref: ExportRef, grid: VoxelGrid) -> Export:
        """Resolve a pinned export that can be placed directly on the requested grid."""
        key = f"{ref.asset}@{ref.revision}:{ref.export}"
        resolved = self.resolve_export(ref.asset, ref.revision, ref.export)
        if resolved is None:
            raise AssetKitError(f"Unknown scene export: {key}")
        export = resolved[2]
        if export.frame is not None and export.frame.convention != "voxel-index":
            raise AssetKitError(f"Incompatible coordinate convention for voxel placement: {key}")
        if export.voxel_grid is None:
            raise AssetKitError(f"Missing voxel grid for {key}")
        if export.voxel_grid != grid:
            raise AssetKitError(
                f"Incompatible voxel grid for {key}: expected {grid.to_dict()}, "
                f"got {export.voxel_grid.to_dict()}"
            )
        return export

    def iter_exports(self) -> tuple[tuple[Asset, Revision, Export], ...]:
        return tuple(
            (asset, rev, exp)
            for asset in self.assets
            for rev in asset.revisions
            for exp in rev.exports
        )

    def match_target(self, target: str) -> tuple[set[str], set[str]]:
        """Return (matched_asset_ids, matched_export_paths) for an asset id, key, or path."""
        matched_assets: set[str] = set()
        matched_paths: set[str] = set()
        for asset in self.assets:
            if target in {asset.id, asset.owner_dir}:
                matched_assets.add(asset.id)
            for rev in asset.revisions:
                for exp in rev.exports:
                    export_key = f"{asset.id}@{rev.id}:{exp.id}"
                    if target in {asset.id, asset.owner_dir, export_key, exp.path}:
                        matched_assets.add(asset.id)
                        matched_paths.add(exp.path)
        return matched_assets, matched_paths

    def counts(self) -> dict[str, int]:
        return {
            "assets": len(self.assets),
            "revisions": sum(len(a.revisions) for a in self.assets),
            "exports": sum(len(r.exports) for a in self.assets for r in a.revisions),
            "parts": sum(len(e.parts) for a in self.assets for r in a.revisions for e in r.exports),
        }

    def to_dict(self) -> list[dict[str, Any]]:
        return [a.to_dict() for a in self.assets]


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssetKitError(f"Invalid JSON in {path}: {exc}") from exc


def _rel(repo: Path, path: Path) -> str:
    return path.resolve().relative_to(repo.resolve()).as_posix()


def _build_spatial(
    *,
    units: str | None = None,
    axes: tuple[str, ...] = (),
    laterality: str | None = None,
    source_frame: str | None = None,
    frame: str | None = None,
    transform: tuple[float, ...] | None = None,
    transform_evidence: str | None = None,
) -> SpatialFrame | None:
    if not any((units, axes, laterality, source_frame, frame, transform, transform_evidence)):
        return None
    return SpatialFrame(
        units=units,
        axes=axes,
        laterality=laterality,
        source_frame=source_frame,
        frame=frame,
        transform=transform,
        transform_evidence=transform_evidence,
    )


def _parse_provenance(data: dict[str, Any] | None) -> Provenance:
    if not data:
        return Provenance()
    frame = data.get("spatial") or data
    transform = frame.get("transform")
    spatial = _build_spatial(
        units=frame.get("units"),
        axes=tuple(frame.get("axes", ())),
        laterality=frame.get("laterality"),
        source_frame=frame.get("sourceFrame") or frame.get("source_frame"),
        frame=frame.get("frame"),
        transform=tuple(float(v) for v in transform) if transform is not None else None,
        transform_evidence=frame.get("transformEvidence") or frame.get("transform_evidence"),
    )
    return Provenance(
        source=data.get("source"),
        subject=data.get("subject"),
        license=data.get("license"),
        registration=data.get("registration", "unknown"),
        registration_note=data.get("registrationNote") or data.get("registration_note"),
        spatial=spatial,
        derived_from=data.get("derivedFrom") or data.get("derived_from"),
        limits=tuple(data.get("limits", ())),
    )


def _load_native_assets(repo: Path, *, inspect_glbs: bool) -> tuple[list[Asset], set[str]]:
    assets: list[Asset] = []
    covered_dirs: set[str] = set()
    for manifest in manifests(repo, "assets.json"):
        doc = _read_json(manifest)
        if not isinstance(doc, dict) or doc.get("schemaVersion") != MANIFEST_VERSION:
            continue
        if not isinstance(doc.get("assets"), list):
            raise AssetKitError(f"Expected an assets array in {manifest}")
        owner_dir = _rel(repo, manifest.parent)
        covered_dirs.add(owner_dir)
        for row in doc["assets"]:
            revs: list[Revision] = []
            for rev_row in row.get("revisions", []):
                exports: list[Export] = []
                for exp_row in rev_row.get("exports", []):
                    raw_path = exp_row["path"]
                    full_rel = (
                        raw_path
                        if (repo / raw_path).exists()
                        else normalize_path(f"{owner_dir}/{raw_path}")
                    )
                    chk = verify(repo, full_rel, exp_row.get("sha256"), exp_row.get("bytes"))
                    tris = exp_row.get("triangles")
                    node_tris: dict[str, int] = {}
                    if (
                        inspect_glbs
                        and full_rel.endswith(".glb")
                        and chk.status in {"verified", "hydrated"}
                    ):
                        stats = inspect_mesh(repo, full_rel)
                        if stats is not None:
                            tris = tris if tris is not None else stats.triangles
                            node_tris = stats.node_triangles
                    parts: list[Part] = []
                    for part_row in exp_row.get("parts", []):
                        selectors = tuple(part_row.get("selectors", ()))
                        if not selectors and part_row.get("selector"):
                            selectors = (part_row["selector"],)
                        part_tris = part_row.get("triangles")
                        if part_tris is None and node_tris:
                            for sel in selectors:
                                if sel in node_tris:
                                    part_tris = node_tris[sel]
                                    break
                        parts.append(
                            Part(
                                id=part_row["id"],
                                label=part_row.get("label", part_row["id"]),
                                selectors=selectors,
                                concepts=tuple(part_row.get("concepts", ())),
                                kind=part_row.get("kind", "mesh-node"),
                                selectable=part_row.get("selectable", True),
                                context_only=part_row.get(
                                    "contextOnly", part_row.get("context_only", False)
                                ),
                                bytes=part_row.get("bytes"),
                                triangles=part_tris,
                                provenance=_parse_provenance(part_row.get("provenance"))
                                if part_row.get("provenance")
                                else None,
                            )
                        )
                    exports.append(
                        Export(
                            id=exp_row["id"],
                            path=full_rel,
                            format=exp_row.get(
                                "format", Path(full_rel).suffix.lstrip(".") or "bin"
                            ),
                            role=exp_row.get("role", "teaching-mesh"),
                            variant=exp_row.get("variant", "normal"),
                            sha256=exp_row.get("sha256") or chk.sha256,
                            bytes=exp_row.get("bytes")
                            if exp_row.get("bytes") is not None
                            else chk.bytes,
                            triangles=tris,
                            storage_status=chk.status,
                            parts=tuple(parts),
                        )
                    )
                revs.append(
                    Revision(
                        id=rev_row["id"],
                        status=rev_row.get("status", "provisional"),
                        recipe=rev_row.get("recipe"),
                        provenance=_parse_provenance(
                            rev_row.get("provenance") or rev_row.get("spatial")
                        ),
                        capabilities=tuple(rev_row.get("capabilities", ())),
                        exports=tuple(exports),
                    )
                )
            assets.append(
                Asset(
                    id=row["id"],
                    title=row.get("title", row["id"]),
                    kind=row.get("kind", "model"),
                    owner_dir=owner_dir,
                    families=tuple(row.get("families", ())),
                    concepts=tuple(row.get("concepts", ())),
                    revisions=tuple(revs),
                    source_manifest=_rel(repo, manifest),
                )
            )
    return assets, covered_dirs


def _load_asset_records(
    repo: Path,
    covered_dirs: set[str],
    existing_ids: set[str],
    *,
    inspect_glbs: bool,
    record_paths: tuple[Path, ...] | None = None,
) -> list[Asset]:
    """Read package-owned asset.record.json declarations without synthesizing directory IDs."""
    assets: list[Asset] = []
    for record_path in (
        manifests(repo, "asset.record.json") if record_paths is None else record_paths
    ):
        owner_dir = _rel(repo, record_path.parent)
        doc = _read_json(record_path)
        if not isinstance(doc, dict) or not doc.get("assetId"):
            if record_paths is not None:
                raise AssetKitError(f"Missing assetId in package record: {record_path}")
            continue
        asset_id = str(doc["assetId"])
        if asset_id in existing_ids:
            raise AssetKitError(f"Duplicate asset id {asset_id!r} in {record_path}")
        covered_dirs.add(owner_dir)
        existing_ids.add(asset_id)

        raw_kind = str(doc.get("kind", "model"))
        kind = raw_kind if raw_kind in ASSET_KINDS else "model"

        concepts = tuple(
            str(c["conceptId"])
            for c in doc.get("concepts", [])
            if isinstance(c, dict) and c.get("conceptId")
        )
        sources_by_id: dict[str, dict[str, Any]] = {
            str(s["sourceId"]): s
            for s in doc.get("sources", [])
            if isinstance(s, dict) and s.get("sourceId")
        }
        parts_by_id: dict[str, dict[str, Any]] = {
            str(p["partId"]): p
            for p in doc.get("parts", [])
            if isinstance(p, dict) and p.get("partId")
        }

        revisions: list[Revision] = []
        for rev_row in doc.get("revisions", []):
            if not isinstance(rev_row, dict) or not rev_row.get("revisionId"):
                continue
            rev_id = str(rev_row["revisionId"])
            rev_status = str(rev_row.get("status", "provisional"))
            if rev_status not in REVISION_STATUSES:
                rev_status = "provisional"

            src_ids = [str(s) for s in rev_row.get("sourceIds", []) if isinstance(s, str)]
            primary_src = sources_by_id.get(src_ids[0]) if src_ids else None
            limits: list[str] = []
            for sid in src_ids:
                src = sources_by_id.get(sid)
                if src:
                    limits.extend(str(x) for x in src.get("limitations", []) if isinstance(x, str))

            rev_part_regs = {
                parts_by_id[str(pid)].get("registration")
                for pid in rev_row.get("partIds", [])
                if str(pid) in parts_by_id
            }
            valid_regs = {r for r in rev_part_regs if r in REGISTRATION_STATES}
            rev_reg = (
                next(iter(valid_regs))
                if len(rev_part_regs) == 1 and len(valid_regs) == 1
                else "unknown"
            )

            rev_prov = Provenance(
                source=(
                    primary_src.get("path") or primary_src.get("title")
                    if primary_src is not None
                    else None
                ),
                subject=primary_src.get("subject") if primary_src is not None else None,
                license=(
                    str(primary_src["license"])
                    if primary_src is not None and primary_src.get("license")
                    else None
                ),
                registration=rev_reg,
                limits=tuple(limits),
            )

            exports: list[Export] = []
            rev_frame = rev_row.get("frame")
            seen_eids: set[str] = set()
            for exp_row in rev_row.get("exports", []):
                if not isinstance(exp_row, dict) or not exp_row.get("path"):
                    continue
                exp_path = normalize_path(str(exp_row["path"]))
                base_eid = str(exp_row.get("id") or Path(exp_path).stem)
                eid = base_eid if base_eid not in seen_eids else exp_path
                seen_eids.add(eid)
                chk = (
                    verify(repo, exp_path, exp_row.get("sha256"), exp_row.get("bytes"))
                    if record_paths is None
                    else None
                )
                tris = exp_row.get("triangles")
                node_tris: dict[str, int] = {}
                if (
                    inspect_glbs
                    and exp_path.endswith(".glb")
                    and chk is not None
                    and chk.status in {"verified", "hydrated"}
                ):
                    stats = inspect_mesh(repo, exp_path)
                    if stats is not None:
                        tris = tris if tris is not None else stats.triangles
                        node_tris = stats.node_triangles

                exp_parts: list[Part] = []
                for pid in exp_row.get("partIds", []):
                    prow = parts_by_id.get(str(pid))
                    if prow is None:
                        continue
                    selectors = tuple(
                        str(s) for s in prow.get("selectors", []) if isinstance(s, str)
                    )
                    part_tris = None
                    if node_tris:
                        for sel in selectors:
                            if sel in node_tris:
                                part_tris = node_tris[sel]
                                break
                    raw_reg = prow.get("registration")
                    reg_state = raw_reg if raw_reg in REGISTRATION_STATES else "unknown"
                    reg_note = (
                        str(raw_reg)
                        if isinstance(raw_reg, str) and raw_reg not in REGISTRATION_STATES
                        else None
                    )
                    exp_parts.append(
                        Part(
                            id=str(prow["partId"]),
                            label=str(prow.get("label", prow["partId"])),
                            selectors=selectors,
                            concepts=tuple(
                                str(c) for c in prow.get("conceptIds", []) if isinstance(c, str)
                            ),
                            triangles=part_tris,
                            provenance=Provenance(
                                source=prow.get("sourcePath"),
                                registration=reg_state,
                                registration_note=reg_note,
                                spatial=_build_spatial(
                                    source_frame=prow.get("sourceFrame"),
                                    frame=prow.get("frame"),
                                    transform_evidence=prow.get("transformEvidence"),
                                ),
                            ),
                        )
                    )

                exports.append(
                    Export(
                        id=eid,
                        path=exp_path,
                        format=str(
                            exp_row.get("format") or Path(exp_path).suffix.lstrip(".") or "bin"
                        ),
                        role=str(exp_row.get("role", "teaching-mesh")),
                        variant=str(exp_row.get("variant", "normal")),
                        sha256=exp_row.get("sha256"),
                        bytes=exp_row.get("bytes"),
                        triangles=tris,
                        storage_status=chk.status if chk is not None else "unverified",
                        parts=tuple(exp_parts),
                        voxel_grid=VoxelGrid.model_validate(exp_row["voxelGrid"])
                        if "voxelGrid" in exp_row
                        else None,
                        frame=CoordinateFrame.model_validate(frame)
                        if isinstance(frame := exp_row.get("frame", rev_frame), dict)
                        else None,
                    )
                )

            revisions.append(
                Revision(
                    id=rev_id,
                    status=rev_status,
                    recipe=rev_row.get("recipe"),
                    provenance=rev_prov,
                    exports=tuple(exports),
                    frame=CoordinateFrame.model_validate(rev_frame)
                    if isinstance(rev_frame, dict)
                    else None,
                )
            )

        assets.append(
            Asset(
                id=asset_id,
                title=str(doc.get("title", asset_id)),
                kind=kind,
                owner_dir=owner_dir,
                concepts=concepts,
                revisions=tuple(revisions),
                source_manifest=_rel(repo, record_path),
                unresolved=tuple(str(u) for u in doc.get("unresolved", []) if isinstance(u, str)),
                status=doc.get("status"),
            )
        )
    return assets


def _project_body_atlas(repo: Path, covered_dirs: set[str], *, inspect_glbs: bool) -> list[Asset]:
    manifest = repo / "body/anatomy-workshop-r1/body-3d-delivery/manifest.json"
    if not manifest.is_file() or "body/anatomy-workshop-r1" in covered_dirs:
        return []
    doc = _read_json(manifest)
    coords = doc.get("coordinates", {})
    raw_matrix = coords.get("RASmm_to_scene")
    flat_matrix = (
        tuple(float(v) for row in raw_matrix for v in row)
        if isinstance(raw_matrix, list) and len(raw_matrix) == 4
        else None
    )
    exports: list[Export] = []
    for item in doc.get("assets", []):
        if not isinstance(item, dict) or not item.get("id") or not item.get("file"):
            continue
        rel_path = normalize_path(f"body/anatomy-workshop-r1/body-3d-delivery/{item['file']}")
        chk = verify(repo, rel_path)
        tris = None
        if inspect_glbs and rel_path.endswith(".glb") and chk.status == "hydrated":
            stats = inspect_mesh(repo, rel_path)
            if stats is not None:
                tris = stats.triangles
        item_spatial = _build_spatial(units=coords.get("units"), transform=flat_matrix)
        item_prov = Provenance(
            source=item.get("provenance"),
            subject=item.get("sourceCase"),
            license=item.get("license"),
            registration="native" if item.get("sourceCase") else "unknown",
            spatial=item_spatial,
        )
        organ_ids = tuple(x for x in item.get("organIds", []) if isinstance(x, str))
        parts: list[Part] = [
            Part(
                id=item["id"],
                label=(
                    item.get("name", {}).get("en")
                    if isinstance(item.get("name"), dict)
                    else str(item.get("name", item["id"]))
                ),
                selectors=(item["id"], item["file"], *organ_ids),
                concepts=organ_ids or (item["id"],),
                kind="glb-component",
                provenance=item_prov,
            )
        ]
        seen_part_ids = {item["id"]}
        for node in item.get("nodes", []):
            if not isinstance(node, dict) or not node.get("anatomy_id"):
                continue
            nid = str(node["anatomy_id"])
            if nid in seen_part_ids:
                continue
            seen_part_ids.add(nid)
            derivation = node.get("derivation", "")
            parts.append(
                Part(
                    id=nid,
                    label=str(node.get("name", nid)),
                    selectors=tuple(x for x in (node.get("name"), nid) if isinstance(x, str)),
                    kind="mesh-node",
                    provenance=Provenance(
                        source=item.get("provenance"),
                        subject=item.get("sourceCase"),
                        license=item.get("license"),
                        registration="native" if derivation == "source-derived" else "illustrative",
                        spatial=item_spatial,
                    ),
                )
            )
        exports.append(
            Export(
                id=item["id"],
                path=rel_path,
                format=Path(rel_path).suffix.lstrip(".") or "glb",
                role="atlas-component",
                sha256=chk.sha256,
                bytes=chk.bytes,
                triangles=tris,
                storage_status=chk.status,
                parts=tuple(parts),
            )
        )
    if not exports:
        return []
    return [
        Asset(
            id="s1233-body-delivery",
            title="Body Systems 3D Delivery Atlas",
            kind="assembly",
            owner_dir="body/anatomy-workshop-r1",
            families=("body-and-support",),
            revisions=(
                Revision(
                    id="r1",
                    status="active",
                    provenance=Provenance(
                        subject="s1233",
                        registration="native",
                        spatial=_build_spatial(units=coords.get("units"), transform=flat_matrix),
                    ),
                    capabilities=("isolate-parts",),
                    exports=tuple(exports),
                ),
            ),
            source_manifest=_rel(repo, manifest),
        )
    ]


def _project_directory_packages(
    repo: Path,
    manifest_dirs: set[str],
    existing_ids: set[str],
    export_paths: set[str],
    *,
    inspect_glbs: bool,
) -> list[Asset]:
    kind_map = {
        "models": "model",
        "assemblies": "assembly",
        "diagrams": "diagram",
        "heart": "model",
    }
    assets: list[Asset] = []
    for root_name, kind in kind_map.items():
        root = repo / root_name
        if not root.is_dir():
            continue
        for pkg in sorted(
            p
            for p in root.iterdir()
            if p.is_dir() and not p.is_symlink() and not p.name.startswith(".")
        ):
            owner_dir = _rel(repo, pkg)
            if owner_dir in manifest_dirs:
                continue
            files = sorted(
                f
                for f in pkg.rglob("*")
                if f.suffix.lower() in MODEL_EXTS
                and not f.is_symlink()
                and f.is_file()
                and not any(part in SKIP_DIRS for part in f.relative_to(repo).parts)
                and f.relative_to(repo).as_posix() not in export_paths
            )
            if not files:
                continue
            by_rev: dict[str, list[Path]] = {}
            for f in files:
                rel_in_pkg = f.relative_to(pkg).parts
                if len(rel_in_pkg) >= 3 and rel_in_pkg[0] == "exports":
                    rev_id = rel_in_pkg[1]
                elif len(rel_in_pkg) >= 2:
                    rev_id = rel_in_pkg[0]
                else:
                    rev_id = "unversioned"
                by_rev.setdefault(rev_id, []).append(f)

            revisions: list[Revision] = []
            for rev_id, rev_files in sorted(by_rev.items()):
                exports: list[Export] = []
                seen_eids: set[str] = set()
                for f in rev_files:
                    rel_path = _rel(repo, f)
                    eid = f.name if f.name not in seen_eids else f.relative_to(pkg).as_posix()
                    seen_eids.add(eid)
                    chk = verify(repo, rel_path)
                    tris = None
                    if inspect_glbs and f.suffix.lower() == ".glb" and chk.status == "hydrated":
                        stats = inspect_mesh(repo, rel_path)
                        if stats is not None:
                            tris = stats.triangles
                    exports.append(
                        Export(
                            id=eid,
                            path=rel_path,
                            format=f.suffix.lower().lstrip("."),
                            role="editable-master"
                            if f.suffix.lower() == ".blend"
                            else "teaching-mesh",
                            sha256=chk.sha256,
                            bytes=chk.bytes,
                            triangles=tris,
                            storage_status=chk.status,
                        )
                    )
                revisions.append(Revision(id=rev_id, status="provisional", exports=tuple(exports)))

            slug = pkg.name if pkg.name not in existing_ids else f"{root_name}-{pkg.name}"
            existing_ids.add(slug)
            assets.append(
                Asset(
                    id=slug,
                    title=pkg.name.replace("_", " ").replace("-", " ").title(),
                    kind=kind,
                    owner_dir=owner_dir,
                    revisions=tuple(revisions),
                    status="legacy-candidate",
                )
            )
    return assets
