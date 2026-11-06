# Incorporated viewer lifecycle

The repair for [#185](https://github.com/qianyizhang/med-assets/issues/185) is
incorporated in the retained Site v50 viewer. Cached navigation suspends rendering
and resize observation, then resumes one render loop. Ordinary unload disposes
resources and revokes document-owned downloads once. Startup failure preserves
verified downloads and language-switchable static fallback until unload.

The historical exact-v40 applicator and its application-only tests are retired.
The v40 fixture remains for the unapplied pharynx recipe and camera failure witness.
Current source identities are owned by
[`tests/viewer/source.json`](../../../tests/viewer/source.json).

Run `python3 tests/viewer/run.py --suite lifecycle` or the required
`python3 tools/verify.py offline`. The actual current module executes in fresh
VMs with browser/Three/transport doubles and per-invocation temporary staging.
Cases cover cached cycles, late RAF/resize/UI callbacks, async startup checkpoints,
parse/render failure, retained fallback and final teardown. Current manifest fetch,
body and transport-verification checkpoints are included.

Historical v40 reproduced 12 failures in the original 15 cases; that result is
history, not a required failure count for current maintenance. Actual browser
BFCache eligibility/navigation, WebGL and device integration remain unverified.
Partial renderer construction and throwing disposers are not claimed fixed.
No asset, camera policy, anatomy or Site publication change is implied.
