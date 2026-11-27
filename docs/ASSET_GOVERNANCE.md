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

The generated catalog is a projection, never an edit surface.

## Domain model

The target model comprises Asset, Revision, Artifact, NamedPart, GeometryVariant, Concept, typed ConceptRelation, SourceSubject, FrameTransform, Composition, LoadablePackage, UseCase, Requirement, TeachingUse, Assessment, Qualification, Adoption and Release.

Concepts form a typed polyhierarchical graph. \`part_of\` and \`is_a\` are hierarchical relations; functional and spatial relations remain typed edges. Concepts and assets are many-to-many. Sources and assets are many-to-many. A selectable component is not automatically an independent asset. A composition may remain consumer-owned or become a maintained composite asset.

## Priority consumers

### Ultrasound Anatomy

The catalog imports scenario requirements from the maintained [Ultrasound Anatomy brief](gallery/use-cases/ultrasound-anatomy.md), plus exact case/part/task/revision evidence from workbench review packages. It preserves distinctions between:

- Original sweep geometry and its source lineage.
- Exact Gallery assets and named source surfaces.
- Case-owned retained geometry.
- Missing anatomy and rebuild requirements.
- Acquisition states, measurements and Doppler observations.
- Simulated B-mode frames and acquired reference images.
- Probe poses, scan planes, imaging fields and registration evidence.

A modeled hepatic-vein teaching surface does not satisfy the separately registered hepatic-vein/caval-junction requirement. HRA liver r02, s1233 CT liver/portal-splenic vein/cava, and the separately labeled HRA exterior reference remain distinct. Fatty-appearance and focal-lesion cases remain provisional until geometry, scan behavior and evidence are assessed. Preserve the ovary/tubal bilingual lesson's two entrances, r02 pins, return paths and explicit lumen-continuity limits.

### Body Systems

The eleven reviewed stops are first-class requirements: skeletal, muscular, respiratory, urinary, cardiovascular, digestive, nervous, endocrine, lymphatic, reproductive and integumentary. Preserve action, observation, review status and exact detail identifier. Do not infer asset adoption from anatomical naming alone. Linked One Breath, cardiac imaging, right-arm, skeletal, pelvic and pathway lessons remain distinct consumers with their own pins and evidence.

### Other consumers

Other lessons, diagrams, experiments and historical studies are indexed as package candidates. They receive no bespoke adapter until a concrete query or migration requires one.

## CLI

Run from the repository root:

\`\`\`sh
python tools/asset_governance.py scan
python tools/asset_governance.py find "hepatic vein" --domain ultrasound-anatomy
python tools/asset_governance.py find "left vesical" --domain body-systems
python tools/asset_governance.py show body-systems:digestive:digestive-s1233-route
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

Applied records are provisional. The tool never invents sources, concepts, part selectors, revisions, qualification or consumer bindings. It pins the plan to source hashes and refuses stale input. Existing records are never overwritten.

Hydration is scoped and dry-run by default:

\`\`\`sh
python tools/asset_governance.py hydrate models/liver/exports/teaching-economy-r02/liver.glb
python tools/asset_governance.py hydrate models/liver/exports/teaching-economy-r02/liver.glb --apply
\`\`\`

The command delegates transfer to Git LFS and checks that requested paths no longer contain pointer text. Exact payload identity remains governed by the existing artifact and transport contracts.

Backfill does not move files, change URLs, delete LFS objects, upload, publish or retire assets. Those require separate reviewed migration plans and existing authorized operations.

## Lifecycle and change safety

The first API is read-only: scan, find, show and impact. Subsequent mutations use a shared plan/apply protocol containing intent, schema version, source hashes, expected target states, before/after pins, affected consumers, required checks and unresolved conflicts. Apply re-reads preconditions, rejects stale plans and is idempotent. Teaching promotion retains its existing journal and recovery. No second writable catalog is introduced.

## Verification

\`\`\`sh
PYTHONPATH=lib python -m unittest tests.test_asset_governance
python tools/asset_governance.py scan >/tmp/asset-catalog.json
\`\`\`

The catalog is not a completeness claim. Unresolved owners, requirements, registrations, rights and readers remain visible.
