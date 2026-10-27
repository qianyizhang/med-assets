# Sources: what we used and learned

This guide points to selected useful sources and the work that actually used or
evaluated them. It is not an exhaustive catalog or an approval registry. Study
records remain the authority for each asset, source version, attribution and
technical, visual, anatomical and runtime limits. Check provider terms before
reuse; independently authored
geometry and code do not acquire a new reuse license merely because a reference
or source has one.

License descriptions reflect linked provider and repository evidence; they do
not grant blanket legal clearance.

## Used or adopted in specific repository studies

- **[Human Reference Atlas: male lymph node v1.2](https://doi.org/10.48539/HBM299.VVXH.634)** — **CC BY 4.0**. Its seven source-labeled meshes support inspecting individual layers. We retain the [original GLB](../models/lymph_node/exports/hra-v1.2/NIH_M_Lymph_Node.glb) unchanged and use layer-visibility views in its [review](../reviews/lymph_node/2026-10-23-hra-v1.2/record.json); [source metadata](datasets/hra/lymph-node-v1.2/metadata.md) records the citation and license. **The vascular node name says blood; its provider metadata says lymph. Its identity is unresolved.** Follicle and paracortex labels are source metadata, not independent histological or clinical validation. This is one node, not a body-wide system.
- **[BodyParts3D / DBCLS](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html)** — publisher's database license **CC BY 4.0**; preserve the historical **CC BY-SA 2.1 Japan** notices in original OBJ headers. The [femur cutaway](../reviews/bone_marrow/2026-10-26-source-cutaway-r05/README.md) uses a source-derived exterior; its cortical inset, network and marrow are independently authored teaching geometry, not measured tissue. See [attribution and source boundary](bone_marrow/source-cutaway-r05/ATTRIBUTION.md). No separate public license is declared there for newly authored additions.
- **[Z-Anatomy](https://github.com/Z-Anatomy/Models-of-human-anatomy)** — selected derivatives **CC BY-SA 4.0**, with the project's historical BodyParts3D attribution retained. The [salivary study](../reviews/salivary_glands/2026-10-26-native-scoped-r02/README.md) uses selected glands, parotid ducts and same-source context. Both submandibular ducts are excluded; a left-source crossing was demonstrated, while the right course was not accepted or independently proven faulty. The atlas lists separately restricted kidney (**CC BY-NC 4.0**) and inner-ear (**CC BY-NC-SA 4.0**) assets; do not apply a blanket license to the archive. [Source/rights details](datasets/z-anatomy/small-static-studies/ATTRIBUTION.md).
- **[NIH 3D upper-airways cast, 3DPX-002305](https://3d.nih.gov/entries/2305)** — nevitdilmen's selected item is **CC BY 4.0**. Its CT-derived airspace cast informed a [source-preserved nasal/sinus display](../reviews/nose_sinuses/2026-10-26-nih3d-airspace-r01/README.md), not a repair of the earlier schematic. It depicts airspace, not mucosa or conchae; a disclosed cyst indentation and detected intersections remain, and physical units/axes are undocumented. [Provenance and license](nose_sinuses/nih3d-airspace-r01/provenance.json).
- **[UFF ds-uct-002 micro-CT](https://zenodo.org/records/3877625)** — Pereira and colleagues, **CC BY 4.0**. Pretreatment Tomo1B supports a [draft tooth research candidate](../reviews/dental_specimens/uff_tomo1b/2026-10-26-r01/README.md), with a source-derived outer boundary and an algorithmic internal-space proxy. Slice selection loses an open channel and creates an algorithmic cap; it is not a complete canal or expert segmentation. [Pinned source and recipe](datasets/uff-ds-uct-002/README.md).
- **[Kuczynski trabecular micro-CT sample](https://doi.org/10.5281/zenodo.11061947)** — **CC BY 4.0**. Used as an independent segmented-bone surface in a [two-panel marrow comparison](../reviews/draft_bone/2026-10-23-marrow-comparison/bounded-record.json), not registered or fitted into the femur. Bone site and donor status are unknown; record/header spacing differs (17.59 vs about 17.409 µm). [Attribution and limits](../reviews/draft_bone/2026-10-23-marrow-comparison/LICENSES.md).
- **[TotalSegmentator dataset, case s1233](https://zenodo.org/records/10047263)** — selected dataset attribution **CC BY 4.0**; its label-source software notice is separately **Apache 2.0**. Bounds of five lung surfaces informed an [authored bronchial illustration](../models/bronchial_tree/exports/authored-central-fairing-r13/README.md); the airway itself is not a segmented airway and its routing remains unvalidated. [Exact source role](../models/bronchial_tree/exports/authored-central-fairing-r13/ATTRIBUTION.md).
- **[Servier Medical Art](https://smart.servier.com/)** — **CC BY 4.0**. Selected [2D atlas](../body/2d-v4/whole-body-anatomy-v4-spatial/README.md) support illustrations are conservatively attributed as redrawn Servier adaptations; other drawings are reference-informed originals. Preserve each part's attribution and change notice, and do not impose the adaptation license on independent originals. [Per-part rights and provenance](../body/2d-v4/whole-body-anatomy-v4-spatial/LICENSE-NOTES.md).
- **[OpenStax Anatomy and Physiology 2e, bone structure](https://openstax.org/books/anatomy-and-physiology-2e/pages/6-3-bone-structure)** — textbook **CC BY-NC-SA 4.0**. Consulted for general bone/marrow relationships in the femur cutaway; no reference figure was copied. It does not supply the derivative's geometry or patient-specific thickness. [Documented reference role](bone_marrow/source-cutaway-r05/provenance.json); check rights of individual credited material before reuse.
- **[Columbia histology laboratory](https://histologylab.ctl.columbia.edu/lab16/) and [Penn State histology collection](https://histopathology.pennstatehealth.net/slideview/MH-109-esophagus/14-slide-1.html)** — reference websites; a reusable license for their images is not established in this repository. Consulted for wall-layer relationships in the [independently authored esophageal teaching segment](../models/esophagus_wall/exports/authored-cutaway-r01/README.md). No slide images or source meshes were copied; illustrative dimensions are not measured histology.

## Evaluated or excluded in these trials

- **[SWIRendo prepared-tooth dataset](https://data.ub.uni-muenchen.de/477/)** — **CC BY-SA 4.0**. Two segmented specimens were examined in a local display pilot; the [source record](datasets/swirendo-pilot/source-map.json) and [validation summary](datasets/swirendo-pilot/validation-summary.json) are retained, but as of 2026-10-27 the pilot geometry is not yet integrated as a repository model. Labels are in progress; a sampled cross-label interface check failed without proving volume overlap. The two members were verified, not the whole archive; specimens are prepared, not a healthy-jaw or clinical model.
- **Z-Anatomy as a direct trachea replacement** — evaluated and **rejected for that use** because the candidate introduced a closed distal spur and coarse joins. This does not reject the separate Z-derived salivary study above. The [trachea review](../reviews/trachea/2026-10-25-host-conforming-cbands-r05/REVIEW.md) retains the negative evidence and describes the limited authored alternative. Selected Z derivatives remain **CC BY-SA 4.0**.
- **[arjun988/blender-skills](https://github.com/arjun988/blender-skills/tree/8f778d2405a214b508d4c7d80742be8e43acdd52)** — **MIT**. Its lookdev and QA Markdown informed matched-view and evidence checks in a local esophageal palette trial; no upstream code, addon or server was installed. A concise practice was proposed in [PR 90](https://github.com/qianyizhang/med-assets/pull/90); follow the PR for its current status. As of 2026-10-27, the palette-only candidate is not a canonical model.

## Practices worth adapting

The local lymph-node trial suggests keeping separately named source layers at
their original transforms and using a clearly labeled **editorial window** to
show relationships while retaining some enclosing context. Its capsule and
medulla were clipped, with no invented tissue caps; the intact original is still
needed to inspect the complete exterior. Follicles and paracortex were more
visible, although the dense vascular mesh still hides some structures. As of
2026-10-27, that candidate remains local and is not the repository's canonical
model. The provider's blood/lymph conflict remains unresolved.

Compare source and candidate with matched cameras and lighting, include a reverse
view, and check the actual export after reimport. Record exactly which surfaces
changed and keep technical, visual, anatomical, clinical and runtime decisions
separate. A useful display or successful geometry check does not establish a
clinical or histological pass.
