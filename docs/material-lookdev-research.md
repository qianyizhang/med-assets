# Material look development · research backlog

- **Status** · 2026-11-04. Future research. [Opaque dental study #219](https://github.com/qianyizhang/med-assets/issues/219) remains the accepted baseline.
- **Goal** · Improve readability in dental close-ups while preserving source geometry, component selection and a neutral clay view.
- **Evidence** · [Original guide](https://x.com/mukadeshinigami/status/2115580095511617850) and media unavailable. [Separate creator post](https://x.com/mukadeshinigami/status/2115706592322617743) and [third-party text copy](https://www.whatpeoplemade.com/i/8k-photoreal-rock-and-moss-material-from-a-single-refere-617743.html) suggest aligned PBR maps and separate shading/displacement masks. Reproduction, reuse rights and medical applicability remain unverified. No experiment or benchmark performed.

| Candidate | Acceptance evidence |
| --- | --- |
| Component materials | Separately selectable tissues, reversible materials and retained teaching colors. Distinct roughness/color only where justified. Label color masks as appearance controls. |
| Aligned maps | Shared UV layout, checked seams, normal orientation and scale under grazing light. glTF base texture RGB is sRGB, factors and vertex colors are linear. ORM uses occlusion/roughness/metalness in RGB, with explicit occlusion binding. [glTF](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#materials) |
| Relief | Prefer subtle authored normal detail. Displacement needs a justified close-up, recorded physical scale, suitable mesh density/map precision and separate geometry review. [Displacement](https://docs.blender.org/manual/en/latest/render/materials/components/displacement.html) |
| Subsurface scattering | Separate experiment with tissue references, scale, topology, renderer-specific inspection and fallback. Random Walk depends on intact geometry. Keep the opaque preset available. [Principled BSDF](https://docs.blender.org/manual/en/5.1/render/shader_nodes/shader/principled.html) |
| Portable export | Keep Blender master and inspect actual GLB after clean reimport. Verify target-viewer extensions and texture/geometry cost. Measure load/frame time in the viewer. |

## Bounded experiment

- **Start condition** · Reprioritized and original references/media inspected with verified reuse terms for any reused content.
- **Inputs** · One authorized tooth-layer export and one gingiva/support context. Compare original, opaque preset and one conservative mapped candidate.
- **Evidence** · Matched camera, lighting, scale and color management. Whole/detail, clay and moving-light views expose boundaries, seams, highlights and flicker. Record material provenance, map hashes and exact renderer/exporter settings.
- **Accept** · Visible teaching benefit, measured cost and preserved geometry. Keep technical, visual, anatomical/clinical and runtime outcomes independent. [Review contract](WORKFLOW.md#visual-comparisons).
