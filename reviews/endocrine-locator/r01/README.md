# Endocrine locator review

Restore the local screenshots from the [body-systems teaching backup](../../../sites/body-systems-survey/README.md#restore-the-media).

[Editable source, model, references and replay](../../../assemblies/endocrine-locator/r01/README.md). The GLB is 1,792,144 bytes, SHA-256 `bf7f9d786f354b9c4e9fb73fc63265752a27033371f8fb19353d7a1b4d951469`. The 1,040,277-byte BLEND is `e9716f1c2e5ae727691274723aa8909c9b4fd9eca16a1a2fdb635ecb45a70dc8`. The [render receipt](renders.json) binds every screenshot to this GLB, identifies visible structures and reports the matched camera scale for each pair.

| Structure or relationship | Straight | Isometric |
|---|---|---|
| Head to pelvis, with islet and male gonad insets | [Anterior](overview-ortho.png) | [Overview](overview-iso.png) |
| Hypothalamic TRH, pituitary TSH and thyroid target | [Axis](thyroid-axis-ortho.png) | [Arrows and target](thyroid-axis-iso.png) |
| Four source-named parathyroids and thyroid | [Posterior](posterior-neck-ortho.png) | [Posterior oblique](posterior-neck-iso.png) |
| Adrenals and pancreas | [Anterior](upper-abdomen-ortho.png) | [Anterior oblique](upper-abdomen-iso.png) |
| Adrenals seen behind pancreas | [Posterior](posterior-abdomen-ortho.png) | [Posterior oblique](posterior-abdomen-iso.png) |
| Illustrative islet cells and capillary | [Anterior](islet-ortho.png) | [Inset](islet-iso.png) |
| Ovaries with alternative male gonad inset | [Anterior](gonads-ortho.png) | [Inset context](gonads-iso.png) |

**Technical passed for scoped geometry.** Clean import found 34 meshes. Two signals start on the source surfaces and end in independent cone tips at the recorded target landmarks. Maximum arrow source/base/tip error was 0.056 µm. Maximum anchor-to-organ surface error was 0.012 µm. These residuals measure agreement with authored coordinates. The exported X positions put each left ovary, testis and adrenal to the subject's left of its right partner.

An earlier cross-atlas placement intersected the right adrenal and pancreas head in 133 triangle pairs. Moving the pancreas anteriorly by 8 mm eliminated all intersections between either adrenal and the five pancreas regions. The [geometry check](../../../assemblies/endocrine-locator/r01/check.py) rejected the earlier actual GLB and passed the delivered GLB. A fresh Blender replay produced a different container SHA-256 (`393c3f5e3c15278bc993cae75e16ad2e91ef84cee94528db83e000547b6255a6`), with identical placements, per-node sets of vertex attribute tuples and triangle position triples including multiplicity. Binary ordering is outside the replay claim.

**Visual passed with limitations.** Inspected all seven clean-import pairs. In the anterior overview the islet and alternate male gonads sit outside the outline. The two signals and their arrowheads separate at neck scale. Four posterior parathyroids become visible when the thyroid turns. In anterior projection the pancreas partly obscures the adrenals, which the posterior view exposes. Projection overlap persists despite the checked 3D clearance. The source head envelope joins hypothalamus and pituitary in one mesh, with color zones distinguishing them. The islet inset represents two endocrine cell types near a capillary; its cell counts and dimensions have no histological significance.

**Anatomy reference-screened.** Credited atlas sources provide gross gland shapes; the linked endocrine references support the two forward hormonal steps and example cell identities. Feedback loops, pituitary sublobes, portal vascular anatomy, histology, clinical use and specialist validation are outside scope. This combined locator uses authored cross-atlas placements.

**Runtime unverified.** Blender clean-import and offline rendering succeeded. The live viewer and interaction performance were not exercised.
