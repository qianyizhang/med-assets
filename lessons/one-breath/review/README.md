# Bounded local review

Later [non-WebGL browser checks in #140](https://github.com/qianyizhang/med-assets/issues/140)
and the [availability-status fix review](availability-status.md) supplement this
historical prototype record. The original images and receipts below are retained.

**Offline visuals and focused code review: pass with limitations. Browser UI and
WebGL: unverified.** The [reviewed storyboard](offline-storyboard.png) is the exact
`v2/offline-storyboard.png` bound in [visual-bindings.json](visual-bindings.json).
It is an offline Blender composition of shared lesson scene snapshots, not a
browser/UI screenshot. Other scene renders remain local/private. No public model
or gallery delivery is implied.

![Offline Blender composition; browser UI and WebGL unverified](offline-storyboard.png)

[Independent review](independent-review.md) records the v1 defects and v2 fixes.
[Checks](checks.json) separate technical, visual, educational and runtime evidence.
[Final snapshot reuse](snapshot-reuse.json) binds the final loader/scene/state
output to the already reviewed v2 meshes, cameras and state without rerendering.
Later fallback/text changes did not invalidate those rendered models.

The [repository setup receipt](repository-setup.json) records the later integration
of the exact repository-hosted lung and V7 trachea inputs. A fresh source checkout
with its own empty LFS store hydrated all four models from GitHub, prepared them
without a private bundle, and passed 17 consumer/state checks plus loopback HTTP
checks. The focused independent setup review passed with limitations. Local LFS
initialization is required before hydration; the initial skipped checkout and its
fix are retained in the receipt.

These checks exercise actual GLB consumption and application state logic, not
browser interaction E2E. The original source checkpoint's separate repository
offline gate passed 183 tests plus its fixed metadata/pointer scope. The earlier
visual receipts above remain historical; no images were rerendered for setup.

The attempted sandboxed Chromium launch failed before creating a page because
the SUID sandbox helper is misconfigured. The environment was not modified to
bypass that failure. Actual controls, layout, WebGL and failure UI require a
supported sandboxed browser before browser-runtime acceptance. The existing
protected CI-only probes were neither invoked nor weakened.
