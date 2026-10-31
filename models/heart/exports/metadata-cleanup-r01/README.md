# Source heart — metadata correctness alternative

Local correctness maintenance under [collection #150](https://github.com/qianyizhang/med-assets/issues/150).
This separate derivative corrects inherited cardiac descriptions on the retained
source-heart surface. It is **not a geometric asset improvement or a new approved
study**. The original `body/breathing/heart_breathing.glb` remains unchanged and
canonical; no catalog, viewer manifest or historical review is redirected.

The exact source has one node, `Heart | source surface`, one mesh/material and
24,000 triangles. Its one clip, `Illustrative breathing · 4 seconds`, contains one
LINEAR translation channel with 81 keys from 0 to 4 seconds and no morph targets.
This is authored illustrative movement of the surface, not cardiac contraction,
valve timing, measured physiology or a complete internal heart.

## Correction and identity

The [seven-field patch](../../../../tests/scene_metadata/heart/approved-patch.json)
is the authoritative old/new value record. It replaces `README`,
`clinical_status` and `animation_model` with the source/clip description above.
It removes unsupported `coordinates`, `reference_phase`, `material_set_names`
and `pericardial_layers` claims. No replacement coordinate or physiological phase
assertion is introduced. The exported GLB does not establish keyboard, cutaway or
material-switch controls.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Original breathing GLB | 2,037,364 | `3894d51df42a6e5941f0d2b076992d5359279f5e3ddb3b6d4ff6c00f58328086` |
| Separate `heart.glb` | 2,037,228 | `50c86dcab55701ca1418e16cd269ded70027663d58d02270ec6df0c8afd488fb` |

The full 2,033,172-byte BIN chunk and every JSON value outside the seven allowed
scene fields are identical. This includes mesh attributes, indices, textures,
materials, transforms, node attribution, animation channels and accessors, and
the existing root motion note. The more specific scene description identifies
the actual translation-only clip. JSON encoding and the GLB length change;
render and animation data do not. Screenshots and rerenders are not applicable.

## Consumers and limits

- The retained [body manifest](../../../../body/breathing/animation-manifest.json)
  already identifies a segmented source heart, the 4-second clip and
  `cutawaySupport: false`. It continues to bind the original bytes. The retained
  [body test](../../../../body/breathing/test_motion.mjs) reads node `view_role`
  and manifest controls; those contracts are preserved. No executable consumer
  of the seven scene fields was found in the tracked viewer/test code.
- Blender 4.3.2's native glTF importer copies scene extras into scene custom
  properties. Actual imports expose the original descriptions before the change
  and the corrected three fields afterward. Imported geometry, node properties,
  materials/image inventory, animation curves and world transforms at all 81
  key times match. This checks import/state behavior without rendering.
- The original body `studio.js` and its historical dependency paths are absent
  from this checkout; its live UI was not tested. The protected runtime fixture
  uses a different authored 0.8-second heart, so it is outside this correction.
  [PR11](https://github.com/qianyizhang/med-assets/pull/11) excluded this heart;
  [PR158](https://github.com/qianyizhang/med-assets/pull/158) changed that separate
  authored heart's exterior presentation. Neither is a source-heart replacement.
- Anatomy/clinical and browser-runtime approval remain unverified. No visual or
  whole-organ acceptance is promoted. This local derivative is not published.

## Provenance and retention

The unchanged node attribution identifies source case `s1233`, `heart.json`,
tb3 revision `75ec4e6530abe4d434b07958e90bdc9dec062bef`, and prior repair,
voxel-remesh and smoothing. The retained raw JSON's SHA-256
`545f45eb67d47965c6e86aa6bd9442069e603a600adaf278db2b90c11cc5f61d`
matches its source manifest and Git blob receipt. This verifies retained source
identity, not a fresh segmentation reconstruction.

Credit Jakob Wasserthal and TotalSegmentator contributors, University Hospital
Basel, [TotalSegmentator v2.0.1](https://zenodo.org/records/10047263).
Keep the existing [NOTICE](../../../../body/breathing/NOTICE.md),
[CC BY 4.0](../../../../body/breathing/CC-BY-4.0.txt), and retained
[Apache-2.0 label license](../../../../body/anatomy-workshop-r1/docs/licenses/TotalSegmentator-v2.0.1-LICENSE.txt).
Changes here are only the seven scene metadata fields; prior display modifications
and artistic materials remain documented. No source-author endorsement is implied.

One additional GLB is retained as the exact, independently inspectable corrected
alternative. It reuses the original embedded BIN rather than introducing new
geometry or texture evidence. The patch replays it exactly; the small
[verification receipt](../../../../reviews/heart/2026-10-30-source-metadata-r01/verification.json)
records scoped checks. No duplicate screenshots or copied source payloads are added.

## Reproduce locally

With the retained GLB payloads available, from repository root:

```sh
python3 tools/patch_scene_metadata.py --patch tests/scene_metadata/heart/approved-patch.json body/breathing/heart_breathing.glb /tmp/heart-metadata-replay.glb
python3 tests/scene_metadata/heart/verify.py
blender --background --factory-startup --python-exit-code 1 --python tests/scene_metadata/heart/import_check.py
python3 tools/verify.py offline
```

The replay output must not already exist. The shared patcher rejects changed
input, old values, paths outside scene extras and unreviewed output identities;
it never overwrites an existing output. Offline tests bind both LFS index
identities and source attribution without requiring hydrated media. The scoped
verifier checks actual payloads; the Blender check is a separate native import
gate. No download, browser, render, upload or publication is performed.
