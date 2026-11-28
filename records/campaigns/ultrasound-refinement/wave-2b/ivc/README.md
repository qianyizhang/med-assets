# Wave 2B · s1233 inferior vena cava

Use the separate s1233 frame-12 exemplar to follow the caval trunk in 3D beside the aorta and locate it deep to the liver in the long-axis sweep. The abdominal survey's fictional visit has its own modeled teaching action. This packet evaluates the CT-derived exterior only. The [asset package](../../../../../models/ivc_s1233/README.md) owns the full case exterior and an abdominal locator for the standalone sweep and companion. The hepatic junction, flow, patency and caliper interpretation remain outside this evidence.

The lower trunk shows fewer bands than the raw label and smoother highlights in the reverse clay view. Subtle bands remain where the narrow kernel preserves the mid-trunk bulge and irregular superior flare. The saved oblique view partially covers the upper cava with liver. The axial and isolated clay views expose its course. The live overlay comes from the frozen case masks.

## Frozen comparison

The [freeze](reference.json) pins the exact previous 17,476-triangle sweep export and saved frame files, CT and mask, voxel-to-RAS grid, and raw 0.5-isovalue arrays. The source has one connected component and zero enclosed gaps. The whole source label spans native slices 140–278 inclusive. The existing abdominal sweep removes slices 271–278 and closes the superior crop boundary. No connected pieces were removed or voids filled. The narrower kernel preserves the fine inferior extension, mid-trunk bulge and superior flare.

Measure nearest triangles globally and nearest line segments in each protected cut in both directions, using a sampling step of 0.5 mm or less. Compare frame 12 and parallel cuts at ±1.5 mm, then axial cuts through the ends and changes in contour. Use the full cuts for acceptance and the imaged sector as context. The maximum allowed distance is 3 mm and the p95 limit is 1.5 mm. Signed volume must remain within 3%. Test 24 turning silhouettes at 3 pixels/mm and require a departure of at most 1 pixel. Require one consistently oriented closed shell with Euler 2 and no intersecting nonincident pairs.

The initial pass lost a 0.77 mm perimeter grazing loop in the +1.5 mm plane. The sampled error was 14.67 mm in plane and 0.70 mm in 3D at RAS (28.14, 157.89, 408.91) mm. At that location the previous sweep reached 15.48 mm in plane. Adjacent native slices show a shallow peripheral shoulder at Z 245–246, disappearing by slice 247. A tapered local correction preserves it in the final candidate. A modest increase in triangle count also brought the abdominal turning silhouette below the unchanged limit.

## Builder checks

| Gate | Abdominal sweep port | Full source extent |
| --- | ---: | ---: |
| Triangles · packed bytes | 6,000 · 108,032 | 5,798 · 104,396 |
| Whole-surface p95 / worst | 0.42 / 0.96 mm | 0.42 / 0.96 mm |
| Protected long-axis cuts p95 / worst | 0.58 / 1.77 mm | 0.58 / 1.77 mm |
| Protected axial cuts p95 / worst | 0.47 / 0.93 mm | 0.41 / 0.85 mm |
| Enclosed volume delta | +0.45% | +0.43% |
| Turning-silhouette worst | 0.90 px | 0.79 px |

- Both fresh replays reproduced both governed SHA-256 values. Both exports are LFS-tracked and passed AssetKit sync and hydrated check-port. Native show and impact resolved the records. AssetKit validate, economy and review check passed. The [wave delivery](../README.md) records the independently checked chapter binding.
- The verifier rejected a 14% X compression of both exports with exit 1. Whole-surface deviations rose to 4.47 mm and volume differences exceeded 13%.
- Chrome requested the exact previous and candidate mesh, pose, grayscale and overlay bytes at frame 12. The disposable compact player used the governed IVC port emitted by the abdominal builder and retained the prior context to isolate the mesh change.

[Previous and r01](../../../../../experiments/ultrasound-sweep/development/asset-reviews/ivc-wave-2b/previous-vs-r01.webp) · [Matched surfaces](../../../../../experiments/ultrasound-sweep/development/asset-reviews/ivc-wave-2b/matched-surfaces.webp) · [Protected planes](../../../../../experiments/ultrasound-sweep/development/asset-reviews/ivc-wave-2b/protected-planes.webp) · [Live frame 12](../../../../../experiments/ultrasound-sweep/development/asset-reviews/ivc-wave-2b/live-frame-12.webp) · [Measurements and identities](../../../../../experiments/ultrasound-sweep/development/asset-reviews/ivc-wave-2b/measurements.json)

Run [check_geometry.py](check_geometry.py) in the package replay environment. Its `freeze` command takes the source case, original staged IVC sweep directory, corresponding original compact study, and a fresh output directory. Its `evaluate` command takes that freeze directory, original staged IVC sweep directory, clean package replay directory, and a fresh output directory. The rendering commands take the verified report and render the exact packed captures. See `--help` for [Blender clay rendering](render_clay.py) and [plate composition](witnesses.py). [Browser capture](capture.mjs) takes the original study URL, disposable candidate study URL, capture directory and final measurement report. Both study URLs use loopback and the candidate uses the standalone path `sweeps/ivc/scenes/inferior_vena_cava.mesh`. Scratch arrays and intermediate renders are retained under ignored `.artifacts/us-wave2b/ivc/` for 30 days.
