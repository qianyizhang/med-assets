# Pharynx/larynx layer inspection

This viewer patch exposes the five existing cartilage components beneath the
muscles in `pharynx_larynx__r03`. It adds cartilage, muscles-plus-cartilage and
reset controls to the existing isolated viewer, plus an explicit “Fit visible
parts” camera action. It creates no model or new
anatomy and does not replace the canonical review dataset.

The patch targets gallery v40 source commit
`11d91eea72408d8995ad9f60cd1c45b6341bd240`; `apply.py` requires the exact
`candidate.js` SHA-256
`9214093398033ab75beeec8c273d1f85a28408ee6096f3fe0bb91723ecc6f80b`.
Copy the authorized viewer source into an independent local directory first:

```sh
python3 gallery/pharynx_larynx/visibility-r01/apply.py /path/to/private/dist/review
```

Only `candidate.js` and the two new `pharynx-inspection` files are written. The
patcher refuses changed baseline bytes, existing output modules and repeated
application. Source data, models, existing camera logic and other candidates
are preserved. Keep the original source copy for rollback. This command does
not fetch source, commit, push, publish or alter a shared checkout.

The visibility controller requires the exact candidate, asset ID, GLB hash,
33 unique source mesh IDs and both required neutral laterality overrides.
Failures leave visibility unchanged. Cartilage shows 5 parts; muscles plus
cartilage shows 30, hiding two ligaments and the pharyngeal raphe. Reset
restores captured original visibility, including any initially hidden parts.
The bilingual panel states what was hidden and lists source-bound labels.
Layer switching changes only visibility; it retains the camera and native
geometry, materials, transforms and raw source names.
“Fit visible parts” frames the effectively visible meshes with a margin while
preserving the viewing direction. It adjusts only the perspective camera and
orbit target. Reset followed by fit restores full-assembly framing. Existing
front/back/left and Fit camera actions retain their v40 behavior.

Source: [unchanged r03 GLB](../../../models/pharynx_larynx/exports/r03/pharynx_larynx.glb),
SHA-256 `d691a60f12d448b9b36d362270429c672c01c7fae0f10a8789ef188dd4c08530`,
5,050,088 bytes. [BodyParts3D attribution](../../../models/pharynx_larynx/exports/r03/ATTRIBUTION.md)
and the [pinned source map](../../../sources/datasets/bp3d-4.0-head-studies/external-source-map.json)
remain applicable. Epiglottic openings and disputed FJ2742/FJ2754 labels are
preserved. This is a dissected exterior study; it does not establish a continuous
mucosal airway, voice or swallowing mechanics, or clinical validity.

## Verification

The five patcher tests run in ordinary offline verification. The scoped Node
tests additionally require the hydrated existing GLB and isolated pinned test
dependencies; Three r180 is a test dependency, not a claim about live vendor bytes.

```sh
npm install --prefix /tmp/pharynx-deps --cache /tmp/pharynx-npm-cache --no-audit --no-fund --save-exact three@0.180.0 jsdom@26.1.0
PHARYNX_TEST_DEPS=/tmp/pharynx-deps node --test tests/pharynx_visibility/visibility.test.mjs
python3 -m unittest discover -s tests -p test_pharynx_visibility_patch.py
python3 tools/verify.py offline
```

`tests/pharynx_visibility/fixtures/record-excerpt.json` is the supplied candidate
record excerpt. It is not a replacement for the 1,061,189-byte canonical
`review-data.json` and does not claim that file's hash. The candidate script
fixture is an exact retained v40 baseline used to test patch application.

To replay offline evidence into a new directory, use Blender 4.3.2, Pillow and
the DejaVu Sans font. This applies controller-selected visibility to a clean
GLB reimport; it does not execute WebGL or capture browser UI:

```sh
PHARYNX_TEST_DEPS=/tmp/pharynx-deps node tests/pharynx_visibility/capture_states.mjs /tmp/pharynx-states.json
blender -b -t 4 --python tests/pharynx_visibility/render.py -- --states /tmp/pharynx-states.json --output /tmp/pharynx-new-renders
python3 tests/pharynx_visibility/compose.py /tmp/pharynx-new-renders
```

See the [dated review](../../../reviews/pharynx_larynx/2026-10-30-visibility/README.md)
for exact output identities, independent findings and remaining browser/delivery
limits. Site deployment is a separate action and is not part of this patch.
