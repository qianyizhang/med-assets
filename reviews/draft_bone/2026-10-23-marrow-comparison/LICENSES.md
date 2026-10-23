# Attribution and reuse

## A. BodyParts3D exterior and teaching derivative

**BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International.**

- Official dataset license: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html (updated 2025-02-27); retained snapshot: `licenses/bodyparts3d-official-license-snapshot.html`.
- License terms: https://creativecommons.org/licenses/by/4.0/
- Raw source: BodyParts3D 4.0, FJ3365 / FMA24474 / BP10053 (right femur), from https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/partof_BP3D_4.0_obj_99.zip . Individual unchanged OBJ retained in `sources/BP3D-FJ3365.obj`.
- Raw OBJ's historic CC BY-SA 2.1 Japan header is preserved, not erased. Current official database license explicitly provides CC BY 4.0; the retained source snapshot documents that distinction.
- Full-exterior derivative changes: mm→m and standard glTF axis conversion, neutral material.
- Container changes: proximal crop, longitudinal section, exact-coordinate duplicate seam remap in derivative only, authored 2.5 mm inward wall/cut rim, display materials/normals. Inner geometry is illustrative and not measured anatomy. Source-derived teaching derivative packaged under CC BY 4.0 with source attribution and change notice.

## B. Independent measured trabecular reference

**Kuczynski, M. (2024). MicroCT Trabecular Bone Samples for Trabecular Thickness and Separation Measures (v1). Zenodo. https://doi.org/10.5281/zenodo.11061947 . CC BY 4.0.**

- Creator affiliation: University of Calgary. License terms: https://creativecommons.org/licenses/by/4.0/
- Direct record API metadata explicitly states `license.id = cc-by-4.0`: `sources/zenodo-record-11061947.json`.
- Selected file: `BMLPL_001_REF_17_SEG_SUB.nii`; publisher MD5 checked. The [ORMIR community listing](https://www.ormir.org/datasets.html) identifies the dataset as human trabecular bone; specific bone site and donor status are not established.
- Changes: midpoint isosurface of binary segmentation (VTK FlyingEdges3D, level 63.5 between labels 0 and 127), mm→m, neutral shading. No smoothing/decimation, component removal, boundary filling, anatomical registration or geometric synthesis. Smooth normals affect shading only.
- Source record states 17.59 µm; actual NIfTI header is ~17.409 µm. Unchanged header spacing used for visible scale bars. Do not describe those bars as independently calibrated.

## Composition and limitations

Attribution and source-specific caveats must travel with each model or panel. Neither source endorses this teaching composition. The models are independent, not a registered assembly or subject-specific reconstruction. No segmented marrow tissue is present. No clinical validation, anatomy pass or intended-consumer runtime pass is claimed. This bounded static comparison was reviewer-inspected; no anatomy/runtime approval follows. Original marrow model remains Needs revision.
