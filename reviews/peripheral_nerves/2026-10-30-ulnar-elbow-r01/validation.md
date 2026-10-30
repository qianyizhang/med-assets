# Local validation receipt

Completed in the Linux cloud executor on **2026-10-30**; Blender **4.3.2**,
Git LFS **3.6.1**. This receipt covers the separate regional supplement.
The exact payload set is [payloads.json](payloads.json): 20 paths, 19 unique
objects, **8,766,724 unique bytes**. It excludes the historical scaffold and full
external source archive.

| Check | Result and boundary |
|---|---|
| Pinned source archive/member | Size and SHA-256 match the [provenance record](../../../sources/datasets/z-anatomy/ulnar-elbow/provenance.json) |
| Source extraction replay | Passed at 03:19 UTC: Blender replay produced exact v1 GLB `206915ffa0b6b625ca17e32f35b893e1d1a103f25bce59f41e02d657ab9e7fd5` |
| `test_build.py` | All **6 scoped tests passed**: deterministic v2 replay, input/output guards, geometry and transform preservation, identity and limits |
| `verify_package.py` | Passed: **2 GLBs, 8 matched raw images, 3 composites, 6 bound locators**; matched camera/light/scale/settings and exact comparison-panel pixels |
| Native geometry screen | Four source/reimport vertex clouds checked bidirectionally; maximum difference below `1.23e-7` native units; numerical tolerance `1e-6`, not anatomical tolerance |
| Independent pixels | [Accepted with limitations at 03:21:23 UTC](independent-v2-review.md); separate from technical checks |
| `python3 tools/verify.py offline` | Passed at 03:25 UTC: **189 tests; 26 transport manifests; 25 foundation records; 591 import references (3 documented updates); 710 LFS pointer identities** |
| Changed-file whitespace | Owned files passed; the two byte-exact upstream license/README copies retain provider whitespace, with their recorded hashes verified |

The broader offline suite does not include these six scoped tests. It does not
hash hydrated media, validate this package's anatomy, fetch remote payloads or
run a viewer. Package checks are invoked separately as described in the
[recipe](../../../tests/peripheral_nerves/ulnar-elbow-r01/README.md).

V2 preserves the v1 binary GLB chunk (SHA-256
`e15913d11d8a080684220192fefce992b8ee43e02955b2f315bc0caa731f5430`),
mesh definitions and transforms. Exact source retention does not resolve the
source's coarse form or retained humerus boundary/nonmanifold edges. The BVH
screen's zero nerve–bone overlap candidates is not a formal clearance or
self-intersection proof.

Anatomy remains **reference-screened**, clinical approval absent and runtime
**unverified**. Whole-context grayscale nerve contrast is limited; the reviewed
color/detail views carry the teaching relationship. Publication and fresh remote
delivery are recorded separately. No issue-count promotion or full-body
replacement is claimed.
