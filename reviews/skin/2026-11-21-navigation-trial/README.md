# Skin envelope navigation trial

Keep the lighter envelope as a recipe-built option for whole-body navigation. The Gallery continues to offer r01 with its [partial assessment](../2026-10-24-bp3d-envelope-r01-bounded-migration/teaching-assessment.json).

| Clean imported export | GLB bytes | Triangles |
| --- | ---: | ---: |
| Pinned FJ2810 control | 4,901,132 | 203,382 |
| Navigation candidate | 3,480,472 | 144,188 |
| Reduction | 1,420,660 (29.0%) | 59,194 (29.1%) |

The candidate meets the geometry and view checks and the 25% triangle target. It falls 1.0 percentage point short of the 30% byte target. The [recipe](../../../models/skin/recipes/navigation-trial/README.md) pins the control and builds candidate SHA-256 `e89de0c33f094e76ba909ba1d5a46a46cf994c0850c080abbf4be43993600b9d` on Blender `fab76e95306d`. Both clean imports had the same world matrix, bounds and indexed seam topology. The protected shoulder, wrist, hand, ankle and foot faces retain their exact positions and normals. The largest two-way sampled surface deviation was 1.68 mm, near the posterior midline at a source height of 0.770 m.

## Paired views

[Anterior and isometric comparison at the 680-pixel teaching scale](overview.webp) · [Neutral hand and foot crops at fourfold scale](hands-and-feet.webp)

The rendered outline shifted by a maximum of **0.25 display pixels** in each view at 4× sampling. The native 680-pixel masks had a one-pixel worst difference in each view after binarization. The largest sampled 4× shifts include the top of the head in both views. The shoulder caps, head and neck outline, torso and knees read the same in the matched overviews. All four interdigital gaps on each hand read in the anterior crops. The thigh occludes part of the left-hand gaps in the isometric view in both revisions, and the visible gaps survive on both sides. The wrist transitions, ankle outlines, toe scallops and heel shapes remain legible. The few changed hand and foot mask samples were at the upper crop edges over a forearm or lower leg.

The control rerenders match the foreground masks of both retained teaching WebPs and the decoded RGBA pixels of both original teaching PNGs. The PNG file digests differ because Blender stamped different text metadata. [Clean-import and render bindings](comparison.json) · [Measurements and evidence identities](pixels.json)

## Body Systems viewer decision

On 2026-11-22, headless Chrome loaded the pinned r01 and candidate bytes in the Body Systems viewer at `bdf5661`. Two temporary scene entries reused the skin and skeleton assemblies, replacing only their envelope input. The anterior and isometric foreground bounds matched r01 on a 773 × 561 canvas. Panning and zooming to the hand showed the wrist and all five digits in both exports. Toggling the surface hid and restored it. In the skeleton assembly the translucent skin aligned with the limbs, and hiding it produced identical skeleton-only captures with 622,754 triangles.

The 1,420,660-byte saving and preserved landmarks justify keeping the recipe for this use. Rebuild the candidate when a navigation view needs it. The existing Gallery lesson uses the retained plates.

## Verification and retention

The complete replay in a fresh directory reproduced the candidate GLB and both WebPs byte for byte. The entry points rejected an unhydrated LFS pointer, an occupied output directory, a changed candidate normal and a tampered capture. `python3.12 tools/verify.py offline` passed 443 tests and 1,006 LFS pointer identities on `276f825` plus this scoped trial in an isolated checkout.

The trial GLB and raw renders are ignored. The two retained comparison sheets add 477,414 current-tree LFS bytes. No files retire in this slice, so the net addition is 477,414 bytes.

The control’s fidelity assessment still needs a direct comparison to the archived FJ2810 member. Its surface-form assessment, browser performance and public cutover remain open.
