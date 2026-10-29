# Trachea r06: an authored airway teaching shell

The existing r05 model is a closed display cast. This separate derivative exposes
three editorial openings and provides a cutaway of the connected Y-shaped airway.
The original r05 file, source attribution and gallery selection are unchanged.
Related issue: [#133](https://github.com/qianyizhang/med-assets/issues/133).

**Recipe delivery only.** The two generated GLBs are local and unpublished. The
[review](../../../../reviews/trachea/2026-10-29-open-airway-r06/README.md) contains
public geometry projections and exact identities of the privately reviewed renders.
The source cast is preserved; the inferred wall is a separate authored teaching
derivative. This is not recovered specimen wall, normal lumen caliber or histology.

## Reproduce

Requires Blender **4.3.2** (including its NumPy), Python 3.11+ for the optional
identity helper, and the existing **hydrated** r05 GLB. No packages are downloaded
by these scripts. An LFS pointer is insufficient. The input is already published
in the repository, but this task used existing local bytes; it did **not** test a
fresh checkout or remote hydration. Code and declared dependencies alone cannot
rebuild the model without that input.

Run from the repository root with a new output directory:

```sh
blender --background --factory-startup --python-exit-code 1 \
  --python models/trachea/exports/open-airway-r06/build.py -- \
  --baseline models/trachea/exports/host-conforming-cbands-r05/trachea_host_conforming_illustration.glb \
  --out /tmp/trachea-r06-new
```

The recipe rejects a wrong input hash and an existing output directory. It writes
`trachea-open.glb`, `trachea-cutaway.glb` and `build-record.json`. A separate local
replay reproduced both final V7 files byte for byte.

| File | Bytes | SHA256 |
|---|---:|---|
| r05 input | 707,132 | `af54ca254e47910ded53c6b690b475ab17236ba47d314fbdd5357dc67849bf4d` |
| `trachea-open.glb` | 962,440 | `eb3ce52962aacc4d109a9840685aa172ca1d97bfc835367f4e36fd32de6b6cbb` |
| `trachea-cutaway.glb` | 1,564,740 | `42b25a9e3de950db1a083da3802d4bb982c9084c425f768824c8973dc08be283` |

## Method and limits

The recipe rejoins export seams within 1e-8 m, sections the existing cast at three
explicit planes, and offsets an inner surface along interpolated source normals.
The nominal **0.6 mm** shell is an illustration setting, not measured tissue.
Offsets are constrained to the editorial cuts and locally reduced at one open-shell
vertex and four cutaway vertices to avoid crossing the cuts. A fitted depth field
opens the anterior side for the cutaway; it is not an anatomical boundary.

The existing 18 illustrative C-bands are retained and sectioned. Their caps are set
back 0.05 mm from the terminal shell cuts to remove coplanar rim interference.
Material names identify the authored inner shell and editorial cut faces. Coarse
source contours, illustrative bands and section positions remain limitations.

[OpenStax A&P 2e §22.1](https://openstax.org/books/anatomy-and-physiology-2e/pages/22-1-organs-and-structures-of-the-respiratory-system)
supports airway continuity, posterior wall closure and division into the primary
bronchi. It does not validate this specimen envelope or the chosen dimensions.
No reference artwork was copied. See [attribution](ATTRIBUTION.md).

Use the [focused check/render commands](../../../../tests/trachea_open_airway/README.md).
Technical checks, independent actual-pixel review, anatomical reference screening,
supported runtime and publication are separate. Browser runtime is unverified;
there is no specialist or clinical approval, gallery promotion or accepted-count change.
