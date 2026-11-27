# AssetKit

**AssetKit** is a standalone, zero-dependency Python 3.12 library and CLI for medical teaching asset management.

It is designed around three goals:
1. **Maintain fewer assets** by separating authoring lineages from runtime delivery payloads.
2. **Cover all teaching use cases** across arbitrary anatomical scales (whole body → system → organ → vessel → tissue/cell) and modalities (3D meshes, assemblies, 2D diagrams, rigs, procedural generators).
3. **Maximize reuse without payload bloat** through measurable delivery economy (load count, part/byte utilization, and soft/hard size caps).

See [DESIGN.md](DESIGN.md) for the canonical domain model, on-disk schemas, and merge/split/overlay principles.

## Quickstart

Sync the `uv` environment (`uv sync`) and run from the repository root:

```sh
# Validate catalog integrity (concept DAG, provenance, pins, artifact hashes)
uv run assetkit validate

# Produce a deterministic JSON snapshot of the catalog
uv run assetkit scan

# Compute reuse, load fan-out, part/byte utilization, and merge/split advice
uv run assetkit economy

# Trace affected consumers, reviews, and selections for an asset, export, or path
uv run assetkit impact liver

# Resolve candidate assets/parts for a consumer's requirements
uv run assetkit resolve ultrasound:sweep:abdomen-tracks:liver
```

## Module Layout

| Module | Responsibility |
| --- | --- |
| `assetkit.model` | The 6 first-class domain types (`Concept`, `Asset`, `Revision`, `Consumer`, `Review`, `Selection`), value objects, and structural validators. |
| `assetkit.storage` | Safe repository path checks, Git LFS pointer vs. hydrated byte verification, and stdlib GLB node/triangle/byte inspection. |
| `assetkit.economy` | Reuse & delivery economy engine: `loads`, `part_utilization`, `byte_utilization`, budget checks, merge/split recommendations, `impact()`, and `resolve()`. |
| `assetkit.workspace` | Declarative manifest loader (`assets.json`, `consumer.json`, `concepts.json`, `reviews/`, `selections.json`) plus non-invasive repository readers. |
| `assetkit.cli` | Deterministic JSON command-line interface. |

## Running Tests

```sh
uv run python -m unittest discover -s src/assetkit/tests -v
```
