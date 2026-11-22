---
description: Reconcile Library file discovery and exact revisions before starting a small assessment pilot.
scope: backlog item
status: stable
last_update: 2026-11-21
document_class: work_record
work_id: AG-GAL-018
work_status: done
work_kind: build
added: 2026-11-21
tags: gallery, evidence
depends_on: AG-GAL-013
residual_of: none
residual_items: none
---

# AG-GAL-018 — Reconcile Library revisions before rating

## Acceptance criteria

- [x] Reconcile tracked geometry paths with the dated survey and ordinary local Library. Account for source inputs, native deliverables, historical records and known unavailable exports.
- [x] Give each public revision a discoverable Library history entry or parent export. Verify the route and exact identity, including explicit unavailable entries. Consolidate duplicate discovery labels through the existing family routes.
- [x] Bind three to five supported assessments to the exact revisions and [rubric](../../../docs/guides/asset-quality.md). Preserve prior judgments and leave unsupported axes Unrated.
- [x] Rank simplification candidates against retained views and consumers. Propose one measured trial.

## Discovery audit before reconciliation

The table compares Git tree `a93f7b6`, the [frozen Survey](../../../sites/anatomy-gallery/README.md) and a normal Gallery build isolated from AG-GAL-016/017. Count Git paths using LFS pointer OID and size or ordinary blob SHA-256 and size. The delivery declarations agree for all 162 paths. The Library column counts file links reached from normal browsing, including revision links. Chrome verified actual bytes for representative GLBs and all newly listed files.

| Format | Git paths / unique digests | Survey inventory / model and product media | Library files before → after |
| --- | ---: | ---: | ---: |
| GLB | 146 / 146 | 141 / 129 | 135 → 135 |
| STL | 10 / 10 | 0 / 0 | 0 → 10 |
| Blender | 5 / 5 | 0 / 0 | 0 → 5 |
| OBJ | 1 / 1 | 0 / 0 | 0 → 0 |

- **GLB reconciliation.** The 129 survey-row files cover family, assembly and product downloads. The other 12 in the survey inventory are ten HRA source GLBs, the pinned [ulnar v1 replay input](../../../models/peripheral_nerves/recipes/ulnar-elbow-r01/README.md) and the [FDI31 interface-locked candidate](../../../reviews/swirendo_fdi31/2026-10-27-interface-locked/README.md). The ten HRA inputs belong to `sources/datasets/hra/` for eye, left/right kidney, four ovary/tubal segments, placenta, prostate-context bladder and uterus. The marrow [BP3D OBJ](../../../sources/datasets/marrow-comparison-v1/) is also an input. Their teaching derivatives carry the public entries. The interface-locked candidate is accessible from the FDI31 family’s history and Compare. The five post-survey GLBs are the distinct s1233 adrenal r03/r04/r05 assembly variants, the seated nail r02 and terminal airspaces r02, all already present in Library.
- **Portable and native deliverables.** Static Cardiac Atlas now lists its ten ED RAS-mm STLs and native rig. Anatomy Workshop, Breathing, animated Cardiac Atlas and the blood-cell study each list their one editable Blender delivery. The added files enter the existing search and **All indexed files** disclosure. The adrenal lineage also matches searches for its three export paths.
- **Path, lineage and revision counts.** The baseline has no tracked byte aliases in these four formats. The older Workshop source-copy aliases of the static cardiac inputs were already consolidated. The two UFF cards (`dental_specimens` and `uff_tomo1b`) point to one export and source lineage. The BodyParts3D adrenal pair and s1233 regional assembly are different lineages. The 99 visible rows are 62 dated families, 31 dated products, and six overlay rows. Some products group multiple assets or are recipe-only, lesson or diagram entries. Of the 135 linked tracked GLBs, 32 have a named revision page or a single-export reviewed entry. One revision can have multiple files, such as trachea r06 or salivary r02. The two legacy dental-tool GLBs are additional exact local Library links backed by the legacy cache and outside the 146 tracked paths.
- **Unavailable and restricted.** The historical [prepared FDI31 r03](AG-GAL-015-verify-static-reviews.md#review-follow-up--recovery-and-compaction) has a Library revision with the expected digest and an availability note. The separate [fitted animated heart](../../../reviews/heart_exterior/2026-10-30-native-visibility-r01/provenance-and-applicability.md) has a known hash and size in its owner record but no Library unavailable revision. The repository-source animation is a different export. FDI31/46 pilot records and the noncanonical [FDI36 experiment](../../../experiments/dental/fdi36-surface-cleanup/README.md) have no corresponding export in this tree. The [fetal study](../../../models/fetus/exports/head-face-junction-r01/README.md) explicitly keeps its original, candidate and images private. Its recipe record may remain visible. The [blood-cell reference exclusion](../../../models/blood_cell_study/source/PROVENANCE.md) applies to restricted reference pixels and the public Blender delivery excludes them.

**Gap at the audit revision.** Of the linked GLBs, 103 appeared only in grouped file lists. Those groups contained 65 model exports, 29 Body exports, eight Heart exports and one hypothalamus–pituitary assembly. This included all 17 metadata-cleanup exports. The bronchial metadata-cleanup path led to its family download, while the FDI31 interface candidate had a history page that path search missed. The STL and Blender files also needed links to their owning deliveries.

## Reconciled Library

The discovery denominator is the Git tree at `e8399bd107cc6129db2d3712113e9cb5a3628664`. **All 135 publicly listable tracked GLBs, 10 STLs and five editable Blender deliveries** resolve to an exact revision or their owning package delivery in the ordinary Library. The [browser verifier](../../../sites/anatomy-gallery/tools/verify_library.mjs) records each path, route, size and digest. It walks the revision links from normal Library rows and searches each public path in the rendered product.

- Model revision names and exact identities come from the frozen Survey export paths, delivery declarations and their owning records. Existing review and recommendation routes keep their original scope. The 17 metadata-only alternatives show their own identities and evidence separately from Workshop, Breathing and other model revisions.
- The Workshop and Breathing histories group the individual GLBs with the editable scenes under their original package deliveries. Static Cardiac Atlas groups three ED GLBs, ten RAS-mm STLs and the native scene. Animated Cardiac Atlas groups the three authored variants with their editable source. The blood-cell Blender file belongs to authored r05. Opaque exterior derivatives have separate records for the Workshop and repository-animation inputs.
- UFF has one discovery entry. `dental_specimens` remains a searchable alias and the old Library bookmark opens `uff_tomo1b/r01`. The two legacy tool GLBs remain searchable by history and are outside the Git denominator.
- The fitted Site animation record shows its exact 8,180,452-byte identity and the provenance for its unavailable state. Historical prepared FDI31 r03 also shows its expected identity. Fetal study, FDI36 and other record-only entries expose their evidence without a model download.
- The ten HRA GLBs, marrow OBJ and ulnar v1 GLB are the 12 documented source or replay inputs. Their scoped teaching derivatives supply the Library records. The parallel [AG-GAL-019 trial](AG-GAL-019-repack-static-heart-exterior.md) generated `static-opaque-exterior-repacked.glb` in its own ignored directory. That candidate is outside the pinned tree and this census. The original was the Gallery export at this baseline. See [AG-GAL-020](AG-GAL-020-adopt-static-heart-repack.md) for subsequent local adoption.

## Teaching assessment pilot

The three original assessment records in local commit `f58366f` bind every score to an exact export, task, source and reviewed views with their digests. Codex assessed them on 2026-11-21 against rubric revision `a1115de`. These are teaching-task judgments. The owner’s previous recommendations and specialist, runtime and delivery status remain attributable to their existing records.

| Exact export | Fidelity | Form | Readability | Economy | Teaching total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ovary–tubal context r01 | 4 | Unrated | 3 | 3 | Partially rated |
| Bronchial central fairing r13 | 4 | 2 | 3 | 2 | 11/16 |
| Esophageal wall cutaway r01 | 3 | Unrated | 3 | 3 | Partially rated |

The ovary locator retains the fine fimbrial fringe and a visible gap from each ovary. The ten source meshes preserve the bilateral relationship, with most triangles spent on the two tubal arcs. The longitudinal wedge exposes the folded lumen and four tunics. Five selectable shells keep both muscle compartments identifiable. The muted outer bands still need the leader. At the pilot, both exports needed a matched neutral close view for a form score. The ovary locator also needed a suitable surface reference for its coarse source shape. [AG-GAL-022](AG-GAL-022-complete-form-assessments.md) records the later review.

The original form observations from Codex (agent review), 2026-11-21, are retained here with the pilot:

- **Ovary–tubal context r01** · “The side details show the thin fringe and cut ends. Evidence for a form score still needs a matched neutral close view and a reference for the coarsely modeled surface.”
- **Esophageal wall cutaway r01** · “The oblique and transverse views show the fold and wedge edges. A matched neutral-material close view of the folded lumen and thin outer rim is missing.”

To read the full original data from this checkout, run

```sh
git show f58366fb0fb7ab5927603e0c7076287b68d0386e:reviews/teaching-assessments/2026-11-21-library-pilot/assessments.json
```

The r13 bronchial fork reads in the overview and both neutral close directions, but the underside remains angular. The fidelity score measures preservation of the authored r09 geometry and protected termini for the stated task. The same-scope mesh has 443,892 triangles, and the pilot had no same-scope lighter geometry. The [later distal trial](AG-GAL-021-simplify-bronchial-distal-sampling.md) measured the tradeoff at teaching zoom. The three assessments cover teaching tasks. Specialist judgments, clinical gates and release recommendations are recorded with their original owners.

## Ranked simplification candidates

| Rank | Evidence and cost | Next action |
| --- | --- | --- |
| 1. Static opaque heart exterior packaging | The [matched close view](../../../reviews/heart_exterior/2026-10-30-native-visibility-r01/images/updated-static-seam-front.png) needs the retained 124 exterior objects, including vessel rims and exposed seam geometry. The 8,951,936-byte [static derivative](../../../heart/exterior-presentation-r01/README.md) has 389 mesh definitions and 152,216 displayed triangles. Of its BIN data, 5,335,492 bytes are in buffer views unreachable from the exported scene. The sibling animation retains another 2,450,800 unreachable bytes. Those bytes have no visible or selectable role in either opaque view. | [Completed static trial](AG-GAL-019-repack-static-heart-exterior.md). The candidate saves 5,543,680 bytes and retains all 124 selectable objects. Decoded scene data and pixels in both matched views agree. [Local adoption and retained r01 delivery](AG-GAL-020-adopt-static-heart-repack.md) followed. |
| 2. Bronchial r13 hierarchy and junction | The [closest r13 view](../../../reviews/bronchial_tree/2026-10-26-authored-central-fairing-r13/evidence/after-close.png) shows the central bifurcation where sampling and highlights matter. r07, r09 and r13 use 443,892 triangles each, one mesh and one primitive, at about 10.66 MB each. R13 changes a local dimple while preserving connectivity. The much smaller 15,088-triangle metadata cleanup has 23 selectable meshes and represents a different authored branch assembly. | Keep r07 and r09 in history. [R09 replay](../../../reviews/bronchial_tree/2026-10-26-authored-lobar-fairing-r09/source-binding.json) uses exact r07, and [r13](../../../models/bronchial_tree/exports/authored-central-fairing-r13/README.md) uses exact r09. Both historical exports also serve current local Compare records. The [completed trial](AG-GAL-021-simplify-bronchial-distal-sampling.md) saved 30.5% of triangles. All 16 terminal neighborhoods and the central Y retained their geometry. The worst silhouette shift was 1.41 pixels at a distal crossing. [AG-GAL-023](AG-GAL-023-adopt-bronchial-distal-sampling.md) adopts the lighter export for first-fork teaching locally and retains r13 as the assessed control. |
| 3. Bronchial r07 reference copy and respiratory replay paths | R07 hashes a 225-line [historical Workshop generator copy](../../../models/bronchial_tree/recipes/authored-junction-repair-r07/README.md) with one line differing from the current Workshop source. Replay guards the copy but never executes it. The Breathing replay had hard-coded authoring paths. | Prove the archived generator digest is independently recoverable before moving that one guard out of the executable dependency list. Require byte-identical r07 from the existing baseline. [AG-GAL-024](AG-GAL-024-retire-builds-and-replay-breathing.md#breathing-replay) made the Breathing recipe portable and verified it against the delivered clips and assembly. |

The rejected thyroid V1 was already retired after the wrong-face weighting and weak visual comparison. The [thyroid review](../../../reviews/thyroid_ct_s0189/2026-10-29-illustrative-exterior-r01/README.md) records its disposition. No active local Library or lesson download was found for it.

The [terminal airspaces r02 section](../../../reviews/body-systems/2026-11-20-surface-quality/README.md#terminal-airspaces) is a counterexample. It spends 8,396 triangles where the earlier 6,734-triangle study had eleven disconnected objects. In the labeled grayscale section the shared septum and pocket openings distinguish the continuous route. The new export retains four selectable regions. It already saves 40.0% against the higher-sampled trial of the same design, with at least 99.86% silhouette overlap in both recorded views. Keep this measured detail and its existing rating. In the [animated heart variants](../../../heart/Cardiac_Atlas_Animated/README.md), tissue and clinical full views both use 222,336 triangles. The tissue variant adds three active maps totaling 6,475,939 bytes for a materials-specific view. The clinical colors already convey circulation categories.

## Historical verification receipt

The isolated build used the Gallery overlay at `a93f7b6` plus the Library patch. The frozen seed matched SHA-256 `340b64f3bd3b13835e16d29c9bcb415265d6be5fbf8195564c9c349390bc4499`. The tested HTML SHA-256 was `e68318da509c1fa589cd7f3296fe13d5a439eff94bc26a90252da30ad0bc1454`. Chrome traversed 99 Library rows and 122 row/history routes, checked the unavailable FDI31 export and verified exact responses for all 15 added files and five sample GLBs. A wrong asset identity returned 404. The full Gallery browser regression, protected runtime build, 13 Gallery tests and required offline gate passed. Measurements count scene-reachable buffer views in the actual hydrated GLBs. Runtime performance remains unmeasured. Local receipts are under `.artifacts/AG-GAL-018-library-audit/`.

The [Breathing guide](../../../body/breathing/README.md) links the delivered clips, Workshop inputs and portable recipe. The [Cardiac Atlas guide](../../../heart/Cardiac_Atlas/docs/README.md#actual-uv-and-baked-texture-deliverables) retains its original render paths. The [Gallery package guide](../../../sites/anatomy-gallery/README.md#files-in-the-imported-atlas-packages) links both current deliveries and the diagnostic evidence.

The [Airway ledger](AG-GAL-013-reconcile-gallery-coverage.md#airway-review) reconciles all nine frozen exports, including the r07 and r09 studies. That audit preceded the assessment pilot. An unassessed axis stays Unrated and a teaching total requires all four axes.


## Local delivery and verification

The implementation commit is `f58366fb0fb7ab5927603e0c7076287b68d0386e`. The independently generated build used Node 24.21.0 and the protected Gallery runtime. The frozen seed SHA-256 is `340b64f3bd3b13835e16d29c9bcb415265d6be5fbf8195564c9c349390bc4499`. The browser-tested HTML SHA-256 is `71321242c32f7284d917c59229d097ffd9696a4a3d02bdfc34c54ed6bf23f121`.

- Chrome 157 traversed 98 Library rows and 101 revision or parent routes. It matched 20 download responses, including all STL and Blender files, and saved the selected metadata-cleanup GLB with its expected digest. It exercised full-path search, history navigation, Back, sharing and reload, the UFF alias and both unavailable revisions.
- Chrome verified the three assessment profiles, Rated and Unrated filters, score ordering, date and rubric attribution, pinned source links, and the bytes of every linked reviewed view. The r09 bronchial sibling stayed Unrated. Assessment layouts at 1024 and 1280 pixels retained the portrait proportions. The full Gallery journey and Static Reviews checks passed, including legacy FDI31 verified downloads and 182 Compare media identities.
- The protected build and 13 Site tests passed. The loopback recovery test passed. A wrong assessment export or view digest was rejected during assembly.
- The repository offline gate passed 440 tests. Payload integrity matched 998 local LFS files totaling 992,668,959 bytes, 25 foundation records and 11 package checks.

Local receipts and captures are under `.artifacts/AG-GAL-018-library-revisions/`. Public cutover remains with the [collection ledger](AG-GAL-013-reconcile-gallery-coverage.md#collection-ledger). [AG-GAL-014](AG-GAL-014-compact-delivery-and-recovery.md) tracks the two legacy Airway downloads.
