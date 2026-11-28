# AssetKit design

AssetKit is the canonical interface for developing and inspecting reusable 3D medical teaching assets. It helps an author rebuild a model from its source, retain its coordinate frame and evidence, and produce a small export that a viewer or lesson can pin. The [liver sweep pilot](PRD.md#liver-sweep-pilot) exercises the handoff from a case-derived 3D export to the existing ultrasound player.

## Asset development and delivery

| Module | Responsibility |
| --- | --- |
| [Registry](registry.py) and [vocabulary](vocab.py) | Package-owned asset identity, revisions, exports, named parts, source identity and spatial frames. Concepts support discovery across scales. They can describe a small part of a larger export or a separately maintained asset. |
| [Build](build.py) and [blobs](blobs.py) | Plan and run package recipes. Inspect mesh statistics and distinguish declared identity, matching LFS pointers, and verified local bytes. Recipes and rebuild tolerances live with the package. |
| [Delivery](delivery.py) | Resolve exact 3D inputs, trace indexed dependencies, and estimate delivery cost. Candidate discovery and declared bundles support planning. Runtime callers need verified bytes and valid selectors for the inputs they load. |
| [Curation](curation.py) | Read task-scoped assessments from their owners. The maintained teaching register owns accepted assessments, Gallery owns selection and routes, and the ultrasound workbench owns its mesh and acquisition-recipe reviews. Qualifications and adoptions are explicit decisions. Transport owns admission, transfer, and recovery. AssetKit projections inform those owners. |
| [Workspace](workspace.py) and [CLI](cli.py) | Present one interface for cross-module queries. Typed [models](models.py) carry structured results across the Python and JSON interfaces. |

One maintained revision can produce several exports for different viewers. Split an exterior and internal anatomy when they have different load patterns. Keep them in a shared frame where a viewer composes them. Bundle files that are routinely loaded together when the combined bytes and decoding cost fit the viewer. Treat size, triangle, and utilization thresholds as prompts to check the actual use. Report declared load cost separately from measured runtime. Promote a part to its own asset when it gains an independent recipe, owner, or release cycle.

Keep source identity, frame, units, laterality, derivation, and reuse rights with the package. Multi-source assemblies can carry part-level provenance and explicit transforms. An illustrative placement and a spatial registration support different claims. Resolve candidates using their recorded selector and frame evidence. Keep an observation about exact bytes separate from a decision that those bytes are suitable for a named use. Record decisions when there is a claim to support.

## Safeguards for package changes

- **Register from evidence.** Give a maintained lineage a stable identity in its owning package. Start newly registered lineages and adoptions as provisional. Keep unknown sources, rights, frames, selectors, and uses explicit. A folder, matching name, or exact selector can help locate a candidate. Qualification requires its own decision.
- **Verify the scope of each decision.** An adoption pins the consumer, revision, export identity, and any required parts. Qualify a named task or scope using evidence bound to the exact export and relevant parts or use. Check hydrated evidence against its recorded digest. Keep an accepted assessment, a qualification decision, an adoption, and a Gallery selection independently visible. The [Cardiac Atlas](../../heart/Cardiac_Atlas_Animated/asset.record.json) records two accepted teaching assessments with provisional adoptions and links to their retained evidence.
- **Review before applying.** Show the owning record, intent, before and after pins, affected readers, and required checks. Preserve existing revision and evidence bindings when introducing a changed export. The [sync command](README.md#register-a-package) binds its plan to the exact record and observed package inputs, including the maintained portable recipe's source and output pins. Apply rechecks the inputs, writes the complete record atomically, and treats an exact already-applied result as a no-op.
- **Trace retirement through the owners.** Use [the retention check](../../docs/WORKFLOW.md#retention) to identify indexed readers, then check external and dynamic references where applicable. Record a disposition for each known reader and verify any required recovery copy. Gallery controls public selections and routes. Transport controls transfer, admission, and recovery.

## Decisions

The records below capture the agreed design direction. The PRD tracks implementation and pilot acceptance. Each decision can move as a standalone ADR.

### Keep AssetKit focused on reusable 3D work

The asset team needs stable revisions and reproducible geometry. Lesson authors need quick changes to sequence, motion, and media. AssetKit owns the lifecycle of reusable 3D outputs, including multi-part anatomy, independent rigs, and shared instrument geometry. Existing lesson tooling owns probe motion, imaging fields, simulation, chapter order, annotations, and comparison choices. Reusable diagrams stay with their illustration packages. Acquired media stays with its source records. Evidence can link to media when an asset review depends on it.

A shared lesson schema would make more lesson state searchable and would tie routine authoring changes to AssetKit. Keep lessons with their current builder and player. Revisit shared lesson tooling when another maintained workflow demonstrably needs the same behavior.

### Read 3D dependencies from the owning lesson configuration

Asset authors need to find who uses an export. A downstream consumer declares the asset ID, revision, export ID, and any selected parts where it already configures the scene. Resolve those fields against the package's canonical export identity and verify expected bytes before loading them. Preserve the digest with a published or frozen use through its existing delivery record.

An AssetKit reader can derive indexed uses from those declarations. Report unresolved inputs and coverage limits. A duplicate consumer manifest would make indexing uniform and add a second edit for every dependency change. A derived use records a dependency. Scoped qualification remains an independent decision. Existing consumer manifests can still be read during migration. The pilot adds its reference to the owning sweep config.

The real pilot uses one package-owned `asset.record.json` for the revision and export. The metadata fixture keeps its versioned `assets.json`. Recognize the AssetKit schema at discovery so a lesson's similarly named inventory remains lesson-owned. For an export placed directly in a voxel scene, compare the export's case, grid shape, and affine into RAS millimetres with the builder's pinned input grid. Treat an absent or different grid as a failed handoff.

### Retain exact outputs for a named use

Track canonical editable inputs, recipes, source and rights records, and the exports needed by maintained readers. Generate routine scan frames, overlays, previews, and delivery inventories in the owning build output. A published lesson, active review, or recovery obligation can require exact bytes. Keep those bytes through the existing delivery, evidence, or archive process and verify the identity on replay or restore.

Runtime transfer, hydrated checkout size, and retained object size answer different questions. Measure each against a named workload or inventory. Keeping every generated version would simplify exact replay and compound storage. Keeping only recipes would lose outputs whose exact bytes cannot be reproduced.

See the repository [ownership and verification rules](../../docs/WORKFLOW.md), [retention policy](../../docs/WORKFLOW.md#retention), and [transport contracts](../../transport/README.md).
