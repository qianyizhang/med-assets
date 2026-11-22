# Lighter meshes for established teaching views

[Accepted decisions](accepted.json) · [Exact source, candidate and view measurements](measurements.json) · [Trial settings](trials.json) · [Work item](../../../records/work-items/items/TAQ-012-test-mesh-economy.md)

The baseline is `7b07c7dd45fec6e1b51a6f6de1d0d3924216c42d`. This review covers all 23 rows in the four 2026-11-22 campaign batches with fidelity, form and readability of at least 3 and economy below 3. Use an option listed in the accepted decisions for its named teaching task. The geometry and byte counts apply to each candidate's own identity. The default exports and their assessment identities still point to the original files.

| Result | Assets |
| --- | --- |
| Earlier local options reimported and verified against their owner digests | Skin envelope and marrow cutaway |
| New options for the reviewed gross views | Aortic tree, full clinical static heart, large intestine, tongue, breasts, prostate, blood cell study, skeleton, ears and pharynx/larynx |
| Lighter files for inspection | Small intestine, placenta, muscle, brain and spinal cord |
| Original retained after the detail guard rejected a captureable trial | Liver, left and right kidneys, and trachea |
| Original retained after seam-protected trials fell below the minimum reduction | Left lung and lung pair |

The largest byte savings among the new options come from the auricles (42.6%), colon (38.5%) and tongue (34.9%). The most conservative candidates leave the named targets untouched and reduce neighboring surfaces, as with the papillae, aortic branches and laryngeal cartilages. Findings and captions in the accepted file identify the intended action and the feature most at risk. The retained review includes the same-camera reimports of four explicitly rejected models and measured failure plates for the other two. For the six retained originals, exact full vertex tuples, unused ranges and index width put the possible lossless saving below 0.2% of the binary payload in every case.

## Build or recover a local option

Run from the repository root with Blender 5.2.3 LTS Release Candidate `fab76e95306d`, NumPy bundled with Blender and an exact hydrated control GLB. Use a fresh directory under `.artifacts/`. The trial's short name appears in [trials.json](trials.json).

```sh
blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 \
  --python reviews/teaching-assessments/refinement-economy/trial.py -- \
  --out .artifacts/taq-012-recovered --only large-intestine --no-render
```

Use the output `.artifacts/taq-012-recovered/large-intestine/candidate.glb` after checking its SHA-256 and byte count against the accepted decision. Add repeated `--only NAME` arguments to build a short list. Omit `--no-render` to produce the matched clean-import frames and camera bindings. A rejected preview writes `rejected-preview.glb`. It is evidence of the failed reduction. A run with only the left lung or lung pair writes a control render and a measured failure receipt. The plate builder pairs each receipt with its protected original detail. Python 3.12 and Pillow 13.0.0 build the comparison plates in a fresh directory:

```sh
python3.12 reviews/teaching-assessments/refinement-economy/plates.py \
  .artifacts/taq-012-recovered .artifacts/taq-012-recovered-plates/views
```

This command requires a run with renders. The receipts bind the output and view bytes. Blender PNG metadata can vary between runs.

The [skin owner recipe](../../../models/skin/recipes/navigation-trial/README.md#replay) builds `build/skin_navigation_trial.glb` in its chosen directory, and the [marrow owner recipe](../../../models/bone_marrow/recipes/lattice-economy-trial/README.md) builds `strong.glb` there. Each owner's review contains the matching digest and its own preservation and recovery checks. To include those already recovered files in a batch comparison, pass `--recovered skin=.artifacts/<owner-run>/build/skin_navigation_trial.glb` or `--recovered bone_marrow=.artifacts/<owner-run>/strong.glb`. The batch independently checks their expected bytes and clean-import shape.

## Checks and limits

The shared trial contracts short edges to surviving source vertices. The edge link must preserve connected regions, and surviving incident faces pass the face-turn check. The recipe freezes index seams, irregular boundaries, extrema and adjacent faces, with more specific bands or exact meshes for named targets. The accepted part receipts record those face counts, the two directed vertex and face-center samples, and the worst source-frame location. Pixel-equivalent surface thresholds use the model span and the part's smaller review scale. The separate one-pixel mask measurement samples the rendered 640 × 640 frames at 50% alpha and includes both views. It is a discrete screen measurement. Both checks use finite samples.

The operation copies surviving normals, colors and UVs from their source vertices. New faces can change their interpolation. Untouched accessors and non-mesh data retain their original bytes even when edited ranges share an original buffer view. The trial reimports the output and checks names, matrices, material slots and shape keys. The small-intestine trial preserves the source animation accessors and sparse displacement rows and samples the surface at weights 0, 0.5 and 1. Its still views and deformation samples cover only the stated gross task.

These are local Workbench shape and material comparisons with fixed cameras. The reported savings are triangle counts and encoded bytes. Spotlighted details inside the teaching views do not establish arbitrary level of detail, exhaustive self-intersection bounds, texture or shader fidelity, continuous motion, delivery availability, browser speed or anatomical validation. Source-specific attribution, editorial and teaching limits remain part of each exact starting export.

The fresh replay reproduced the 21 emitted GLB identities and the clean reimport triangle counts. Guard checks rejected an occupied output directory, a different recovered option and an unresolved LFS pointer. All 46 retained plates match the byte identities in the measurements.

The retained plates and measurements support active decisions. Raw renders and derived GLBs live under ignored `.artifacts/`; the exact controls and reproducible recipes provide recovery.

## Serve recovered candidates locally

After replay, run `python3.12 tools/teaching_assessments.py PATH_TO_REPLAY_OUTPUT` from the repository root. The command copies only approved, digest-matched GLBs into the loopback content store. It can collect files from multiple output directories and can be repeated. A conflicting existing file fails verification. Open the asset in **Compare → Teaching asset refinements** for the verified download and its exact-file decision.

TAQ-012 recorded alternate downloads at its review date. The [current teaching editions](../target-economy/README.md) identify which alternatives subsequently became maintained starting files.
