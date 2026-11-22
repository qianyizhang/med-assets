# One Breath · left main bronchus cutaway review

Trace the exposed channel down the trachea to the fork, then follow the branch toward the patient's left. The exact [V7 section](../../../models/trachea/exports/open-airway-r06/trachea-cutaway.glb) retains the original One Breath asset identity. Use the [labeled teaching views](views/left-main-teaching.webp) to check the branch and recover exterior context.

An isolated anterior view exposes the channel and both distal cuts. A closer neutral oblique still shows the fork and the lane to the left outlet. The laterality labels use the [lesson's port coordinates](../../../lessons/one-breath/assets.json) in the same frame. The posterior oblique recovers exterior context from the separately selectable illustrative bands. The sleeve, inner surface and opened anterior side are authored over a cast-derived host. The exposed route illustrates topology and relative position. It does not depict measurement, airflow, histology or finer distal anatomy.

## Exact-file check

Blender 5.2.3 separately imported the tracked V7 download. The [owning topology receipt](../../trachea/2026-10-29-open-airway-r06/cutaway-geometry.json) confirms one connected, closed cutaway shell surface with 3,408 welded vertices and 6,812 triangles, no failed edge incidence, no zero-area triangles and no detected nonadjacent shell self-contacts in the finite-precision screen. It preserves both branch outlets as editorial section rims. The full GLB has 19 selectable meshes, 21 material primitives and 24,942 triangles. Three material regions distinguish the inner wall, outer wall and editorial cut. Each of the 18 separately selectable C-bands supplies context in a rotated view.

The original [V7 review](../../trachea/2026-10-29-open-airway-r06/README.md) records the reuse boundary between V6 and V7. The connected-airway sample graph was measured on the V6 open-shell model and serves that earlier open-shell exercise. This cutaway assessment traces the exposed surface in fresh exact-V7 renders.

## Same-scope size trial

A [matched trial](views/left-main-encoding-comparison.webp) packed only normals using the already checked open-shell technique. The original V7 export is 1,564,740 bytes. The scratch trial is 1,100,744 bytes, a 29.7% saving. Positions and indices are byte-identical. The largest tested normal-direction change is 0.372° on an illustrative band cut. All four matched image pairs differ by at most one level in any 8-bit RGB channel.

Retain the exact V7 model for the current lesson and its verified download. The packing trial establishes a smaller option if download size warrants a separate edition with its own Gallery and lesson evidence. The assessed original uses full-precision normal streams and retains its own measured bytes and score.

## Replay and credit

Use Blender 5.2.3 with the hydrated V7 GLB and a fresh render directory. Assemble the verified PNGs with Python 3.12 and Pillow 11.3.

```sh
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P reviews/teaching-assessments/2026-11-23-trachea-cutaway/review.py -- \
  models/trachea/exports/open-airway-r06/trachea-cutaway.glb .artifacts/trachea-v7-review
python3.12 reviews/teaching-assessments/2026-11-23-trachea-cutaway/plates.py \
  .artifacts/trachea-v7-review .artifacts/trachea-v7-plates
```

The [render receipt](render.json) pins camera, selected objects and raw image identities. The [plate receipt](views/plates.json) pins the public-facing evidence and its matched pixel differences. The [assessment](campaign-assessments.json) binds the exact V7 file. The cast-derived host retains TotalSegmentator s1233 attribution, CC BY 4.0, and the original label-source notice. [Attribution and anatomy references](../../../models/trachea/exports/open-airway-r06/ATTRIBUTION.md)
