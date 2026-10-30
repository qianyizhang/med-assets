# Native cuff-muscle localization — bounded static review

![Six selected native surfaces with whole-subset and close views](v2/teaching.png)

The [accepted shoulder baseline](../2026-10-24-shoulder-bounded-migration/display/f9b8fb7db5fe35ef8e09d6f4e093af6852feaea15ddf2d6268ced5d87fafdcc2.webp)
and its detail were inspected before source work. They intentionally omit cuff
muscles. This new study adds anterior/posterior muscle localization against scapula
and humerus; it does not replace the baseline or diagnose a fault in that study.
These are different selections and cameras, not a registered Original / Updated pair.

- **Model:** one [GLB and canonical inventory](../../../models/joints/exports/z-rotator-cuff-r01/README.md),
  703,536 bytes / six surfaces / 38,678 triangles. Hash
  `edf5c2fc5322adc1c75703143b3fba5a2be3ecd87d5559bce1441c1977a4eb30`.
- **Source preflight:** exact pinned ZIP/member verified; six actual `.r` muscle/bone
  meshes and four native views independently inspected. No attachment-marker tissue.
- **Iteration:** [V1](v1/teaching.png) had a crowded S/4 legend. V2 shortens only the
  S caption; model, anatomy pixels, camera, lights and labels' surface targets stay
  unchanged. The unique failed V1 sheet is retained; duplicate model/captures are not.
- **Review:** [independent findings](independent-review.md). Color is preferred:
  [grayscale](v2/grayscale.png) is a diagnostic with weaker tissue contrast.
- **Limits:** localization only. Source topology warnings and missing structures
  remain; no attachment, tendon-continuity, action, clinical, motion or runtime pass.

## Source / Export and checks

![Matched native source and clean GLB reimport](v2/source-export.png)

This is **Source / Export**, with matched native cameras and display settings.
[checks.json](checks.json) contains exhaustive coordinate/triangle comparisons and
seven visible ray-hit label targets in both source and export. All 38,678 triangles
match as position-bound multisets; maximum world-coordinate error is
`1.2383438274810032e-7` native units, below the `5e-7` float32 accounting tolerance.
That tolerance is not an anatomical accuracy estimate. Reimport merges 25 duplicate
scapula vertices while preserving triangle surfaces and multiplicity.

Four matched raw source/export view pairs are retained and consumed by
[composition.json](v2/composition.json). Mean absolute RGB differences are
0.000018–0.000170 on a 0–255 scale; maximum individual channel difference is 14.
No visible shape/relationship difference was found. Different overview/detail
targets and scale are explicit in the shared recipe; each Source / Export pair matches.

Passed locally: source hash gate, clean import, byte-identical second GLB build,
actual payload/image hashes, five scoped failure tests and **210 aggregate offline
tests** (26 transport manifests, 25 historical records, 591 import references,
773 LFS pointers). Actual Blender wrong-source and existing-output refusals passed.
The reviewer's missing-label guard finding is fixed and covered by empty, omitted
and duplicate presentation-label cases. Existing shoulder and unrelated packages
are unchanged. All 13 new LFS payloads (7,495,712 bytes) passed fresh GitHub size/hash
readback into an empty store after branch upload. No hosted CI or browser-runtime
run is claimed by this local record.

Publication is not complete: automatic approval review denied the new public issue
because it did not recognize trusted authorization for that repository/publication.
No issue was created or retried, and #150 was not edited. The isolated branch is
uploaded; the concise issue/PR briefs are retained for the coordinator. No merge or
Site change. Exact tested implementation is `304a1594d5f8bae958f104f3f6e378236100cad6`;
this follow-up records delivery only and reuses those unchanged checks and artifacts.

## Replay

Blender 4.3.2, Python 3.11+, Pillow 12.3.0 and Noto Sans CJK Regular are used.
Obtain the exact `Startup.blend` using the inventory's pinned archive route, verify
both hashes, and extract only that member. Do not run source scripts or add-ons.
Output directories must be new.

```sh
blender -b --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python tests/rotator_cuff/replay.py -- --source /path/Startup.blend --out /tmp/cuff-new
python3 tests/rotator_cuff/compose.py --run /tmp/cuff-new --out /tmp/cuff-presentation \
  --previous-teaching reviews/joints/2026-10-30-rotator-cuff-r01/v1/teaching.png
python3 tests/rotator_cuff/verify.py
python3 tests/test_rotator_cuff.py
python3 tools/verify.py offline
```

Use `--no-render` for source/export geometry replay, not visual approval.
`compose.py --version 1` reconstructs the failed V1 caption. Native renderer uses
Cycles CPU, 64 samples, no denoising, 900×900 pixels, AgX, exposure 0, gamma 1.
Only labels and layout are composed; no anatomy pixels are edited.

Resolved preparation failures: factory-empty scenes need an explicit World;
this Blender build lacks OpenImageDenoise, so denoising is disabled; Blender's
library load mutates its assigned name list, so the recipe passes a copy. The first
posterior S pick hit infraspinatus and was rejected; the retained pick hits scapula.
These were tool/pick failures, not anatomical repairs. No failed anatomy candidate
was hidden or replaced. Reused source license files avoid duplicate attribution copies.
