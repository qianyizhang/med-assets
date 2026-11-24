# Ultrasound Anatomy

**Status.** Design brief in discussion. The first learner task, page structure and visual treatment are proposed.

## Purpose and proposed outcome

Help a learner connect the location and orientation of an ultrasound probe to the anatomy a scan plane crosses. In the first worked example, the learner should be able to find the gallbladder in a synthetic grayscale view and use the matching anatomical section to explain its position relative to the liver.

Use **Ultrasound Anatomy** as the collection name. The topics have different exam purposes. Use *screening* for a specifically named context such as abdominal aortic aneurysm (AAA) screening. The page teaches spatial relationships. Any synthetic grayscale image is identified as an illustration. [AIUM abdominal aorta practice parameter](https://onlinelibrary.wiley.com/doi/10.1002/jum.70167) · [USPSTF breast guidance](https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/breast-cancer-screening) · [USPSTF thyroid guidance](https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/thyroid-cancer-screening)

## Proposed first example

Show the probe on a regional locator, a labelled section through the source anatomy and a synthetic grayscale view of that same section. Record probe position, plane orientation, image orientation, depth, units and source identity. Keep the labeled section and grayscale view aligned so a learner can trace the same landmark. When a locator and detail come from different frames, label the transition.

Echodemo uses one probe pose to drive a torso view, labeled anatomy and synthetic B-mode. It cuts a common 3D source or supplies authored cross-section shapes, then applies a tissue-specific grayscale renderer. Use the correspondence as a teaching pattern. The existing cardiac imaging package supplies a local example of storing the plane and orientation with a synthetic image. Its ultrasound-style fan has its own plane. [Echodemo development notes](https://github.com/douyang/echodemo/blob/main/DEVELOPMENT.md) · [Cardiac imaging package](../../../heart/synthetic-imaging/beating-heart/imaging/README.md)

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

1. Agree on the primary learner, the job the page should serve for them and the action that demonstrates the outcome.
2. Prototype viable page openings and how a learner moves between the probe, section and grayscale view. Use the prototypes to settle whether the opening presents an orientation, a worked example or an exercise.
3. Build the selected first stop in the ordinary Gallery with actual assets. Walk the learner action and record the exact source revisions, views and observed failures or limitations.
4. Refine the page and specific assets that prevented the learner action. Repeat that action after each material change. Use the result to decide which topic to add next and which views still need new sources.
