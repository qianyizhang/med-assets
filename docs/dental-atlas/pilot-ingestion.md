# First source-backed dental pilot: ingestion findings

**Research candidate, not finished teaching assets. Checked 2026-10-26.** The 52-tooth inventory remains a target, not acquired coverage. This pilot concerns only prepared permanent FDI 31 (mandibular left central incisor) and FDI 46 (mandibular right first molar), each with 4 independently named author-labelled surfaces. Primary teeth remain unbuilt.

## R03 local research/display outcome

Independent technical/source and actual-pixel review accepted the narrower **local prepared-specimen, independently toggled-layer research/display pilot** on 2026-10-26. This does not authorize publication or turn the samples into finished teaching assets.

|Candidate|Bytes|Faces|Status|
|---|---:|---:|---|
|FDI 31|13,239,300|664,678|4 named layers; local research/display only|
|FDI 46|47,401,584|2,376,218|4 named layers; local research/display only|

Exact candidate SHA-256 values and curated checks: [validation-summary.json](../../sources/datasets/swirendo-pilot/validation-summary.json). Binaries and local review receipts are not included in this documentation PR.

- **Technical positives:** all 8 layers retain source face-connected island counts and guarded per-island topology signatures; independent global boundary/nonmanifold/Euler checks agree. Actual float32 GLB reimport has 0 zero-area triangles.
- **Topology limit:** source open boundaries/nonmanifold contacts remain. Preservation is not manifold certification.
- **Actual visual work:** 18 rendered images reviewed—16 original matched views and 2 corrected full-frame FDI 31 pulp views. The original pulp pair was top-clipped; the camera-only correction closes that evidence gap without changing geometry. Static Blender inspection, not browser testing.
- **Fidelity scope:** conservative bidirectional surface-distance bounds are approximately 0.010–0.075 mm before the 0.00001 mm export allowance, relative to extracted masters. Some exceed the 0.040 mm source grid. Computational bounds are not biological accuracy.
- **Interface caution:** 3 sampled FDI 31 LOD points shift into foreign source-label regions by 0.0141–0.0154 mm (~0.35–0.39 voxels). This does not establish volumetric overlap, but **inter-tissue consistency remains unpassed**. Separate-layer simplification is not a disjoint, watertight multitissue model.
- **Measurement caveat:** PCU singleton-query anomaly reproduced; affected measurements replaced with all-triangle naive checks.
- **Cross-check:** 18/18 sampled batched queries matched naive checks. Future helpers still need singleton guards.
- **Still withheld:** dental-expert/anatomical and clinical teaching approval, complete-root/healthy-atlas claims, cross-tissue consistency, simulation and runtime approval. The 2 candidates total ~60.6 MB/~3.04 M faces; size reduction alone is not performance acceptance.

Keep T2 preparation, all source `inprogress` labels, source truncation (including 46 dentin/pulp/bone), retained islands and independent specimen frames visible. Primary teeth and the remaining 50 inventory teeth remain unbuilt. No clinical procedure parameters or treatment advice are introduced.

## Source clearance and contents

[SWIRendo, Open Data LMU](https://data.ub.uni-muenchen.de/477/) explicitly licenses the dataset **CC BY-SA 4.0**. Credit Benz, Leander; Heck, Katrin; Walter, Elias, *Data: Visualization of Pulpal Structures by SWIR in Endodontic Access Preparation* (2024), DOI 10.5282/ubm/data.477. Derivatives need attribution, change notice and compatible ShareAlike terms; this does not relicense other repository assets.

- No login, account creation, terms submission, purchase or private-source access.
- Downloaded public readme/filelist and only 2 segmentation ZIP members via HTTP ranges, not the 1.1 GB archive. Member CRC32, uncompressed sizes and SHA-256 checked; ZIP ETag pinned. No whole-archive SHA claim.
- Did not acquire raw scan volumes or donor photographs. Inspected segmentation headers contain specimen codes/technical labels, no patient identifiers observed; not a formal privacy certification.
- Exact member identities, hashes, license evidence and header fields: [`source-map.json`](../../sources/datasets/swirendo-pilot/source-map.json).

## Corrections that must feed future ingestion

| Field | Finding | Required behavior |
|---|---|---|
|Resolution|Readme acquisition 0.032 mm; delivered labelmaps 0.040 mm isotropic|Use the actual file affine/spacing, not prose acquisition values.|
|Label IDs|31: Pulp 4 / Bone 3; 46: Pulp 3 / Bone 4|Parse each file's segment names; no shared numeric tissue-map assumption.|
|Frame|LPS, zero origin, isolated specimens|Keep original registration within each specimen. Do not place both at the same origin as a mouth or register to BP3D by eye.|
|Status|All segment tags say `Segmentation.Status:inprogress`|Published data is evidence, not an independent anatomy pass.|
|Preparation|Source T2 access-prepared specimens|Do not fill the opening or label them intact normal teeth.|
|Truncation|31 bone; 46 dentin/pulp/bone touch maxZ|Retain open source cutoffs; do not fabricate missing roots/apices or caps.|
|Small islands|31 pulp 7 mask islands; 46 pulp 20|These are source mask components, not inferred root/canal counts. Keep unless explicitly reviewed.|

The source-labelled Pulp volume is not histological verification or a nerve/vessel tree. Cementum, PDL and gingiva are not supplied by these 4 labels. Bone denotes the source specimen context, not a complete jaw.

## Extraction and validation contract

- One file per specimen, 4 named nodes. Derived by 0.5-isosurface marching cubes with the actual affine; millimetres→metres only. No resampling, smoothing, filling, synthetic tissue or discarded islands in the masters.
- Technical checks separate from anatomy: finite vertices, 0 zero-area faces, consistent winding, 4 objects per export and round-trip face counts/bounds. Source clipping and non-watertight regions remain visible warnings, not repaired passes.
- Native high-poly masters are 51.3 MB/116.2 MB: **not publication-ready web assets**. Display derivatives must be measured against those masters, not accepted only because they are smaller.
- First generic quadric simplification changed topology and was rejected. Subsequent candidates use explicit topology/boundary preservation, per-island processing and rollback on failed topology/bounds checks. No island deletion to hit a budget.
- Report bidirectional point-to-triangle deviation in mm and relative to 0.040 mm. Distinguish sampled maxima from conservative continuous bounds; a bound includes a known sample-covering radius. Neither establishes anatomical accuracy.
- Compare exact before/after hashes using matched cameras and neutral clay. Include source-preparation, crop and label-confidence captions. Static Blender views are not browser/runtime QA or dentist approval.

