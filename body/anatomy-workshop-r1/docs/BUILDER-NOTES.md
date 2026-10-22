# Body 3D source and integration review
Checked 2026-10-21. This folder contains read-only copies fetched through the GitHub connector. No tb3 repository changes or model trials were made.

## Exact sources
Repository: qianyizhang/tb3
Pinned revision: 75ec4e6530abe4d434b07958e90bdc9dec062bef (2026-10-13)
Canonical source directory: https://github.com/qianyizhang/tb3/tree/75ec4e6530abe4d434b07958e90bdc9dec062bef/presentation/task-explorer/anatomy
Local files: tb3/presentation/task-explorer/anatomy/
source-receipts.json records pinned file URLs and Git blob hashes. All 24 fetched files passed byte-identical Git blob checks; all 18 organ JSONs match the SHA-256 recorded in the source manifest.
geometry-review.json records geometry bounds, topology checks and source boundary flags.

The 18 source-derived objects are liver, kidney_left, kidney_right, spleen, pancreas, stomach, gallbladder, heart, five named lung lobes, aorta, trachea, pulmonary_vein, vertebrae_L3 and prostate.
Seventeen come from one retained example, s1233. Prostate comes from s1336 and must stay standalone or be explicitly labeled as a separately placed teaching object.

## Rights and fidelity
Preserve NOTICE.md, CC-BY-4.0.txt, the manifest, and ../assets/Apache-2.0.txt with redistributed derivatives.
Attribution: Jakob Wasserthal and the TotalSegmentator contributors, University Hospital Basel. TotalSegmentator v2.0.1: https://zenodo.org/records/10047263 ; paper https://doi.org/10.1148/ryai.230024 .
The retained tb3 notice uses CC BY 4.0 dataset attribution, while its selected-source receipt separately records Apache-2.0 for labels. Keep both notices. Do not relicense this source-derived set as original/CC0. Credit authors, link terms, identify changes, and avoid endorsement claims.
Selected-source receipt: https://github.com/qianyizhang/tb3/blob/75ec4e6530abe4d434b07958e90bdc9dec062bef/groups/anatomy-audit/experiments/ct-organ-segmentation-astra-xhigh/source/selected-source-manifest.json .
Public checks: Zenodo confirms the exact subset/version/archive; its parsed page did not expose the license value and its API was inaccessible. Thus the specific per-component terms above are verified from the retained manifest, notice and license files, not newly inferred from Zenodo's blank Rights field. The official source software repository displays Apache-2.0. CC BY conditions: https://creativecommons.org/licenses/by/4.0/ .

These retained surfaces are not native high-resolution scans. Original derivation keeps the largest component, smooths sigma 0.65 voxels, uses marching cubes at 0.5, 15 windowed-sinc iterations at passband 0.1, quadric decimation, and rounding to 0.01 mm. Main organs range approximately 700–2000 triangles; their LODs are approximately 154–300 triangles. They preserve recognizable source-case shape, not diagnostic surface detail. Further smoothing can shrink features. Tiny branches may be absent because only the largest source component was retained. All 18 manifest image-boundary-truncation flags are false.

Edge-incidence review found boundary/nonmanifold edges in heart (2/5), liver (1/4), lung_lower_lobe_left (2/1), lung_lower_lobe_right (2/2). Other 14 pass this limited closed-edge test. This is not a watertightness/self-intersection certification. Do not overwrite originals. If a Boolean-ready derivative is needed, repair a named copy, record the operation, and recheck.

## Coordinates and schema
JSON schema:
- vertices: arrays of [R,A,S] in millimetres
- faces: triangle vertex indices
- lod: its own vertices/faces
- id, source_case, coordinates: metadata
Stored geometry has not been recentered or normalized.
World display/glTF metres: x=-R/1000, y=S/1000, z=A/1000. This is right-handed, +X patient left, +Y superior, +Z anterior. Apply one common assembly recenter transform, recording its exact matrix. Never center every organ independently before assembling it.
Native Blender with +X left, +Y posterior, +Z superior in metres: (-R,-A,S)/1000. Export to glTF normally maps Blender (x,y,z) to (x,z,-y).

Sanity checks from source bounds:
- Left kidney center R=-89.5 mm; right kidney R=+71.6 mm.
- Left kidney superior center S=314.2 mm; right kidney S=289.4 mm.
- Liver center R=+48.1 mm, spleen R=-102.9 mm.
- Left lung centers R<0 and right lung centers R>0.
- Source torso includes no source-derived head, whole skeleton or body skin.

tb3 AnatomyPart interface: {id,label,vertices,faces,normals?,provenance}.
AnatomyAssets.get(name) supports individual organ IDs and abdomen, torso, chest, chest-ct, lungs, airways, heart, ultrasound, kidneys, spine. The current implementation converts RAS to (-R,S,A), performs one display-only Loop subdivision, then independently fits each requested group. The returned coordinates are display coordinates, so use raw JSON for physical assembly/export.
Do not import the frontend's separately fitted heart and kidneys into a supposedly common physical body frame.

## Existing detailed cardiac asset
Local existing deliverables: /workspace/scratch/57dbce61b79b/asset-library/dist/downloads/Cardiac_Atlas_Blender_and_Source.zip and Cardiac_Atlas_Exported_Meshes.zip.
Original Blender uses 1 BU=25 mm, axes +X left,+Y posterior,+Z superior. Its glTF roots already convert to metres with axes +X left,+Y superior,+Z anterior.
Its source origin is arbitrary near the ventricular base. It was not extracted from or registered to s1233.
A curated placement may visually replace source heart.json, but publish the placement matrix and caption it “illustrative placement of an independently authored heart.” Keep the unmodified source heart available as an alternative. No CT, MRI or ultrasound should be presented as corresponding to that hybrid assembly.
Existing cardiac GLBs are static ED frame 1; the .blend holds the authoritative pulse/valve rig. Do not claim new GLB animation unless clips are exported and tested.

## Recommended first coherent set
Thoracic/abdominal collection: source lung lobes and trachea, abdominal organs and kidneys, aorta and source heart; separately linked detailed heart study; schematic kidney cutaway, bronchial hierarchy, digestive conduits and brain study.
This matches tb3 segmentation/label auditing, supplied-object identity, landmarks, correspondence, tubular paths and motion explanation. It does not fabricate a selected-case prediction or scoring reference.
Missing full-body systems remain explicitly schematic or not modeled. Do not present an approximate 28-organ assembly as a complete clinical atlas.

## Polished reusable packaging
- Preserve untouched source JSONs and provenance in sources/.
- Editable Blender master with named collections and stable anatomy_id custom properties; keep source shells, derived cutaways and authored internals in distinct collections.
- Export assembled GLB and per-organ GLBs in metres. Include geometry.json with vertex/face/normal arrays for tb3's embedded offline renderer.
- Export one shared physical assembly and independent centered showcase variants, labeled differently. Each centered derivative has source-to-asset and asset-to-assembly matrices.
- Author genuine UVs with named layer. Bake or generate actual BaseColor, Roughness and tangent-space OpenGL +Y Normal PNGs; label them illustrative tissue material, not source imaging. BaseColor is sRGB, roughness/normal linear Non-Color.
- Preserve a neutral matte preset, a tissue-style preset and a transparent teaching preset. Transparency is not X-ray/MR/ultrasound physics.
- Use separate static cutaways to reveal authored internals. A clipped exterior shell alone is a geometric section, not evidence of source interior anatomy.
- Animation clips can demonstrate breathing or urine/air travel, but identify motion as authored schematic. Camera rotation is not physiology; deformation must not imply material tracking or physiological validation.
- Manifest per asset: id, label, group, source/procedural category, source case where relevant, source URL/revision/hash, units/axes, transform, provenance, attribution/license, derivation, LOD counts, materials/UV maps, animation clip names/duration, limitations, checksums.
- Include README, attribution, coordinate contract, tb3 import example and portable offline preview. The repo browser uses indexed geometry and embedded assets; GLBs are a reusable interchange deliverable.
- QC must reopen .blend and GLBs, verify sizes/axes, IDs, index bounds, finite geometry/normals, UV presence/coverage, texture bindings, animation clips, transparent rendering, screenshots and mobile interaction.

## Schematic anatomy guidance
Kidney: outer cortex surrounds medulla; broad pyramid bases face cortex and pointed papillae face the collecting system. Keep cortex between pyramids as renal columns. Urine route is papilla → minor calyx → major calyx → pelvis → ureter. Hilum is medial. Internal geometry is an original teaching construction; the source shell does not supply cortex or pelvis segmentation. Source: NIH/NCI SEER https://training.seer.cancer.gov/anatomy/urinary/components/kidney.html .
Bronchi: trachea divides into right/left main bronchi; right is generally shorter, wider, more vertical. Each main bronchus supplies lobar branches: right upper/middle/lower, left upper/lower. The right upper branch separates before the bronchus intermedius continues to middle/lower. Use five labeled lobar routes; avoid claiming a complete segmental tree. Sources: https://www.ncbi.nlm.nih.gov/books/NBK537353/ and https://pmc.ncbi.nlm.nih.gov/articles/PMC7122111/ .
Existing procedural brain source is in staged anatomy.ts, function brain(). It creates two generic folded hemispheres, cerebellum and brainstem. This is a recognition schematic without anatomical gyral labels, patient-scale coordinates, white matter or segmentation provenance; return value is independently display-fitted. Re-authoring it in physical scale needs an explicit design scale.

