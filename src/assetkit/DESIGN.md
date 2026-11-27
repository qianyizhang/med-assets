# AssetKit Design

## 1. Design Goals

Medical teaching repositories face a fundamental structural tension:
- **Authors want fewer maintained assets** and maximum reuse: edit an organ contour once and propagate improvements to every lesson, tour, and viewer.
- **Use cases want tailored granularity and variations**: an overview stop only needs an outer liver surface; an ultrasound sweep needs internal portal/hepatic veins; a pathology case needs a fatty appearance or focal lesion; a micro-anatomy lesson zooms into bone marrow or blood cells.
- **Runtimes want lean payloads**: loading a 15 MB multi-part file just to show one exterior shell wastes bandwidth and GPU memory, while splitting every vessel into 40 tiny files creates excessive load fan-out.

AssetKit resolves this tension by **separating the Authoring Plane from the Delivery Plane**, decoupling **Concept granularity from Asset granularity**, and governing packaging with **automated economy metrics**.

---

## 2. Core Concepts

AssetKit has **6 first-class entities**. Everything else (`Package`, `Export`, `Part`, `Provenance`, `Requirement`, `Pin`, `Artifact`) is a structured value object owned by one of these six.

### 2.1 `Concept` (Semantic Vocabulary — Polyhierarchical DAG)
An anatomical, physiological, or clinical entity (e.g., `skeletal-system`, `vertebral-column`, `L3-vertebra`, `bone-marrow`, `blood-cell`, `liver`, `hepatic-vein`, `focal-lesion`).
- **Created on demand at any zoom level.** There is no fixed taxonomic depth.
- **Polyhierarchical & acyclic:** Hierarchical edges (`part_of`, `is_a`) form a DAG (a concept may have multiple parents, cycles are rejected). Cross-cutting functional/spatial edges (`located_in`, `produces`, `participates_in`, `supplied_by`, `drains_to`, `articulates_with`) connect across systems (e.g., `bone-marrow` is `located_in` `bone`, `produces` `blood-cell`, and `participates_in` `immune-response`).
- **Decoupled from Assets:** One Concept can be satisfied by a coarse `Part` inside a whole-body `Asset` *and* by a dedicated high-detail `Asset`. A detail can graduate into its own `Asset` later without breaking historical references—both map to the same `Concept`.

### 2.2 `Asset` (Authoring & Maintenance Unit)
An independently maintained, reusable work with a stable slug ID (`liver`, `elbow`, `s1233-body-delivery`, `testis-pathway`, `ultrasound-bmode-generator`) and `kind` (`model | assembly | diagram | rig | generator | detail`).
- **Not 1:1 with filesystem directories:** A repository directory (maintenance package) may declare `0`, `1`, or `N` Assets in its manifest.
- **Not 1:1 with source subjects:** Hybrids and multi-source Assets are first-class. Medical honesty is enforced via **per-part provenance and registration**, not by forbidding multi-source assets.
- **Variants & overlays:** State or pathology variations (`normal`, `fatty`, `focal-lesion`, `cutaway`, `flexed-20deg`) are modeled as recipe parameters, material overrides, or additive overlays rather than cloning the whole Asset.

### 2.3 `Revision` (Immutable Iteration + Compiled Delivery Exports)
A point-in-time iteration of an `Asset` (`r02`, `teaching-economy-r02`, `r1`), owning:
- **`recipe`**: Path to the reproducible build script or editable source.
- **`default_provenance`**: Default `source`, `subject`, `license`, `units`, `axes`, `laterality`, and `registration` (`native | registered | fitted | illustrative | synthetic | unknown`).
- **`capabilities`**: Declared interactive or generative abilities (`isolate-parts`, `play-motion`, `bmode-sweep`, `edit-labels`).
- **`exports`**: One or more concrete **Delivery Exports** produced by this Revision (`id`, `role`, `format`, `path`, `sha256`, `bytes`, `triangles`, `variant`, `parts`).
  - Each **`Part`** inside an Export declares its addressable `id`, `selectors` (GLB node name, Blender object, SVG layer), `concepts`, `selectable` vs `context_only`, optional per-part `bytes`/`triangles`, and optional **`provenance` override** (supporting hybrids and foreign-lineage details cleanly).

### 2.4 `Consumer` (Demand Side — Experiences & Delivery Surfaces)
An authored teaching experience or external surface (lesson stop, ultrasound sweep/tour, interactive scene, or published site).
- Owns **`requirements`**: Machine-readable statements of what the consumer needs (`concept`, optional `parts`, `variant`, `subject`, `capabilities`, and `status`: `satisfied | provisional | open-gap | rebuild-required`).
- Owns **`pins`**: Explicit dependencies binding a requirement to `(asset_id, revision_id, export_id, parts, sha256, registration, transform?)`.
- A consumer may also own local one-off plates/files without promoting them to reusable Assets.

### 2.5 `Review` (Immutable Qualification Evidence)
A dated evidence record evaluating an exact `(asset_id, revision_id, export_id/path, sha256)` or `part` against a named learner task or clinical/spatial check.
- Records independent axes (e.g., fidelity, form/surface, teaching readability, mesh economy), exemptions, limitations, and status (`accepted | provisional | blocked | rejected`).
- **Never inferred** from anatomical naming or part-selector matching.

### 2.6 `Selection` (Editorial & Release Curation)
An explicit maintainer decision separate from both existence and review:
- Which `Revision` is `recommended` for an `Asset`.
- Which `(Export, Task)` is `selected` as a collection default.
- Which `Exports` are admitted for public CDN/object delivery.

---

## 3. Authoring-vs-Delivery Economy & Rules of Thumb

Because Consumers declare the exact `parts` they use and Exports declare their `parts`, `bytes`, and `triangles`, AssetKit computes a deterministic economy report for every Consumer and Asset:

### 3.1 Automated Metrics
- **Load count (`loads`)**: Distinct Exports fetched by a Consumer.
- **Part utilization (`part_utilization`)**: `used_parts / total_parts_in_loaded_exports`.
- **Byte utilization (`byte_utilization`)**: `used_part_bytes / total_loaded_bytes` (when per-part byte/triangle weights are available from GLB inspection or manifests; otherwise reported as `null` rather than guessed).
- **Reuse count (`reuse_count`)**: Number of distinct Consumers pinning an Asset or Export.
- **Budget status**: Checked against configurable `BudgetPolicy` soft/hard caps:
  - Single Export bytes: soft `1.5 MB`, hard `4.0 MB`
  - Single Export triangles: soft `50,000`, hard `150,000`
  - Consumer total load bytes: soft `5.0 MB`, hard `12.0 MB`
  - Consumer load count: soft `5` files, hard `12` files
  - Minimum utilization floor: `0.35` (35%) for multi-part Exports

### 3.2 Merge / Split / Overlay / Duplicate Principles

| Trigger / Situation | Rule |
| --- | --- |
| **Same anatomical lineage, different granularity** (e.g. outer liver vs. internal vessels) | **Keep 1 Asset → Split Exports** into a lightweight base Export + additive detail Export(s) in the same coordinate frame. |
| **Surface or pathology variation** (e.g. normal vs. fatty vs. focal lesion) | **Prefer Variant / Composable Overlay** (material parameter or small additive mesh) over cloning the base Asset. |
| **Foreign-lineage detail fits a teaching task better** (e.g. authored lesion on CT liver) | **Allow as Composable Overlay or Baked Hybrid**, requiring explicit per-part/per-pin `provenance` and `registration` (`fitted` or `illustrative`) + stated limits. |
| **Low utilization (`< 35%`) or Export exceeds soft size cap** | **Split Export** so overview consumers stop downloading hidden detail. |
| **High load fan-out (`loads > 5`) with tightly co-loaded Exports under byte cap** | **Merge Exports** into a regional/system delivery bundle. |
| **Detail needs its own scale, recipe, or independent release cycle** (e.g. `L3-vertebra`, `bone-marrow`) | **Promote Part → New Asset** mapped to the same `Concept`. |
| **Frozen historical evidence or incompatible stylized deformation** | **Explicit Duplicate** with `derived_from` provenance and a documented retention reason. |

---

## 4. On-Disk Representation

AssetKit avoids both monolithic hand-edited catalogs and 1-file-per-directory boilerplate. Four canonical declarative JSON formats are owned by their respective domains:

1. **Package Asset Manifest (`assets.json`)** — owned by any directory maintaining `1..N` reusable Assets.
2. **Consumer Manifest (`consumer.json`)** — owned by any lesson, tour, or site declaring `requirements` and `pins`.
3. **Concept Graph (`concepts.json`)** — compact shared file declaring only Concepts and typed edges referenced by Assets/Consumers.
4. **Reviews & Selections** — immutable per-review JSON files and structured selection records.

The unified **Catalog**, **Economy Report**, **Impact Graph**, and **Frontend Delivery Bundle** are compiled projections produced by `assetkit`, never hand-edited.

---

## 5. Verification & Storage Invariants

- **Shallow-checkout safe:** Every Artifact declaration (`path`, `sha256`, `bytes`) is verified offline against either hydrated file bytes (`verified`) or Git LFS pointer text (`pointer-match`), never claiming a pointer is hydrated content.
- **No symlink escape:** All repository paths are normalized and rejected if they escape the repository root or traverse symlinks.
- **No silent inference:** `resolve()` separates exact selector + compatible-frame candidates from concept-graph matches and flags missing qualification (`review_status: "unreviewed"`).
