# Bone context and trabecular architecture: independent comparison

A limited reviewer-inspected **static comparative teaching supplement**, not a completed marrow replacement. Original marrow remains Needs revision; accepted-study count does not increase.

- BP3D right-femur exterior is preserved separately. The proximal container adds an **authored 2.5 mm inner boundary/rim**, not measured cortex or marrow.
- Independent measured-reference surface comes from **segmented bone**, not marrow. Do not attach, tile or enlarge it into the femur.
- Two final native PNG panels are separate: **no registration or shared scale**.
- Header spacing is ~17.409 µm; record prose says 17.59 µm. Discrepancy unresolved; bars are header-derived, not independently calibrated.
- Bone site, donor age/health and anatomical orientation are unknown. No anatomy or browser-runtime pass.

## Sources and rights
Original small BP3D OBJ and public Zenodo NIfTI are included. Geometry/render change notices and CC BY 4.0 attribution are in `reviews/draft_bone/2026-10-23-marrow-comparison/LICENSES.md`; historical BP3D source header is preserved.

Independent dataset: **Kuczynski, Michael (2024), University of Calgary**, DOI https://doi.org/10.5281/zenodo.11061947 . Exact selected file `BMLPL_001_REF_17_SEG_SUB.nii`, SHA `b52e275cb5e56b58393626fcaf6d81b1ae9b1fd039d20db09f38a60b0db3ff7c`; publisher MD5 verified. This is original public segmented-bone data, not a newly sanitized derivative. Empty free-text header fields and no extensions were independently checked.

## Verification and replay boundary
```
python tests/marrow_comparison/verify_bounded_receipt.py
python tests/marrow_comparison/prepare_replay.py --output /new/replay-directory
```
The second command only copies supplied inputs/scripts into a new workspace; it does not execute Blender/VTK. From that workspace, `python tools/check_models.py` reruns limited structural checks; `python tools/extract_reference.py` needs VTK/NumPy and reconstructs unsmoothed PLY; `blender -b --disable-autoexec -P tools/replay_container.py` reconstructs the illustrative container method. Scientific software must already be available. No automatic network fetch/install.

No promise of byte-identical GLBs across versions or final-panel re-rendering: native source render inputs/full failed history are deferred. Exact two final panel PNGs and source-specific measurements are retained.

**Lesson:** connected planar loops can still read as brackets. Real source structure supports comparison but does not establish source site, segmented marrow or specimen registration.
