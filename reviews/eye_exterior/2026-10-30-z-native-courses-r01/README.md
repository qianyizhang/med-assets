# Source-native eye exterior courses

The useful change is a distinct source-authored course around each globe, with a
visible trochlear turn and bounded optic segment. Parent review of the actual old
schematic and native witnesses selected this scope. The schematic already has
simple straps and rods; this is an additive source-context supplement, not a claim
that the baseline lacked those structures. This worker did not obtain the old
baseline pixels and does not claim to have inspected them.

## Artifact and evidence

- GLB SHA256 `39fd2cc18b2352b2ac73b46e76f486aa7eb7a8c0cc301a77a9b178a1cb8f70b9`;
  674,580 bytes, 20 surfaces, 35,884 triangles, two source-side scenes.
- [Teaching SVG](presentation/teaching.svg) / [PNG](presentation/teaching.png)
  and [grayscale](presentation/teaching-grayscale.png).
- Matched source/evaluated-export reimport views: [source R oblique](presentation/matched-source-R-oblique.png),
  [source L oblique](presentation/matched-source-L-oblique.png),
  [source R posterior detail](presentation/matched-source-R-posterior.png).
  These compare the native source with its export, not the old schematic.

The source/export cameras, orthographic scale, lighting, exposure, background and
neutral display roles match. The three accepted source renders are reused with
their exact hashes. Export renders come from clean import of the actual delivered
GLB. No selected geometry is cropped; native render margins are at least 96.226px.
Composition crops preserve at least 40px around the oblique geometry, and all
panel pixels remain exact outside the declared editorial leaders.

## Scoped checks and limits

`build-receipt.json` and `bindings.json` record exhaustive per-object checks:
the independently decoded GLB recovers the exact source local triangle-corner
positions/normals and native world matrices. The 20 source names, side mapping,
source parents, counts and neutral materials are checked. Existing source gaps,
overlaps, mirrored transforms and two beveled optic curves remain. Annotation
parents are recorded but not exported; this is a static surface subset, not a rig.

Two separate Blender processes produced identical GLB, bindings and build receipt
(`determinism.json`). The source master hash was checked before
and after extraction. Eight offline failure tests reject vertex/normal edits,
fitting translations, source-label changes, source-action shaders, missing surfaces
and unintended default-scene mixing.

Clean Blender reimport is a separate numeric check. Maximum world-coordinate
difference is `1.1920928955078125e-7` native units, within four float32 ULPs at the
source's largest world coordinate. Maximum matrix-component difference is
`3.5762786865234375e-7`. A provisional exact-normal reimport check failed:
Blender-imported custom normals differ by at most `0.0006637564` in vector distance.
The GLB NORMAL data itself remains exact. The reimport shading-direction budget
is separately 0.1 degrees; it is not an anatomical tolerance or a geometry repair.

Actual matched RGB images are very close, **not pixel-identical**: 167, 433 and
291 of 900,000 pixels differ in source R oblique, R posterior and L oblique.
The largest mean channel difference is 0.000369 on a 0–255 scale; maximum single
channel difference is 16. These sampled render metrics supplement decoded geometry
checks and actual visual inspection; they do not replace review.

The worker inspected all three reimport views, the teaching PNG, grayscale and
the teaching SVG reopened/rendered by Inkscape 1.4. Native labels remain readable,
the optic end is visibly bounded and unilateral panels avoid an implied bilateral
bridge. Source-bound ray hits anchor the nine numbered leaders. Independent review passed at
`54fcdc2f26f8850213e8b72febe8dfc4d32bc682`: the reviewer verified all 37 private
bundle entries, independently ran the 32-file payload check, inspected the reopened
teaching SVG and matched oblique/posterior pixels, and found no blocking presentation
issue. Unilateral views and explicit optic endpoints resolve the source-witness
bilateral-bridge concern. No artificial v2 geometry/image edit was made.
Anatomy/clinical approval and browser runtime remain
unverified; source labels and source units are not independently calibrated anatomy.

## Replay

Use Blender 4.3.2 with auto-execution disabled, Python/Pillow and Noto Sans CJK.
All output directories must be new. Supply the pinned original `Startup.blend`
from the source manifest; no source scripts or add-ons are needed or executed.

```sh
blender -b --factory-startup --disable-autoexec -t 4 \
  -P tools/eye_exterior/build_blender.py -- \
  --source /path/to/exact/Startup.blend \
  --reference sources/datasets/z-anatomy/eye-exterior-courses/source-inventory.json \
  --output /tmp/eye-build-new
blender -b --factory-startup --disable-autoexec -t 4 \
  -P tools/eye_exterior/render_blender.py -- \
  --candidate /tmp/eye-build-new/eye-exterior-courses.glb \
  --bindings /tmp/eye-build-new/bindings.json \
  --cameras tools/eye_exterior/cameras.json \
  --source-images reviews/eye_exterior/2026-10-30-z-native-courses-r01/renders \
  --output /tmp/eye-render-new
python3 tools/eye_exterior/compose.py \
  --renders /tmp/eye-render-new --output /tmp/eye-presentation-new
python3 -m unittest discover -s tests -p test_eye_exterior.py -v
python3 tools/eye_exterior/verify_payload.py --root .
```

Hydrate the package's LFS assets before payload replay. The complete offline gate passed on the delivery tree: 213 tests, 26 transport
manifests, 25 foundation records, 591 import references and 772 LFS pointer
identities. Hydrated package checks are separate; offline CI does not verify media
bytes, runtime or anatomy. The delivery follow-up changes this review text and its
manifest only; reviewed geometry, images, cameras and scripts remain unchanged.
Draft delivery references #150 without closing its broader collection scope.
The anterior study and #99 remain unchanged; no merge or Site publication is
part of this delivery.
