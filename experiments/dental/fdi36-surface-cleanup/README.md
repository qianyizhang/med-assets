# FDI36: bounded occlusal-surface cleanup experiment

References #217. **Retained noncanonical experiment; not an accepted intact/restoration baseline.**

Disposition (2026-11-06): preserve this bounded study on main. The larger caries
and cleaning scopes are deferred in the [consolidated dental plan](../../../docs/dental-atlas/PLAN.md);
their issue closure does not mean delivery or validation.

![Original v5 / Updated v6, matched views](evidence/original-updated.png)

## Result

- Repeated scallops were traced to voxel resampling: they appear after a 0.06 mm voxel union before smoothing, while the retained analytic input is smooth. Recomputing imported normals alone does not fix them.
- Reprojecting only the upper crown restores its analytic surface. Local positive ridge controls bound existing basins; a smooth groove-depth combination never exceeds the original maximum depth.
- The repeated corrugation is substantially removed. The continuous crown silhouette is retained, and 315,893 exported triangles wholly below 3.5 mm remain exactly unchanged.
- **Attribution corrected 2026-11-04:** the hard hooked outline and mesial ledge-like contrast are shadow-dependent in matched views, not established construction creases. See the [dated correction](#shadow-attribution-correction-2026-11-04). The high-detail intact baseline for #217 remains unaccepted.

![Matched occlusal detail with overview locator](evidence/occlusal-detail.png)

Markers identify authored regions, not validated anatomy. These are actual clean GLB reimports, not generated reference images. The colours are illustrative; the material boundary is not a validated histological CEJ.

## Shadow attribution correction (2026-11-04)

A later lighting-control inspection used the exact unchanged updated GLB bound in `review.json`. Toggling only Workbench cast shadows removes the hard hooked outline and ledge-like contrast in matched occlusal-detail and three-quarter views, with cavity rendering still enabled. Coordinates, vertex/corner normals, connectivity and material assignments remain identical. An independent replay reproduced all four diagnostic image arrays and the unchanged mesh/normal/topology/material signature.

The shadow-on decoded pixels exactly match the earlier native views; the PNG container bytes differ. The original images are retained, not replaced by the shadow-off views. The underlying groove/ridge form remains, and this test does not prove every surface derivative is smooth.

The `gates.visual.scope` text in `review.json` records the original interpretation: “Hooked central junction and mesial ledge remain.” Its implication of an established geometry defect is superseded by this dated attribution correction only. That historical review, `replay-result.json`, recipes and evidence bytes remain unchanged. No v7 geometry was built or is justified by this symptom. Anatomy/reference and runtime acceptance remain separate and unmet; this is not a baseline pass. Any further morphology change needs a specific defect supported by neutral/reference views or direct geometry evidence, rather than this cast-shadow outline alone.

## Scope and source

This is original educational geometry, not a scan or patient model. [Oral Facial Anatomy Online](https://ecampusontario.pressbooks.pub/oralfacialonline/chapter/tooth-morphology-part-a/) and [Wheeler's indexed mandibular-molar chapter](https://elsevier-elibrary.com/contents/fullcontent/59012/epubcontent_v2/OEBPS/B978141606209700012X.htm) supplied qualitative cusp/root and ridge/fossa relationships. Every numerical dimension, contour and local field is authored. No source images or third-party code were copied; their licences are not inherited by this geometry. No new repository-wide or third-party asset licence is inferred here.

No lesion, prepared state, restoration, internal tissue, clinical guidance, canonical registration or new external hosting is included. Editable masters and unsuccessful trials stay private. Generated baseline/updated files are ignored by Git; the PR contains recipes, checks and retained review evidence only.

## Replay

Prerequisites: Blender 4.3.2 with bundled NumPy. The ordinary offline field tests require only Python's standard library. Run from this experiment directory and use fresh output directories:

    blender -b -t 8 --python-exit-code 1 --python build_baseline.py -- baseline
    blender -b -t 8 --python-exit-code 1 --python revise_surface.py -- updated
    blender -b -t 8 --python-exit-code 1 --python verify_render.py -- updated
    blender -b -t 4 --python-exit-code 1 --python verify_exports.py
    blender -b -t 4 --python-exit-code 1 --python verify_source_guard.py

The revision re-exports the loaded baseline master and checks its complete GLB hash, binding transforms, materials, normals and semantic nodes as well as decoded geometry. It does not require the `.blend` container hash, which can vary between equivalent builds. It preserves all X/Y coordinates and all lower vertices. It rejects an existing output directory and a mismatched source.

From the repository root:

    python3 -m unittest discover -s tests -p 'test_fdi36_surface_fields.py' -v
    python3 tools/verify.py offline

The five focused tests check field bounds, absence of a second depression field, named ridge controls, preservation assertions and source/output guards. They are not anatomical tests. The full repository offline gate must run on the publisher's reconciled commit; no CI or security configuration is changed.

## Evidence and retention

`review.json` binds the exact baseline/updated GLBs and two matched images. The update has 446,904 triangles and 10,747,776 bytes. Finite/unit normals, positive areas/volume, connected closed welded-copy topology and decoded export/reimport checks pass. The rendered import is untouched; topology welding happens only on a disposable copy.

The two images are retained because they provide independent whole-context and close-up evidence of this visible change. They use the repository's existing PNG/LFS rules. No new Blob/Site transport is introduced. Preserve their bytes when publishing; do not substitute pointer text for an image upload.

Offline technical and limited visual review do not establish anatomical, clinical, bite/occlusion or runtime acceptance. Runtime remains unverified. The bounded study is retained independently of the deferred production outcomes in the plan. #217 is closed by consolidation, not by accepting this experiment as its baseline.
