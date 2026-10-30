# Independent v2 review — scoped pass

**Verdict: pass with limitations for the private source-defined opaque-exterior presentation derivatives.** The concrete v1 metadata findings are corrected. Actual v2 images preserve the reviewed v1 result: exposed internal chord/leaflet participation is removed according to the original native visibility rule, while exterior contours, coronary routes, great vessels and source gaps remain. No further visual or metadata defect was found in this bounded review.

## Exact reviewed outputs

| Derivative | SHA256 |
|---|---|
| `../../../heart/exterior-presentation-r01/exports/static-opaque-exterior.glb` | `595380d0aff153db4494fc5f9e8ffba062d0732c2bf0886242ebe1a188d3806f` |
| `../../../heart/exterior-presentation-r01/exports/animated-source-opaque-exterior.glb` | `aec9c13d3b9a0fa919bdc362ed17c582f895f77fc44f5e29cd184cea57599e0f` |

I decoded both actual GLBs and independently recomputed these hashes.

## Actual visual review and binding

Inspected actual v2 images:

- Static: `images/updated-static-whole-front.png`, `seam-front.png`, `seam-neutral.png`.
- Local animated-source at t0: `images/updated-animated-source-whole-front.png`, `seam-front.png`.

Independently verified each image hash against its binding, its binding to the exact v2 artifact, and the original/candidate camera position, rotation, target, orthographic scale, lights and bounds. Independently decoded the five v1/v2 image pairs: all pixels are exactly identical; PNG file bytes differ because capture-date/render-time metadata differ. The additional v1 static oblique view remains valid evidence because the independent whole-document/BIN comparison confirms that only three scene-description fields changed between v1 and v2.

The opaque exterior no longer displays the pale RV chord fan or triangular tricuspid leaflet seen in the original export. The remaining space below the crossing tube is visible and unchanged; it is not concealed by a new surface. Source schematic forms and color conventions remain. This is useful presentation correction, not geometric repair of the RV inlet apparatus.

## V1 findings resolved

Both v2 files change only `animation_model`, `animation_delivery` and `pericardial_layers` from their v1 values. All other JSON and the entire BIN payload are unchanged.

- The static file now identifies itself as an end-diastolic snapshot without an animation clip and not the editable native source. Its actual animation count is zero.
- The animated file describes only retained exterior morphs and explicitly excludes valve/chord participation. It identifies the portable 0.8-second exterior clip separately from the unchanged editable original/internal assets.
- Both files explicitly state that the removable parietal envelope and internal valve/support nodes are absent from the exterior scene. Neither implies that a material/cutaway selector is available.

These statements match the actual 124 participating mesh nodes and source-defined omissions. No geometry change was needed to address the metadata findings.

## Technical evidence reviewed

Read the differential-verification and actual Blender reimport-check implementations, the 15-check replay/failure report, and the exact v2 reimport receipts. The static receipt compares all 124 retained exterior objects at rest. The animated receipt compares all 124 objects at 25 authored samples, with exact original/candidate world-coordinate hash equality; all four chamber walls move and the endpoint returns exactly. I independently checked receipt artifact bindings, frame equality, 25-sample count, nonzero wall motion and endpoint equality. These are sampled source-motion preservation checks, not physiological motion or browser-runtime certification. The builder's 15 regression tests were inspected as recorded results; I did not represent them as independently rerun.

My additional independent metadata/image/binding checks are retained in `checks/independent-v2-checks.json`.

## Remaining boundaries

- Original/native/full/cutaway assets and all prior diagnostic/review evidence remain the references; the internal RV inlet/valve/papillary/chord geometry is not repaired or newly approved.
- The animated derivative uses exact local source `6912d439271c3525230a90fe403d586000e6a66ab37f82bf0419604181e52263`. It does not update or certify the absent fitted canonical `17b26d1459c0fbbbc71d051452c4074d1237683ffe02c1a8021d7ac83583857a`.
- The review provides no anatomy/clinical, continuous-time motion, browser-runtime, performance or publication approval. No publication was performed by the reviewer. Issue #150 remains broader than this presentation slice.

Portable copy: evidence paths relocated; the original reviewer note remains in the private worker bundle.

## Follow-up provenance and applicability review

Independent source review found consistent project-authored provenance in the
analytic generator, heart-specific manifest entry and prior owner import records.
Both exact inputs contain no image textures or external image/buffer URIs. The
absence of a separate public reuse license does not establish uncertain imported
ownership or block owner-authorized project delivery; no license grant is added.

The reviewer independently reran the retained canonical-fixture comparison:
228 names/node indices and 912 scalar weights match exactly. The source's 248
nodes versus the canonical record's 249 remain distinct. The scoped v2 visual
pass is unchanged; exact fitted-canonical replacement remains unverified.
