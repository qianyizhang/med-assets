# Asset Governance

The governance library is a repository-native read model and controlled migration interface. It does not replace package-owned recipes, source/import records, review evidence, teaching promotion, Gallery release selection or transport.

## Ownership

- Asset identity, revisions, named parts and exports belong to the package maintaining the editable work or pinning an upstream source.
- Source owners retain provenance, rights, subject, units, axes and laterality.
- Assembly/registration owners retain transforms, landmarks, error and registration scope.
- Lessons own learner actions and exact teaching-use pins.
- Reviews own dated observations and evidence.
- Gallery owns public selection, routes, rendering and release membership.
- Transport owns upload admission, transfer and readback.

The generated catalog is a projection, never an edit surface. Existing package-manifest declarations are imported with their owning manifest and exact artifact path. The reader distinguishes verified hydrated bytes, a matching Git LFS pointer, missing payloads and identity mismatches; it does not claim a pointer is hydrated content.

## Domain model

The target model comprises Asset, Revision, Artifact, NamedPart, GeometryVariant, Concept, typed ConceptRelation, SourceSubject, FrameTransform, Composition, LoadablePackage, UseCase, Requirement, TeachingUse, Assessment, Qualification, Adoption and Release.

Concepts form a typed polyhierarchical graph. \`part_of\` and \`is_a\` are hierarchical relations; functional and spatial relations remain typed edges. Concepts and assets are many-to-many. Sources and assets are many-to-many. A selectable component is not automatically an independent asset. A composition may remain consumer-owned or become a maintained composite asset.

## Priority consumers

### Ultrasound Anatomy

The catalog imports scenario requirements from the maintained [Ultrasound Anatomy brief](gallery/use-cases/ultrasound-anatomy.md), 32 authored case records and their 163 case-view requirements, the complete 32 authored case tours and 410 acquisition chapters, 16 top-level sweep-track definitions, source-declared missing/rebuild geometry requirements, and exact case/part/task/revision evidence from workbench review packages. The 410 chapter records are derived by invoking the same `case-evidence.mjs` and owner `playable.js` chapter functions used by the workbench, rather than maintaining a second parser or hard-coded inventory. These are consumer requirements/evidence records, not 32 or 410 new assets. The 28 standalone donor-sweep coverage declared by the playback verifier remains distinct from the 16 top-level authored sweep-track definitions. It preserves distinctions between:

- Original sweep geometry and its source lineage.
- Exact Gallery assets and named source surfaces.
- Case-owned retained geometry.
- Missing anatomy and rebuild requirements.
- Acquisition states, measurements and Doppler observations.
- Simulated B-mode frames and acquired reference images.
- Probe poses, scan planes, imaging fields and registration evidence.

A modeled hepatic-vein teaching surface does not satisfy the separately registered hepatic-vein/caval-junction requirement. HRA liver r02, s1233 CT liver/portal-splenic vein/cava, and the separately labeled HRA exterior reference remain distinct. Fatty-appearance and focal-lesion cases remain provisional until geometry, scan behavior and evidence are assessed. Preserve the ovary/tubal bilingual lesson's two entrances, r02 pins, return paths and explicit lumen-continuity limits.

### Body Systems

The eleven reviewed stops, eleven system assemblies and every indexed detail plate are first-class consumers: skeletal, muscular, respiratory, urinary, cardiovascular, digestive, nervous, endocrine, lymphatic, reproductive and integumentary. Preserve action, observation, review status, exact detail identifier, paired display frames, legends, source references and scope limits. An assembly ID may intentionally be reused by its overview detail; identity includes the plate kind. Do not infer asset adoption from anatomical naming alone. Linked One Breath, cardiac imaging, right-arm, skeletal, pelvic and pathway lessons remain distinct consumers with their own pins and evidence.

### Accepted teaching assessments

The library also imports all 130 currently accepted teaching assessments, including the exact export and view hashes, task text, source references, four-axis observations, target disposition, attribution, and whether the assessment is the maintained selection or an accepted alternative. This preserves the distinction between an accepted assessment and the selected default. It does not infer a Body Systems or Ultrasound consumer binding unless an exact consumer pin exists.

### Other consumers

Structured `lessons/*/lesson.json` files are indexed as consumer-owned records. Their exact export/model paths, display plates, reviews and attribution references remain distinct pins. Path-only lesson pins resolve to current package exports but are not promoted to immutable revision pins. Other lessons, diagrams, experiments and historical studies remain lightweight package candidates until a concrete query or migration requires a richer adapter.

## Exact part discovery and resolution

The package adapter imports explicit part selectors from existing source records where available: Body Systems 3D delivery manifests (including node IDs and source-case declarations), the whole-body 2D canonical-part manifest, the Cardiac Atlas anatomy manifest, explicit HRA region keys, kidney layer keys, dental source inventories and the ovary/tubal build receipt. Each part retains the metadata file that declared it, its selector, source case/frame when declared, geometry kind, derivation and scope. A source-node mapping or schematic part is not silently promoted to a loadable, registered 3D asset.

Use `resolve` to compare a consumer's declared part IDs with those exact selectors:

```sh
python tools/asset_governance.py resolve ultrasound:sweep:abdomen-tracks:liver
python tools/asset_governance.py resolve ultrasound:sweep:thyroid-tracks:thyroid-right
python tools/asset_governance.py resolve ultrasound:sweep:abdomen-tracks:liver --part liver
```

An exact selector plus exact source-case match produces an **exact binding candidate**, not a qualified teaching asset. Anatomical suitability, spatial registration, license compatibility, learner-task evidence and runtime behavior remain separate gates. Unknown source frames, missing selectors and conflicting candidates remain visible.

## CLI

Run from the repository root:

\`\`\`sh
python tools/asset_governance.py scan
python tools/asset_governance.py find "hepatic vein" --domain ultrasound-anatomy
python tools/asset_governance.py find "left vesical" --domain body-systems
python tools/asset_governance.py show body-systems:digestive:digestive-s1233-route
python tools/asset_governance.py resolve ultrasound:sweep:abdomen-tracks:liver
python tools/asset_governance.py impact package:models/liver
\`\`\`

Outputs are deterministic JSON. A package candidate is not a confirmed asset lineage.

## Backfill and hydration

Create a proposal:

\`\`\`sh
python tools/asset_governance.py backfill plan --output .artifacts/asset-backfill.plan.json
\`\`\`

Every decision defaults to \`defer\`. Review granularity and ownership. For an accepted proposal, set \`decision\` to \`accept\` and supply a stable unique \`assetId\`. Then apply:

\`\`\`sh
python tools/asset_governance.py backfill apply --plan .artifacts/asset-backfill.plan.json
\`\`\`

Applied records are provisional. The tool never invents sources, concepts, part selectors, revisions, qualification or consumer bindings. It pins the plan to source hashes, manifests and export identities and refuses stale input. Reapplying an identical plan is idempotent; conflicting existing records are rejected.

Hydration is scoped and dry-run by default:

\`\`\`sh
python tools/asset_governance.py hydrate models/liver/exports/teaching-economy-r02/liver.glb
python tools/asset_governance.py hydrate models/liver/exports/teaching-economy-r02/liver.glb --apply
\`\`\`

The command delegates transfer to Git LFS and checks that requested paths no longer contain pointer text. Exact payload identity remains governed by the existing artifact and transport contracts.

Backfill does not move files, change URLs, delete LFS objects, upload, publish or retire assets. Those require separate reviewed migration plans and existing authorized operations.

## Lifecycle and change safety

The first API is read-only: scan, find, show, resolve and impact. Resolution distinguishes exact export identity, exact part-selector candidates, explicit package-source references, acquired-reference links and unresolved relationships. A part candidate is not anatomical, spatial-registration, rights or teaching qualification. Subsequent mutations use a shared plan/apply protocol containing intent, schema version, source hashes, expected target states, before/after pins, affected consumers, required checks and unresolved conflicts. Apply re-reads preconditions, rejects stale plans and is idempotent. Teaching promotion retains its existing journal and recovery. No second writable catalog is introduced.

## Verification

The library uses Python 3.11+ standard-library dataclasses, strict repository-path checks and JSON contracts. It adds no database, service, runtime package dependency or second source of truth. Run its focused suite through unittest discovery, or run the repository's full offline gate:

\`\`\`sh
PYTHONPATH=lib python -m unittest discover -s tests -p 'test_asset_governance.py'
python tools/asset_governance.py scan >/tmp/asset-catalog.json
python tools/verify.py offline
\`\`\`

The catalog is not a completeness claim. Unresolved owners, requirements, registrations, rights and readers remain visible.


## Controlled lifecycle operations

Lifecycle mutations edit only the owning package's asset.record.json. They never modify the catalog, move geometry, delete LFS objects, upload, publish Gallery routes or alter consumer content. Every mutation follows inspectable plan then explicit apply:

```sh
python tools/asset_governance.py lifecycle plan --action qualify --asset anatomy:liver:hra --payload .artifacts/qualification.json
python tools/asset_governance.py lifecycle apply --plan .artifacts/asset-lifecycle.plan.json
```

Supported actions: refine (append owner-reviewed concepts, sources, parts or revisions), assess (record revision-scoped assessment), qualify (record scoped reviewer decision and evidence), adopt (pin consumer, revision, export digest/size, parts and requirements; always starts provisional), promote (requires qualification, no unresolved record issues, concepts, sources, parts and verified export bytes), deprecate, retire and archive. Retirement requires a disposition for every indexed reader. Archive is metadata-only and blocked while a reader remains frozen. Neither action deletes bytes.

Plans carry complete before/after records, source hashes, expected record digest, affected consumers and required checks. Apply rejects stale source/target state, recomputes the action from its payload, verifies the after-state digest and is idempotent. An empty impact report covers only currently indexed adapters, not unknown external readers. Regenerate plans after conflicts; do not hand-edit their after-state.

Payloads are JSON objects. Refine uses {"set":{"concepts":[],"sources":[],"parts":[],"revisions":[]}}. Qualification uses {"revisionId":"r01","qualification":{"qualificationId":"q01","scope":"anatomy-and-runtime","reviewer":"reviewer-id","assessedAt":"2026-11-27","decision":"qualified","evidence":[{"path":"reviews/asset/review.json","sha256":"<64-hex-digest>"}]}}. Consumer-specific qualification can instead supply useId alongside qualification to qualify that exact adoption independently of the asset revision. Evidence entries must reference hydrated repository files with matching SHA-256 digests. Adoption uses {"use":{"useId":"consumer:asset","consumerId":"lesson:example","revisionId":"r01","exportPath":"models/asset/asset.glb","sha256":"<64-hex-digest>","bytes":123,"partIds":["part-id"],"requirementIds":["requirement-id"]}}. These are contract examples, not approval of any repository asset mapping.


The resolver also joins exact candidates to package-owned records when present. Its output exposes revision IDs/status, export path/digest/size, part membership, source declarations, recorded frame/transform fields, revision qualifications and consumer-specific adoption pins. Missing records remain explicit. An exact path/selector is still only a candidate; a qualified result requires a matching maintained revision and scoped evidence. Registration and rights compatibility are never inferred from a path or label.


## First reviewed migration pilot: Cardiac Atlas

The first package-owned backfill is `heart/Cardiac_Atlas_Animated/asset.record.json`, with asset identity `anatomy:heart:cardiac-atlas`. It follows the explicit shared-source statement in the Heart assets owner README and the `shared-source-r01` delivery README: one editable Blender source owns the static great-vessel teaching export and the focused ventricular-wall-motion export. It is one maintained lineage, not one asset per mesh/node or export.

The provisional record contains five exact named parts and their GLB node selectors: aorta, pulmonary trunk, left pulmonary artery, right pulmonary artery, and complete left ventricular wall. It pins two revision exports by SHA-256 and byte size. The source and export coordinate frames are recorded separately: native Blender +X patient left / +Y posterior / +Z superior at 25 mm per Blender unit; GLB +X patient left / +Y superior / +Z anterior with the documented 0.025 metre root conversion. This is a source-to-export relationship, not patient registration.

Two existing selected teaching assessments are adopted as provisional uses: distinguish the pulmonary trunk from the aortic arch, and distinguish ventricular contour change from rigid shift. Their exact consumer IDs, revision, export digests, parts and requirement IDs are pinned. The accepted assessments are not silently promoted to qualification. The asset and both uses remain provisional because no separate task-specific qualification has been approved. Source license/attribution and canonical ontology mappings remain unresolved. The other package exports, including the full animated presentations and earlier wall-motion export, are not assigned to this revision until their source/variant relationships are reviewed. The documented schematic vessel-junction gap and the non-clinical educational scope remain explicit limits.
