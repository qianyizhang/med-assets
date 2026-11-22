# Replay the local marrow lattice trial

Run from the repository root with Blender 5.2.3 LTS Release Candidate `fab76e95306d` and the exact hydrated r05 GLB.

```sh
blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 \
  --python models/bone_marrow/recipes/lattice-economy-trial/trial.py -- \
  --control models/bone_marrow/exports/authored-source-cutaway-r05/marrow_cutaway.glb \
  --out .artifacts/marrow-lattice-replay
```

Use a fresh output directory. Add `--check-only` to build and check geometry without rendering. The recipe rejects a different input digest or occupied output. It edits the lattice only. Cortex and marrow accessor bytes, scene, nodes, materials and mesh declarations are preserved. The script clean-imports both generated GLBs. It records exact-weld topology, vertex/face-center nearest-surface samples in both directions, protected-region samples and matched raw views.

The moderate and strong requests use collapse ratios of 0.72 and 0.48 after exact-position welding. Low vertex weights resist collapse near the cortical shell or where an inward normal ray indicates thin lattice. This protection uses finite measurements on the authored surface. It has no relation to measured anatomical strut thickness. Use the strong export as a recipe-built local teaching option under the same scope as r05. The digest, measured trade-off and comparison views are in the [trial review](../../../../reviews/bone_marrow/2026-11-22-lattice-economy-trial/README.md). Retain the [r05 attribution and limits](../../../../reviews/bone_marrow/2026-10-26-source-cutaway-r05/README.md).
