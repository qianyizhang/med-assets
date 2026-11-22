# UFF candidate review — 2026-10-26

**DRAFT research illustration only.** The owner requested repository and Site browser review after a private review package was delivered. Earlier private-review conclusions are historical; current publication does not promote anatomy or runtime status.

## Review goal

Compare the scan-derived outer tooth surface and the simplified display version, then inspect the source overlays showing why the internal-space proxy is incomplete. The result is useful for reviewing the extraction method, not for approving canal anatomy or a clinical procedure.

[Browser review](https://anatomy-dental-review.landy123007.chatgpt.site/) provides the images and exact downloads without requiring a local viewer.

<details>
<summary>Candidate identity and technical receipts</summary>

- Candidate: SHA-256 `46694985ff0162a4220d959528847446ffe48b3be41e481f5890429500e2d3b3`.
- Corrected extracted master: `7b7e58a7c8149538dffdeebf9f6f079ccb47f6be1fc53db93510b80073ad9790`.
- [LOD measurements](lod-report.json), [export checks](export-check.json), [independent checks](independent-check.json), [review summary](independent-review-summary.md).
- `media/`: 3 matched master/display pairs plus native and terminal source overlays. All public PNG metadata removed; [sanitization receipt](media-sanitization.json) verifies identical decoded RGBA pixels and records superseding hashes.

</details>

## Read the negative evidence first

The space proxy is 3D exterior-connected. Per-slice selection loses an open channel and creates an algorithmic closing surface. The terminal overlay shows the actual source limitation. It is not a complete canal or an anatomical endpoint.

Unknown FDI, health, laterality and anatomical orientation remain unknown. No enamel/dentin/cementum separation, expert label validation, clinical teaching approval or simulation claim.

The hosted page, static images and exact downloads passed browser checks. The cloud browser reached file verification but could not initialize WebGL. That check left interactive rendering open.

### Hosted inspector follow-up · 2026-11-21

The [historical inspector](https://anatomy-dental-review.landy123007.chatgpt.site/viewer/) rendered the 20,434,544-byte r01 GLB in disposable Chrome for Testing using SwiftShader on this Mac. The page verified the full candidate digest above. Hiding each named component in turn changed the rendered view. At two slider positions (25% and 75%), source-X clipping produced distinct images of the hard boundary. Reload reopened both components with clipping off.

During forced WebGL context loss the page still reported ready and left its controls visible. After the browser restored the context, resetting the camera and toggling the hard boundary produced distinct renders again. This run covers the historical inspector in this browser. Gallery-native presets, loss feedback and performance remain open. The original proxy endpoint finding stands.
