Offline visual verdict: pass-with-limitations. No remaining blocking teaching-scale defect in the viewed v2 scenes or storyboard.

I personally inspected v2 airway.png, mechanics-rest.png, mechanics-in.png and offline-storyboard.png with view_image. The cyan route now follows the visible bent tracheal lumen and both branches; the v1 exterior-marker defect is resolved. Rest/inhalation views visibly couple expansion to descent of the authored diaphragm guide. The storyboard is legible, unclipped, bilingual in its teaching captions, and explicitly labeled OFFLINE COMPOSITION with browser UI unverified. It clearly separates source-derived lungs/authored airway cutaway from the authored, non-scale exchange schematic. Smaller airways remain explicitly omitted.

The previously viewed v1b EN/中文 exchange PNGs remain applicable: the corresponding v2 SVGs are byte-identical. O₂ points from alveolar air into blood and CO₂ in the reverse direction; the thin barrier and separate air/blood regions remain clear. EN port labels now say Left/Right main bronchus, matching 中文.

Code screening covered state.mjs, scene.mjs, exchange.mjs and app.mjs, plus route/port metadata. Separate breathClock freezes airway-marker positions on pause while elapsed continues exchange; phase 0.5 now has an end-inspiration cue. Reset retains language and asset status while returning to stage 0/phase 0; stage/language transitions preserve the shared breath. The unavailable-WebGL path disables breath controls, uses the rest snapshot at initial/reset state, marks it Static preview, hides live progress, and has bilingual missing-image text.

Final narrow source recheck: app.mjs image.onerror now begins with `if(!image.isConnected)return;`. Detached previews cannot repopulate the notice after stage or language changes through this callback, resolving the remaining reported code defect. No remaining concrete defect was found in this bounded offline visual/code review. This is source inspection, not a browser-runtime result.

Limits: this is an offline pixel review and bounded code screen, not a browser/UI, WebGL, performance, clinical, anatomical, or quantitative simulation approval. Browser launch was reported blocked before page launch by the configured Chromium SUID sandbox; I did not retry or bypass it. Layout/label collision and interaction behavior in the actual browser remain unverified. Morphs, diaphragm/ribs, route markers and alveolus are illustrative; no airway pressure/flow calculation, distal tree, measured wall, specimen registration, or master-geometry correction is established. No renders or tests were run by this reviewer; builder test results are separate evidence. No repository files or remote state were changed.

Candidate: local working tree on `wip/one-breath-lesson`, base `5690af119d6ba18a1247879651515dec07d9af9b`. Lesson files are uncommitted; the base commit alone does not identify the reviewed candidate. Exact source SHA256 values follow.

| Source under lessons/one-breath | SHA256 |
|---|---|
| state.mjs | `3e52661f6f11cd63411b658b4cb2fad24d5a9d857161df65e1c9d27fd8b0451d` |
| scene.mjs | `60c33a7be79e7bc6a917e045c8c765f30847399b1a5afd40e9c1cad384ce3b14` |
| exchange.mjs | `d7d2e6bccde8d577dfb7ade32eb104bbeacc0b14de8fa9c067dbce64ac50ffc2` |
| app.mjs | `ed86a2d4ce2a9bd654a269b956054d9685a8ee8d65fce49aa90b32ca8109a2a7` |
| assets.json | `5912784546119831b3fac9a1788834de49a0fb2eaf1e3bc7005b0c44c2b33806` |

| Actual viewed evidence, relative to the retained offline evidence root | SHA256 |
|---|---|
| v2/airway.png | `7d93258ecff26166d90bd30f8d878c695e18763d21035761b8cee6a7eedcfece` |
| v2/mechanics-rest.png | `fdfb3bc1365efe592f5de1b11da2ea05c7d2c34aed80723cc8554e7f5c549fcb` |
| v2/mechanics-in.png | `18c7c4e6fca672b44a22ca50fc5d46913397ad8384c731bd7f02d137e24d0b14` |
| v2/offline-storyboard.png | `d6eb778453cf94a5cf6ac699628ef8360f016e48685f6483de8367b6d4ac6b75` |
| v1b/exchange-en.png | `02ad3b4506431f098118ccb2ecc629aad7934161343b32ea25f24f848a3f6a0e` |
| v1b/exchange-zh.png | `948320123e853c240331e26952c3db32a8401437d43e8afc4546eef1a1839399` |

Unchanged exchange vector identities (same v1b/v2):
- `exchange-en.svg`: `cb3c53027392f96bd1f24614a1728381670d05f5a0b35a2805af4de6d7c4f5a0`
- `exchange-zh.svg`: `b336fc0aab128152e3cf3544245a4e8c72efc6f1ddee7c51cf0fc5d8f093b360`
