---
description: Add coached gland-location and parotid-course practice to the two Head & Neck stops.
scope: Anatomy Gallery Head & Neck
status: stable
last_update: 2026-11-23
document_class: work_record
work_id: AG-GAL-030
work_status: done
work_kind: build
added: 2026-11-23
depends_on: AG-GAL-028
tags: gallery, lessons
---

# AG-GAL-030 — Practice salivary gland locations and parotid duct course

**Owner** · Head & Neck lesson maintainer.

The original stop explained the answer beside a teaching plate. The new stop asks the learner to locate or trace a relationship and then check it against numbered anatomy. The [existing source comparison](../../../reviews/salivary_glands/2026-10-26-native-scoped-r02/README.md) still explains the excluded submandibular course.

| Stop | Learner action and feedback |
| --- | --- |
| Gland locations | Start with the mandible and paired mylohyoid. Hold the superior oblique view while hiding them. Match all six visible gland shapes into three pairs. Reveal the numbered pair key to check placement relative to the jaw and oral floor. |
| Parotid duct course | Start with the left gland, duct, mandible and superficial masseter. Follow the tube over the muscle. Hide the surrounding tissues at the same scale and camera angle. Reveal the numbered landmarks on the context view to check the visible course. |

## Acceptance

- [x] Both existing routes start with the question and an unlabelled view. Each layer uses the same camera and has an unlabelled still. Reveal shows a numbered image and a text explanation.
- [x] Select only named parts from the reviewed [shared r01](../../../models/salivary_glands/exports/z-native-shared-r01/README.md) and [public r02](../../../models/salivary_glands/exports/z-native-scoped-r02/README.md) selections. Preserve mandible, floor and superficial masseter in context. Retain the exclusion of both submandibular ducts, with the right source course unaccepted and the left crossing documented. The lesson covers gross placement and the visible parotid surface course. Outlets, lumens and complete duct routing remain outside scope.
- [x] Verify both routes, layers, answer reveal, unavailable model response, source disclosure, Compare, Library and the oral-spaces return in the built Gallery.

## Plate replay and evidence

The [view definition](../../../lessons/salivary-practice/views.json) supplies each exact node selection and orthographic view in glTF metres to the Gallery and [Blender render](../../../lessons/salivary-practice/render.py). The [plate compositor](../../../lessons/salivary-practice/plates.py) adds numbers solely to the two answer plates. The six WebPs are imported by the lesson and total 90,560 bytes. The source is the CC BY-SA 4.0 [Z-Anatomy derivative](../../../sources/datasets/z-anatomy/salivary-region/License.txt), with the upstream BodyParts3D and contributor credits carried by that record.

From the repository root, use Blender 5.2.3 and Pillow 11.3.0 with a fresh output directory. `replay` is the path of a new scratch directory.

```sh
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  --python lessons/salivary-practice/render.py -- --out "$replay/shared-r01"
python3 lessons/salivary-practice/plates.py --renders "$replay/shared-r01" --out "$replay/plates"
```

The render also accepts `--edition z-native-scoped-r02`. Clean imports and matched renders of all four views from both editions gave identical pixel bounds. At 960 × 720, 154 to 271 pixels per view changed, with at most two levels of RGB difference and 11 levels of alpha difference on the silhouette. Every numbered leader endpoint ray-hit its intended named mesh in both editions. The same bundled fallback therefore serves both editions at this scale. Exact GLB identities are in the [shared r01 assessment](../../../reviews/teaching-assessments/2026-11-23-salivary-shared-source/campaign-assessments.json) and [r02 decision](../../../reviews/salivary_glands/2026-10-26-native-scoped-r02/decision.json).

## Local Gallery verification

Starting revision `fa6d599`. The focused Gallery build's HTML SHA-256 was `c55569ae56f70b3247e52bd85f36dd4463a2fd2130296caccac19ebdff9e3891`. Chrome exercised the questions, exact reference images, keyboard marker and answer reveal on both ordinary routes. The four rendered 3D views kept the jaw, floor and masseter relationships in their fixed frames. An injected 503 preserved the matching still and offered a retry that reopened 3D. The r02 source views, exact local r01 Library targets, Compare return and Chinese oral-spaces return all opened. A second hostname on the local preview exercised the public route branch and fetched both exact indexed r02 GLBs. The public Gallery was outside this local verification.
