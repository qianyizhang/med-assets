"""Supply / authoring context: AssetRegistry, Asset aggregates, and per-part Provenance."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .blobs import inspect_mesh, normalize_path, verify
from .errors import AssetKitError
from .vocab import ConceptGraph

ASSET_KINDS = frozenset({"model", "assembly", "diagram", "rig", "generator", "detail"})
REVISION_STATUSES = frozenset({"provisional", "active", "deprecated", "retired"})
REGISTRATION_STATES = frozenset(
    {"native", "registered", "fitted", "illustrative", "synthetic", "unknown"}
)
SKIP_DIRS = frozenset({".git", ".artifacts", "node_modules", "__pycache__", ".venv", "src"})
MODEL_EXTS = frozenset({".glb", ".gltf", ".blend", ".svg", ".obj", ".stl"})


@dataclass(frozen=True)
class Provenance:
    """Source, subject, spatial frame, and registration honesty record."""

    source: str | None = None
    subject: str | None = None
    license: str | None = None
    units: str | None = None
    axes: tuple[str, ...] = ()
    laterality: str | None = None
    registration: str = "unknown"
    transform: tuple[float, ...] | None = None
    derived_from: str | None = None
    limits: tuple[str, ...] = ()

    def validate(self, context: str) -> None:
        if self.registration not in REGISTRATION_STATES:
            raise AssetKitError(f"Invalid registration '{self.registration}' in {context}")
        if self.transform is not None and len(self.transform) != 16:
            raise AssetKitError(f"Transform matrix must have 16 values in {context}")


@dataclass(frozen=True)
class Part:
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

    def validate(self, context: str) -> None:
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
            self.provenance.validate(f"{context}:part:{self.id}")


@dataclass(frozen=True)
class Export:
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

    def validate(self, context: str) -> None:
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
            part.validate(f"{context}:{self.id}")


@dataclass(frozen=True)
class Revision:
    """An immutable iteration of an Asset."""

    id: str
    status: str = "provisional"
    recipe: str | None = None
    provenance: Provenance = field(default_factory=Provenance)
    capabilities: tuple[str, ...] = ()
    exports: tuple[Export, ...] = ()

    def validate(self, asset_id: str) -> None:
        if not self.id.strip():
            raise AssetKitError(f"Revision requires non-empty id in asset '{asset_id}'")
        if self.status not in REVISION_STATUSES:
            raise AssetKitError(f"Invalid revision status '{self.status}' in {asset_id}@{self.id}")
        self.provenance.validate(f"{asset_id}@{self.id}")
        seen: set[str] = set()
        for exp in self.exports:
            if exp.id in seen:
                raise AssetKitError(f"Duplicate export id '{exp.id}' in {asset_id}@{self.id}")
            seen.add(exp.id)
            exp.validate(f"{asset_id}@{self.id}")


@dataclass(frozen=True)
class Asset:
    """An independently maintained reusable work (authoring unit)."""

    id: str
    title: str
    kind: str
    owner_dir: str
    families: tuple[str, ...] = ()
    concepts: tuple[str, ...] = ()
    revisions: tuple[Revision, ...] = ()
    source_manifest: str | None = None

    def validate(self) -> None:
        if not self.id.strip() or not self.owner_dir.strip():
            raise AssetKitError(f"Asset requires non-empty id and owner_dir: {self}")
        if self.kind not in ASSET_KINDS:
            raise AssetKitError(f"Invalid asset kind '{self.kind}' on '{self.id}'")
        seen: set[str] = set()
        for rev in self.revisions:
            if rev.id in seen:
                raise AssetKitError(f"Duplicate revision '{rev.id}' on asset '{self.id}'")
            seen.add(rev.id)
            rev.validate(self.id)


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
        if include_legacy_adapters:
            existing_ids = {a.id for a in assets}
            atlas = _project_body_atlas(root, covered_dirs, inspect_glbs=inspect_glbs)
            for item in atlas:
                existing_ids.add(item.id)
            assets.extend(atlas)
            assets.extend(
                _project_directory_packages(
                    root, covered_dirs, existing_ids, inspect_glbs=inspect_glbs
                )
            )
        return cls(tuple(assets))

    def validate(self, vocab: ConceptGraph | None = None) -> list[str]:
        warnings: list[str] = []
        known_concepts = vocab.ids if vocab is not None else set()
        seen: set[str] = set()
        for asset in self.assets:
            if asset.id in seen:
                raise AssetKitError(f"Duplicate asset id '{asset.id}'")
            seen.add(asset.id)
            asset.validate()
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
        return [asdict(a) for a in self.assets]


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssetKitError(f"Invalid JSON in {path}: {exc}") from exc


def _rel(repo: Path, path: Path) -> str:
    return path.resolve().relative_to(repo.resolve()).as_posix()


def _parse_provenance(data: dict[str, Any] | None) -> Provenance:
    if not data:
        return Provenance()
    transform = data.get("transform")
    return Provenance(
        source=data.get("source"),
        subject=data.get("subject"),
        license=data.get("license"),
        units=data.get("units"),
        axes=tuple(data.get("axes", ())),
        laterality=data.get("laterality"),
        registration=data.get("registration", "unknown"),
        transform=tuple(float(v) for v in transform) if transform is not None else None,
        derived_from=data.get("derivedFrom") or data.get("derived_from"),
        limits=tuple(data.get("limits", ())),
    )


def _load_native_assets(repo: Path, *, inspect_glbs: bool) -> tuple[list[Asset], set[str]]:
    assets: list[Asset] = []
    covered_dirs: set[str] = set()
    for manifest in sorted(repo.rglob("assets.json")):
        if any(part in SKIP_DIRS for part in manifest.relative_to(repo).parts):
            continue
        owner_dir = _rel(repo, manifest.parent)
        covered_dirs.add(owner_dir)
        doc = _read_json(manifest)
        for row in doc.get("assets", []):
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
        item_prov = Provenance(
            source=item.get("provenance"),
            subject=item.get("sourceCase"),
            license=item.get("license"),
            units=coords.get("units"),
            registration="native" if item.get("sourceCase") else "unknown",
            transform=flat_matrix,
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
                        units=coords.get("units"),
                        registration="native" if derivation == "source-derived" else "illustrative",
                        transform=flat_matrix,
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
                        units=coords.get("units"),
                        registration="native",
                        transform=flat_matrix,
                    ),
                    capabilities=("isolate-parts",),
                    exports=tuple(exports),
                ),
            ),
            source_manifest=_rel(repo, manifest),
        )
    ]


def _project_directory_packages(
    repo: Path, covered_dirs: set[str], existing_ids: set[str], *, inspect_glbs: bool
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
        for pkg in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")):
            owner_dir = _rel(repo, pkg)
            if owner_dir in covered_dirs:
                continue
            files = sorted(
                f
                for f in pkg.rglob("*")
                if f.is_file()
                and f.suffix.lower() in MODEL_EXTS
                and not any(part in SKIP_DIRS for part in f.relative_to(repo).parts)
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
                )
            )
    return assets
