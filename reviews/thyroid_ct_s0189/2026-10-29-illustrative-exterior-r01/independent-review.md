# Independent v2 visual review

Reviewed at 2026-10-29T16:31:10Z. **Verdict: pass-with-limitations** for the isolated illustrative exterior. The viewed result supports a useful scoped draft; it does not complete same-sample tracheal-relationship acceptance for issue #148.

Candidate: `thyroid-illustrative-exterior.glb`, **152,124 bytes**, SHA256 `4c2dee513f713fd8d649e7d1928ba3859ce1d25e81468e707b65a5fbeeee216a`.

Baseline: retained `thyroid_ct_s0189_source_frame.glb`, **151,580 bytes**, SHA256 `4add07e2efed2d67efb1d4ba225a109fe448043c79182e3d2e1a96e671534883`. The original remains separate and unchanged.

- Inspected all ten actual 900 × 900 clean-import Cycles PNGs: matched whole, oblique, ridge-detail, reverse and side views. These are offline export evidence, not browser screenshots.
- The corrected ridge-facing selection visibly softens the parallel surface ridges, especially across the larger lobe in whole/oblique views and the side view. The detail pair shows softened smaller scallops while broader source depressions remain.
- Gross lobe shape and sample asymmetry remain readable. The deep U and narrow continuous bridge are retained. No visible new gap, forced symmetry, obvious ballooning or lobe collapse appears in these sampled views. Further global smoothing is not justified by these pixels.
- Matched lower lighting makes the surface change easier to assess. View names and negative-Y selection describe the retained coordinate/view setup; they do not establish anatomical orientation. Broad depressions are not interpreted as pathology or identified tissue structures.

Independent technical scope: recomputed candidate and ten PNG sizes/SHA256 values, checked image-to-artifact bindings, matched camera/target/scale/pixel/sample/material settings for all five pairs, and inspected exported derivative/clinical/unit/runtime extras. All matched the supplied records. Source identity and provenance screening from v1 are reused.

The builder's `build-record.json` reports unchanged 4,172 vertices/8,340 faces, maximum movement 0.609 mm, RMS 0.205 mm, central-band maximum 0.279 mm and volume change approximately +0.00055%. This reviewer did not rerun the build, geometry checks, replay, rendering or test suites. Those reported measurements are not anatomical accuracy tolerances. Pixels do not establish exhaustive freedom from self-intersection.

Limits remain: this is an illustrative treatment of one TotalSegmentator s0189 clinical-source exterior, not a healthy/normative atlas or improved segmentation. Preserve the retained CC BY 4.0 attribution and source-unit caveat. Exact same-sample trachea context is external, so tracheal clearance/collision and relation preservation are unverified; no unrelated trachea was used. No new internal anatomy, specialist, clinical or browser/intended-consumer runtime approval is given. Issue #148 should remain open for its unresolved relationship scope.

Exact visual evidence, relative to this directory:

| PNG | Bytes | SHA256 |
| --- | ---: | --- |
| `renders/original-whole.png` | 721,525 | `3f20f2ee2a77288dd7c6a5808d8887636d480899aa86fb10c3df6aeb5817143a` |
| `renders/updated-whole.png` | 716,789 | `b09b6e9e39e154cf88223ff3012d1452fe26fcc9f5d5f2af63107ecb6e6ecee6` |
| `renders/original-oblique.png` | 765,590 | `480c4b40d8a1d424d598294b084d3a9cd7853aa2825fad06a9af7f3b1fa40acc` |
| `renders/updated-oblique.png` | 758,624 | `f73b70f64c817eda798e16a23aeee8f78b03ed469096cc9d8e63559dd0d48b22` |
| `renders/original-ridge-detail.png` | 877,990 | `b3b77804525f0447c182b1f468ec1c60320f204779e562952d4167bbbd264b2e` |
| `renders/updated-ridge-detail.png` | 871,859 | `2af5bced93b7329435e06aff2c1587041a1da99755ab84e8a7021cf72a496320` |
| `renders/original-reverse.png` | 706,941 | `9d95b407431d1c753de581bd1db41e1efbb040605c42585f8e3cebdd5a0d620f` |
| `renders/updated-reverse.png` | 699,531 | `f2432606a7d1b12eb86600b62b51f1148501727464333ec7d87d74ce3a673a01` |
| `renders/original-side.png` | 640,985 | `c85cc131210b38f622365dac473f785c1f246a53a6f96acc7f2b0ff88bc9053b` |
| `renders/updated-side.png` | 636,357 | `e83ea59f66132e2cf2c4ed18b404e826a1e46929f7681bc85ee328344cbc08fa` |

Bindings: `renders/raster-bindings.json`. Only this independent review note was written by the reviewer; no source, candidate, implementation or existing evidence was changed.
