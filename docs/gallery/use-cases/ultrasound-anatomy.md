# Ultrasound Anatomy

**Status.** The local candidate has a first Abdomen stop and a linked asset review. The other four tours are planned.

## Purpose and outcomes

**Tour.** A learner who knows basic anatomy and is new to ultrasound connects a probe pose on the body to the projected scan. Give each topic its own tour divided into meaningful stops on a shared scaffold. At each stop, show the probe and synthetic scan together. Reveal the matching anatomical section when it helps explain the image. In the first worked example, the learner should find the gallbladder in grayscale and explain its position relative to the liver.

**Asset review.** An author can see what a tour uses, identify the part or prop that limits its teaching value and open the exact asset or review to work on it. Organize by tour and stop, then by anatomy, body context, props and derived views as relevant. Explain each item's role in the view. Use the existing Asset Library for revision and download identity, and Compare or the owning review for findings. Link between a tour stop and its asset breakdown with the stop preserved on return.

Use linked pages. The collection opens either the tour or its asset review, and each stop links straight to the relevant part. Start with authored probe poses per stop. A later lesson can add free probe movement when finding the view by moving the probe is itself a learner task.

Use **Ultrasound Anatomy** as the collection name. The topics have different exam purposes. Use *screening* for a specifically named context such as abdominal aortic aneurysm (AAA) screening. The page teaches spatial relationships. Any synthetic grayscale image is identified as an illustration. [AIUM abdominal aorta practice parameter](https://onlinelibrary.wiley.com/doi/10.1002/jum.70167) · [USPSTF breast guidance](https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/breast-cancer-screening) · [USPSTF thyroid guidance](https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/thyroid-cancer-screening)

## First example

Show the probe on a regional locator, a labelled section through the source anatomy and a synthetic grayscale view of that same section. Record probe position, plane orientation, image orientation, depth, units and source identity. Keep the labeled section and grayscale view aligned so a learner can trace the same landmark. When a locator and detail come from different frames, label the transition.

Echodemo uses one probe pose to drive a torso view, labeled anatomy and synthetic B-mode. It cuts a common 3D source or supplies authored cross-section shapes, then applies a tissue-specific grayscale renderer. Use the correspondence as a teaching pattern. The existing cardiac imaging package supplies a local example of storing the plane and orientation with a synthetic image. Its ultrasound-style fan has its own plane. [Echodemo development notes](https://github.com/douyang/echodemo/blob/main/DEVELOPMENT.md) · [Cardiac imaging package](../../../heart/synthetic-imaging/beating-heart/imaging/README.md)

The asset review for this stop should name the liver, gallbladder, body locator, probe and generated views. Begin with the view that supports the learner's task, then show matched overview, orthographic or section evidence where it exposes a strength or a defect. Record revision, camera or plane, scale, material and source. Pair a concrete observation with its consequence for the tour. For example, a reference image may be needed to review the wall's grayscale appearance. Use the existing [visual comparison requirements](../../WORKFLOW.md#visual-comparisons) and [teaching-asset rubric](../../guides/asset-quality.md).

The [Abdomen lesson package](../../../lessons/ultrasound-anatomy/README.md) owns the first pose, paired views, replay and source limits. The learner identifies a marker in the grayscale and can reveal the same section to check its relationship to the liver. The asset review identifies the probe placement and grayscale appearance as the next evidence gaps.

## Starting assets and open gaps

The initial inventory used med-assets `e51891b`. Local s1233 masks shared a spatial header, and sampled axial sections confirmed the coverage described below. A rendered plate still needs review for readability and resemblance to the intended ultrasound view.

| Topic | Available starting point | What the next level needs |
| --- | --- | --- |
| Abdomen | Same-case s1233 liver, gallbladder and right kidney. Sampled liver–gallbladder and liver–kidney mesh cuts produced closed contours. [Workshop anatomy](../../../body/anatomy-workshop-r1/README.md) · [Digestive assembly](../../../assemblies/workshop-s1233/README.md) | Choose one named plane and review the visible landmarks and their grayscale appearance. |
| Abdominal aortic aneurysm | The s1233 aorta, inferior vena cava and L3 appear on common axial slices. The retained iliac artery labels stop short of the aorta label. [Vascular sources](../../../assemblies/workshop-s1233/README.md) | Author and review the infrarenal aneurysm, wall and lumen to teach a measurement. Review the bifurcation before depicting it as continuous. |
| Thyroid | The s1233 thyroid, trachea and paired carotids appear on common axial slices. The separate s0189 asset supports exterior orientation. [Same-case assembly](../../../assemblies/endocrine-locator/r02/README.md) · [s0189 exterior](../../../models/thyroid_ct_s0189/exports/illustrative-exterior-r02/README.md) | Review the isthmus, superficial tissue and intended probe view. |
| Breast | The editable regional plate shows fat, lobules and ducts. The HRA breast pair provides gross exterior and posterior context. [Breast plate](../../../body/2d-v4/whole-body-anatomy-v4-spatial/regions/breast.svg) · [HRA breast pair](../../../models/breasts_hra/exports/teaching-economy-r01/README.md) | Review a section through skin, fat, glandular tissue and chest wall before building a paired grayscale view. Give any lesion example its own source and review. |
| Pregnancy | The regional schematic shows fetus, placenta, cord and amniotic cavity. The full-term placenta supports a separate surface-orientation example. [Pregnancy plate](../../../body/2d-v4/whole-body-anatomy-v4-spatial/regions/pregnancy.svg) · [Placenta](../../../models/placenta/exports/teaching-economy-r01/README.md) | Obtain a stage-specific fetal and maternal source before teaching a standard plane or measurement. The retained fetal study is age-unspecified and its media are private. [Fetal study](../../../models/fetus/exports/head-face-junction-r01/README.md) · [ISUOG mid-trimester guidance](https://www.isuog.org/static/4e2ed89e-fa8a-42c2-9c0929cd89cb58ff/ISUOG-Practice-Guidelines-routine-mid-trimester-fetal-ultrasound.pdf) |

## Decisions and progression

1. Walk the first stop with a learner. Record where the locator, tissue boundary, wording or evidence prevents finding the target and explaining its relationship.
2. Review the fixed scan field against a suitable ultrasound reference, including the gallbladder wall and superficial field. Improve the probe representation or source registration if the current locator fails to orient the learner.
3. Repeat the learner action and asset-review handoff after each material change. Use the result to decide which topic to add next and which views need new sources.
