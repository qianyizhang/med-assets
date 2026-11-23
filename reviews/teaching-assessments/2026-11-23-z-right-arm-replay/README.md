# Right-arm source replay review

The [shared recipe](../../../models/joints/recipes/z-right-arm/README.md)
builds four teaching subsets from one exact Z-Anatomy source input.
Blender 4.3.2 on macOS rebuilt all four, reproduced the cuff GLB byte for byte,
and reimported the normal and disposable-edit GLBs for each selection.
The earlier exact elbow, shoulder and ulnar files continue to carry their own
historical evidence.

| Teaching task | Current exact-file teaching plates | Decoded comparison |
| --- | --- | --- |
| Find the elbow capsule and inspect the annular relationship | [Anterior and deep oblique](views/elbow-teaching.webp) | 8,332 oriented triangles, including exact index streams for the humerus, radius and ulna. The capsular overview and deep view keep the same named occluders. |
| Orient the capsule, humeral head and scapula, then expose the glenoid | [Anterior and deep oblique](views/shoulder-teaching.webp) | 36,700 triangles, including the 36,698 existing oriented faces and two zero-area scapular faces. The glenoid and spine anchors project to the same coordinates. |
| Find the cuff muscles around the scapular spine and on the reverse | [Existing exact teaching sheet](../../joints/2026-10-30-rotator-cuff-r01/v2/teaching.png) | 38,678 triangles and the complete original GLB reproduced. Fresh matched anterior and posterior captures have identical pixels. |
| Follow the ulnar nerve beside the medial epicondyle and olecranon | [Posteromedial and medial landmarks](views/ulnar-teaching.webp) | 9,136 oriented triangles with identical bone streams and placement. The thin nerve reproduces the same world surface within 0.000015 mm. Three matched views, including whole-arm context, have identical pixels. |

Decoded positions were compared bidirectionally in world coordinates. The maximum
Euclidean gap was 0.000121 mm over all four studies. Oriented matching preserves
face multiplicity and distinguishes reversals from index-order changes.
The elbow and ulnar radii, ulnae and humeri retain their original oriented face
counts, with shared source vertices and world registration. On matched triangles,
the largest per-component 99th percentile of corner-angle changes is 0.011°. The elbow
and shoulder humeri have a maximum corner delta of 0.320°. The nerve's is 0.006°.
Material mode, sidedness, colors, roughness and capsule opacity agree. Ulnar
numeric material factors differ by less than 0.00000002 from float encoding.

Both extra scapular triangles have **zero area in the decoded GLB**. Each repeats
one position exactly. Both lie inside a patch with a 1.14 mm diameter.
Five matched corner normals at the same position differ by more than 1°,
with a 34.7° maximum. The closest changed-triangle vertex is 52.5 mm from the
recorded glenoid-labrum anchor and 71.3 mm from the recorded scapular-spine anchor.
The original shoulder's baked native encoding was retained after testing direct
local-frame export. That trial retained the two extra collapsed triangles,
increased the scapular count of corners differing by more than 1° to 23, and
changed four distal-ulna diagonals. The baked encoding avoids those ulna changes
and keeps all nonzero-area oriented faces.

The 560 × 560 comparison pairs use fresh clean imports, matched orthographic
camera and scale, 24 Cycles samples and AgX exposure. The worst paired mean RGB
difference was 0.00026 on a 0–255 scale. The largest single-channel difference
was 24 in the shoulder view. Selected landmarks were checked at the nearest
reimported surface vertices against the source coordinates from the earlier
reviews, with unchanged projections at the recorded precision. Landmark labels
locate the visible gross relationship. The comparison does not establish
patient scale, soft-tissue attachment or complete anatomy.

In the verification command, moving one disposable humeral vertex by 0.1 mm in
the source changed exactly one vertex in each of the four clean reimports.
Topology and other members' positions and corner normals were identical.
Reusing an existing output and a wrong source hash both failed. An injected
failure after the first export left no output or staging folder, and rerunning at
that destination succeeded with four exact active deliveries. The check used
base revision `3db3f60` plus the shared-replay changes represented by the exact
asset identities in the [assessments](campaign-assessments.json).

## Reproduce the three current teaching plates

Run from the repository root with the assessed GLBs hydrated. The
[renderer](render.py) reads their identities from the assessment and renders the
six crops. It uses the original joint camera contract and the retained ulnar
view targets with [shared scene setup](../../../lessons/right-arm-parts/arm_scene.py).
The [plate script](plates.py) owns the bilingual titles, legend
and projected label positions. Verification checks each produced WebP against
its recorded byte count and SHA-256.

```sh
right_arm_plate_replay="$(mktemp -d)"
blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 \
  --python reviews/teaching-assessments/2026-11-23-z-right-arm-replay/render.py -- \
  --out "$right_arm_plate_replay/renders"
python3 reviews/teaching-assessments/2026-11-23-z-right-arm-replay/plates.py \
  --input "$right_arm_plate_replay/renders" --out "$right_arm_plate_replay/plates" --verify
```

Verified byte for byte on macOS with Blender 4.3.2 using Cycles CPU and
Python 3.9.6 with Pillow 11.3.0, FreeType 2.13.3 and libwebp 1.5.0.
The default fonts are macOS Arial
(`/System/Library/Fonts/Supplemental/Arial.ttf`) and STHeiti Medium
(`/System/Library/Fonts/STHeiti Medium.ttc`). Use the same font files for
exact replay through `--latin-font` and `--chinese-font` on other installs.

Z-Anatomy / BodyParts3D geometry and rendered evidence use CC BY-SA 4.0, with
historical BodyParts3D / DBCLS CC BY-SA 2.1 Japan credit.
[Provider attribution](../../../sources/datasets/z-anatomy/joint-regional-studies/upstream/ATTRIBUTION.md)
