# Source identity and canonical applicability

The source records support project-authored Cardiac Atlas geometry. The original
[source README](../../../heart/Cardiac_Atlas/docs/README.md) describes analytic
shapes, hand-authored vessel paths and procedural materials, with no downloaded
anatomical asset or external texture required. Its anatomy references inform the
teaching organization; they are not imported meshes. The exact two input GLBs
contain no image textures.

The [workshop manifest](../../../body/anatomy-workshop-r1/manifest.json) marks
`heart_detailed` as `sourceKind: authored`, `sourceCase: null`, and a prior
independently authored Cardiac Atlas fitted pedagogically. This is distinct from
the collection's separately attributed segmented organs. The retained build
recipe imports the prior Cardiac Atlas full/cutaway exports for this asset.

The repository owner's import commits
[`b1a42b7`](https://github.com/qianyizhang/med-assets/commit/b1a42b7e744de0e7845cb467fb84605260ef9510)
and [`82bc1c6`](https://github.com/qianyizhang/med-assets/commit/82bc1c6bb32aae9da3392c995df212b7edb098fc)
already distributed the original animation, editable generator and static
collection. The [import manifest](../../../metadata/asset-manifest.json) preserves
their Library/Drive archive identities. Existing
[runtime attribution](../../runtime/2026-10-23-software-ci-heart-lymph/ATTRIBUTION.md)
also identifies the fitted animation as project-authored.

No unresolved third-party geometry provenance appears in these records. The
package has no separate public reuse license; this derivative grants none. That
absence is distinct from the owner's authorization to deliver their project work.
The draft scope is these two derivatives, the bounded recipe/checks and actual
own-rendered review images. It includes no new external anatomical asset, native
source upload, Site deployment or clinical claim.

## Three distinct identities

| Asset | Existing location | Bytes | SHA256 |
|---|---|---:|---|
| Static input | `body/anatomy-workshop-r1/meshes/heart_detailed.glb` | 9,056,304 | `83dd48731d0cc67e8aa61abbd7b03163fb01bcba78f501e9d2c939927aaecf6e` |
| Tested original animation | `heart/Cardiac_Atlas_Animated/Heart_Clinical_Animated.glb` | 8,180,224 | `6912d439271c3525230a90fe403d586000e6a66ab37f82bf0419604181e52263` |
| Fitted canonical animation | Site-relative `body/3d/assets/motion/heart_animated_clinical.glb` | 8,180,452 | `17b26d1459c0fbbbc71d051452c4074d1237683ffe02c1a8021d7ac83583857a` |

The canonical URL is recorded in
[`source-provenance.json`](../../runtime/2026-10-23-software-ci-heart-lymph/source-provenance.json).
It has **no identified tracked repository path**. `assets/heart.glb` in
`ci/glb-runtime-fixture.json` is the runtime harness's transient download
destination, not a retained repository asset.

The exact fitted bytes were absent from the available checkout/history and local
LFS store. The recorded Site host is outside this executor's configured HTTP
destinations; no request, denial, access change or alternate route was attempted.
On 2026-10-30 the connected GitHub read for
[run 39937314430](https://github.com/qianyizhang/med-assets/actions/runs/39937314430)
returned no artifacts. The workflow retains them for three days. The repository
retains derived receipts and images, not the original downloaded GLB.

## What can be verified with existing repository assets

[`compare_canonical_fixture.py`](../../../tests/heart_exterior/compare_canonical_fixture.py)
independently decodes the actual repository-source animation and compares it with
the retained exact-canonical fixture. All 228 track names/node indices, 247 mesh
and 251 primitive counts, and 912 scalar weights at 0, 0.2, 0.4 and 0.8 seconds
agree, with zero numerical error. The source has 248 nodes; the canonical receipt
records 249. See [the exact result](checks/canonical-fixture-compatibility.json).

```sh
python3 tests/heart_exterior/compare_canonical_fixture.py --source-repo . --output /tmp/heart-canonical-samples-new.json
```

This is recorded-sample compatibility, not proof of canonical mesh data, fitting
transforms, all intermediate samples, clean reimport or replacement applicability.
The byte/transform gap cannot be resolved from these retained samples alone.

**Verified scope:** exact static input to static derivative; exact original
repository animation to animated-source derivative, including all 25 authored
samples after clean reimport. **Unverified scope:** applying this repair to the
fitted canonical `heart_animated` artifact. No canonical replacement or Site
integration is included. The next bounded step is obtaining the exact 8,180,452
bytes through an already authorized accessible source, then running the same
membership, reimport, motion and matched-image checks against that identity.
