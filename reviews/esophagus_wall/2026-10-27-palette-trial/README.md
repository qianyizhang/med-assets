# Esophageal wall palette trial — WIP disposition

[Issue 102](https://github.com/qianyizhang/med-assets/issues/102). **Keep as a local teaching-color candidate; do not replace the canonical GLB or sheets yet.** The candidate makes the inner circular and outer longitudinal muscle bands easier to tell apart in matched oblique and transverse views. The blue and slate layers look like deliberate color codes, not histologic tissue. This is a visual readability gain only.

The independently authored [baseline cutaway](../../../models/esophagus_wall/exports/authored-cutaway-r01/README.md) remains the teaching supplement. Its five meshes represent four tunics, with muscularis externa split into two compartments. Thicknesses, folds, wedge, length, and colors are illustrative. The source's anatomy, clinical, and browser-runtime limits still apply.

## Identity and technical check

| Local GLB | SHA-256 | Bytes |
| --- | --- | ---: |
| Canonical baseline | `e4f51a86040ef115776fe06a33443982f7b63243332681e53dadaa77f81c05f5` | 201,328 |
| Palette candidate, local only | `c7ec6420edbd62f94b85610e1c51f6fa4dd31dc008248c19a9731ac5cef0c311` | 201,344 |

The trial verifier compared parsed GLB JSON after restoring the five `baseColorFactor` fields: everything else matched. Every non-JSON chunk, including mesh data, was byte-identical (binary chunk SHA-256 `53fbd63b3632950d18da9edbf6293489cab43a2aa529eac7113b809921680701`). Both have five meshes and 7,700 triangles; node transforms, names, layer order, alpha, metallic and roughness values are unchanged. Fresh Blender 4.3.2 reimports reported identical cameras and geometry diagnostics. The verifier rejected a changed geometry byte and a changed roughness field. These checks establish a material-only derivative, not new anatomical validity.

The portable [palette replay](../../../tests/esophagus_wall/palette_trial.py) requires the exact hydrated baseline GLB and refuses an existing output directory. It verifies the reviewed candidate hash and writes **local** baseline/candidate files and a receipt:

```sh
python3 tests/esophagus_wall/palette_trial.py \
  --input models/esophagus_wall/exports/authored-cutaway-r01/esophagus-wall-cutaway-r01.glb \
  --params tests/esophagus_wall/parameters.json \
  --output /tmp/esophagus-palette-NEW
```

No generated GLB or image is part of this proposal. The canonical generator and original asset are unchanged.

## Visual review and bilingual legend

The local trial rendered both GLBs with the same three cameras, lights, exposure, Cycles CPU settings, and 1000 × 1100 resolution. The baseline oblique render reproduced the canonical oblique pixels exactly. I inspected the original-size transverse images, matched oblique and grayscale comparisons, and freshly composed English and Chinese teaching sheets from the candidate's actual renders. Their numbered anchors land in the same five compartments, and both language versions remain legible at the reviewed size. The sheets are local review evidence, not proposed replacement media.

| Inside → outside | English legend | 中文图例 | Candidate sRGB code |
| ---: | --- | --- | --- |
| 1 | Composite mucosa | 黏膜（合并表示） | `#A93664` |
| 2 | Submucosa | 黏膜下层 | `#F2D38C` |
| 3 | Inner circular muscle | 内环行肌层 | `#276D8A` |
| 4 | Outer longitudinal muscle | 外纵行肌层 | `#D1905A` |
| 5 | Adventitia | 外膜 | `#596878` |

The closest adjacent median display-luma gap in eroded transverse regions rose from 5.45 to 27.62 on an 8-bit scale. This describes these pixels; it is not an accessibility or anatomy threshold. In grayscale, neighboring bands are easier to follow, though the thin adventitia still relies on its numbered leader at sheet size. The stronger false-color treatment costs naturalistic appearance, so any eventual viewer should label it as an illustrative compartment palette.

Local retained evidence: `oblique-comparison.png` SHA-256 `470c29af2cde1dc0476b7ccff778014762f34d6501468b29d3a74719a12f0da5`; `cross-section-comparison.png` `9c72140ad567105298347c4bdb58365231b1493c7475be54dfcafb5f78c2561b`; grayscale `72368e51985346e760beafb9c60983215b5617c24a6fe379e02c99c66bf4e321`. The bilingual sheets and comparison images are retained in the local trial workspace; remote image delivery has not succeeded, so independent hosted pixel review is still pending.

Fresh candidate-pixel bilingual sheet SHA-256 values: English `88de3df3f84a07edce69badfd04743313c4f3ae21351e9a2fecf7a035a8a3481`; Chinese `6379e27ac0b0622ab00da323088bfae37f7d29e0b1ad45b7cada2a499e96c63c`. They use the existing label-sheet scripts unchanged and are local review drafts.

## Gates and next decision

| Gate | Current result |
| --- | --- |
| Technical | Passed for the exact material-only diff and clean Blender reimport; geometry unchanged. |
| Visual usefulness | Local reviewer favors keeping the candidate for teaching-layer discrimination, with the false-color limitation. Hosted reviewer inspection remains pending. |
| Anatomy / clinical | No new acceptance; existing illustrative geometry and omissions remain. |
| Target viewer / publication | Unrun; no canonical model, media, Site, or transport change. |

Promote only after a reviewer can inspect the exact matched images and the target viewer verifies the candidate's exported colors and bilingual legend. If the false-color treatment conflicts with the broader collection or viewer, revise or reject this candidate without changing the baseline.
