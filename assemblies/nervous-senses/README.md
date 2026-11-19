# Nervous system and the five special senses

Restore the local Blender scene and GLB files from the [body-systems teaching backup](../../sites/body-systems-survey/README.md#restore-the-media).

Open [the portable teaching scene](nervous-senses.glb) or [the editable Blender source](nervous-senses.blend). Use the named mesh prefixes to isolate the central pathway and each local section. The inset positions are independent teaching stations. Only the central group uses an approximate head-to-thigh frame.

| Study | What to follow |
| --- | --- |
| Central, posterior view | A lower-limb touch or position afferent can travel proximally in the right sciatic nerve. The short ochre bridge represents the lumbosacral plexus and ventral ramus contributions. Follow the selected mixed nerve to its dorsal root and ganglion. The ipsilateral dorsal-column overlay ascends to the lower medulla. The pale ventral root joins the same mixed nerve. The other levels provide orientation. |
| Hearing | The right concha leads to the sectioned external canal and tympanic membrane. Follow the malleus, incus and stapes to the oval window. In the cochlear spiral an enlarged hair cell represents the organ of Corti receptor. Its afferent passes through the spiral ganglion and joins the cochlear division of VIII. |
| Balance | The three green loops represent the semicircular canals. Locate the utricle and saccule. The enlarged utricular macular hair cell supplies an example afferent via the vestibular ganglion to the vestibular division of VIII. The two divisions join at the short common nerve. |
| Vision | The opened right sclera exposes the posterior retinal strip. A rod, bipolar relay and retinal ganglion cell lead to a ganglion axon and the source optic nerve. Receptor shapes are enlarged. The source nerve is truncated. |
| Smell | Cilia face the nasal cavity at the apical end of an olfactory receptor neuron. Its basal axon enters a filament of cranial nerve I and reaches an illustrative glomerulus of the bulb. |
| Taste | The enlarged taste bud sits in an anterior fungiform papilla. Follow the microvilli at its taste pore, receptor cell and an afferent destined for the chorda tympani branch of VII. |

## Geometry and ownership

[Inputs](inputs.json) pins each reused GLB. [Placement matrices](placements.json) map their imported Blender world coordinates into this assembly. Blender +Z is superior, +Y posterior, +X patient left in the central scene. glTF uses metres, +Y superior, +Z anterior. The authored right sciatic bridge and cervical bridge connect staged atlas ends. Vertebral level, actual plexus formation, histological synapses, intracranial cortical relays and patient registration are outside scope. The separate ear and eye sections have pupil/conchal access and are enlarged 2× and 1.8×, respectively. Magnified receptor cartoons have their own scales.

| Compared candidate | Admission and modifications |
| --- | --- |
| [BP3D brain](../../models/brain/exports/bodyparts3d-4.0-atlas-r2/README.md) and [r04 cord](../../models/spinal_cord/exports/authored-roots-r04/README.md) | Reuse the 49-part brain, cord and selected representative root levels. A translation of each group places the truncated medulla near the cord. Use the reviewed dorsal and mixed structures at one descending sample. The full r04 has other overlapping descending roots and carries its original whole-model review status. |
| [Right sciatic study](../../reviews/peripheral_nerves/2026-10-30-sciatic-hip-r01/README.md) | Reuse the original right nerve extent. Keep the source's proximal branches and distal cutoff. Bones and the unresolved piriformis relationship are outside this signal-tracing view. The plexus bridge attaches at one surface vertex of one proximal strand. |
| [Auricle](../../models/ears_z/exports/r04/README.md), [eye](../../reviews/eye_exterior/2026-10-30-z-native-courses-r01/README.md) | Keep the right half of the bilateral auricle compound and place it beside the authored canal. Open the right sclera with a plane and retain the right optic nerve. Both use illustrative matte colors. The pinna has source-open boundaries. The collection's separately licensed Dundee inner-ear geometry was excluded. The simplified ear internals are newly constructed from coordinates. |
| [Nasal airspace](../../models/nose_sinuses/recipes/nih3d-airspace-r01/README.md), [gross tongue](../../models/tongue_authored_study/README.md) | The nasal cast represents the lumen. The tongue shows gross papillary patches. Neither provides the local receptor–afferent interface. Keep them as gross orientation studies and supply two enlarged independent cell schematics. |

The body-systems survey consumes this coordinated study. Keep the exact inputs at their existing owners. The nervous-senses assembly owner maintains the procedural source, one editable scene, one portable export and scoped review images.

### Reference screening and attribution

The sensory relationships follow OpenStax *Anatomy and Physiology 2e* [13.4](https://openstax.org/books/anatomy-and-physiology-2e/pages/13-4-the-peripheral-nervous-system), [14.1](https://openstax.org/books/anatomy-and-physiology-2e/pages/14-1-sensory-perception) and [14.2](https://openstax.org/books/anatomy-and-physiology-2e/pages/14-2-central-processing). Those references informed relationships; their text, images and geometry are absent from the models.

The brain retains [BodyParts3D / DBCLS credit](../../models/brain/exports/bodyparts3d-4.0-atlas-r2/ATTRIBUTION.md). Z-derived auricle, eye and sciatic geometry, adaptations and derived images retain **Z-Anatomy — The libre 3D atlas of anatomy — CC BY-SA 4.0**, with **BodyParts3D — The Database Center for Life Science — CC BY-SA 2.1 Japan**. Eye attribution also credits Cranial Nerves and Foramina by University of Dundee, CAHID, CC BY 4.0. See [full upstream credits](../../sources/datasets/z-anatomy/small-static-studies/upstream/License.txt), [eye credits](../../sources/datasets/z-anatomy/eye-exterior-courses/ATTRIBUTION.md), [sciatic provenance](../../sources/datasets/z-anatomy/sciatic-hip/provenance.json) and [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). The [cord owner](../../models/spinal_cord/exports/authored-roots-r04/README.md) asserts no separate public license. A combined public redistribution decision remains open.

## Replay

Use Blender 5.2.3 and fresh output directories. Run from the repository root with hydrated pinned assets.

```sh
owner=assemblies/nervous-senses
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P "$owner/build.py" -- .artifacts/nervous-senses-replay
python3.12 "$owner/compare_replay.py" "$owner/nervous-senses.glb" .artifacts/nervous-senses-replay/nervous-senses.glb
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P "$owner/check.py" -- "$owner/nervous-senses.glb"
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P tools/render_teaching.py -- --glb "$owner/nervous-senses.glb" --views "$owner/views.json" --output .artifacts/nervous-senses-review
python3.12 tests/review_records/validate_record.py reviews/nervous-senses/record.json
```

[Eight matched pairs, findings and limits](../../reviews/nervous-senses/README.md).
