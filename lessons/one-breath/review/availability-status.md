# Availability status · #140

The model-error notice and disabled breath control previously appeared alongside
“At rest / Ready for one breath.” The same stale cue appeared during model loading.
This bounded revision gives availability priority in the mechanics and airway
stages, in English and Chinese. The exchange diagram retains its independent
gas selector and directional cue.

Related: [#140](https://github.com/qianyizhang/med-assets/issues/140), which remains
open for full 3D acceptance. Baseline: `45bcb953518783337918845aa826a9d16725fe1c`.
The open-PR scan on 2026-10-30 found no overlapping fix; the only earlier One Breath
PR was merged #141.

## Original / Updated behavior

This table records source and DOM-double observations; it is not a browser capture.

| State | Original phase / cue | Updated phase / cue |
| --- | --- | --- |
| Loading or retry, EN | At rest / Ready for one breath | Loading models / Loading the teaching models… |
| Failed model load, EN | At rest / Ready for one breath | Models unavailable / Retry assets |
| Failed model load, 中文 | 静息 / 准备体验一次呼吸 | 模型不可用 / 重试加载 |
| Ready models, no WebGL, preview pending or missing | Static preview / Offline composition · motion unavailable | 3D unavailable / Breath motion unavailable |
| Ready models, no WebGL, preview image loaded | Static preview / Offline composition · motion unavailable | Same explicit static labels, after the image load event |
| Exchange, CO₂ selected, 中文 | 静息 / 血液 → 空气 | 气体交换 / 血液 → 空气 |

With a renderer and loaded models, the existing rest/inhale/peak/exhale/pause cues
remain. A failed breath resumes as paused after recovery, retaining progress;
reset restores rest and retains the language and availability. Loading or failed
states never regain readiness through language, stage or reset actions.

The new `lessonStatus` derives the two labels without changing motion state.
`renderUI` uses it on each relevant state change. A preview load event may switch
to static-preview labels only while that image remains attached; delayed load or
error callbacks from earlier language/stage views cannot overwrite the current UI.
Stage 3 uses neither model availability nor preview status to select its cue.

## Checks and independent review

Executed in the selected cloud worker on 2026-10-30:

- **Pass: 26 focused Node tests.** The 17 existing state/actual-model consumer
  checks, six bilingual availability-transition checks and three app-event checks
  all passed. Command from the repository root:

  ```sh
  node --test lessons/one-breath/tests/state.test.mjs lessons/one-breath/tests/consumer.test.mjs lessons/one-breath/tests/ui.test.mjs
  ```

  The added app tests execute the real `app.mjs` body with DOM/loader/renderer
  doubles. They cover pending load, 404, corrupt-response failure, retry/recovery,
  both renderer branches, language changes, all stages, gas selection, reset,
  preview success/failure and detached callbacks. They do not verify ESM loading,
  browser layout, actual image decoding, WebGL or animated camera behavior.
- **Regression control:** the new app-event tests against the original main
  `app.mjs`/`state.mjs` failed all three cases. Both availability journeys observed
  the original “At rest / Ready for one breath” while loading; the preview case
  lacked the new image-load callback. The updated app passed all three.
- **Pass: required offline verification.** `python3 tools/verify.py offline`
  passed 205 tests, 26 transport manifests, 25 historical foundation records,
  591 import references (3 documented updates) and 760 LFS pointer identities.
  This command does not verify media payloads or browser runtime.
- **Pass: exact consumer inputs.** The documented preparation hydrated and
  verified all four retained GLBs and five pinned Three.js files. Their local
  staged sizes/SHA-256 values were checked again against `assets.json` and
  `ci/glb-runtime-fixture.json`; source assets and both manifests are unchanged.
- **Pass: independent focused review.** A separate reviewer inspected the
  working diff and ran all 26 Node tests plus `git diff --check`. No blocking
  findings. The reviewer confirmed availability precedence, exchange independence,
  detached-callback handling and the small shared derivation. Its request to
  update the README test command/count was addressed. Browser/visual/3D checks
  were explicitly outside that review.

Reviewed production-file SHA-256 values (unchanged after independent review):

| File | SHA-256 |
| --- | --- |
| `app.mjs` | `69795997258972045989b7f02dd49182b8f69e12321687de494e6c2d3bf35eb2` |
| `state.mjs` | `bd00ae21ef290cbce909fb9b747ae5f1bba2f220056c1cb6c197d7d138df76be` |

## Browser evidence gap and next check

The retained actual missing-model screenshot and desktop/narrow browser findings
are described in [#140](https://github.com/qianyizhang/med-assets/issues/140).
Those screenshot bytes are not in this checkout. The earlier offline storyboard
remains historical model evidence and does not show this UI change.

Current matched Original/Updated desktop/narrow captures and real browser
interaction remain **blocked by unavailable supported runtime**, not passed:

```text
cloud-agent-desktop --help
Orbit desktop is unavailable

cloud-agent-browser-runtime show
Browser runtime failed: The Orbit OS browser launcher requires ORBIT_OS=true and BROWSER_HEADLESS=false
```

These were availability diagnostics only. No browser was launched, no runtime
variables were spoofed and the earlier failed Chromium sandbox experiment was
not repeated. The loopback server, CSP, model identity checks, loader, pinned
dependencies and protected CI-only runtime probes are unchanged. No model,
anatomical content, CSS/layout, other task artifact or earlier receipt changed.

Next: use the supported managed preview to compare baseline/current at matching
desktop and 500 px narrow viewports. Exercise missing/corrupt model → retry →
recovery; switch EN/中文, stages and reset; inspect preview-present/missing states
and both exchange directions. Keep this PR draft until the current visible
status behavior is inspected. Full 3D, smaller-phone, animation/camera and
clinical acceptance remain separate; no merge or Site publication is included.
