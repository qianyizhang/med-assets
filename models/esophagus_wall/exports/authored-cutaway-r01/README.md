# Esophageal wall — illustrative longitudinal cutaway r01

## Useful improvement
A short, open wedge segment exposes the folded luminal surface and the ordered wall compartments, instead of adding cosmetic texture to the smooth full-organ tube. Five individually named GLB meshes represent **four tunics**: mucosa, submucosa, muscularis externa (inner circular and outer longitudinal compartments), and adventitia. This is an educational supplement, **not a replacement of the original full-organ asset or its animation**.

The sibling canonical review folder contains `teaching-sheet.png` (English), `teaching-sheet-zh-CN.png` (Chinese), and one exact-reimport `oblique.png`. `esophagus-wall-cutaway-r01.glb` is the exact rendered 3D model. Portable generators and parameters in `tests/esophagus_wall/` reproduce the editable Blender scene and renders; redundant native scenes are not duplicated here. All three raw views were reproduced during verification; the retained oblique image and bilingual sheets were made after clearing the Blender scene and reimporting the exported GLB, not by rendering a different native mesh.

## Anatomical content and omissions
- The mucosa is deliberately one composite compartment. Its non-keratinized stratified squamous epithelium, lamina propria, and muscularis mucosae are **not separately resolved**. The broad luminal folds are a schematic cue, not a measured count or patient-specific lumen shape.
- Submucosa is a separate compartment; its glands, vessels and submucosal plexus are omitted.
- Muscularis externa is split into inner circular and outer longitudinal compartments. The names indicate typical fiber orientation; individual fibers and the myenteric plexus are not modeled. Muscle composition varies along the organ and is not encoded here.
- Adventitia is the illustrative thoracic outer coat. This is not a model of the abdominal serosal covering or gastroesophageal junction.
- Ends and the 90-degree longitudinal wedge are editorial cuts, not wounds or native anatomy. The model contains neither a sphincter nor a physiological opening/closing mechanism.

**All thickness ratios, six-fold lumen, segment length, colors, and cut geometry are explanatory choices—not measured histology.** No quantification of tissue dimensions, clinical interpretation, pathology, or peristalsis is supported. No whole-organ anatomy or browser-runtime pass follows from technical checks.

## Source verification
Primary teaching collections consulted 2026-10-25:
1. Columbia University, Human Histology Laboratory, [Gastrointestinal System I](https://histologylab.ctl.columbia.edu/lab16/): validates the four-coat sequence and inner-circular/outer-longitudinal muscle arrangement.
2. Columbia University, [Esophagus, human slides 32 and 33](https://histologylab.ctl.columbia.edu/lab16/esophagus/): validates human mucosal components and regional muscle-type variation. The model does not attempt that cellular detail.
3. Brelje & Sorenson, Medical Histology Collection, [MH 109 Esophagus](https://histopathology.pennstatehealth.net/slideview/MH-109-esophagus/14-slide-1.html): confirms the same mucosal, submucosal and muscular compartments on a human histology specimen. That specimen lacks adventitia; the outer layer is supported by the general wall-organization reference, not inferred from an absent specimen layer.

No histology images, slide tiles, diagrams, proprietary textures or copied source meshes are embedded. The geometry is independently authored from analytic functions, not segmented from those references. No third-party license is applied to this independently authored geometry, and no new public reuse license is granted by this package. Authorized public storage or publication is distinct from a reuse license grant. Reference websites retain their rights.

## Relation to baseline and source experiments
The unchanged original [authored baseline](https://heart-anatomy-imaging-lab.landy123007.chatgpt.site/body/3d/assets/drafts/pelvis/esophagus.glb) has SHA-256 `3ee499bbc94fc91a1b0d5b74e92b91f9293bfb523f9118302a1c524b6b08a24c`. It includes the muscular tube, two lumen-end cues, and passive respiratory support animation (not peristalsis). All remain unchanged in that original file. The new cutaway is static and independent, not aligned to the baseline or inserted into its motion rig.

An alternative smooth exterior study did not materially improve teaching detail and was not advanced. This cutaway instead exposes useful compartment organization. **No Z-Anatomy geometry is included.** The discarded experiments are intentionally excluded from this lean delivery.

## Reproduce / verify
```
python tests/esophagus_wall/replay.py --output /path/to/NEW-output-directory
# Optional explanatory proportions (never measured anatomy):
python tests/esophagus_wall/replay.py --params tests/esophagus_wall/parameters.json --output /path/to/another-NEW-directory
```
Blender 4.3.2, Cycles CPU, 96 samples, fixed seed 17, no denoising. The review receipts bind exact GLB SHA-256 and record per-layer finite/positive-volume checks and **1e-8 m tolerance-weld edge diagnostics**, not exact-index topology or manifold proof. Closed solids describe model compartments, not tissue impermeability or a biological lumen validation.

The replay refuses an existing output directory. Dependencies: Blender 4.3.2, Python 3, Pillow, DejaVu Sans and Noto Sans CJK fonts. `parameters.json` exposes illustrative dimensions/folds/wedge and is validated for positive nested layers. The default parameters reproduce the reviewed GLB byte-for-byte. Changing parameters creates a new unreviewed teaching variant, not a validated anatomy model.

Coverage accounting: **0 additional whole organs**. This is an approved teaching supplement. PNG metadata was stripped without changing decoded pixels; original hashes are retained in `png-metadata-receipt.json` in the review directory.
