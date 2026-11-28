# AssetKit

**AssetKit** is the repository's canonical Python 3.12 library and CLI for developing, reviewing, and delivering reusable 3D medical teaching assets.

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

# Discover and inspect assets, parts, assessments, and decisions
uv run assetkit find cardiac-atlas
uv run assetkit show anatomy:heart:cardiac-atlas

# Compute reuse, load fan-out, part/byte utilization, and merge/split advice
uv run assetkit economy

# Trace affected consumers, reviews, and selections for an asset, export, or path
uv run assetkit impact anatomy:s1233:liver-window@r01:liver

# Inspect indexed AssetKit uses alongside evidence, recovery, and other retention records
uv run python tools/verify.py retained models/liver_s1233/exports/r01/liver.mesh

# Resolve candidate assets/parts for a consumer's requirements
uv run assetkit resolve ultrasound:sweep:abdomen-tracks:liver

# Plan declared loads and inspect storage status, or list indexed anatomy gaps
uv run assetkit bundle <consumer-id>
uv run assetkit gaps --prefix ultrasound:

# Plan or execute a Python revision entry point
uv run assetkit build <asset-id> <revision-id> [--apply]

# Preview missing identity fields and affected readers before changing the record
uv run assetkit sync <package>/asset.record.json
uv run assetkit sync <package>/asset.record.json --apply --expect-plan <planToken>

# Compare a native export to an independent recipe, assignment, or release pin
uv run assetkit check-port <asset-id>@<revision-id>:<export-id> \
  --record <package>/asset.record.json --path <payload> --sha256 <digest> --bytes <count>

# Inspect Gallery entries or R2 demand from selections and consumer pins
uv run assetkit compile --target gallery
uv run assetkit compile --target r2
```

A bundle preserves one item per use, including its transform. Totals count each pinned export once. Check each item’s storage status and digest before runtime use. Both default and native-only R2 projections include demand from exact maintained selections. The transport owner controls upload admission.

Gallery Library entries and recipe inputs appear in `impact`. A candidate Library route can list several downloads without loading any of them. The [Gallery release guide](../../docs/gallery/asset-library.md#making-a-release-selection) describes how to update those bindings.

Default queries include directory-discovered files with status `legacy-candidate`. An exact governed export path resolves through its owner record. Use `--native-only` for acceptance of a governed dependency.

## Inspect a teaching review

Use the export key to see the task, scores and evidence attached to the exact file.

```sh
uv run assetkit --native-only show anatomy:hra:liver@r02:teaching-economy
uv run assetkit --native-only show anatomy:s1233:liver-window@r01:liver
uv run assetkit show ultrasound:case:echo-aortic-stenosis:psax-av-section:aortic-valve-cusp-1
```

The HRA review asks the learner to locate the posterior bare area. The ultrasound review asks the learner to distinguish the broad right lobe from the narrower left extension on the s1233 mesh. Each assessment applies to its own geometry, task and rubric. The Gallery starting file is an editorial selection. Asset qualifications require an explicit decision.

AssetKit discovers mesh-bound workbench reviews by the SHA-256 of a native packed export. Inspect the export with `show` or `impact` to see the scores, rubric, image identities and any chapter fingerprint. The modeled echo cusp remains a recipe-bound review. The CLI shows its recorded case, chapter, part and recipe fingerprint. In Python, `workspace.show(review_id, delivery=compact_directory)` checks that fingerprint against an assembled delivery. The [workbench](../../experiments/ultrasound-sweep/README.md) owns the review collection.

Run `uv run assetkit review check` to validate the maintained teaching register and scorecard. The [promotion guide](../../docs/guides/teaching-assessments.md) covers preview, apply and recovery.

## Register a package

1. Write the owner record with explicit IDs, source references, and stored coordinate conventions. A revision frame may also apply to its exports. Give an export its own frame when storage uses a different convention. Declare known axes and units in `frame`, link its evidence, and keep patient or source identity separate. An `unverified-frame` names the matching issue from the record's `unresolved` list. Use the [batch contract](../../docs/MIGRATION_SPEC.md#record-contract) for the allowed conventions and placement rules.
2. Preview `sync` and review the changes, input fingerprints, and affected readers. Apply using the returned `planToken` or the Python functions `plan_record_sync()` and `apply_record_sync()`. Identical token reuse preserves the installed bytes. Sync rejects changes to a pinned export, the reviewed record, or its observed inputs. The metadata fixture still supports its `assets.json` sync command.
3. Run `check-port` with an expected identity from the package assignment or an existing owner pin. Supply repeatable `--selector` flags and `--triangles` for independent expectations when available. The command requires an exact native owner and verifies every declared selector on the selected hydrated export. `--allow-lfs-pointer` permits a match on both pinned SHA-256 and size in offline CI. A pointer receipt omits mesh statistics. The Python API is `check_port(repo, PortExpectation(...))`.
4. Follow the package's replay instructions and reader acceptance. The generic `build` command runs Python entry points, including those that require Blender. An owner-defined JSON recipe uses the package's documented command, as in the [HRA liver rebuild](../../models/liver/exports/teaching-economy-r02/README.md#rebuild). AssetKit verifies the maintained portable recipe's declared source and output pins against the record and local artifacts.

Use the [package change safeguards](DESIGN.md#safeguards-for-package-changes) for evidence, qualification, and retirement. For hydration and archived recovery, use the [transport workflow](../../transport/README.md).

## Submodules (Bounded Contexts)

| Submodule | Context | Responsibility |
| --- | --- | --- |
| `assetkit.blobs` | Foundation | Safe repository path checks, Git LFS pointer vs. hydrated byte verification, and stdlib GLB v2 mesh stats. |
| `assetkit.vocab` | Semantic | Polyhierarchical `ConceptGraph` DAG decoupled from asset granularity. |
| `assetkit.registry` | Supply / Authoring | `AssetRegistry`, `Asset → Revision → Export → Part` aggregates, per-part `Provenance`/`Registration`. |
| `assetkit.build` | Build and sync | Python recipe planning and execution, canonical sync planning, and atomic apply. |
| `assetkit.records` | Package admission | Canonical identity, declared source and output pins, coordinate frames, and native port acceptance. |
| `assetkit.delivery` | Demand & Packaging | `DeliveryGraph`, `Consumer` requirements & pins, `bundle_for()`, `resolve()`, `open_gaps()`, `economy()`, `impact()`. |
| `assetkit.curation` | Evidence & Release | `CurationStore`, immutable `Review`s, editorial `Selection`s, `compile_gallery()`, `plan_r2_sync()`. |
| `assetkit.cli` | Interface | Thin deterministic JSON CLI over `Workspace`. |

## Running Tests

```sh
uv run pytest src/assetkit/tests
```
