# Source-qualified molar root/support teaching segment

Related issue: #180. Private PR candidate; no publication or clinical promotion.

![Selected source location](media/locator.png)
![Root support](media/detail-plate.png)

## Scope
- Teeth 35–37, root shape, neighbouring teeth, cortical and inner-bone context.
- Separate orange synthetic-PDL view; shells retain original positions.
- Flat blue/rose cut faces are editorial display planes, not anatomical surfaces.
- Inner bone is a volume, without trabecular microstructure. Crown relief is not suitable for restorative/caries teaching. No internal enamel/dentin/pulp, gingiva or nerves are added.

## Source and attribution
Cristian Diaz, Carlos Andres Ferro Sanchez, Oscar Campo. *Data of synthetic 3D models of the human jaw, including teeth, ligaments, and bone structures*, v1, 2024-09-12.
Primary dataset: https://data.mendeley.com/datasets/xjsx7nfhj8/1 . DOI: https://doi.org/10.17632/xjsx7nfhj8.1 . CC BY 4.0 as stated on the primary page; no embedded licence file was found in the ZIP. This derivative crops bone and assigns illustrative materials. Original source labels and registration are retained, not clinically validated.

Original ZIP: Human Lower Jaw Dataset.zip, 109558383 bytes, SHA256 902e50c488e8c09bda23bfa6f1d01d5e0ed5528e2738731c2199270ad232e87a. STL units inferred from paired IGES headers: scale1, MM. One common mm-to-m conversion; no per-object repositioning. PDL nominal0.25mm is author-modelled, not measured tissue thickness.

## Delivery and retention
Two final GLBs serve distinct views: molar/root support and unmoved opaque PDL shells. Four images provide whole-jaw location, final detail, PDL view and matched V2/V3 comparison. No source or historical derivative is overwritten. Full source ZIP, source masters, V1/V2, failed exports and investigation history remain preserved in the private recovery archive; they are not duplicated into this bounded package. Source inventory pins every used STL. No catalog or live consumer promotion is included.

## Evidence and limits
Final V3: finite GLB data, valid indices and clean reimport topology passed. Tooth/PDL/cortical decoded geometry matches reviewed V2. Independent review accepted final detail, occlusal and PDL views. SHA identities in package-manifest.json bind the exact retained files; original review-record.json remains unchanged.

Exact Boolean trials failed on inner bone; FAST on untouched source gave a closed crop. Initial export had1degenerate triangle; explicit triangulation fixed it. Rejected trial identities are preserved in the recovery archive. Numerical agreement with an independent crop is a cross-check, not clinical proof.

Anatomy/clinical and live WebGL are unverified. Repo offline verification is separate from artifact-byte checks; hosted CI has not run for this private package. The previous browser denial is not retried. This package does not close #180 automatically.

## Replay
Use Blender4.3.2 and the independently verified extracted source archive. Replay.py refuses an existing output directory:

    blender -b --python replay.py -- --source /path/to/Human\ Lower\ Jaw\ Dataset --output /path/to/new-replay

This portable wrapper pins all8source hashes/sizes before output creation and changes source/output path selection from the retained V3 build recipe. Export/renders are unchanged. A portable-wrapper replay has not been rerun; existing exact-V3 export/reimport evidence is retained, not rebranded as a new replay pass. Run `python3 verify_package.py` to verify delivered bytes and all GLB primitives. Replaying requires inspecting actual renders separately.
