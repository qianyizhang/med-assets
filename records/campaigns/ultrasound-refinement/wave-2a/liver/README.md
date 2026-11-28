# s1233 liver r02 · Wave 2A builder receipt

**Lead disposition · Adopt for the named exterior-orientation task.** See the [wave decision](../README.md) for the final scores and chapter binding. The following receipt records the builder’s trial and proposed scores.

The rebuilt liver uses about **90% fewer bytes and triangles** than r01. Its broad right lobe, narrower left extension and inferior cleft remain visible in the neutral clay views. The decisive whole-surface, axial section, topology, volume and silhouette gates passed. The lead subsequently adopted `abdomen-survey / abd-liver` for whole-lobe orientation and scored fidelity 3/4. The review proposal covers exterior orientation at the saved oblique portal acquisition.

| Evidence | What to inspect |
| --- | --- |
| [Exact r01 and r02](../../../../../experiments/ultrasound-sweep/development/asset-reviews/liver-wave-2a/previous-vs-r02.webp) | Read the large and small lobe outlines and the inferior cleft. The dome terraces soften. Some shallow inferior relief remains. |
| [CT half-label and r02](../../../../../experiments/ultrasound-sweep/development/asset-reviews/liver-wave-2a/matched-surfaces.webp) | Identical clay, camera and scale within each row. The r02 highlight runs across the broad dome without the raw voxel terraces. |
| [Protected axial sections](../../../../../experiments/ultrasound-sweep/development/asset-reviews/liver-wave-2a/protected-planes.webp) | Three cuts centered on slice 207 and two details of the source channels restored or bridged during refinement. |
| [Actual player at frame 12](../../../../../experiments/ultrasound-sweep/development/asset-reviews/liver-wave-2a/live-frame-12.webp) | Each WebGL view used the corresponding pinned mesh byte for byte. Probe pose, simulated scan and tissue overlay match. |
| [Measurements](../../../../../experiments/ultrasound-sweep/development/asset-reviews/liver-wave-2a/measurements.json) · [Proposed scores](../../../../../experiments/ultrasound-sweep/development/asset-reviews/liver-wave-2a/reviews.json) | Both directions, worst locations, protected sections, exact browser captures, negative test and witness hashes. |

## Source and shaping

- [Before-shaping freeze](frozen.json) pins the original r01 bytes, case and mask digest, affine, half-label, saved frame 12, same-case scan artifacts and three axial cuts at offsets −1.5, 0 and +1.5 mm. The exact r01 owner replay also matched after adding r02. The existing chapter uses an illustrative liver view. The disposable native comparison is on the standalone s1233 sweep.
- The public TotalSegmentator s1233 label has one foreground component with four handles by the 6-connected voxel calculation. The narrow channels have uncertain identity. The task concerns the liver exterior and the inferior indentation visible around axial slice 207.
- The recipe smooths a signed-distance field in all three directions on a 0.75 mm working grid and uses a stronger axial kernel for the dome. It protects the inferior cleft with a smaller kernel. The distributed mask is aligned to canonical RAS. The scanner orientation is unavailable, and the visible terraces follow the distributed axial grid.
- Initial smoothing for a single shell shortened a deep channel near source voxel `(156, 151, 236.5)`. This produced an 8.03 mm half-label-to-export global maximum. The final recipe preserves this and nearby narrow folds with local masks informed by lightly smoothed native occupancy. Restoring the inferior passage introduced a handle. A compact field correction centered at `(171, 178.5, 219.5)` with a 1.5 mm support radius added 12 foreground samples on the fine grid, producing a connected bridge while preserving both adjoining recesses. Tests that raised voxel Euler by introducing an isolated bead were rejected on clean mesh import.
- Blender used curvature-sensitive quadric collapse to 12,000 triangles. The output is one outward closed manifold with no open edges, nonmanifold edges, degeneracies or nonincident intersections.

## Exact gate results

| Gate | r02 observation |
| --- | --- |
| Replays and native admission | Two clean replays reproduced SHA-256 `711014c7f2fe14381640a98abe46155fa2fec541bab773ab10c9d72370ecb9a1`, 216,032 bytes. AssetKit record sync, hydrated `check-port` and `validate` passed locally. |
| Whole surface vs raw half-label | Larger directional p95 0.89 mm and maximum 2.95 mm. The r01 comparison is 0.63 and 3.22 mm using the same sampling. |
| Protected slices 206, 207 and 208 | Largest full-cut p95 ≤1.5 mm and maximum 2.95 mm. Cleft-window maximum 1.08 mm. The three cuts preserve both banks. |
| Enclosed volume and closed solid | −0.33% from the half-label. Euler 2, one component and positive signed volume. |
| Tessellation | 0.90 px maximum departure against the dense shaped surface across 24 orthographic views at 3 px/mm. |
| Distorted disposable copy | A 12 mm RAS x translation returned status 1 on the same geometry checker. It failed global, protected-plane and silhouette gates. Largest global departure was 14.08 mm. |
| Saved player | The normal liver builder and compact assembly passed on an isolated native r02 pin with the updated regional staging tree. Chrome for Testing 158 rendered both live views without a page error. Each loaded its own exact mesh once and decoded frame 12, the matching overlay and the acquired reference. All 49 poses and 98 scan and overlay images matched. The largest first-ray contact error was 0.174 mm. |

The saved oblique cut is a separate diagnostic from the frozen axial cleft bracket. A small interior feature gives a half-label-to-export maximum of 8.45 mm in the oblique cut, up from 7.87 mm on r01. It persists on the unclipped oblique plane. The live view demonstrates orientation and the broad silhouette. Its overlay is sampled from the source mask. The geometric bridge offers no evidence of channel patency or a hepatic-vein junction. The acquired comparison depicts a different case.

## Reproduce the receipt

Use the [owner replay command](../../../../../models/liver_s1233/README.md#replay) twice in fresh paths and compare the output hashes. The commands below use the replay environment from that package, the retained compact r01 comparison as `LIVER_BASELINE`, and `LIVER_SCRATCH` pointing to a new subdirectory under the ignored campaign staging root. Put a clean `r02.mesh` and its optional `r02-dense.npz` there first.

```sh
LIVER_RECEIPT=records/campaigns/ultrasound-refinement/wave-2a/liver

PYTHONPATH="$PWD/experiments/ultrasound-sweep${PYTHONPATH:+:$PYTHONPATH}" \
  python -W error::RuntimeWarning "$LIVER_RECEIPT/measure.py" \
  --case "$S1233_CASE" --baseline "$LIVER_BASELINE" \
  --candidate "$LIVER_SCRATCH/r02.mesh" --dense "$LIVER_SCRATCH/r02-dense.npz" \
  --output "$LIVER_SCRATCH/measured"

uv run assetkit sync models/liver_s1233/asset.record.json
uv run assetkit check-port anatomy:s1233:liver-window@r02:liver \
  --record models/liver_s1233/asset.record.json \
  --path models/liver_s1233/exports/r02/liver.mesh \
  --sha256 711014c7f2fe14381640a98abe46155fa2fec541bab773ab10c9d72370ecb9a1 \
  --bytes 216032 --triangles 12000
uv run assetkit validate
```

`measure.py` verifies the frozen inputs before checking both directions and writes the results before returning nonzero on a failed gate. For the negative control, run the same command with a disposable packed copy whose x coordinates have all been incremented by 8 voxels. Use a fresh `--output` directory.

For live evidence, rebuild `liver` with `build_abdomen.py --track liver` and assemble a compact delivery in an isolated source and staging tree with the candidate pin. Run [player.mjs](player.mjs) with the baseline delivery, candidate delivery, fresh capture path and exact candidate SHA-256 as its four arguments. [render_clay.py](render_clay.py) uses the retained Blender rig to render the clean meshes. [witnesses.py](witnesses.py) builds the four comparison plates from those renders, the measured cuts and browser captures. The retained measurements attach the replay and browser identities to the geometric output.

Tested from `e3961e616c8ef71ea2d9b49b8cb94358c0ad3373` with local Wave 2A work. The initial retained regional stage had stale carotid and aortic receipts. The refreshed lead stage resolved assembly, permitted a 28-sweep disposable comparison and left the exact liver baseline intact.
