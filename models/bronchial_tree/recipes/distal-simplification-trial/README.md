# Trial distal simplification of r13

The teaching task is to trace the first fork of the authored exterior from the
trunk into both main branches. This trial compares the exact r13 GLB with one
lighter derivative at the views used in the
[Library assessment](../../../../records/work-items/items/AG-GAL-018-reconcile-library-revisions.md#teaching-assessment-pilot).

## Comparison defined before the build

Reuse the r13 diagnostic framing at 1000 × 850. Compare the neutral whole tree
at 237.15 mm, the front and opposite neutral fork at 45 mm, and the 45 mm
rotated underside view. Add a reverse whole view at the same overview scale
to see distal branches obscured in the original whole view.

Protect the central trunk and Y within |X| ≤ 28 mm in Blender coordinates,
the established left and right lobar neighborhoods within 12 mm, and all
16 terminal neighborhoods within 6 mm. Require identical oriented triangles,
positions and encoded normals on every face that touches a protected vertex.
Check the remaining exterior on clean reimport for one consistently oriented,
closed component with Euler characteristic 2, with no new degenerates or
lost tips. Compare branch placement in both directions using vertex and
face-center distances to the other surface. The maximum sampled distance
must stay below 0.20 mm.

The simplification must preserve the first-fork teaching cue and visible branch
paths, caps and junction contours in the paired views. Screen foreground masks
at 50% alpha for a worst silhouette shift of at most two pixels at the locked
output size. Inspect the largest visible difference and the accepted left
fairing and central Y separately. The trial aims to remove at least a quarter
of the triangles and reduce total GLB bytes.

## Replay

Run from the repository root. Use Blender 5.2.3 LTS Release Candidate
(`fab76e95306d`) and Python 3.12 with NumPy 2.4.6, Pillow 12.2.0 and
SciPy 1.17.1 for the image measurements. Supply the hydrated
[r13 export](../../exports/authored-central-fairing-r13/README.md) and use
fresh output directories.

```sh
recipe=models/bronchial_tree/recipes/distal-simplification-trial
source_glb=models/bronchial_tree/exports/authored-central-fairing-r13/bronchial_central_fairing.glb
trial=.artifacts/bronchial-distal-replay
mkdir "$trial"
blender --background --factory-startup --threads 4 --python-exit-code 1 \
  --python "$recipe/simplify.py" -- --input "$source_glb" --out "$trial/build"
blender --background --factory-startup --threads 4 --python-exit-code 1 \
  --python "$recipe/compare.py" -- --source "$source_glb" \
  --candidate "$trial/build/bronchial_distal_trial.glb" --output "$trial/capture"
python3.12 "$recipe/compare_pixels.py" "$trial/capture" "$trial/sheets"
```

The recipe tries five rounds of local edge collapses, in order of edge
length, on the lateral branches. Each uses an edge of at most 0.60 mm
and contracts to a surviving r13 vertex. The common neighbors must be
exactly the two corners opposite that edge, and remaining incident
triangles must turn by at most 22.5°. If neither endpoint preserves
those checks, the edge stays. Positions and encoded normals come
directly from the surviving vertices. Only the geometry buffers and
generator field change.

The builder rejects other input identities and existing destinations.
The comparison checks the reimported mesh, the source correspondence and
the protected faces. The pixel checker binds inputs to the capture
receipt, compares the native PNGs, and writes labeled sheets.
[Exact export and reviewed evidence](../../../../reviews/bronchial_tree/2026-11-21-distal-simplification-trial/README.md)
