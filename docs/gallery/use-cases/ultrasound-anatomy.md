# Ultrasound Anatomy · Tour specification

The local Abdomen, Thyroid, Breast and Pregnancy tours are the reference implementation for exploring ultrasound anatomy. Visitors can follow a probe through an authored sweep, inspect the corresponding section, and compare a modeled image with a named acquired view from another case. The collector and author-facing asset display will be designed jointly after reviewing the abdomen set. [Local tour and replay](../../../experiments/ultrasound-sweep/README.md) · [Campaign](../../../records/campaigns/ultrasound-gallery.md)

## Audience and outcome

A visitor familiar with basic anatomy should be able to connect the probe footprint, imaging field, intersected structures, and projected image. At a reference keyframe they can point out the relationship and inspect differences in shape, depth or landmarks across cases. The current tour supports exploration. Exercises, assessment, measurements, disease classification and narration are possible later uses.

The five collection topics are Abdomen, abdominal aortic aneurysm (AAA), Thyroid, Breast and Pregnancy. Name the exam purpose for each topic. Abdomen provides a general anatomy exploration. Reserve screening claims for specifically supported contexts such as AAA. [AIUM abdominal aorta practice parameter](https://onlinelibrary.wiley.com/doi/10.1002/jum.70167) · [USPSTF thyroid guidance](https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/thyroid-cancer-screening)

## Tour contract

| Surface or action | What the visitor gets |
| --- | --- |
| Select a sweep | A direct, reloadable route for the named organ and side. The sweep opens at its designated comparison with the corresponding pose and images. The previous gallbladder entry still opens the gallbladder sweep. |
| Orbit the patient | One orbitable scene containing patient exterior, probe, wireframe imaging field, and internal structures. The selected organ or regional vessel segment is the pivot. Changing frame or torso opacity preserves camera orientation. [Spatial terms](../../../GLOSSARY.md#ultrasound-acquisition) |
| Select a camera view | Oblique, axial, coronal and sagittal presets orient the **3D camera**. Reselecting a preset restores its framing after manual orbit. The sweep timeline continues to own the sampled ultrasound plane. Clinical multiplanar reconstructions would require separate image reslicing and are outside these camera presets. |
| Adjust torso opacity | Move continuously from an external contact view to isolated probe and internal geometry. Retain the value across playback, reference ticks, camera presets and a round trip through the current asset review. |
| Play or scrub | One ordered pose sequence drives probe, field, section and simulated scan. Support pause, replay, keyboard scrubbing, patterned phase spans, and labeled reference ticks. Decode images before switching them. Keep control bounds stable as the readout changes. |
| Inspect a reference | Show simulated and acquired images side by side. The anatomy overlay uses named structure labels in matching hues. At intermediate frames, name the nearest acquired reference. If a reference uses a different level, window, or crop, label the comparison honestly. |
| Inspect sources | Fold acquisition credit, licensing, transformations, and case limits into Sources. The context-specific reference and its source stay reachable from the current keyframe. |
| Recover from missing media | A missing scan affects its frame. A missing reference or failed WebGL scene has its own unavailable state. Keep the other views and navigation usable. |

## Abdomen coverage

The core set uses general abdominal ultrasound regions in the [AIUM abdominal imaging checklist](https://www.aium.org/docs/default-source/accreditation/case-study-requirements/abdominal.pdf) to select anatomy targets. Each row is a bounded sweep through one example CT case. The two reference stops illustrate a change of plane or landmark, with additional study-specific limits recorded in the [reference record](../../../experiments/ultrasound-sweep/research/README.md).

| Sweep | First reference stop | Second reference stop |
| --- | --- | --- |
| Gallbladder | Long axis beside the liver | Short axis through the same organ |
| Liver | Oblique view through portal branches | Hepatic tissue beside the IVC |
| Portal vein | Along the main portal vein | Across the main portal vein |
| Pancreas | Body and portal venous landmark | Oblique head |
| Spleen | Splenic long axis | Cross-section compared with an acquired hilar view |
| Right kidney | Right renal long axis | Right renal short axis |
| Left kidney | Left renal long axis | Left renal short axis |
| Abdominal aorta | Long axis | Transverse with adjacent IVC |
| Inferior vena cava | Long axis | Transverse with adjacent aorta |

Four supporting acquired views show the extrahepatic bile duct, a hepatic vein below the diaphragm, the pancreatic tail through the spleen, and the right kidney beside the liver. The first two have no independent segmentation in s1233. The right renal long-axis model includes only small fragments of liver. The acquired views supply a point of comparison for those gaps. Duct tracing and measurements, hepatic-vein assessment, Doppler flow and pathology require other evidence. The ordinary aortic sweep identifies vessel orientation. The separate AAA topic requires a reviewed aneurysm, wall and lumen. This prototype does not establish completeness of a diagnostic abdominal examination.

## Thyroid coverage

The [right lobe](http://127.0.0.1:8874/index.html?sweep=thyroid-right) and [left lobe](http://127.0.0.1:8874/index.html?sweep=thyroid-left) each open in transverse section. Rotate toward the longitudinal stop to follow the lobe along its length. A high-frequency linear probe has a flat footprint. Its rectangular field uses parallel scan lines. The transverse image places patient right on screen left and the longitudinal view places cranial on screen left.

The trachea provides medial context and the paired common carotids provide lateral context. The **Isthmus** tick on either sweep opens the same midline pose and acquired view of the tissue bridge over the trachea. Playing from that tick moves the probe from the midline to the selected lobe before the rotation. The four lobe comparisons preserve the published side and plane. The right longitudinal reference includes color Doppler. The simulation shows grayscale anatomy. [Choi, standard thyroid images, Figure 1](https://clinicalultrasound.org/upload/pdf/cu-8-1-7.pdf#page=3)

The s1127 thyroid mask spans both lobes and their connecting bridge. Its gland lies deeper than the acquired examples. The tours demonstrate orientation and relationships in one model. Clinical acquisition requires additional levels, longitudinal positions and review of other neck structures. [AIUM head and neck practice parameter](https://www.aium.org/docs/default-source/resources/guidelines/extracranial_head_neck.pdf)

## Breast coverage

The [right breast sweep](http://127.0.0.1:8874/index.html?sweep=breast) pairs a peripheral view through the breast layers with a view along a duct beneath the nipple. In the radial view the probe’s long axis points toward the nipple. Scrub between the two to see the probe move relative to the areola. The comparison at the first stop identifies the layers from skin to chest-wall muscle. The second comparison shows the nipple and a duct along its length. The sources leave the side and clock-face position unspecified. [Layered anatomy, Figure 2](https://doi.org/10.4103/0971-3026.63045) · [Nipple and duct, Figure 1B](https://doi.org/10.3348/kjr.2019.0831)

The probe and rectangular field share coordinates with a sculpted Human Reference Atlas breast and a female skin surface. The glandular lobes, fat, ducts and nipple supply the tissue boundaries for the simulated image. The deeper fat, pectoralis and chest wall are illustrative. The final scan plane follows about 3 cm of modeled duct, with an 8 mm gap to the visible nipple. This regional sweep covers normal anatomical relationships. A whole-breast examination would require additional windows. [Mammary gland model](https://doi.org/10.48539/HBM989.SNHP.535) · [Breast ultrasound anatomy and scanning patterns](https://www.uclahealth.org/departments/radiology/education/breast-imaging-teaching-resources/birads/basics-breast-ultrasound)

## Pregnancy coverage

Both pregnancy routes use a singleton teaching model at **about 12 weeks**. The published fetal profile displays 12 weeks 2 days, and the posterior placenta comparison is a dating scan at 12 weeks 4 days. Published 11–14-week views informed the fetal proportions and the relationship of uterus, fluid, fetus and placenta. The lower abdomen, uterine position, fetal pose and probe contacts are authored in maternal right–anterior–superior coordinates. The private fetal study and the full-term placenta supply no geometry or images to these routes. [Stage-specific anatomy](https://doi.org/10.1002/ajum.12109) · [ISUOG 11–14-week guidance](https://doi.org/10.1002/uog.26106)

| Route on the isolated preview | Frame 12 | Frame 48 |
| --- | --- | --- |
| [Posterior placenta](http://127.0.0.1:8878/index.html?sweep=pregnancy-placenta) | With the curved probe low on the maternal midline and its marker directed cranially, identify the bladder anteriorly and placenta along the far uterine wall. | Follow the moving footprint toward the maternal right and turn the marker rightward. The transverse section crosses the placental contour and adjacent fluid. The acquired traced margin lies near the probe in a different case and plane. |
| [Fetal profile and head](http://127.0.0.1:8878/index.html?sweep=pregnancy-fetus) | Find the head and trunk together in the midsagittal profile. The acquired image retains its original crown–rump calipers. | Slide cranially while rotating the probe to intersect the head across its long axis. Identify the cranial outline, midline and paired choroid plexuses. |

The four acquired comparisons have figure-specific credits and reuse records. The first maternal reference documents a normal-appearing placenta at that visit in a pregnancy with a later complication. The routes teach spatial relationships in one static model. Fetal motion, Doppler flow, clinical measurements, diagnosis and a complete first-trimester examination are outside their scope. [Acquired sources and comparison limits](../../../experiments/ultrasound-sweep/research/README.md#pregnancy)

## Content, assembly and acceptance

The sweep record identifies the source CT or atlas, spatial axes, selected tissues, unit conversion, ordered probe poses, imaging field shape and physical dimensions, section palette, orbit target, keyframe labels, frame numbers and reference identities. Use the same pose for 3D and raster sampling. Verify actual contact at each authored window. Give an atlas-derived display exterior, sampled patient envelope and any other illustrative placement explicit provenance. Store each acquired image’s author, source, reuse terms, editing history and case differences with the image record. The ordered sequence is the source for a future video export. [Sweep recipes](../../../experiments/ultrasound-sweep/README.md) · [Source and replay policy](../../WORKFLOW.md)

Accept a sweep after replay from pinned inputs, verifying the target inside the imaging field and the named endpoint relationships, inspecting the simulated/section/acquired views together, and exercising the direct route, orbit, presets, opacity, play/pause, source and error paths. Independent clinical review is required for claims about scanning technique or sonographic fidelity. The acquired set is the baseline for later appearance work.

## Asset display and integration

The current review groups a keyframe into 3D anatomy, simulated scan, and acquired ultrasound. The visitor can orbit the combined probe and sector, inspect the origin of either image, open related anatomy where available, and return to the same frame. The abdominal set now gives us concrete material to review together: shared models and props, sweep-specific placements, image pairs, revisions, rights, and defects. The asset hierarchy, display and editing workflow remain open for that session. The broader [Asset Library](../asset-library.md) owns revision and download identity.

The earlier [fixed gallbladder stop](../../../lessons/ultrasound-anatomy/README.md) is still the built-in Anatomy Gallery candidate. The local sweep study is the tour under review. Public site integration, transport admission, and publication are later delivery decisions. The Echodemo project and the repository’s cardiac section package supply precedents for synchronized geometry and images. [Echodemo development notes](https://github.com/douyang/echodemo/blob/main/DEVELOPMENT.md) · [Cardiac imaging package](../../../heart/synthetic-imaging/beating-heart/imaging/README.md)

## Starting assets and open gaps

The initial inventory used med-assets `e51891b`. Local s1233 masks shared a spatial header, and sampled axial sections confirmed the coverage described below. The nine abdomen sweeps now have paired image review. Independent sonographic assessment remains open.

| Topic | Available starting point | What the next level needs |
| --- | --- | --- |
| Abdomen | Same-case s1233 liver, gallbladder and right kidney. Sampled liver–gallbladder and liver–kidney mesh cuts produced closed contours. [Workshop anatomy](../../../body/anatomy-workshop-r1/README.md) · [Digestive assembly](../../../assemblies/workshop-s1233/README.md) | The local abdomen tour covers nine sweeps. Each has two acquired comparisons. Four supporting views extend the available normal anatomy. Bile ducts and hepatic veins have no independent label in this case. |
| Abdominal aortic aneurysm | The s1233 aorta, inferior vena cava and L3 appear on common axial slices. The retained iliac artery labels stop short of the aorta label. [Vascular sources](../../../assemblies/workshop-s1233/README.md) | Author and review the infrarenal aneurysm, wall and lumen to teach a measurement. Review the bifurcation before depicting it as continuous. |
| Thyroid | The s1233 thyroid, trachea and paired carotids appear on common axial slices. The separate s0189 asset supports exterior orientation. [Same-case assembly](../../../assemblies/endocrine-locator/r02/README.md) · [s0189 exterior](../../../models/thyroid_ct_s0189/exports/illustrative-exterior-r02/README.md) | The prototype uses s1127 for both lobe sweeps to preserve its connected thyroid, same-case airway and vessels. The acquired midline view supplies an isthmus comparison. |
| Breast | The editable regional plate shows fat, lobules and ducts. The HRA breast pair provides gross exterior and posterior context. [Breast plate](../../../body/2d-v4/whole-body-anatomy-v4-spatial/regions/breast.svg) · [HRA breast pair](../../../models/breasts_hra/exports/teaching-economy-r01/README.md) | The local tour now pairs two modeled sections with acquired normal-anatomy examples. The chest-wall layers are illustrative. A lesion example needs its own source and review. |
| Pregnancy | The regional schematic shows fetus, placenta, cord and amniotic cavity. The full-term placenta supports a separate surface-orientation example. [Pregnancy plate](../../../body/2d-v4/whole-body-anatomy-v4-spatial/regions/pregnancy.svg) · [Placenta](../../../models/placenta/exports/teaching-economy-r01/README.md) | The [late first-trimester tours](#pregnancy-coverage) now pair authored maternal and fetal geometry with stage-documented acquisitions. Clinical plane qualification and measurement remain open. The retained fetal study is age-unspecified and its media are private. [Fetal study](../../../models/fetus/exports/head-face-junction-r01/README.md) · [ISUOG mid-trimester guidance](https://www.isuog.org/static/4e2ed89e-fa8a-42c2-9c0929cd89cb58ff/ISUOG-Practice-Guidelines-routine-mid-trimester-fetal-ultrasound.pdf) |
