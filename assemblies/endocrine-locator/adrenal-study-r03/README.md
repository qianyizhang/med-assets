# s1233 adrenal teaching study

Open the [teaching GLB](s1233-adrenals-teaching.glb). Use the amber glands to identify the left and right adrenals against their
ipsilateral kidneys. Select all five structures individually. The posterior
orthographic view clarifies laterality and the oblique view shows depth
relative to the kidneys and pancreas. With the camera looking from the back,
patient left is viewer left.

The derivative uses the [r02 s1233 abdomen export](../r02/README.md) as its
preservation reference. It keeps its case, names, anatomy IDs, source extras,
and coordinate frame in metres (+X left, +Y posterior, +Z superior in Blender).
The two secondary pancreas surface shells stay fixed. Four contextual and
target labels each have a single shell. The source grid has 1.5 mm isotropic
spacing. Colors indicate teaching roles. See the [source terms and credit
notice](../../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md) and
[original review](../../../reviews/endocrine-locator/r02/README.md).

## Replay

Replay the r02 owner first if the exact source GLB is missing. Run from the
repository root with Blender 5.2.3 and a fresh output path. On macOS obtain
command-specific approval before the first headless Blender command.

```sh
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P assemblies/endocrine-locator/adrenal-study-r03/build.py -- \
  --source .artifacts/body-systems-refinement-2026-11-19/endocrine/s1233-adrenals.glb \
  --output .artifacts/gallery-quality-2026-11-20/adrenal-replay
```

The recipe checks the source SHA-256, smooths each principal shell with a
bounded displacement, then reduces triangles by edge collapse. A gland-only
normal offset restores the volume of the two target shells. The offset
holds vertices within 0.25 mm of a directional bound and cannot exceed
0.375 mm anywhere. It rejects flipped faces and new nonadjacent-triangle
intersections from that offset. The two smaller pancreas shells retain
their original geometry and receive the same context material.

The clean import must retain selection identity, laterality, component
counts, Euler characteristics, and boundary and nonmanifold edge counts.
It must preserve the set of intersecting shell pairs and the primitive
counts. The sampled two-way distances must stay within one source voxel
with the 95th percentile within half a voxel. Secondary shells use a
3 μm sampled maximum. Directional extrema must remain within one voxel
and surface-area centroids within half a voxel. Target volume drift is
limited to 0.5%, with up to 13% allowed for context shells. The recipe
produces the editable BLEND, portable GLB, mesh receipt and matched render
receipt. Use `--geometry-only` for a replay without renders. A failed build
or a wrong source leaves no new result directory.

## Review

The [gallery review](../../../reviews/body-systems/2026-11-20-surface-quality/README.md) includes both angles and the per-part results. The
`geometry.json` receipt binds the pin, recipe, Blender version, exact exports,
component measurements and surface changes. The paired posters independently
import the exact source and derivative with a shared camera fit and lighting.
Grayscale render inspection is included in the local review. The evidence
covers the portable geometry and posters. Source masks, clinical accuracy,
interactive viewer performance and accessibility have separate acceptance
criteria.
