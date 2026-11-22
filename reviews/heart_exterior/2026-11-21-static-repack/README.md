# Static opaque heart repack

The separate candidate passed the local packaging trial. It saves **5,543,680 bytes (61.93%)** and retains 124 selectable objects, 128 primitives, 152,216 triangles and all 15 used materials. [AG-GAL-019](../../../records/work-items/items/AG-GAL-019-repack-static-heart-exterior.md)

| GLB | Bytes | SHA-256 |
| --- | ---: | --- |
| Original `static-opaque-exterior.glb` | 8,951,936 | `595380d0aff153db4494fc5f9e8ffba062d0732c2bf0886242ebe1a188d3806f` |
| Updated `static-opaque-exterior-repacked.glb` | 3,408,256 | `221c8be48c44f49ebbc4a52b2ce4094a5c4b15ea1be01db39038ac8a8f4a52b5` |

The packer removes 265 meshes, 25 materials, 898 accessors and 898 buffer views unreachable from the static scene. The removed views account for 5,335,492 bytes, with 12 further BIN bytes in alignment padding and 208,176 bytes in the shorter JSON chunk. A fresh build produced the same export bytes.

- The static verifier resolved 436 retained accessors and compared 586,713 decoded elements with their encoded bytes. Mesh and node names, root order, hierarchy, transforms, material assignments, material values and extras matched exactly. The candidate has only reachable table entries and their aligned BIN bytes.
- Both clean Blender imports match at all 80,367 evaluated world-space vertex coordinates. Each of the same 124 visible mesh objects was selected individually in both imports.
- The 960 × 960 whole front view retains the clinical colors. The neutral close-up targets the right atrial and ventricular seam below the pulmonary trunk. Both pairs use the r01 orthographic cameras and lighting at frame zero, with 48 CPU Cycles samples and AgX. The decoded RGBA8 buffers have zero differing pixels in each pair. The same Blender 5.2.3 LTS Release Candidate (`fab76e95306d`) rendered both exports. The historical review used Blender 4.3.2.
- The normal CLI and injected failures checked input identity, deterministic replay, destination preservation and simultaneous writers. The verifier refused corrupt geometry, material, transform and hierarchy changes, an unreachable mesh, surplus BIN bytes, insufficient savings and mismatched render evidence.
- Both r01 controls replayed byte-for-byte. The existing hydrated package check and all 15 r01 replay and failure checks passed. The repository offline and payload-integrity gates passed. [Exact evidence and counts](checks.json)

The ignored local bundle `.artifacts/AG-GAL-019-heart-repack/` holds the GLB, `Original/` and `Updated/` comparison views, exact camera and light bindings, and full check output. Git retains the recipe and evidence digests. Rebuild the GLB from the [pinned r01 export](../../../heart/exterior-presentation-r01/README.md#static-repack-candidate) if the local bundle is retired.

The result supports [AG-GAL-020's separate local Gallery adoption](../../../records/work-items/items/AG-GAL-020-adopt-static-heart-repack.md). The trial establishes packaging parity. The clinical and geometric limits from the [r01 review](../2026-10-30-native-visibility-r01/README.md) apply to both files.

## Repeat the paired import and pixel checks

Run from the repository root with the variables from the [package recipe](../../../heart/exterior-presentation-r01/README.md#static-repack-candidate). Set `blender_bin` to the headless Blender executable and make FFmpeg available on PATH. Use the same Blender build for the whole pair.

```sh
recipes=heart/exterior-presentation-r01/recipes
reference=reviews/heart_exterior/2026-10-30-native-visibility-r01/updated-static-bindings.json
"$blender_bin" --background --factory-startup --python-exit-code 1 --python "$recipes/reimport_motion.py" -- \
  --source "$source_glb" --candidate "$candidate_glb" --output "$evidence/reimport.json"
"$blender_bin" --background --factory-startup --python-exit-code 1 --python "$recipes/verify_repack_selection.py" -- \
  --source "$source_glb" --candidate "$candidate_glb" --output "$evidence/selection.json"
"$blender_bin" --background --factory-startup --python-exit-code 1 --python "$recipes/render.py" -- \
  --source "$source_glb" --out "$evidence/Original" --kind static --views whole-front,seam-neutral \
  --match "$reference" --label Original
"$blender_bin" --background --factory-startup --python-exit-code 1 --python "$recipes/render.py" -- \
  --source "$candidate_glb" --out "$evidence/Updated" --kind static --views whole-front,seam-neutral \
  --match "$evidence/Original/bindings.json" --label Updated
python3.12 heart/exterior-presentation-r01/verify_repack.py --source "$source_glb" \
  --candidate "$candidate_glb" --renders "$evidence"
```
