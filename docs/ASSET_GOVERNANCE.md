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

The catalog imports scenario requirements from the maintained [Ultrasound Anatomy brief](gallery/use-cases/ultrasound-anatomy.md), 32 authored case records and their 163 case-view requirements, 16 top-level sweep-track definitions, source-declared missing/rebuild geometry requirements, and exact case/part/task/revision evidence from workbench review packages. These are separate requirement/evidence records, not 32 or 163 new assets. The wider published workbench target of 32 tours and 410 chapters remains a consumer acceptance target; the current adapter does not claim that every generated tour chapter has been independently reconciled. It preserves distinctions between:

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
