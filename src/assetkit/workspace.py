"""Workspace loader for AssetKit.

Reads native declarative manifests (concepts.json, assets.json, consumer.json)
and non-invasively projects existing repository layouts for side-by-side testing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model import (
    Asset,
    AssetKitError,
    Catalog,
    Concept,
    ConceptEdge,
    ConceptGraph,
    Consumer,
    Export,
    Part,
    Pin,
    Provenance,
    Requirement,
    Review,
    Revision,
    Selection,
)
from .storage import check_artifact, inspect_glb, normalize_repo_path, safe_path

SKIP_DIRS = frozenset({".git", ".artifacts", "node_modules", "__pycache__", ".venv", "src"})
MODEL_EXTS = frozenset({".glb", ".gltf", ".blend", ".svg", ".obj", ".stl"})


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


def _load_concepts(repo: Path) -> ConceptGraph:
    candidates = [repo / "concepts.json", repo / "sources" / "concepts.json"]
    concepts: list[Concept] = []
    edges: list[ConceptEdge] = []
    for path in candidates:
        if not path.is_file():
            continue
        doc = _read_json(path)
        for row in doc.get("concepts", doc.get("nodes", [])):
            concepts.append(
                Concept(
                    id=row["id"],
                    label=row.get("label", row["id"]),
                    aliases=tuple(row.get("aliases", ())),
                )
            )
        for row in doc.get("edges", []):
            edges.append(
                ConceptEdge(
                    subject=row["subject"],
                    predicate=row["predicate"],
                    object=row["object"],
                    evidence=row.get("evidence"),
                )
            )
    return ConceptGraph(tuple(concepts), tuple(edges))


def _load_native_assets(repo: Path, inspect_glbs: bool) -> tuple[list[Asset], set[str]]:
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
                        else normalize_repo_path(f"{owner_dir}/{raw_path}")
                    )
                    chk = check_artifact(
                        repo, full_rel, exp_row.get("sha256"), exp_row.get("bytes")
                    )
                    tris = exp_row.get("triangles")
                    node_tris: dict[str, int] = {}
                    if (
                        inspect_glbs
                        and full_rel.endswith(".glb")
                        and chk.status in {"verified", "hydrated"}
                    ):
                        stats = inspect_glb(safe_path(repo, full_rel))
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


def _load_native_consumers(repo: Path) -> list[Consumer]:
    consumers: list[Consumer] = []
    for manifest in sorted(repo.rglob("consumer.json")):
        if any(part in SKIP_DIRS for part in manifest.relative_to(repo).parts):
            continue
        owner_path = _rel(repo, manifest)
        doc = _read_json(manifest)
        for row in doc.get("consumers", []):
            reqs = tuple(
                Requirement(
                    id=r["id"],
                    description=r.get("description", r["id"]),
                    status=r.get("status", "open-gap"),
                    concepts=tuple(r.get("concepts", (r["concept"],) if r.get("concept") else ())),
                    parts=tuple(r.get("parts", ())),
                    variant=r.get("variant"),
                    subject=r.get("subject"),
                    capabilities=tuple(r.get("capabilities", ())),
                )
                for r in row.get("requirements", [])
            )
            pins = tuple(
                Pin(
                    asset_id=p["asset"],
                    revision_id=p["revision"],
                    export_id=p["export"],
                    requirement_id=p.get("requirement"),
                    parts=tuple(p.get("parts", ())),
                    sha256=p.get("sha256"),
                    registration=p.get("registration", "unknown"),
                    transform=tuple(float(v) for v in p["transform"])
                    if p.get("transform") is not None
                    else None,
                    limits=tuple(p.get("limits", ())),
                )
                for p in row.get("pins", [])
            )
            consumers.append(
                Consumer(
                    id=row["id"],
                    title=row.get("title", row["id"]),
                    kind=row.get("kind", "other"),
                    owner_path=owner_path,
                    requirements=reqs,
                    pins=pins,
                    local_files=tuple(row.get("localFiles", ())),
                )
            )
    return consumers


def _project_existing_body_atlas(
    repo: Path, covered_dirs: set[str], inspect_glbs: bool
) -> list[Asset]:
    """Project body-3d-delivery/manifest.json as one multi-export Atlas Asset."""
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
        rel_path = normalize_repo_path(f"body/anatomy-workshop-r1/body-3d-delivery/{item['file']}")
        chk = check_artifact(repo, rel_path)
        tris = None
        if inspect_glbs and rel_path.endswith(".glb") and chk.status == "hydrated":
            stats = inspect_glb(safe_path(repo, rel_path))
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
        parts: list[Part] = []
        # Include the delivery component itself as a selectable part token + its child nodes
        organ_ids = tuple(x for x in item.get("organIds", []) if isinstance(x, str))
        parts.append(
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
        )
        seen_part_ids = {item["id"]}
        for node in item.get("nodes", []):
            if not isinstance(node, dict) or not node.get("anatomy_id"):
                continue
            nid = str(node["anatomy_id"])
            if nid in seen_part_ids:
                continue
            seen_part_ids.add(nid)
            derivation = node.get("derivation", "")
            node_prov = Provenance(
                source=item.get("provenance"),
                subject=item.get("sourceCase"),
                license=item.get("license"),
                units=coords.get("units"),
                registration="native" if derivation == "source-derived" else "illustrative",
                transform=flat_matrix,
            )
            parts.append(
                Part(
                    id=nid,
                    label=str(node.get("name", nid)),
                    selectors=tuple(x for x in (node.get("name"), nid) if isinstance(x, str)),
                    kind="mesh-node",
                    provenance=node_prov,
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


def _project_existing_packages(
    repo: Path, covered_dirs: set[str], existing_ids: set[str], inspect_glbs: bool
) -> list[Asset]:
    """Non-invasively discover reusable assets under models/, assemblies/, diagrams/, heart/."""
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
            # Group files by their revision folder (e.g., exports/<rev>/file)
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
                    eid = f.name
                    if eid in seen_eids:
                        eid = f.relative_to(pkg).as_posix()
                    seen_eids.add(eid)
                    chk = check_artifact(repo, rel_path)
                    tris = None
                    if inspect_glbs and f.suffix.lower() == ".glb" and chk.status == "hydrated":
                        stats = inspect_glb(f)
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

            slug = pkg.name
            if slug in existing_ids:
                slug = f"{root_name}-{pkg.name}"
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


def _project_existing_consumers(repo: Path, existing_ids: set[str]) -> list[Consumer]:
    consumers: list[Consumer] = []

    # 1. Body Systems reviewed stops
    stops_path = repo / "lessons/body-systems/reviewed-stops.json"
    if stops_path.is_file():
        doc = _read_json(stops_path)
        for row in doc.get("stops", []):
            cid = f"body-systems:{row['system']}:{row['detail']}"
            if cid in existing_ids:
                continue
            existing_ids.add(cid)
            consumers.append(
                Consumer(
                    id=cid,
                    title=f"{str(row['system']).title()} · {row['detail']}",
                    kind="lesson-stop",
                    owner_path=_rel(repo, stops_path),
                    requirements=(
                        Requirement(
                            id=row["detail"],
                            description=row["action"],
                            status="satisfied" if row.get("status") == "passed" else "provisional",
                        ),
                    ),
                )
            )

    # 2. Ultrasound sweep tracks (structured JSON only — no JS regex scraping)
    us_dir = repo / "experiments/ultrasound-sweep"
    if us_dir.is_dir():
        for track_file in sorted(us_dir.glob("*-track*.json")):
            doc = _read_json(track_file)
            common = doc.get("common", {})
            for sweep in doc.get("sweeps", []):
                if not isinstance(sweep, dict) or not sweep.get("id"):
                    continue
                cid = f"ultrasound:sweep:{track_file.stem}:{sweep['id']}"
                if cid in existing_ids:
                    continue
                existing_ids.add(cid)
                case = sweep.get("case", common.get("case"))
                parts = tuple(
                    p for p in sweep.get("parts", common.get("parts", [])) if isinstance(p, str)
                )
                reqs = tuple(
                    Requirement(
                        id=f"part:{p}",
                        description=f"Ultrasound sweep anatomy part '{p}'",
                        status="provisional",
                        parts=(p,),
                        subject=case,
                    )
                    for p in parts
                )
                consumers.append(
                    Consumer(
                        id=cid,
                        title=sweep.get("title", sweep["id"]),
                        kind="ultrasound-sweep",
                        owner_path=_rel(repo, track_file),
                        requirements=reqs,
                    )
                )
    return consumers


def _project_existing_reviews_and_selections(repo: Path) -> tuple[list[Review], list[Selection]]:
    reviews: list[Review] = []
    review_dir = repo / "reviews/teaching-assessments"
    if review_dir.is_dir():
        for path in sorted(review_dir.rglob("*.json")):
            doc = _read_json(path)
            if not isinstance(doc, dict):
                continue
            rows = doc.get("assessments")
            if not isinstance(rows, list):
                rows = [doc] if "export" in doc and "task" in doc else []
            for idx, row in enumerate(rows, 1):
                if not isinstance(row, dict) or "export" not in row or "task" not in row:
                    continue
                exp = row["export"]
                exp_path = exp.get("path") if isinstance(exp, dict) else None
                if not isinstance(exp_path, str):
                    continue
                task_id = str(row.get("taskId") or row.get("id") or f"{path.stem}:{idx}")
                target_status = (row.get("target") or {}).get("status", "accepted")
                status = "blocked" if target_status == "blocked" else "accepted"
                rid = f"review:{_rel(repo, path)}#{idx}"
                axes = row.get("axes")
                scores = (
                    {
                        f"axis{i + 1}": a.get("score")
                        for i, a in enumerate(axes)
                        if isinstance(a, dict)
                    }
                    if isinstance(axes, list)
                    else (axes if isinstance(axes, dict) else {})
                )
                reviews.append(
                    Review(
                        id=rid,
                        export_path=exp_path,
                        task_id=task_id,
                        task=str(row["task"]),
                        status=status,
                        owner_path=_rel(repo, path),
                        sha256=exp.get("sha256"),
                        scores=scores,
                    )
                )

    selections: list[Selection] = []
    sel_path = repo / "docs/gallery/maintained-selections.json"
    if sel_path.is_file():
        doc = _read_json(sel_path)
        seq = 0
        for col in doc.get("collections", []):
            if not isinstance(col, dict):
                continue
            col_id = col.get("id")
            for fam in col.get("families", []):
                if not isinstance(fam, dict):
                    continue
                fam_id = fam.get("id")
                for exp in fam.get("exports", []):
                    if not isinstance(exp, dict) or not exp.get("path"):
                        continue
                    seq += 1
                    selections.append(
                        Selection(
                            id=f"selection:{seq}:{col_id}:{fam_id}",
                            kind="teaching-default",
                            export_path=str(exp["path"]),
                            owner_path=_rel(repo, sel_path),
                            collection_id=col_id,
                            family_id=fam_id,
                            task_id=exp.get("taskId"),
                            review_id=exp.get("assessmentSha256"),
                        )
                    )
    return reviews, selections


def load_catalog(
    repo: Path,
    *,
    include_legacy_adapters: bool = True,
    inspect_glbs: bool = False,
) -> Catalog:
    """Load an AssetKit Catalog from native manifests and optional legacy repo adapters."""
    root = repo.resolve()
    concepts = _load_concepts(root)
    assets, covered_dirs = _load_native_assets(root, inspect_glbs=inspect_glbs)
    consumers = _load_native_consumers(root)
    reviews: list[Review] = []
    selections: list[Selection] = []

    if include_legacy_adapters:
        existing_asset_ids = {a.id for a in assets}
        atlas_assets = _project_existing_body_atlas(root, covered_dirs, inspect_glbs=inspect_glbs)
        for a in atlas_assets:
            existing_asset_ids.add(a.id)
        assets.extend(atlas_assets)
        assets.extend(
            _project_existing_packages(
                root, covered_dirs, existing_asset_ids, inspect_glbs=inspect_glbs
            )
        )
        existing_consumer_ids = {c.id for c in consumers}
        consumers.extend(_project_existing_consumers(root, existing_consumer_ids))
        rev, sel = _project_existing_reviews_and_selections(root)
        reviews.extend(rev)
        selections.extend(sel)

    return Catalog(
        repository=str(root),
        concepts=concepts,
        assets=tuple(assets),
        consumers=tuple(consumers),
        reviews=tuple(reviews),
        selections=tuple(selections),
    )
