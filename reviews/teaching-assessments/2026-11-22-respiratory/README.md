# Respiratory starting-file review

Codex inspected the ten starting files in the [maintained register](../../../docs/gallery/maintained-models.md#respiratory) on 2026-11-22 at `f6f87c4b81e4e9cf069a378d01d075c6cc7df95b`. The [machine-readable judgments](campaign-assessments.json) bind each task, reference, exact artifact and reviewed view. Scores below use fidelity, form, readability and economy in that order.

| Starting file | Scores | Decision and open evidence |
| --- | --- | --- |
| Breathing assembly | 3 / 3 / 2 / 2 | Keep for illustrative gross motion. The [side-view supplement](../../../records/work-items/items/TAQ-003-test-respiratory-improvement.md#breathing-view-trial--2026-11-22) exposes flattening. The exact assembly inventory identifies the cost of motion and context beyond these seven teaching parts. |
| [Bronchial first fork](views-1.jpg) | 4 / 2 / 3 / 4 | Keep r14 for the first fork. The protected junction retains its angular underside and right collar/pocket. Look again before extending the close-up task to the junction surface. |
| [Static diaphragm](views-2.jpg) | 3 / 2 / 3 / 2 | Keep for gross dome shape. Verify the source openings and descending projections before teaching named anatomy. Test whether the broad static dome can be lighter while keeping the thin rims. |
| [Left lung](views-3.jpg) | 3 / 3 / 3 / 2 | Keep for the two lobes and their oblique fissure. Locate the lower-lobe satellite and explain its origin before attempting removal or simplifying the base. |
| [HRA lung pair](views-4.jpg) | 4 / 3 / 3 / 2 | Keep as a source specimen. Use the grouped-lobe study for isolation at the whole-lobe level. Measure whether smaller cartilage samples preserve visible rings and hilar relations. |
| [Nasal airspace cast](views-5.jpg) | 4 / 2 / 3 / 2 | Keep as a CT airspace specimen. The inferior cutoff, central roughness, source pathology and retained intersections limit use. Check narrow channels before testing lower sampling. |
| [Pharynx and larynx](views-6.jpg) | 3 / 3 / 3 / 2 | Keep for cartilage orientation with isolation. Preserve neutral overrides for two disputed constrictors. Prioritize testing the contextual muscle cost before changing cartilage at the teaching zoom. |
| [Right lung](views-7.jpg) | 3 / 3 / 3 / 3 | Keep for three lobes and two fissures. Assess illustrative motion separately if it is part of a learner task. |
| [Terminal airspaces](views-8.jpg) | 4 / 3 / 4 / 4 | Keep r02 with its oblique and grayscale teaching views. Further close zoom exposes some faceting. Specialist review remains open. |
| [Trachea open shell](views-9.jpg) | 4 / 3 / 3 / 2 | Keep r06 for finding the three mouths. Use the separate cutaway for the internal junction. The 18 rings dominate the mesh budget and a lighter ring trial must protect the proximal rim and posterior gap. |

## Evidence and limits

Blender 5.2.3 LTS Release Candidate `fab76e95306d` loaded each hydrated GLB in a fresh scene and captured palette-front and neutral oblique/reverse views. Each JPEG shows the three views in that order, assembled from 640 × 640 source PNGs. Here “front” identifies the camera in the import coordinate frame. It carries no anatomical orientation claim for exports without a recognized native frame. The [render receipts](renders.json) record cameras, scales, visible objects, triangle counts and raw capture hashes. The [GLB component receipt](mesh-components.json) counts per-node vertex-connected components by exact positional welding across encoded primitives. The inspection preserves encoded transforms and does not infer anatomical connection between separate nodes.

The [motion sample](motion.json) comes from the exact delivered .blend. It records evaluated Blender world-space bounds, with +Z superior and the coordinates in metres. It compares frames 1, 49 and 121 rather than assuming identical endpoints. The [candidate view receipt](motion-compare.json) binds the rendered frames to the same assembly. The candidate is reviewed as a supplement alongside the [existing phase renders](../../../body/breathing/README.md#files-and-attribution). The review captures and assembly trajectory checks establish scoped local evidence without a specialist or browser-motion acceptance.

Replay the eight raw motion frames from the repository root with the exact assembly hydrated and an unused output directory.

```sh
blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 \
  --python reviews/teaching-assessments/2026-11-22-respiratory/compare-motion.py \
  -- .artifacts/respiratory-motion-replay
```

The retained JPEGs use 500 × 500 Lanczos-resized tiles with phase and view labels above each panel. Their encoded hashes are in the candidate receipt. The raw capture script records the same camera and pose bindings independently of the labeled composition.

The replay reproduced the camera and selection receipts exactly. Across eight raw captures, the maximum difference was one 8-bit RGB code value and the mean absolute difference was under 0.00004 code values per channel.

Run `blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 --python reviews/teaching-assessments/2026-11-22-respiratory/neutral-motion.py -- .artifacts/respiratory-neutral-replay` for the [neutral phase pair and exact assembly inventory](neutral-motion.json). The mesh inventory counts loop triangles by material slot and connected pieces after welding identical local-coordinate vertices in each mesh. Action channels are F-curves associated with each object's or shape key's assigned action slot.
