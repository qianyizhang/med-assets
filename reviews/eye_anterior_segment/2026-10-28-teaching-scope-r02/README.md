# Right anterior eye: bounded teaching decision

**Scope:** retain the unchanged HRA seven-component export for source inspection; use only the cornea–iris–lens layer-hidden view to teach broad anterior order. **Reject the retained zonular/ciliary geometry for teaching attachment anatomy.** The rejection is a decision, not an unresolved promise to validate every source defect. No replacement GLB or whole-eye reconstruction is proposed.

The source, earlier exports and historical records remain intact. This decision supersedes the historical absolute `sourceMissingStructures`/“source has no” wording, but does not rewrite those records or promote their anatomy/runtime gates. The [original inventory screen](../2026-10-27-source-coverage-r01/README.md) remains useful evidence.

## Provider discrepancy

The [provider README](../../../sources/datasets/hra/eye-male-right-v1.3/HRA-README.md) describes an added long posterior ciliary artery, changed optic nerve, shifted/thinned muscles and rotated inferior oblique muscle. This is repeated in `was_derived_from.description` of the [specific eye-male-right v1.3 metadata](../../../sources/datasets/hra/eye-male-right-v1.3/hra-live-metadata.json), whose `was_derived_from.distributions[0].downloadUrl` is exactly the URL in [source.json](../../../sources/datasets/hra/eye-male-right-v1.3/source.json). It is not merely a generic collection description.

The pinned 20,697,584-byte GLB (SHA-256 `1a6ecc528e98e0bddb8e2905e4ddb799eb471383f7274dbb9bdd1676b06be73b`) has 26 nodes, of which 23 are mesh nodes, with 23 meshes and 21 materials. Its [crosswalk](../../../sources/datasets/hra/eye-male-right-v1.3/crosswalk.csv) names all 23 mesh nodes plus the right-eye group. Two other grouping nodes have no crosswalk rows. Seven mesh nodes are selected and the other 16 excluded; there is no separately named optic nerve, extraocular muscle or long posterior ciliary artery. Optic disc and ciliary muscle names are present. Neither material names nor an optic-disc label establishes an optic-nerve mesh.

**Unresolved distribution/description discrepancy:** the record does not establish whether the description is stale, refers to other geometry, or describes tissue merged into a named mesh. No collection-level explanation or geometric absence is asserted, and no source mesh is relabeled to make the prose fit.

## Claim-to-reference decisions

| Proposed teaching claim | Decision and applicable evidence |
|---|---|
| Cornea is anterior to the iris/pupil opening, with the lens behind the iris. | **Keep broad order only.** [NEI How the Eyes Work](https://www.nei.nih.gov/eye-health-information/healthy-vision/how-eyes-work), first three explanatory paragraphs; [NEI Parts of the Eye](https://www.nei.nih.gov/sites/default/files/2019-06/parts-of-the-eye.pdf), page 2, Cornea/Iris/Lens/Pupil entries. These references establish the relationship; a local image check establishes only that the model displays it. Light goes through the pupil opening, not through the iris tissue. |
| The pale-blue disk is a pupil surface. | **Reject/correct label.** In this export it is the illustratively colored opaque lens seen through the iris opening. The source pupil mesh is excluded. The pupil is an opening, per NEI page 2. |
| Ciliary body, muscle and processes are interchangeable labels. | **Reject.** [NLM MeSH Ciliary Body D002924](https://meshb.nlm.nih.gov/record/ui?ui=D002924), Scope Note, distinguishes the muscle-containing and process-containing portions. HRA node names are source labels, not independent validation of their boundaries or placement. |
| Ciliary muscles affect lens shape through zonules; zonules support the lens. | **Keep as explanatory reference text only.** [NEI glossary](https://www.nei.nih.gov/sites/default/files/nei-pdfs/nei_executive-summary.pdf), printed pages 17–18, Ciliary Muscles and Zonules. This static export does not demonstrate the mechanism. |
| The rods demonstrate normal fiber thickness/count, origin, capsular insertion, branching, or a universal process-tip-to-equator connection. | **Omit from teaching and reject as a demonstrated claim.** No inspected reference validates these mesh endpoints. [Streeten 1977](https://pubmed.ncbi.nlm.nih.gov/844993/), abstract, is original human microscopy describing fibrillar capsular insertion and a surface network, not validation of these rods. Abstract-only evidence; full-text microscopy was not inspected. The source-named geometry is retained only in diagnostic views. |
| The pointed/faceted corneal rim represents normal shape or thickness. | **Reject.** NEI describes a clear dome; the inherited angular silhouette and open boundaries are model limitations. Guarded normal changes affect shading, not the rim geometry. Broad order teaching does not authorize shape measurement. |

References were screened on 2026-10-28. NEI and NLM terminology support broad facts; the original microscopy abstract adds context, not quantitative tolerances. No specialist/clinical approval is claimed.

## Rendering and omitted teaching geometry

The exact export remains [anterior_segment.glb](../../../models/eye_anterior_segment/exports/hra-v1.3-r01/anterior_segment.glb), SHA-256 `457b08b1edab5fc39db3b49e09635091721847e06262b7cb937fd006223c6750`. The reproducible [detail renderer](../../../tests/eye_anterior_segment/detail_review.py) imports it into an empty Blender scene. It makes no geometry, transform or material edits. Full/hidden pairs share camera, projection, scale, lighting and exposure.

The permitted `anterior-order-three-structures` and `corneal-profile-three-structures` images hide the ciliary body, ciliary muscle, ciliary processes and suspensory-ligament nodes. This **omits** unsupported attachment geometry from the teaching image; it does not reconstruct tissue or turn a hidden-layer image into a physical section. Posterior and oblique endpoint views retain the source labels only for diagnostic review. They are not recommended teaching plates.

Opaque lens color, translucent cornea, double-sided surfaces and editorial hiding do not demonstrate physical optics, living-tissue appearance, normal histology, accommodation, surgical anatomy, watertightness or clinical accuracy. The corneal silhouette must not be used for curvature/thickness teaching. The limited three-structure image demonstrates order only.

## Reproduce the focused local checks

With exact existing LFS eye bytes, Python 3.11+, NumPy, Pillow, DejaVu Sans, and Blender 4.3.2:

```sh
python3 -m unittest discover -s tests -p test_eye_source_coverage.py
python3 tests/eye_anterior_segment/verify_source_coverage.py
python3 tests/eye_anterior_segment/replay.py --output /tmp/eye-replay-NEW
blender -b --python tests/eye_anterior_segment/detail_review.py -- --output /tmp/eye-detail-NEW
python3 tests/eye_anterior_segment/verify_detail_review.py --output /tmp/eye-detail-NEW
python3 tests/eye_anterior_segment/make_teaching_plate.py --output /tmp/eye-detail-NEW
```

Output directories must be new. Review all native 1000×1000 PNGs, especially both matched endpoint pairs and both full/three-structure pairs. `render-manifest.json` binds the views to the export and records visibility, camera, settings and pixel-file hashes. The captioned `teaching-order.png` retains every decoded render pixel and explicitly distinguishes the lens from the pupil opening; `teaching-order-grayscale.png` is only a readability diagnostic. Rendering success is not visual or anatomical acceptance. No new export means no new downstream export-runtime claim; the retained GLB's browser-runtime gate stays unverified.

The six synthetic stdlib tests are discovered by existing lean offline CI. Exact payload validation, four-export replay and fresh rendering are local gates, not hosted-CI substitutes. No unrelated full-suite run is required for this bounded decision.


## Observed outcome and delivery

The [scoped decision](decision.json) separates the technical, visual, anatomical and runtime gates. Local Blender 4.3.2 produced nine native views; both reviewers inspected the endpoint detail pairs, anterior views and corrected profiles, plus the captioned color and grayscale teaching plates. The [render receipt](local-render-manifest.json) and [caption receipt](teaching-plate-manifest.json) retain exact hashes and settings.

Posterior and oblique superior-sector details show blunt cylindrical rods, shorter exposed ends in the dark lens-to-process gap, and long rods extending beyond visible process contours. Layer hiding exposes more rod length. These observations do not prove actual tissue detachment or biological insertion; they justify rejecting these images as attachment lessons. The three-structure image improves broad-order reading and its caption corrects the pupil/lens confusion. Corrected profiles include the entire corneal silhouette and retain visible angular poles/rim; shape and thickness claims remain rejected. Grayscale retains distinguishable boundaries, without an accessibility claim.

The first local profile framing cropped a corneal pole. Both profile cameras were widened together and the complete batch rerendered in a new directory. The other seven views retained identical decoded RGB pixels. Original diagnostics were preserved.

**Delivery status:** code, decision and text receipts are in this PR. The eleven PNGs are retained as local review deliverables, not committed as unuploaded LFS pointers or published through a Site. Reproduction commands above produce the full evidence. Parent independent acceptance remains pending; no issue closure, canonical promotion or consumer integration follows automatically.

| Issue #100 acceptance | Bounded result |
|---|---|
| Reproduce inventory and explain mismatch or mark unresolved | Exact 23-mesh inventory and 7/16 partition reproduced; provider-specific discrepancy explicitly unresolved. |
| Map teaching claims to anatomical references | Claim/reference table distinguishes general anatomy, source labels and inspected model appearance. |
| Inspect matched details; correct or omit misleading geometry/labels | Native matched endpoint and profile views reviewed; unsupported ciliary/zonular geometry omitted from teaching views; pupil/lens caption corrected. |
| Explain illustrative materials and cuts; exclude optical/clinical claims | Explicit in the teaching caption and scope; no physiological or surgical use. |
| Separate decisions; preserve source/provenance | Scoped gates recorded; intact source/export/history retained. Parent review pending. |
