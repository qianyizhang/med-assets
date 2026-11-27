# AssetKit

**AssetKit** is a Python 3.12 library and CLI for developing, reviewing, and delivering reusable 3D medical teaching assets.

It is designed around three goals:
1. **Maintain fewer assets** by separating authoring lineages from runtime delivery payloads.
2. **Support 3D work at different scales**, from whole-body assemblies to a single structure, with stable parts and explicit coordinate frames.
3. **Maximize reuse without payload bloat** through measurable delivery economy (load count, part/byte utilization, and soft/hard size caps).

See [DESIGN.md](DESIGN.md) for ownership, delivery rules, and architectural decisions. The [PRD](PRD.md#liver-sweep-pilot) specifies the liver sweep pilot and its acceptance checks. The quickstart below describes the current CLI, including support for existing consumer records.

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
