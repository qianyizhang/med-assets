# s1233 illustrative adrenal exteriors

Find the left and right adrenal glands relative to the kidneys and pancreas.
Use the posterior view for laterality and the isolated gland view to compare
outlines. The amber glands are the teaching targets. The kidneys and pancreas
provide context in the original s1233 coordinate frame.

This is an interpreted teaching exterior. The recipe fills one unverified
segmentation tunnel in each adrenal and three in the principal pancreas
shell. It retains both secondary pancreas shells and the large open
indentation in the left renal hilum region. The kidney shells are genus zero
in both versions. The indentation has a back wall in the source mesh and
is distinct from a through-tunnel. The earlier [r03 geometry-preserving
teaching derivative](../adrenal-study-r03/README.md) and [r02 source
reference](../r02/README.md) preserve the original tunnels.

Normal adrenal outlines vary across people. CT studies report an inverted
Y and variants with shortened or absent limbs. A normal-shape reference
informs review of the curved and compact gland silhouettes here. The source
images would be needed to establish the anatomy of this case. [Moreau et al.,
normal adrenal CT study](https://pubmed.ncbi.nlm.nih.gov/7441594/)

The GLB retains all five `anatomy_id` values, source extras and laterality.
Each mesh also carries `derivation`, `parent_glb_sha256` and
`inferred_tunnel_closures` in portable extras. Coordinates are Blender
metres with +X left, +Y posterior and +Z superior. The
[s1233 source terms and credit notice](../../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md)
apply.

## Replay and review

Hydrate the pinned r03 GLB with Git LFS. Install the numeric dependencies
in a Python 3.12 environment and run Blender 5.2.3 from the repository root.
On macOS get command-specific approval before the first headless Blender
invocation.

```sh
python3.12 -m venv .artifacts/adrenal-r04-python
.artifacts/adrenal-r04-python/bin/python -m pip install \
  -r assemblies/endocrine-locator/adrenal-study-r04/requirements.txt

blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P assemblies/endocrine-locator/adrenal-study-r04/build.py -- \
  --science-python .artifacts/adrenal-r04-python/bin/python \
  --output .artifacts/gallery-surface-r04/adrenal-replay
```

The recipe converts each principal r03 shell into a solid on a 0.6 mm work
grid. It fills sealed regions and smooths the signed field with a Gaussian
of 1.55 mm for glands, 1.92 mm for pancreas and 2.70 mm for kidneys. The
isovalue compensates for erosion by matching the sampled solid volume, with
a 0.375 mm cap on the shift. Gaussian smoothing and cavity fill were
sufficient for the pinned input. The recipe searches from radius zero
upwards for the smallest additional morphological closing radius that
produces a single exterior. It then triangulates and reduces the exterior.
Secondary pancreas shells bypass reconstruction.

The replay runs in a temporary directory and publishes the local result
directory after export, clean import, geometry checks and renders succeed.
Use `--geometry-only` to omit renders. The checks require closed manifold
shells, the recorded decrease in genus, the original number of components
and primitives, unchanged laterality and selection metadata, preservation of
satellite surfaces, and no new surface intersections. The measured geometry
changes describe this derivative relative to r03. There is no clinical
acceptance threshold.

The local result is in `.artifacts/gallery-surface-r04/adrenal/`.
`geometry.json` binds the geometry, recipe and metrics.
`renders/renders.json` binds matched whole assembly, isolated adrenal and
neutral material comparisons from independent clean imports. The same
camera and lighting apply to each pair. Use the neutral pairs to separate
shape differences from the effect of the satin context and warmer gland
materials.


The [durable review](../../../reviews/endocrine-locator/adrenal-study-r04/README.md)
records the paired views, deviations and limitations. To replay the exact
mesh sections through the two original gland openings, run the diagnostic
against the final portable export.

```sh
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P assemblies/endocrine-locator/adrenal-study-r04/section.py -- \
  --updated assemblies/endocrine-locator/adrenal-study-r04/s1233-adrenals-illustrative.glb \
  --output .artifacts/gallery-surface-r04/adrenal/tunnel-sections.json
```

Both sections verify a straight line through the r03 opening, with no
triangle hit in either direction. The same point is inside the r04 shell.
The left witness lies in the upper part of the segmented silhouette, about
12 mm below its superior extent. The right witness lies in an inferior fold,
about 3 mm above the inferior extent. These locating measurements describe
the meshes. The openings are smaller than the original 1.5 mm grid spacing
in the measured planes.
