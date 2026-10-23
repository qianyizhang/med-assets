# HRA single lymph-node teaching study

One unchanged source GLB, not a whole-body lymphatic system or a new clinical model. Seven source meshes; 851 boundary and 1,602 non-two-incidence edges remain. Source node key 7 says blood while extras say lymph: use neutral “Source vascular network (label conflict)”. Static visual approval is scoped to prior inspected layer contacts; anatomy reference screening is not clinical approval. Runtime unverified.

The source GLB is also the export; do not duplicate it. Source/license metadata is in sources/datasets/hra/lymph-node-v1.2. Review record and 3 lossy published WebP derivatives are in reviews/lymph_node/2026-10-23-hra-v1.2. Historical render-evidence.json records original PNG hashes and visibility settings; those lossless PNGs and native Blender scene are deferred, not missing claimed dependencies of this small import.

After git lfs pull, from repo root:

```sh
python tests/review_records/validate_record.py --root . reviews/lymph_node/2026-10-23-hra-v1.2/record.json
blender --background --factory-startup --disable-autoexec --python tests/lymph_node/review_exact_source.py -- --model models/lymph_node/exports/hra-v1.2/NIH_M_Lymph_Node.glb --output /tmp/lymph-review-new --checks-only
```

Omit --checks-only to render the source-native views into a new output directory. Never overwrite retained evidence. Blender 4.3.2 was used for the earlier source review; renderer/platform variation can change image bytes. Reproduction means declared source/camera/visibility/lighting, not a claim of bit-identical PNGs across environments.

## Import checks, 2026-10-23

- Fresh Blender 4.3.2 replay completed all 12 declared views from the unchanged GLB; 7 meshes, 851 boundary /1,602 non-two-incidence edges, 0 zero-area triangles reproduced. This is recipe execution, not a new anatomy/runtime approval or bit-identical contact-sheet claim.
- Local foundation record/hash validation passed.
- The four LFS payloads (7,776,280 bytes) were independently fetched from GitHub outside the upload runner at 08:45:08 UTC; every SHA/size and GLB/WebP magic matched before pointer publication. Upload run: https://github.com/qianyizhang/med-assets/actions/runs/39926775746 . This is transport verification, not model quality CI.
