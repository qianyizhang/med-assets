# Locate the adrenals from behind

Open the [regional teaching GLB](s1233-adrenals-regional.glb) and find each gland above and medial to its ipsilateral kidney. Look down 30° from behind and 20° toward patient left for the five-part overview. The straight posterior view confirms laterality. Turn the isolated right gland to its anterolateral face to see the broad surface roll into the inferior margin. [Matched views and scored review](../../../reviews/endocrine-locator/adrenal-study-r05/README.md)

The five selectable objects retain the s1233 frame, names, anatomy IDs, laterality and source metadata. Blender uses metres with +X left, +Y posterior and +Z superior. The scan-derived shapes and context stay at one scale. The capsule palette, small clear coat and gradual change in roughness illustrate the exterior. The color follows a smooth measure of local modeled bulk. It carries no histological or perfusion information.

## Source and interpretation

The two glands are reconstructed from the same-case [r02 label-derived surfaces](../r02/README.md) on a 0.6 mm work grid. The acquisition label spacing was 1.5 mm. The kidneys and all three pancreatic shells retain the [r04 exterior geometry](../adrenal-study-r04/README.md). Credit Jakob Wasserthal, TotalSegmentator contributors and University Hospital Basel under the [s1233 source terms](../../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md).

The field smooths the main gland face more strongly across axial steps and narrows its kernel at the two ends. A finer local field preserves the right inferior cleft present in consecutive traced sections. The lowest traced slices guide a small upward turn at the outside of each terminal plate. That rounding and the one closed tunnel per gland are editorial. Three earlier pancreatic tunnel closures remain. The left distal tip, right superior apex, right inferior plate and cleft can be checked in the [case sections](../../../reviews/endocrine-locator/adrenal-study-r05/case-sections.png). For an external comparison of the major planes and finish, see Mikael Häggström’s [gross specimen photograph](https://commons.wikimedia.org/wiki/File:Adrenal_glands.jpg).

## Replay

Use Blender 5.2.3 and Python 3.12 from the repository root. Hydrate the r04 GLB and restore the SHA-pinned r02 GLB from the [r02 recipe](../r02/README.md) or the [teaching backup](../../../sites/body-systems-survey/README.md#restore-the-media). Use fresh output directories. On this Mac obtain command-specific approval for the first headless Blender invocation.

```sh
python3.12 -m venv .artifacts/adrenal-r05-python
.artifacts/adrenal-r05-python/bin/python -m pip install \
  -r assemblies/endocrine-locator/adrenal-study-r05/requirements.txt

blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P assemblies/endocrine-locator/adrenal-study-r05/build.py -- \
  --case .artifacts/body-systems-refinement-2026-11-19/endocrine/s1233-adrenals.glb \
  --science-python .artifacts/adrenal-r05-python/bin/python \
  --output .artifacts/gallery-surface-r05/adrenal-replay
```

The result contains the editable BLEND, portable GLB, reduced comparison GLB, geometry measurements and matched 800 × 640 renders from clean imports. Use `--geometry-only` to omit the renders. The lighter trial keeps five objects, all seven shells and the same teaching materials. Wrong case identity, a failed field process or a geometry-check exception leaves the destination unpublished. [Geometry and nine-plane measurements](../../../reviews/endocrine-locator/adrenal-study-r05/geometry.json) · [Bound views](../../../reviews/endocrine-locator/adrenal-study-r05/renders.json)

For the exact review figures, download Häggström’s CC0 [original photograph](https://upload.wikimedia.org/wikipedia/commons/1/15/Adrenal_glands.jpg) to a local scratch path. The plate recipe checks its SHA-256 and all supplied render identities before composing any figure. Run on the replay package or the retained review directory. Figure typography uses Georgia and Arial on macOS with system fallbacks elsewhere.

```sh
.artifacts/adrenal-r05-python/bin/python assemblies/endocrine-locator/adrenal-study-r05/plates.py \
  --review .artifacts/gallery-surface-r05/adrenal-replay \
  --specimen .artifacts/gallery-surface-r05/adrenal-work/haggstrom-reference.jpg \
  --output .artifacts/gallery-surface-r05/adrenal-replay-figures
```
