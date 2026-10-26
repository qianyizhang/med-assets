# First source-backed dental pilot: ingestion findings

**Research candidate, not finished teaching assets. Checked2026-10-26.** The52-tooth inventory remains a target, not acquired coverage. This pilot concerns only prepared permanent FDI31 (mandibular left central incisor) and FDI46 (mandibular right first molar), each with4 independently named author-labelled surfaces. Primary teeth remain unbuilt.

## Source clearance and contents

[SWIRendo, Open Data LMU](https://data.ub.uni-muenchen.de/477/) explicitly licenses the dataset **CC BY-SA4.0**. Credit Benz, Leander; Heck, Katrin; Walter, Elias, *Data: Visualization of Pulpal Structures by SWIR in Endodontic Access Preparation* (2024), DOI10.5282/ubm/data.477. Derivatives need attribution, change notice and compatible ShareAlike terms; this does not relicense other repository assets.

- No login, account creation, terms submission, purchase or private-source access.
- Downloaded public readme/filelist and only2 segmentation ZIP members via HTTP ranges, not the1.1GB archive. Member CRC32, uncompressed sizes and SHA-256 checked; ZIP ETag pinned. No whole-archive SHA claim.
- Did not acquire raw scan volumes or donor photographs. Inspected segmentation headers contain specimen codes/technical labels, no patient identifiers observed; not a formal privacy certification.
- Exact member identities, hashes, license evidence and header fields: [`source-map.json`](../../sources/datasets/swirendo-pilot/source-map.json).

## Corrections that must feed future ingestion

| Field | Finding | Required behavior |
|---|---|---|
|Resolution|Readme acquisition0.032mm; delivered labelmaps0.040mm isotropic|Use the actual file affine/spacing, not prose acquisition values.|
|Label IDs|31:Pulp4/Bone3;46:Pulp3/Bone4|Parse each file's segment names; no shared numeric tissue-map assumption.|
|Frame|LPS, zero origin, isolated specimens|Keep original registration within each specimen. Do not place both at the same origin as a mouth or register to BP3D by eye.|
|Status|All segment tags say `Segmentation.Status:inprogress`|Published data is evidence, not an independent anatomy pass.|
|Preparation|Source T2 access-prepared specimens|Do not fill the opening or label them intact normal teeth.|
|Truncation|31 bone;46 dentin/pulp/bone touch maxZ|Retain open source cutoffs; do not fabricate missing roots/apices or caps.|
|Small islands|31 pulp7 mask islands;46 pulp20|These are source mask components, not inferred root/canal counts. Keep unless explicitly reviewed.|

The source-labelled Pulp volume is not histological verification or a nerve/vessel tree. Cementum, PDL and gingiva are not supplied by these4 labels. Bone denotes the source specimen context, not a complete jaw.

## Extraction and validation contract

- One file per specimen,4 named nodes. Derived by0.5-isosurface marching cubes with the actual affine; millimetres→metres only. No resampling, smoothing, filling, synthetic tissue or discarded islands in the masters.
- Technical checks separate from anatomy: finite vertices,0 zero-area faces, consistent winding,4 objects per export and round-trip face counts/bounds. Source clipping and non-watertight regions remain visible warnings, not repaired passes.
- Native high-poly masters are51.3MB/116.2MB: **not publication-ready web assets**. Display derivatives must be measured against those masters, not accepted only because they are smaller.
- First generic quadric simplification changed topology and was rejected. Subsequent candidates use explicit topology/boundary preservation, per-island processing and rollback on failed topology/bounds checks. No island deletion to hit a budget.
- Report bidirectional point-to-triangle deviation in mm and relative to0.040mm. Distinguish sampled maxima from conservative continuous bounds; a bound includes a known sample-covering radius. Neither establishes anatomical accuracy.
- Compare exact before/after hashes using matched cameras and neutral clay. Include source-preparation, crop and label-confidence captions. Static Blender views are not browser/runtime QA or dentist approval.

## Acceptance still pending

Independent technical/visual review, scoped dental-expert review, surface/island interpretation and appropriate source coverage. Keep these as prepared-specimen studies unless a reviewer approves a narrower teaching use. No claim that the remaining50 teeth or internal structures have been created. No clinical procedure parameters or treatment advice are introduced.
