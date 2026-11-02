# Candidate viewer: truthful recovery after context loss

Source-bound repair for [#192](https://github.com/qianyizhang/med-assets/issues/192).
The canonical viewer and lifecycle-v2 package can retain ready wording and active
camera/render callbacks after renderer context loss. Cached return can resume the
unavailable view. This package requires the already-merged lifecycle-v2 source;
it does not change the canonical fixture or deploy the live Site.

## Behavior

A `webglcontextlost` listener is owned by the interactive view from renderer
setup onward, including asynchronous model parsing. Loss permanently fails that
view for this document: animation/resize/control work stops, controls/renderer
are disposed, the loss listener is detached, and EN/中文 unavailable text plus an
explicit Reload page action appears. Verified downloads and static evidence
remain usable; they retain document lifetime and are released on ordinary unload.

Locale changes preserve the unavailable state and translate recovery instructions.
Detached old reload buttons and disposed documents cannot trigger reload through
the handler. Cached return and context-restored events do not initialize another
viewer. Reloading the document is the explicit recovery policy, rather than
claiming WebGL restoration succeeded.

A guarded parse wait and final readiness checkpoint reject late startup work.
Late parse failure cannot replace the recovery notice. Normal failed fetch/parse
keeps the existing blocked fallback/error and locale behavior; source bytes are
not relabeled corrupt merely because rendering was lost.

The patch preserves camera/visibility logic and source transforms. It modifies
neither the existing lifecycle implementation nor the separate camera-reset code.
The shared test harness is extracted from the existing lifecycle tests; their 15
behavior cases/assertions remain unchanged.

## Exact source and dependencies

Apply to an independent copy, in lifecycle-first order:

```sh
python3 gallery/candidate-lifecycle/r01/apply.py PATH_TO_CANONICAL_REVIEW
python3 gallery/candidate-context/r01/apply.py PATH_TO_REVIEW
```

The applicator rejects wrong source, missing/changed exact dependency modules,
existing context modules and repeat application before writes. No source fetch,
Git write, deployment or credential is performed. Model/data files are unchanged.

| Identity | SHA-256 |
| --- | --- |
| Required lifecycle-v2 input | `d11cffd8a69ee32cc70ccd6712064b5e5f4c8c0f9f710614453007c640461b1e` |
| Lifecycle + context output | `f3b016b44200851e7b1084c6d94973f65a588797f37fcf175aad0317543a62ba` |
| Context module | `b1e704c6445c6fd8bdfd3bff644784b4473c2f22642947cbb053d4ac464c0bf8` |
| Optional lifecycle + camera input | `855b9555acad27bdeb29876d02e3a72216fd659ed772dfa29cd166e16ffc9dc7` |
| Optional lifecycle + camera + context output | `071f9d29ba8c689f785b7272ed3ae1041d51dc4e97e569c61ba1497b43a4b61a` |

PR #191 is **not a dependency** of default tests or application. Optional
composition was separately checked using its preserved exact reviewed package:
lifecycle first, camera reset second, context loss third. The applicator accepts
that one exact composed source and requires its exact reset module. Its code or
tests are not copied here. Default hosted/offline tests run entirely from this
branch's declared base plus this diff and clear the optional test module setting.

## Checks and evidence boundary

```sh
python3 -m unittest discover -s tests -p test_candidate_context_patch.py -v
python3 tools/verify.py offline
```

Eleven required Python tests cover guarded application/ownership and full-module
VM runs. The actual canonical and lifecycle-v2 modules reproduce respectively
12 and 10 failures out of 14 context cases. Updated code passes all 14 and retains
all 15 existing lifecycle cases. Completion counts, failure status and absence of
skips/cancellations/todo are asserted; missing Node or modules fail the command.
Browser/renderer/DOM/transport APIs are doubles, not WebGL or a browser engine.

Covered: loaded/lost view, parse-loading loss, late success/failure, first-frame
loss, failed fetch/parse, absent static evidence, both locales, static/download preservation, stale camera/
RAF/resize actions, cached/restored return, listener teardown and explicit reload.

Separately run optional camera composition passes 14 context + 15 lifecycle VM
cases, and 14 actual-pinned-controls CPU cases from the preserved camera package.
Those external CPU cases are not copied into or claimed as this branch's hosted
scope. No new models/images/vendor payloads or historical evidence are retained
in this package. Private failed-before logs and reviews remain separate.

Independent code/VM review accepted this bounded behavior. Actual browser context
loss/restoration, import-map resolution, WebGL rendering and device/real-model
integration remain unverified. No screenshots or rendered-runtime pass is claimed.
No clinical/anatomical promotion, other-lesson change or Site publication occurs.
