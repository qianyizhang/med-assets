# Candidate viewer: cached-navigation lifecycle

Repository patch and tests for [#185](https://github.com/qianyizhang/med-assets/issues/185).
The canonical v40 viewer disposes controls/rendering and revokes the decoded gzip
Blob download on every `pagehide`, leaving ready UI without a restoration path.
This is source/handler evidence, not an actual-browser BFCache reproduction.

The patch suspends rendering and resize observation for persisted navigation,
then resumes one render loop on persisted return. It preserves renderer, controls
and decoded downloads across cached navigation. Ordinary unload disposes viewer
resources, revokes document-owned downloads once and removes lifecycle listeners.
Generation checks reject stale RAF callbacks; initialization checkpoints and UI/
resize guards prevent late work after document disposal.

A failed interactive startup releases only viewer resources. The valid download
and language-switchable static fallback remain usable until ordinary unload.
These are regressions found during independent review of the first revision and
fixed in the reviewed second revision. No additional model, camera, visibility,
label, transport-validation or security behavior is changed.

## Exact source and application

The existing immutable fixture is
[`candidate-v40.js`](../../../tests/pharynx_visibility/fixtures/candidate-v40.js),
bound by the existing pharynx patch documentation to canonical Site source
`11d91eea72408d8995ad9f60cd1c45b6341bd240`.

| File | SHA-256 |
| --- | --- |
| Canonical `candidate.js` | `9214093398033ab75beeec8c273d1f85a28408ee6096f3fe0bb91723ecc6f80b` |
| Updated `candidate.js` | `d11cffd8a69ee32cc70ccd6712064b5e5f4c8c0f9f710614453007c640461b1e` |
| `viewer-lifecycle.mjs` | `2e2b67adb61140feefa64ffae50207258aa507bb555ebe8549c6b7b0989e8969` |

Use an independent copy of canonical `review/`:

```sh
python3 gallery/candidate-lifecycle/r01/apply.py /path/to/independent/review
```

The applicator requires the exact canonical hash and unique integration anchors.
It changes only `candidate.js` and adds `viewer-lifecycle.mjs`, refusing an existing
module, repeat application or modified source. It performs no fetch, Git operation,
Site write or deployment. Existing data, models and source archive stay untouched.
Other patches against canonical v40 require a separately reviewed composition;
this guard deliberately does not accept an already-patched script.

## Verification and limits

```sh
python3 -m unittest discover -s tests -p test_candidate_lifecycle_patch.py -v
python3 tools/verify.py offline
```

The seven required Python tests check exact source/output hashes, deterministic
application, refusal without writes and preserved camera/visibility code. They
also execute the actual original and patched ES modules through 15 Node VM
lifecycle cases: updated passes 15; canonical passes 3 and fails the 12 expected
regressions. Both runs require complete execution without skips/cancellations.
Browser, Three.js and transport-contract APIs are test doubles. No npm packages,
model payloads or screenshot evidence are needed. Screenshots are not applicable:
this is lifecycle/source delivery with no new visual appearance claim.

Covered: duplicate cached hide/show, final unload, stale RAF/resize/UI callbacks,
startup across eight async boundaries, startup while cached, parse/first-render
failure, retained fallback download and language switching.

Independent review accepted the second revision after both fallback regressions
were corrected. Actual browser BFCache eligibility/navigation, WebGL/context
restoration and device/camera/visibility integration remain **unverified**.
Existing partial-renderer-construction and throwing-disposer failures are not
claimed fixed. No anatomical/clinical acceptance or Site publication is implied.
