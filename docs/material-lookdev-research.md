# Material look development: future research

**2026-11-04 · Research backlog, not current production work.** Better materials
may help close-up teaching images, but do not repair anatomy or establish clinical
accuracy. This note does not reopen the accepted opaque dental study
[#219](https://github.com/qianyizhang/med-assets/issues/219), implement translucency,
change assets, or authorize publication.

## Reference and evidence boundary

Starting reference: [mukadeshinigami's linked X post](https://x.com/mukadeshinigami/status/2115580095511617850).
The original article and media could not be retrieved, so their pixels, complete
method and reproducibility were **not verified**. A separate
[October 29 creator post](https://x.com/mukadeshinigami/status/2115706592322617743),
available as a [third-party text copy](https://www.whatpeoplemade.com/i/8k-photoreal-rock-and-moss-material-from-a-single-refere-617743.html),
describes aligned PBR maps, separate rock/moss responses, and different masks for
shading versus displacement. These are attributed workflow leads, not direct
verification of the linked guide, its results, or medical suitability. No creator
images, textures or scripts are copied here; reuse rights remain unverified.

## Practical directions worth testing later

1. **Separate appearance from tissue identity.** Keep independently selectable
   components and reversible material assignments. Use distinct roughness and
   colour responses where the source supports distinct components; preserve
   teaching/vertex colours and a neutral clay view. A colour mask is an appearance
   control, not a tissue segmentation. Our inference: a coherent small material
   family is more useful than applying one glossy shader to every surface.

2. **Make the maps agree before adding resolution.** Use a common UV layout and
   aligned colour, roughness and normal maps. Inspect seams, normal orientation
   and scale under grazing light. For glTF, base-colour texture RGB is sRGB,
   factors/vertex colours are linear, and normal/roughness/metalness/AO are data.
   ORM packing is R=occlusion, G=roughness, B=metalness; packing alone does not wire
   the occlusion input. Generated relief is authored detail, not a measurement
   recovered from one photograph. [glTF material specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#materials)

3. **Choose relief for the shot.** Bump/normal detail changes shading, not the
   silhouette. True displacement changes geometry and needs adequate subdivision;
   high-precision height maps reduce stepping. Start with subtle normal detail;
   test displacement only where a close-up justifies its memory cost, with recorded
   physical scale and no invented anatomical landmarks. Smoothing a height mask
   may reduce spikes but does not validate the resulting shape.
   [Blender displacement](https://docs.blender.org/manual/en/latest/render/materials/components/displacement.html)

4. **Treat subsurface scattering as a separate experiment.** Scattering distance,
   object scale and geometry matter; Random Walk can misbehave with holes or
   overlapping faces. Do not use opacity as a substitute for tissue optics or copy
   rock/moss parameters onto enamel or gingiva. Any future SSS/transmission preset
   needs appropriate tissue references, renderer-specific review and an explicit
   fallback; the accepted opaque set remains valid within its narrower scope.
   [Blender Principled BSDF](https://docs.blender.org/manual/en/5.1/render/shader_nodes/shader/principled.html)

5. **Judge exported assets, not just a beauty render.** Keep a Blender authoring
   master and verify the actual GLB's materials/textures after clean reimport.
   Core glTF PBR does not represent an arbitrary Blender node graph or a Cycles
   displacement setup. Review supported extensions in the intended viewer rather
   than assuming parity. Report file/texture memory and triangles separately from
   measured load time/frame time; an 8K map or attractive still is not a performance
   result. [glTF specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#materials)

## Small future experiment, only when reprioritized

Use one already-authorized tooth-layer asset and one support/gingiva context.
Compare the original, accepted opaque preset and one conservative mapped candidate
with identical camera, scale, lighting and colour management. Inspect whole/detail,
clay and moving-light views for lost boundaries, seams, noisy highlights and
flicker. Preserve source geometry; a displacement branch requires its own measured
geometry review. Record source/license, map hashes, renderer/exporter versions and
settings. Accept only a visible teaching benefit with measured cost and no hidden
source defects. Keep technical/export, visual, anatomy/clinical and actual-runtime
decisions separate under the existing [review contract](REVIEW_CONTRACT.md).

First prerequisite: inspect the original guide/media and any downloadable source
with verified reuse rights. No experiment, benchmark or clinical validation was
performed for this research note.
