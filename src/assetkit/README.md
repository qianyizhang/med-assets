# AssetKit

**AssetKit** is a standalone Python 3.12 library (Pydantic v2 domain models + Typer CLI) for medical teaching asset management, structured as **6 DDD bounded contexts**.

It is designed around three goals:
1. **Maintain fewer assets** by separating authoring lineages from runtime delivery payloads.
2. **Cover all teaching use cases** across arbitrary anatomical scales (whole body → system → organ → vessel → tissue/cell) and modalities (3D meshes, assemblies, 2D diagrams, rigs, procedural generators).
3. **Maximize reuse without payload bloat** through measurable delivery economy (load count, part/byte utilization, and soft/hard size caps).

See [DESIGN.md](DESIGN.md) for the DDD submodule architecture, invariants, economy rules, and trade-offs, and [PRD.md](PRD.md) for the post-port estimate, APIs, and Ultrasound Anatomy workflows.

## Quickstart

Sync the `uv` environment (`uv sync`) and run from the repository root:

```sh
# Check index structure and declared relationships
uv run assetkit validate

# Discover and inspect maintained assets, parts, assessments, and decisions
uv run assetkit find cardiac-atlas
uv run assetkit show anatomy:heart:cardiac-atlas

# Compute reuse, load fan-out, part/byte utilization, and merge/split advice
uv run assetkit economy

# Trace affected consumers, reviews, and selections for an asset, export, or path
uv run assetkit impact liver

# Resolve candidate assets/parts for a consumer's requirements
uv run assetkit resolve ultrasound:sweep:abdomen-tracks:liver

# Plan declared loads and inspect storage status, or list indexed anatomy gaps
uv run assetkit bundle <consumer-id>
uv run assetkit gaps --prefix ultrasound:

# Plan/execute a revision recipe or sync manifest hashes/GLB stats from disk
uv run assetkit build <asset-id> <revision-id> [--apply]
uv run assetkit sync <package>/assets.json [--apply]

# Inspect Gallery entries or R2 demand from selections and consumer pins
uv run assetkit compile --target gallery
uv run assetkit compile --target r2
```

A bundle preserves one item per use, including its transform. Totals count each pinned export once. Check each item’s storage status and digest before runtime use. The R2 projection lists demand. The transport owner controls upload admission.

## Submodules (Bounded Contexts)

| Submodule | Context | Responsibility |
| --- | --- | --- |
| `assetkit.blobs` | Foundation | Safe repository path checks, Git LFS pointer vs. hydrated byte verification, and stdlib GLB v2 mesh stats. |
| `assetkit.vocab` | Semantic | Polyhierarchical `ConceptGraph` DAG decoupled from asset granularity. |
| `assetkit.registry` | Supply / Authoring | `AssetRegistry`, `Asset → Revision → Export → Part` aggregates, per-part `Provenance`/`Registration`. |
| `assetkit.build` | Build & Sync Seam | Recipe `BuildSpec`/`BuildRunner` execution seam (Python & headless Blender) and `sync_manifest()`. |
| `assetkit.delivery` | Demand & Packaging | `DeliveryGraph`, `Consumer` requirements & pins, `bundle_for()`, `resolve()`, `open_gaps()`, `economy()`, `impact()`. |
| `assetkit.curation` | Evidence & Release | `CurationStore`, immutable `Review`s, editorial `Selection`s, `compile_gallery()`, `plan_r2_sync()`. |
| `assetkit.cli` | Interface | Thin deterministic JSON CLI over `Workspace`. |

## Running Tests

```sh
uv run pytest
```
