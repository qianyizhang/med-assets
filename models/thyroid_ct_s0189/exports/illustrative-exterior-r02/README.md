# s0189 thyroid illustrative exterior r02

The lower rear band of the retained s0189 teaching exterior has locally reduced corrugation. Use the medial bridge and unequal lobes to recognize the same specimen hallmarks. The local Anatomy Gallery recommends r02 for the bridge task. The [r01 export](../illustrative-exterior-r01/thyroid-illustrative-exterior.glb) remains available in Library history and through its existing published delivery.

| Export | Bytes | SHA-256 |
| --- | ---: | --- |
| `thyroid-illustrative-exterior.glb` | 152,288 | `6bc4f4da8bc91a058da8f9c78fca8618e3ace90580cac499adf48981bc18608e` |

The support mask selects rear-facing vertices of the mid-to-lower band and pins the transverse central region within 9 mm of the midline. The r01 material, indices and coordinate frame are carried through. The final export moves 984 positions up to 0.381 mm relative to r01. Against the unretouched retained s0189 surface, the independently reimported maximum movement is 0.609 mm. Signed volume differs from that retained surface by −0.29%. The original 1.5 mm convention informed the presentation cap. Neither the cap nor the comparison measures tissue accuracy.

The [TAQ-011 comparison and evidence](../../../../reviews/teaching-assessments/refinement-form/README.md) record the matched views and independent reimport. The [r02 assessment](../../../../reviews/teaching-assessments/refinement-form/campaign-assessments.json) binds the unchanged bridge task to this export and the actual teaching plate. The [r01 owner record](../../illustrative-exterior-r01/README.md) explains the earlier treatment and the limits of the retained label surface. This reconstruction shows a case-specific exterior with no registered tracheal context, verified internal anatomy, or verified clinical use.

Credit Jakob Wasserthal and TotalSegmentator contributors, University Hospital Basel, [TotalSegmentator v2.0.1](https://zenodo.org/records/10047292). Retain the [source attribution](../../illustrative-exterior-r01/ATTRIBUTION.md) and [CC BY 4.0 terms](../../illustrative-exterior-r01/CC-BY-4.0.txt) when reusing the model or views. The additional r02 modification is localized fairing of the rear-band presentation.

## Rebuild

Use Python 3.12 and NumPy 2.2.6 with the two pinned hydrated baselines. The recipe checks the protected surface and exact reviewed GLB identity.

```sh
python3.12 models/thyroid_ct_s0189/recipes/illustrative-exterior-r02/build.py .artifacts/rebuild-thyroid-r02
```
