# Thyroid illustrative exterior / 甲状腺示意外表面

Separate derivative for [issue #148](https://github.com/qianyizhang/med-assets/issues/148):
reduce distracting repeated surface ridges while retaining this sample's unequal
lobes, deep recess and narrow bridge. The original sample export is unchanged.

- [Updated GLB](../exports/illustrative-exterior-r01/thyroid-illustrative-exterior.glb)
- [Matched views and review](../../../reviews/thyroid_ct_s0189/2026-10-29-illustrative-exterior-r01/README.md)
- [Attribution and modifications](ATTRIBUTION.md)

The source is the retained TotalSegmentator s0189 clinical-source exterior, not a
healthy or normative atlas. This treatment is illustrative, not improved
segmentation or measured tissue. No internal structures are added.

## Treatment and scale

The hypothesis was that localized Laplacian smoothing would reduce repeated
scan-resolution corrugation without erasing broad source depressions. Blender
4.3.2's established Laplacian Smooth modifier applies eight iterations at strength
0.35, with volume preservation and normalized weights. The sampled negative-Y
ridge-facing surface receives more influence; the opposite face and central
bridge receive less. These are editorial source-coordinate selections, not
anatomical orientation or tissue classification.

The retained source used a published 1.5 mm label-spacing convention. At this
educational viewing scale, the approximately 0.61 mm maximum / 0.20 mm RMS vertex
movement is a presentation adjustment; it is not an anatomical accuracy bound.
Broad depressions and asymmetry remain. Metres are inherited from the previous
affine conversion; the original unit header was unspecified. No recentering,
registration, new topology or sample normalization is exported.

## Reproduce from a hydrated checkout

Requires Git LFS and Blender 4.3.2; no raw dataset download or Python dependency
installation. From the repository root:

```sh
git lfs install --local
git lfs pull --include='models/thyroid_ct_s0189/exports/source-candidate-02/thyroid_ct_s0189_source_frame.glb'
blender --background --factory-startup --python-exit-code 1 --python models/thyroid_ct_s0189/illustrative-exterior-r01/build.py -- --root . --out /tmp/thyroid-exterior-replay
```

Use a new output directory. The recipe rejects a wrong source identity and an
existing output directory. A replay produced byte-identical GLB output; image
pixels may vary across render hardware. The recipe does not reproduce the earlier
raw-label extraction, whose inputs remain external.

## Limits

The exact same-sample trachea is absent from the retained GLB and local context
files. No replacement anatomy was registered. Tracheal clearance and the full
relationship criterion of #148 remain unverified. Offline Cycles views and export
integrity do not establish specialist, clinical or intended-consumer/browser
runtime approval. No gallery or Site integration is included.
