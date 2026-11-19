# Sensory routes in context

Restore the local screenshots from the [body-systems teaching backup](../../sites/body-systems-survey/README.md#restore-the-media).

| Combined and isolated studies | Isometric | Straight |
| --- | --- | --- |
| Whole right sciatic–cord–brain route | [Overview](central-iso.png) | [Posterior](central-ortho.png) |
| Selected roots and plexus bridge at the lower cord | [Root](root-iso.png) | [Posterior](root-ortho.png) |
| Whole ear, right auricle to inner ear | [Ear](ear-iso.png) | [Ear](ear-ortho.png) |
| Auditory inset, from tympanum at inner end of canal | [Hearing](hearing-iso.png) | [Hearing](hearing-ortho.png) |
| Vestibular inset, above the cochlear spiral in the ear overview | [Balance](balance-iso.png) | [Balance](balance-ortho.png) |
| Right eye cutaway, receptor to optic nerve | [Vision](vision-iso.png) | [Vision](vision-ortho.png) |
| Olfactory epithelial neuron to bulb | [Smell](smell-iso.png) | [Smell](smell-ortho.png) |
| Taste receptor to VII afferent | [Taste](taste-iso.png) | [Taste](taste-ortho.png) |

All sixteen views came from the [same portable GLB](../../assemblies/nervous-senses/nervous-senses.glb). The source studies are compared in the [owner record](../../assemblies/nervous-senses/README.md). [Renders](renders.json) binds the camera scale, view direction, visible meshes, bounds and image hashes. Each pair has a common scale. Local studies isolate named meshes and refit their bounds.

- **Technical.** Blender clean import recovered 134 meshes. All 45 tested neighboring surface pairs intersect in the final mesh, including the sciatic and mixed-nerve ends of the authored bridge, dorsal root–overlay–medulla, ossicles, optic-nerve and receptor joins. This tests placement and gross topological continuity at teaching scale. It does not simulate transmission or prove microanatomical synapses. A first candidate failed the rod-to-retinal strip test with 0.421 mm display separation. After placing the receptor against the strip all contact tests passed. A fresh independent build reproduced all scene nodes, transforms, materials, triangle-corner positions, normals, UVs and winding exactly. Blender varied GLB accessor/index packing across processes, including single-thread builds. The stored export SHA and evidence identify the selected file.
- **Visual.** Inspected the eight Cycles pairs after reimport. The root detail separates dorsal from ventral in the oblique projection; their long stems overlap in the straight projection. The full ear shows the canal beside the concha and both end organs. Auditory and vestibular isolates expose the two nerves and proximal common trunk. Some inner structures are hidden by the pinna from the medial angle. The cut eye exposes its posterior relay; the other two standalone views place the receptor between its exposed apical end and its afferent output. Relative receptor sizes and colors are editorial.
- **Anatomy.** Reference-screened for introductory relationships. The route stages unregistered sources. The afferent is represented by its named gross nerve/roots and a superficial dorsal-column overlay. The auricle and eye sections have authored joins. Cell and ganglion positions, signal speeds and tissue dimensions are outside the claim. No specialist or clinical assessment.
- **Runtime.** Offline import and rendering exercised. Interactive WebGL, device performance and clinical use remain unverified.

The dated [spinal root review](../spinal_cord/2026-10-29-authored-roots-r04/README.md) predates the [candidate delivery receipt](../../models/spinal_cord/exports/authored-roots-r04/delivery.json). The exact tracked GLB was hydrated and rehashed for this composition. The r04 contains sampled roots and cord; it omits vertebrae.

[Review record and hash bindings](record.json) · [Source placement and transformations](../../assemblies/nervous-senses/placements.json)
