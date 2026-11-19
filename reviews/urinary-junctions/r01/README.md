# Urinary junctions · 19 November 2026

Restore the local screenshots from the [body-systems teaching backup](../../../sites/body-systems-survey/README.md#restore-the-media).

[Assembly, exact inputs, coordinates and replay](../../../assemblies/urinary-junctions/r01/README.md). GLB SHA-256 `637ebe6bec902bf933c1c9ba2ab77a7cec0ef3bf58bbea6047c26665a40e5ead`. Editable BLEND `69979f136547d119d688a64f7913dc492f7b6c5a86794c6074e65f5cae17e238`. The [render receipt](renders.json) binds all 14 images, visible parts, matched scales and camera axes to this export.

| Inspect | Isometric | Straight |
|---|---|---|
| Both kidney sections, ureters, bladder and filter inset | [Overview](overview-iso.png) | [Anterior](overview-ortho.png) |
| Left pelvis and proximal ureter | [Left](left-renal-iso.png) | [Anterior](left-renal-ortho.png) |
| Right pelvis and proximal ureter | [Right](right-renal-iso.png) | [Anterior](right-renal-ortho.png) |
| Left ureter meeting the trigone | [Left](left-vesical-iso.png) | [Anterior](left-vesical-ortho.png) |
| Right ureter meeting the trigone | [Right](right-vesical-iso.png) | [Anterior](right-vesical-ortho.png) |
| Bladder neck and urethral outlet | [Outlet](outlet-iso.png) | [Anterior](outlet-ortho.png) |
| Capillary tuft, capsule and proximal tubule | [Filtration](filtration-iso.png) | [Anterior](filtration-ortho.png) |

**Technical.** Two fresh builds yielded byte-identical GLBs. Clean import recovered 58 meshes. Ten junction checks sampled both exported surfaces, including four junctions independently per side and the two shared outlet connections. Maximum surface deviation at the ten anchor centres was 1.50 × 10⁻⁸ m against a 0.05 mm tolerance. Moving the right distal ureter 4 mm produced a 2.29 mm miss at the lower-course junction and was rejected.

**Visual.** The straight overview separates both kidney sections, their ureters, and the two bladder entries. Toggling the named section removes occlusion at the trigone. The supplementary plots fit only the selected neighbouring segments to distinguish small connections. The source and authored tube ends retain visible seams where their inclinations and radii change. The capillary tuft and proximal tubule are discernible in both inset angles.

**Anatomy.** Gross route and filter concept reference-screened. The sections and directed overlays illustrate route order. The filtration barrier, capillary fenestrations and measured filtration or urine flow are outside scope. The joins establish local geometric contact, without proof of a continuous open lumen. No specialist/clinical validation.

**Runtime.** Local Blender import and CPU rendering passed. Live viewer behaviour and performance are unverified.
