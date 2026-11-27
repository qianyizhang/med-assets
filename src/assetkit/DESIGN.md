# AssetKit Design

## 1. Design Goals

Medical teaching repositories face a structural tension:
- **Authors want fewer maintained assets** and maximum reuse: edit an organ contour once and propagate improvements to every lesson, tour, and viewer.
- **Use cases want tailored granularity and variations**: an overview stop only needs an outer liver surface; an ultrasound sweep needs internal portal/hepatic veins; a pathology case needs a fatty appearance or focal lesion; a micro-anatomy lesson zooms into bone marrow or blood cells.
- **Runtimes want lean payloads**: loading a 15 MB multi-part file just to show one exterior shell wastes bandwidth and GPU memory, while splitting every vessel into 40 tiny files creates excessive load fan-out.

AssetKit resolves this tension through **DDD bounded contexts** built as **deep modules** (small interfaces hiding real complexity behind clean seams), separating the **Authoring Plane** from the **Delivery Plane**, decoupling **Concept granularity** from **Asset granularity**, and governing packaging with **automated economy metrics**.

---

## 2. Submodule Architecture (6 Bounded Contexts)

```
                        ┌───────────────────────────────┐
                        │  assetkit.cli / Workspace     │  ← Thin facade & CLI
                        └───────┬───────┬───────┬───────┘
                                │       │       │
          ┌─────────────────────▼─┐   ┌─▼───────▼────────────┐   ┌───────────────────────┐
          │   assetkit.delivery   │   │  assetkit.curation   │   │    assetkit.build     │
          │  Demand & Packaging   │   │  Evidence & Release  │   │   Recipe Execution &  │
          │  (Consumers, Bundles, │   │  (Reviews, Selections│   │   Manifest Sync Seam  │
          │   Economy, Gaps,      │   │   Gallery/R2 compile)│   │  (BuildRunner, Sync)  │
          │   Resolution, Impact) │   └──────────┬───────────┘   └───────────┬───────────┘
          └──────────┬────────────┘              │                           │
                     └───────────────────────────┼───────────────────────────┘
                                                 ▼
                                   ┌───────────────────────────┐
                                   │     assetkit.registry     │  ← Authoring & Supply
                                   │  (Assets, Revisions,      │
                                   │   Exports, Parts,         │
                                   │   Per-Part Provenance)    │
                                   └──────┬─────────────┬──────┘
                                          │             │
                            ┌─────────────▼──┐       ┌──▼─────────────┐
                            │ assetkit.vocab │       │ assetkit.blobs │  ← Foundation
                            │ (Concept DAG)  │       │ (Path, LFS,    │
                            └────────────────┘       │  GLB Stats)    │
                                                     └────────────────┘
```

| Submodule | Bounded Context | Owns (Aggregates / Value Objects) | Deep Interface (Key Operations) | Complexity Hidden |
| --- | --- | --- | --- | --- |
| `assetkit.blobs` | Foundation / Storage Truth | `BlobRef`, `MeshStats` | `normalize_path`, `verify`, `inspect_mesh` | Symlink/path-escape guards, Git LFS pointer vs. hydrated SHA-256 streaming, stdlib GLB v2 decoding. |
| `assetkit.vocab` | Semantic Vocabulary | `ConceptGraph`, `Concept`, `ConceptEdge` | `load`, `validate`, `expand`, `ancestors`, `descendants`, `related` | Polyhierarchical DAG cycle checks, multi-parent zoom traversal, cross-system functional edges. |
| `assetkit.registry` | Authoring & Supply | `AssetRegistry`, `Asset`, `Revision`, `Export`, `Part`, `Provenance`, `SpatialFrame` | `load`, `validate`, `get`, `resolve_export`, `match_target` | 1-to-N package→asset mapping, `asset.record.json` & `assets.json` loading, multi-export atlases, per-part provenance & spatial frames. |
| `assetkit.build` | Recipe Execution & Sync | `BuildSpec`, `BuildResult`, `BuildRunner`, `SyncDiff` | `plan_build`, `run_build`, `sync_manifest` | Python vs. headless Blender recipe dispatch behind a swappable `BuildRunner` seam, dry-run planning, hash/triangle manifest refresh. |
| `assetkit.delivery` | Demand & Packaging | `DeliveryGraph`, `Consumer`, `Requirement`, `Pin`, `RuntimeBundle`, `BudgetPolicy`, `EconomyReport`, `ImpactResult`, `ResolveResult` | `load`, `validate`, `bundle_for`, `resolve`, `open_gaps`, `economy`, `impact` | Pin hash verification, runtime load bundling, utilization/budget math, merge/split/overlay heuristics, legacy consumer adapters. |
| `assetkit.curation` | Evidence & Release | `CurationStore`, `Review`, `Qualification`, `Adoption`, `Selection`, `QualificationStatus`, `GalleryProjection` | `load`, `validate`, `qualification_for`, `compile_gallery`, `plan_r2_sync` | Exact-digest assessment/qualification/adoption separation, *reviewed* vs. *qualified* vs. *selected* vs. *shipped*, downstream Gallery & R2 projections. |

---

## 3. Core Concepts & Invariants

1. **`Concept` (`assetkit.vocab`):** Polyhierarchical DAG created on demand at any zoom level (`skeletal-system` → `vertebral-column` → `L3-vertebra` → `bone-marrow` → `blood-cell`). Hierarchical edges (`part_of`, `is_a`) are acyclic; cross-cutting edges (`located_in`, `produces`, `participates_in`, `supplied_by`, `drains_to`) connect across systems. Completely decoupled from Asset granularity.
2. **`Asset` & `Revision` (`assetkit.registry`):** Authoring unit (`model | assembly | diagram | rig | generator | detail`), **not** 1:1 with directories or source subjects. Hybrids and foreign-lineage details are first-class via per-part `Provenance`, composed `SpatialFrame`, and `registration` (`native | registered | fitted | illustrative | synthetic | unknown`).
3. **`Consumer` (`assetkit.delivery`):** Authored teaching experience or surface owning machine-readable `Requirements` (including `open-gap` / `rebuild-required`) and exact `Pins` (`asset@rev:export`, `parts`, `sha256`, `registration`, optional `transform`).
4. **`Review`, `Qualification`, `Adoption` & `Selection` (`assetkit.curation`):** `Review` is immutable dated assessment evidence bound to an exact non-null export `sha256`; `Qualification` is an explicit task/scope approval decision (never inferred from an accepted assessment, missing digest, or anatomical naming); `Adoption` records an owner-declared consumer use (`provisional` until qualified); `Selection` is an explicit editorial/release choice.

The Gallery export flag summarizes exact-digest decisions across uses. Resolution filters those decisions to the requested task, consumer and part. Revision-only decisions remain visible in the asset record. The R2 projection inventories demand for the transport owner.

### Modeling & Serialization Rules (`assetkit.models`)

- **Use `AssetModel` (Pydantic v2 `BaseModel`)** with `frozen=True`, `alias_generator=to_camel`, `populate_by_name=True`, and `extra="forbid"` for serialized records and query results. Workspace and the in-memory stores compose those records.
- **No ad-hoc `dict[str, Any]` builders in queries or projections:** `show`, `find`, `impact`, `resolve`, `bundle`, `compile_gallery`, and `plan_r2_sync` return typed `AssetModel`s (or discriminated unions like `ShowAssetResult | ShowConsumerResult | UnknownTargetResult`).
- **Decompose optional field bags into composed value objects:** attach cohesive sub-models (e.g., `Provenance.spatial: SpatialFrame | None`) instead of flattening 10+ `| None` fields onto one struct, and serialize via `to_dict()` / `to_json()` (`exclude_none=True`) so JSON output omits unset fields.
- **Expose cross-module queries on `Workspace`:** callers use `ws.show()`, `ws.find()`, `ws.impact()`, `ws.resolve()`, `ws.bundle()`, `ws.economy()`, `ws.compile_gallery()`, and `ws.plan_r2_sync()`, while individual submodules remain directly testable.

---

## 4. Authoring-vs-Delivery Economy & Merge/Split Rules

`delivery.economy(registry, policy)` computes `loads`, `part_utilization`, `byte_utilization`, and `reuse` against configurable soft/hard caps (default: export `1.5 MB` / `4.0 MB`, `50k` / `150k` tris; consumer `5 MB` / `12 MB`, `5` / `12` loads; minimum `35%` utilization):

| Trigger / Situation | Rule |
| --- | --- |
| Same lineage, different granularity (outer surface vs. internal vessels) | **1 Asset → Split Exports** (lightweight base + additive detail overlay in the same frame). |
| Surface or pathology variation (fatty, focal lesion, cutaway) | **Variant / Composable Overlay** over cloning the base Asset. |
| Foreign-lineage detail fits a task better (e.g., authored lesion on CT liver) | **Composable Overlay or Baked Hybrid** with explicit per-part/pin `provenance` + `registration: illustrative \| fitted`. |
| Low utilization (`< 35%`) or export exceeds soft byte/tri cap | **Split Export** (`split-export` recommendation). |
| High load fan-out (`loads > 5`) with tightly co-loaded exports under byte cap | **Merge Exports** (`merge-bundle` recommendation). |
| Sub-structure needs its own scale, recipe, or independent release cycle | **Promote Part → New Asset** mapped to the same `Concept`. |
| Frozen historical evidence or incompatible stylized deformation | **Explicit Duplicate** with `derived_from` provenance and retention reason. |

---

## 5. Architectural Alternatives & Trade-offs

We evaluated two alternative boundary cuts before settling on the 6-submodule layout above:

| Alternative | Trade-off vs. Current 6-Submodule Layout |
| --- | --- |
| **Fold `curation` into `delivery` (and/or split `economy` out)** | Fewer top-level files, *but* conflates **consumer demand** (what a lesson/tour needs and loads) with **editorial/release governance** (who reviewed an export, which revision is recommended in Gallery, what gets uploaded to R2). Keeping `curation` separate preserves the invariant that *used*, *reviewed*, and *selected* are independent lifecycles. If `delivery` grows later, `economy` can become a private internal module behind `delivery`'s interface without breaking callers. |
| **Keep build observation inside `registry.sync_package()` instead of `assetkit.build`** | Simpler if `assetkit` never invokes recipes. Having a dedicated `assetkit.build` submodule with a `BuildRunner` Protocol seam gives recipes a uniform dry-run/execute/verify/sync contract (covering Python scripts, headless Blender, and test fakes) while keeping `registry` pure and side-effect-free. |
