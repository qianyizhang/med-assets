# Ultrasound Anatomy · Tour specification

The local abdomen, thyroid, carotid, breast and pregnancy tours are the reference implementation for exploring ultrasound anatomy. Visitors can follow a probe through an authored sweep, inspect the corresponding section, and compare a modeled image with a named acquired view from another case. The collector and author-facing asset display will be designed jointly after reviewing the abdomen set. [Local tour and replay](../../../experiments/ultrasound-sweep/README.md) · [Campaign](../../../records/campaigns/ultrasound-gallery.md)

## Audience and outcome

A visitor familiar with basic anatomy should be able to connect the probe footprint, imaging field, intersected structures, and projected image. At a reference keyframe they can point out the relationship and inspect differences in shape, depth or landmarks across cases. The current tour supports exploration. The aortic survey displays a calculated model span. Free caliper placement, exercises, assessment, disease classification and narration remain possible later uses.

Current topics cover abdominal anatomy, abdominal aortic screening, thyroid, common carotid, breast and pregnancy. Name the exam purpose for each topic. Abdomen provides a general anatomy exploration. Reserve screening claims for specifically supported contexts such as abdominal aortic aneurysm (AAA) screening. [AIUM abdominal aorta practice parameter](https://onlinelibrary.wiley.com/doi/10.1002/jum.70167) · [USPSTF thyroid guidance](https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/thyroid-cancer-screening)

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

Four supporting acquired views show the extrahepatic bile duct, a hepatic vein below the diaphragm, the pancreatic tail through the spleen, and the right kidney beside the liver. The first two have no independent segmentation in s1233. The right renal long-axis model includes only small fragments of liver. The acquired views supply a point of comparison for those gaps. Duct tracing and measurements, hepatic-vein assessment, Doppler flow and pathology require other evidence. The ordinary aortic sweep identifies vessel orientation. The screening survey below follows the nondilated model through three abdominal levels. An aneurysm example would require reviewed wall and lumen geometry. This prototype does not establish completeness of a diagnostic abdominal examination.

## Normal aortic screening survey

The [screening survey](http://127.0.0.1:8874/index.html?sweep=aortic-screening) follows the abdominal aorta from a proximal transverse section through the mid aorta to just above the iliac bifurcation. The imaging plane stays perpendicular to the local vessel centerline as the probe moves down the abdomen. A fitted BodyParts3D exterior supplies the torso, with its contact surface matched to the source CT along the probe path. Look for the aorta in front of the vertebral body and distinguish it from the adjacent inferior vena cava. **Long and short axes** opens the companion tour for inspection of the vessel in two orientations.

**AP span** shows the anterior–posterior extent of the segmented artery within the selected plane. The calipers are computed from the native CT mask and projected into the displayed scan. At the three reference stops they span about 24, 19 and 17 mm respectively. The acquired proximal image identifies the celiac trunk, the mid image identifies the superior mesenteric artery, and the distal image shows a single aortic cross-section. Those branches have no separate labels in the model. Its distal stop lies above the upper extent of the separate iliac masks.

This survey illustrates the sweep and measurement landmarks in one CT case. Clinical screening requires additional views, wall identification and acquisition-specific measurements. The model calipers describe the segmentation boundary. The original clinical calipers and annotations belong to the published cases. [Acquired sources and limitations](../../../experiments/ultrasound-sweep/research/aortic-screening.json) · [AIUM adult abdominal aorta practice parameter](https://doi.org/10.1002/jum.70167)

## Thyroid coverage

The [right lobe](http://127.0.0.1:8874/index.html?sweep=thyroid-right) and [left lobe](http://127.0.0.1:8874/index.html?sweep=thyroid-left) each open in transverse section. Rotate toward the longitudinal stop to follow the lobe along its length. A high-frequency linear probe has a flat footprint. Its rectangular field uses parallel scan lines. The transverse image places patient right on screen left and the longitudinal view places cranial on screen left.

The trachea provides medial context and the paired common carotids provide lateral context. The **Isthmus** tick on either sweep opens the same midline pose and acquired view of the tissue bridge over the trachea. Playing from that tick moves the probe from the midline to the selected lobe before the rotation. The four lobe comparisons preserve the published side and plane. The right longitudinal reference includes color Doppler. The simulation shows grayscale anatomy. [Choi, standard thyroid images, Figure 1](https://clinicalultrasound.org/upload/pdf/cu-8-1-7.pdf#page=3)

The s1127 thyroid mask spans both lobes and their connecting bridge. Its gland lies deeper than the acquired examples. The tours demonstrate orientation and relationships in one model. Clinical acquisition requires additional levels, longitudinal positions and review of other neck structures. [AIUM head and neck practice parameter](https://www.aium.org/docs/default-source/resources/guidelines/extracranial_head_neck.pdf)

## Common carotid coverage

The [right](http://127.0.0.1:8874/index.html?sweep=carotid-right) and [left](http://127.0.0.1:8874/index.html?sweep=carotid-left) routes explore the common carotid trunk in grayscale. At **Transverse**, find the dark arterial cross-section. As the probe rotates, watch the lumen lengthen until both walls are visible at **Longitudinal**. The magnified section shows the same sampled plane at a smaller field of view.

The arteries come from the matched s1127 CT masks. A contrast-visible segment of the right internal jugular vein was traced on 34 consecutive CT slices cranial to the right brachiocephalic confluence. Each side has its own artery and probe poses. Only the right jugular has a verified vein trace in this study. The acquired transverse panel shows a carotid beside the jugular vein and leaves its side unspecified. The acquired longitudinal image shows a right common carotid and also provides a shape comparison for the left tour. Its wall markings belong to the published study. This is an orientation study of the common trunk. Duplex assessment adds flow imaging and further vessel segments. [Reference records](../../../experiments/ultrasound-sweep/research/carotid.json) · [AIUM extracranial cerebrovascular practice parameter](https://doi.org/10.1002/jum.15877)

## Breast coverage

Three linked right-sided routes explore normal breast and axillary anatomy. Each has 49 sampled poses, two acquired comparisons and an orbitable probe and imaging field.

| Route | What to explore | What the comparison shows |
| --- | --- | --- |
| [Layer survey](http://127.0.0.1:8874/index.html?sweep=breast) | Follow four overlapping passes outward and inward across progressively lower windows. **Scan path** shows their positions on the skin. Read the section from skin and subcutaneous fat through fibroglandular tissue and posterior fat to pectoralis. | Two published examples of breast layers. Their exact locations relative to the survey are unknown. |
| [Nipple and ducts](http://127.0.0.1:8874/index.html?sweep=breast-subareolar) | Slide the probe across the areolar region, rotate across or along a duct, and rock the probe heel-to-toe. The probe starts in contact. Toggle **Firmer pressure** at the same pose to compress the tissue another 3 mm. | Axial and longitudinal views from the same published figure. The acquired comparison follows probe rotation. |
| [Axillary nodes](http://127.0.0.1:8874/index.html?sweep=axilla) | Follow one illustrative right axillary node. The shallow long-axis view isolates the elongated node and its fatty hilum. Rotate through the same node as imaging depth increases from roughly 2.2 to 4.9 cm, bringing the neighboring vessels into view. | A published normal node in an elongated profile, followed by a short-axis view of the regional vessels and muscle. The second image establishes regional orientation. |

Projected onto the front of the posed atlas, the four passes reach about 44% of the right breast fat silhouette. This measures the model’s projected footprint. Clinical coverage depends on tissue sampled through depth. The HRA mammary gland and skin provide the external contour and gross anatomy. Mixed fibroglandular tissue and the posterior tissue planes add continuity between the retained lobules and chest wall. The focused route includes 45 combinations of slide, rotation and heel-toe angle. The layer survey uses a modeled supine contour that reduces anterior breast projection relative to the pectoral fascia. The focused route samples a shallower, 2.6 cm field through the nipple. The native nipple exterior and a modeled basal surface form one volume. The radial view samples a native duct near that volume.

All three breast routes seat a rigid linear probe against a two-dimensional footprint sampled on the patient surface. Shallow tissues flatten under the face. Displacement tapers past the footprint and with depth. The viewer deforms the displayed mesh and the generator samples the tissue section using the same displacement field. The pressure control changes displacement, with no measured force or calibrated elasticity. The axillary node, surrounding vessels and muscle are authored teaching geometry registered to the female exterior. Independent sonographic review and whole-breast examination coverage remain open. [HRA mammary model](https://doi.org/10.48539/HBM989.SNHP.535) · [UCLA breast scan patterns](https://www.uclahealth.org/departments/radiology/education/breast-imaging-teaching-resources/birads/basics-breast-ultrasound) · [Nipple scanning technique](https://doi.org/10.3348/kjr.2019.0831) · [Acquired references and limitations](../../../experiments/ultrasound-sweep/research/README.md#breast)

## Pregnancy coverage

[Open the pregnancy sequence](http://127.0.0.1:8874/index.html?sweep=pregnancy-early). Four teaching windows across the three trimesters show how the question changes as pregnancy progresses. Choose a week range, then a sweep within that stage. The two existing 12-week links still open at their original comparison. The stage models are independent examples of a singleton pregnancy.

| Modeled stage and focus | Sweep | Named comparisons |
| --- | --- | --- |
| About 7 weeks · location and development | [Gestational sac and embryo](http://127.0.0.1:8874/index.html?sweep=pregnancy-early) | Intrauterine sac, yolk sac beside embryo, cardiac region. The acquired M-mode strip shows cardiac movement over time. |
| About 12 weeks · profile and placenta | [Fetal profile and head](http://127.0.0.1:8874/index.html?sweep=pregnancy-fetus) | Nuchal region and nasal bone, whole midsagittal profile, axial head and paired choroid plexuses. |
| | [Posterior placenta](http://127.0.0.1:8874/index.html?sweep=pregnancy-placenta) | Midline view of the posterior placenta with the maternal bladder anteriorly, then a transverse placental section. |
| About 20 weeks · anatomy survey | [Brain and face](http://127.0.0.1:8874/index.html?sweep=pregnancy-mid-brain) | Transventricular head, transthalamic biometry plane, posterior fossa, coronal face and upper lip, sagittal profile. |
| | [Heart and great vessels](http://127.0.0.1:8874/index.html?sweep=pregnancy-mid-heart) | Four chambers, left ventricular outflow, right ventricular outflow, three vessels, three vessels and trachea. |
| | [Abdomen and urinary tract](http://127.0.0.1:8874/index.html?sweep=pregnancy-mid-abdomen) | Abdominal circumference plane with stomach and umbilical vein, kidneys, bladder, fetal abdominal cord insertion. |
| | [Spine and limbs](http://127.0.0.1:8874/index.html?sweep=pregnancy-mid-spine-limbs) | Longitudinal spine, femoral shaft, hand and foot. |
| | [Placenta and cervix](http://127.0.0.1:8874/index.html?sweep=pregnancy-mid-placenta) | Lower placental edge relative to the internal cervical os, then the placental end of the cord. |
| About 32 weeks · growth, presentation and fluid | [Presentation, placenta and fluid](http://127.0.0.1:8874/index.html?sweep=pregnancy-late-presentation) | Head at the lower uterine segment, anterior placenta, vertical fluid window. Related anatomy includes a separate posterior placental edge and cervical os. |
| | [Growth planes](http://127.0.0.1:8874/index.html?sweep=pregnancy-late-biometry) | Axial head, abdominal circumference and femoral length planes. Published calipers belong to their acquired cases. |
| | [Umbilical cord sampling site](http://127.0.0.1:8874/index.html?sweep=pregnancy-late-cord) | Fetal abdominal insertion and a free cord loop, with an acquired umbilical artery Doppler trace. Related views show the fetal middle cerebral and maternal uterine artery sampling sites. |

The curved probe, skin contact, 3D field, grayscale raster and tissue overlay use the same pose. At selected stops **Magnify section** resamples a smaller area of that physical plane. A yellow outline on the 3D field locates the magnified area. **Full field** restores the surrounding context. Stepping away from the stop restores the full field automatically. The original private, age-unspecified fetal study and full-term placental export supply no input to these stage models. [Recipes and checks](../../../experiments/ultrasound-sweep/README.md) · [Acquired images and rights](../../../experiments/ultrasound-sweep/research/README.md#pregnancy)

The objective is orientation to principal normal singleton scan sequences. Each model has a fixed fetal pose. Dating, nuchal thickness, growth velocity, estimated weight, fluid indices and vascular resistance require clinical acquisitions and interpretation. Static models do not establish viability or generate measured flow. Multiple gestation and indication-specific pathology are separate topics. The sequence is organized around the published [early-pregnancy lexicon](https://doi.org/10.1148/radiol.240122), [11–14-week examination](https://doi.org/10.1002/uog.26106), [mid-trimester anatomy survey](https://doi.org/10.1002/uog.24888) and [third-trimester examination](https://doi.org/10.1002/uog.27538).

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
| Abdominal aortic aneurysm | The s1233 aorta, inferior vena cava and L3 appear on common axial slices. The retained iliac artery labels stop short of the aorta label. [Vascular sources](../../../assemblies/workshop-s1233/README.md) | The normal survey displays AP spans of the segmented artery. An abnormal-finding milestone still needs a reviewed aneurysm with identifiable wall and lumen. The model preserves the separation between the aortic and iliac masks. |
| Thyroid | The s1233 thyroid, trachea and paired carotids appear on common axial slices. The separate s0189 asset supports exterior orientation. [Same-case assembly](../../../assemblies/endocrine-locator/r02/README.md) · [s0189 exterior](../../../models/thyroid_ct_s0189/exports/illustrative-exterior-r02/README.md) | The prototype uses s1127 for both lobe sweeps to preserve its connected thyroid, same-case airway and vessels. The acquired midline view supplies an isthmus comparison. |
| Breast | The editable regional plate shows fat, lobules and ducts. The HRA breast pair provides gross exterior and posterior context. [Breast plate](../../../body/2d-v4/whole-body-anatomy-v4-spatial/regions/breast.svg) · [HRA breast pair](../../../models/breasts_hra/exports/teaching-economy-r01/README.md) | Three local routes pair breast layers, nipple and ducts, and axillary anatomy with six acquired comparisons. Deep layers and axillary anatomy include illustrative geometry. A lesion example needs its own source and review. |
| Pregnancy | The regional schematic shows fetus, placenta, cord and amniotic cavity. The full-term placenta supports a separate surface-orientation example. [Pregnancy plate](../../../body/2d-v4/whole-body-anatomy-v4-spatial/regions/pregnancy.svg) · [Placenta](../../../models/placenta/exports/teaching-economy-r01/README.md) | The [four pregnancy stages](#pregnancy-coverage) now pair authored maternal and fetal geometry with published acquisitions and identify comparison-age differences. Clinical plane qualification and measurement remain open. The retained fetal study is age-unspecified and its media are private. [Fetal study](../../../models/fetus/exports/head-face-junction-r01/README.md) · [ISUOG mid-trimester guidance](https://www.isuog.org/static/4e2ed89e-fa8a-42c2-9c0929cd89cb58ff/ISUOG-Practice-Guidelines-routine-mid-trimester-fetal-ultrasound.pdf) |
