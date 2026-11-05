# Dental video workflow experiments

Three **48-second narrated storytelling experiments** share one script, voice and score, but use different visual treatments. This collection preserves their editable code and reviewed result. It is **not the actual-asset treatment-procedure prototype**: the films use original schematic illustrations, not the developed anatomical GLBs. Existing source assets and earlier dental studies are unchanged.

![Matched-time views of all three treatments](results/storyboard.jpg)

| Treatment | Exact reviewed result | Editable source |
|---|---|---|
| Before the hole: contrast-led motion graphics | [HyperFrames MP4](results/hyperframes.mp4) | [HTML/SVG generator](hyperframes/build_story.py) |
| The Decay File: captioned editorial diorama | [Remotion MP4](results/remotion.mp4) | [React/SVG composition](remotion/src/index.tsx) |
| The Mineral Ledger: native causal geometry | [ManimGL MP4](results/manimgl.mp4) | [Original 3b1b scene](manimgl/mineral_ledger.py) |
| Synchronized comparison, one audio track | [Three-panel MP4](results/comparison.mp4) | [Comparison recipe](comparison.py) |

Read the [shared narration and shot script](SHARED-SCRIPT.md), [comparison findings](COMPARISON.md), [result hashes and review boundaries](results/manifest.json), and [replay instructions](REPLAY.md). The three-panel result is for shot/pacing comparison; watch the individual 720p films to judge text. The sheet samples actual decoded films at 3, 10, 19, 27, 36 and 45 seconds. Different art/camera choices are intentional, not matched-anatomy comparisons.

## Reuse and status

- All final films: 48 seconds, 30 fps, 1,440 frames, H.264 plus AAC stereo. The same frozen 48 kHz WAV drives all three.
- HyperFrames 0.9.8 / GSAP 3.14.2; Remotion 4.0.540 / React 19.1.0; original ManimGL 1.7.2, not Community Edition. Lockfiles are retained.
- Technical encoding and sampled visual review passed with limits. Direct listening, clinical/anatomical approval and supported interactive-runtime testing remain unverified. The voice is local, non-cloned Kokoro `af_heart`; the score is original procedural audio. See [audio provenance](audio/README.md).
- These are illustrative mechanism/assessment/prevention stories, not validated anatomy, molecular simulation or a procedural training guide. A filling is one common option after assessment, not a universal prescription.
- Related dental story/lookdev context: [#217](https://github.com/qianyizhang/med-assets/issues/217), [#219](https://github.com/qianyizhang/med-assets/issues/219). This experiment archive does not complete or close those asset/procedure acceptance criteria.

## Recorded collection checks

On 2026-11-04, collection checks verified the hashes and sizes of all eight media
inputs/results and fully decoded all four retained movies. Two fresh HTML builds
matched the recorded original hash. New HyperFrames/Remotion movies and the
comparison re-encode completed but differed from the retained movie hashes;
ManimGL was not rebuilt because native Cairo/Pango headers were unavailable.

Direct LFS upload and a fresh, empty-store GitHub readback matched all eight
objects (28,007,051 bytes). A separate builder lacked Git HTTPS credentials, so
no independent second remote-byte result is claimed. These are historical
collection results, not a fresh check of this checkout. The result manifest owns
artifact identities; redundant collection and transport receipt files are retired.

## Retention decision

The final MP4s are in **Git LFS**, not ordinary Git blobs. Their animation sources are deterministic in intent, but bit-identical complete movie reconstruction has not been established across the recorded browser/GL/encoder pipelines. The final Manim movie includes a natively rerendered label-correction segment and a re-encode; the complete corrected scene source is retained, without pretending that its next encode matches the saved movie hash. Fresh full HyperFrames/Remotion builds and comparison re-encoding succeeded during collection, but all three resulting hashes differed from the retained originals. Preserve the exact reviewed exports until independent repeated rebuilds establish safe hash-only retention.

The HTML generator has been replayed twice and matches its recorded output hash, so generated `index.html` is **not** committed. One shared WAV is retained because voice regeneration is not a guaranteed bit-identical rebuild. Fonts are retained once with their notice; preparation makes disposable consumer copies. The small storyboard is a review entrypoint. The comparison MP4 preserves the already-reviewed synchronized result; it is not a duplicate of any individual movie. Result hashes are authoritative in one manifest.

No source ZIP, renderer caches, installed packages, model weights, TTS runtime, silent intermediates, frame sequences, duplicate WAVs, or generated per-renderer receipts are committed. Preparation and future QA write to new ignored work directories. Preserve source identities and current deliverables; retire spent intermediates under the [repository retention policy](../../docs/WORKFLOW.md#retention). Review this retained experiment by 2026-12-05 for continued teaching or workflow-comparison use.

## Rights and sources

All tooth/prop illustrations and scene code were authored for these experiments. No source mesh, artwork or code was copied from a style gallery. Dependencies retain their own terms; no blanket license is added here. DejaVu notices are in [fonts/LICENSE.txt](fonts/LICENSE.txt); GSAP retains its header notice. Check [Remotion licensing](https://www.remotion.dev/docs/license/pricing) for the intended organization/use.

Educational sources: [NIDCR tooth decay](https://www.nidcr.nih.gov/health-info/tooth-decay), [the decay process](https://www.nidcr.nih.gov/health-info/tooth-decay/more-info/tooth-decay-process). Technical skills/source links and workflow failures are documented in [COMPARISON.md](COMPARISON.md). A human listening pass and qualified dental review are required before patient-facing publication.
