# Ultrasound Anatomy · Tour specification

The local sweeps and cardiac cycle study let visitors explore ultrasound anatomy. Visitors can follow a probe through an authored sweep, inspect the corresponding section, and compare a modeled image with a named acquired view from another case. The collection calls for linked Teaching and Development pages. Teaching offers standalone sweeps and composed exam tours. Development gives authors collection-wide Motion and B-mode rendering views, with a direct path to the sweep and keyframe behind each observation. [Use Cases requirements](README.md) · [Local tour and replay](../../../experiments/ultrasound-sweep/README.md) · [Campaign](../../../records/campaigns/ultrasound-gallery.md)

For new or changed acquisitions, start with the [3D modeling standard](#3d-modeling-standard-for-sweeps-and-tours). For an exam tour, also apply [exam acceptance](#acceptance).

## Audience and outcome

A visitor familiar with basic anatomy should be able to connect the probe footprint, imaging field, intersected structures, and projected image. At a reference keyframe they can point out the relationship and inspect differences in shape, depth or landmarks across cases. The aortic survey displays a calculated model span. The bilateral carotid exam adds free calipers, sampled flow measurements and reconstruction from a recorded sweep. Adult cardiac echo includes measurements on the beating model and illustrative Doppler exercises. Narration remains a possible later use.

Current topics cover abdominal anatomy, abdominal aortic screening, thyroid, common carotid, breast, pregnancy and adult cardiac echo. Name the exam purpose for each topic. Abdomen provides a general anatomy exploration. Reserve screening claims for specifically supported contexts such as abdominal aortic aneurysm (AAA) screening. [AIUM abdominal aorta practice parameter](https://onlinelibrary.wiley.com/doi/10.1002/jum.70167) · [USPSTF thyroid guidance](https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/thyroid-cancer-screening)

## Sweeps and exam tours

A **sweep** is the smallest independently playable teaching activity. Its case anatomy, probe track and imaging field determine the pose, intersected section and B-mode frames. A **keyframe** names a view worth stopping on. A **tour** composes frame ranges from these sweeps on one timeline. Several named sections can teach different movements within the same sweep.

An exam tour owns the case, section order, referral, reading, curves and impression. Each acquisition section selects a sweep, a source-frame interval, the applicable case parameters and its evidence frames. Learners can play or scrub across section boundaries. Consecutive sections of one sweep keep the same viewer and camera. A section that starts at another probe position should explain the repositioning. The tour embeds the sweep’s pose view and B-mode output together and can give them a different layout. A case-specific change to anatomy or probe position feeds both views. An SVG can supply a waveform, diagram or annotation alongside the acquisition.

For a shared sweep, reopen a tour chapter’s evidence frame in the standalone player. With identical inputs, the probe pose, anatomical section and B-mode image should agree. Scrubbing or replaying the chapter should advance the same frames in both places. Retain existing coverage, and identify chapters that need a new sweep or case variant before migrating their findings and measurements.

The Tours index groups teaching sequences by purpose. AAA screening is one scenario with three exam tours. Each uses the shared tour controls and embeds the same case-specific vascular sweep that the learner can open independently. In [Three landmarks in the liver window](../../../experiments/ultrasound-sweep/composed-tour/index.html), the learner follows the gallbladder, a portal branch and the cava as one liver sweep moves medially. A pinned starting plane preserves the spatial comparison. The targeted sweeps provide long- and short-axis evidence for each identity. The remaining exam families use the same [tour timeline](../../../experiments/ultrasound-sweep/composed-tour/tour.js). Each visit keeps one [case viewer](../../../experiments/ultrasound-sweep/tours/case-sweep.js) open while the learner plays or scrubs across acquisitions. Report links seek to the saved finding. The [standalone sweep player](../../../experiments/ultrasound-sweep/study.js) is the reference for the synchronized views.

## Scan scenarios

A **full exam tour** follows one case from its referral through an ordered sequence of scan acquisitions to its impression. Visitors can play the full sequence, scrub to a frame, jump to a section, and replay the view that supports a finding. The [Tours index](http://127.0.0.1:8874/tours/index.html) links to local playable visits for all ten surveyed scenarios. The [worked casebook](http://127.0.0.1:8874/cases/index.html) supplies companion illustrations, measurements and acquired comparisons. Check each visit against the coverage below and its [case package](../../../experiments/ultrasound-sweep/cases/README.md). Clinical coverage and fidelity remain open for sonographer review.

### Exam coverage survey

The survey at `a4c9877` identified gaps in the standalone sweeps and exams. Use the resulting checklist to review modeled coverage in the full visits. Each package records its delivered views and limits.

| Scenario | Coverage to verify |
| --- | --- |
| [Abdominal survey and focused exams](#abdomen-coverage) | Complete liver, biliary, pancreatic, splenic, renal, aortic and IVC coverage. Add organ and duct measurements, positional reassessment and Doppler where indicated, and bladder views for a complete urinary-tract exam. [AIUM abdomen](https://doi.org/10.1002/jum.70430) |
| [AAA screening and diagnostic evaluation](#normal-aortic-screening-survey) | Follow the aorta through the bifurcation and save the largest clinical diameter. Exercise negative, positive and indeterminate screening results. Add longitudinal and iliac views and aneurysm characterization for diagnostic evaluation. [AIUM abdominal aorta](https://doi.org/10.1002/jum.70167) |
| [Thyroid and nodules](#thyroid-coverage) | Cover both lobes and the isthmus, record lobe dimensions, and assess relevant cervical nodes. Add nodule localization, three-dimensional measurement, feature scoring and TI-RADS assessment. [AIUM head and neck](https://www.aium.org/docs/default-source/resources/guidelines/extracranial_head_neck.pdf) · [ACR TI-RADS](https://www.acr.org/clinical-resources/clinical-tools-and-reference/reporting-and-data-systems/ti-rads) |
| [Bilateral carotid duplex](#bilateral-carotid-duplex-exam) | Complete normal documentation and add a plaque case with grayscale and color assessment, spectral samples before, at and beyond the narrowing, and a stenosis impression. Record limited visualization. [IAC vascular standards](https://intersocietal.org/wp-content/uploads/2026/08/IACVascularTestingStandardsAug2026.pdf#page=24) |
| [Breast and axilla](#breast-coverage) | Add systematic whole-breast coverage for supplemental screening. For diagnostic visits, localize and measure a finding in orthogonal planes, including retroareolar and axillary cases, and record the BI-RADS assessment. [ACR screening](https://gravitas.acr.org/PPTS/GetDocumentView?docId=61) · [ACR diagnostic breast ultrasound](https://gravitas.acr.org/PPTS/GetDocumentView?docId=124) |
| [Early pregnancy](#pregnancy-coverage) | Add dating and cardiac activity recording, maternal and adnexal assessment, transvaginal views when needed, and an uncertain-location pathway. [SRU first-trimester lexicon](https://doi.org/10.1148/radiol.240122) |
| [11–14-week pregnancy scan](#pregnancy-coverage) | Add crown–rump length and nuchal translucency acquisition, cardiac activity and plurality, and the remaining basic fetal anatomy views. [ISUOG 11–14 weeks](https://doi.org/10.1002/uog.26106) |
| [Mid-trimester anatomy survey](#pregnancy-coverage) | Complete the organ checklist, including orbits, chest and diaphragm, transverse spine and all four limbs. Record biometry and cardiac activity. Let learners reattempt or document an unobtainable view. [ISUOG mid-trimester survey](https://doi.org/10.1002/uog.24888) |
| [Third-trimester growth and assessment](#pregnancy-coverage) | Add biometry, estimated fetal weight, prior comparison, a measured fluid pocket and indication-specific Doppler acquisition. [ISUOG third-trimester scan](https://doi.org/10.1002/uog.27538) |
| [Adult transthoracic echo](#cardiac-cycle) | Record a comprehensive exam with consistent views, chamber and valve measurements, Doppler and pericardial assessment. Add a finding-driven pathway such as aortic stenosis, including alternate Doppler windows and an integrated report. [ASE exam protocol](https://www.asecho.org/guideline/comprehensive-tte-in-adults/) · [ASE reporting](https://www.asecho.org/guideline/guidelines-for-the-standardization-of-adult-echocardiography-reporting/) |

### Acceptance

Apply the [3D modeling standard](#3d-modeling-standard-for-sweeps-and-tours) to each acquisition before assessing the assembled visit.

1. Map each required and indication-triggered acquisition to a playable chapter. Record gaps where the anatomy or acquisition is missing or still in draft. A companion plate can explain a gap.
2. Review the normal, abnormal and technically limited pathways for each scenario through full-exam playback. In each visit, follow the same case across positions, planes and indicated Doppler samples. Show the repeat attempt and residual blind spot when a required view is unobtainable.
3. From the final impression, trace each reported finding and measurement to its labeled case frame, clip or waveform. Verify that the visitor can jump to and replay that acquisition. Withhold measurements unsupported by the available acquisition. In the positive AAA visit, for example, scrub from the neck through the sac to the bifurcation. At the largest section, check the outer wall, thrombus and lumen against the grayscale boundaries, then verify that the report restores that same section with outer-wall calipers. Quizzes and learner assessment are deferred. [AIUM documentation](https://www.aium.org/docs/default-source/resources/guidelines/documentation.pdf)

The batch covers the Gallery's existing exam families. Additional families such as non-obstetric pelvic, venous, lung, trauma and musculoskeletal ultrasound need separate scenarios. [AIUM practice parameters](https://www.aium.org/resources/practice-parameters)

## 3D modeling standard for sweeps and tours

A learner should be able to point to the probe’s contact, follow its imaging plane into the patient and identify the structure responsible for the current B-mode finding. The primary assets for a modeled acquisition are the case’s 3D anatomy and its B-mode renderer. The same standard applies to standalone sweeps and tour chapters.

### Choose and build the anatomy

1. **Reuse the acquisition where it fits.** Start with the closest sweep and its pinned assets. Record the learner task, case, side, target, and the protected landmarks and relationships visible in the scan. Reuse the sweep when these agree. If the chapter needs a different case, pathology, or plane, record where the closest source falls short and which anatomy, acquisition, or fit must change. For a batch of similar chapters, inspect a representative acquisition in the delivered player before replicating the approach. [Asset admission](../../WORKFLOW.md#asset-admission)
2. **Reuse or adapt the anatomy before authoring a replacement.** Keep the compatible baseline anatomy and isolate the case-specific changes where practical. Use same-case sources for structures whose relative position matters, or document registration and its limits. Record the source and fit of a borrowed exterior separately. A fitted exterior supplies patient orientation and contact. Its provenance does not establish the fidelity of the internal anatomy.
3. **Use procedural geometry where there is evidence for the intended task.** A new or simplified model needs an editable recipe and a suitable anatomical reference. Label inferred construction and state its limits. Approximate shapes, point samples and companion plates can support development or a bounded teaching purpose. If they leave a required landmark, boundary or measured relationship unsubstantiated, keep the acquisition in draft or show the specific gap and withhold the unsupported finding or measurement. Label generated visual references. Check anatomy against source evidence and sonographic appearance against independently acquired ultrasound.

| What the model must show | How to build and review it |
| --- | --- |
| A recognizable patient and case anatomy | Use a fitted, attributed exterior and internal surfaces that preserve the relevant side, stage, pathology and spatial relationships. Check the task-critical shape in the assembled scene and the labeled scan plane. |
| The physical probe and its field | Seat the appropriate curved, linear, phased-array or endocavitary probe at the authored external or internal contact. Transform the footprint, image-width direction and beam together. Show the sampled field at its physical depth and width or sector angle. Outline a magnified or cropped raster within that plane. |
| One acquisition frame | For simulated B-mode, use the same case, transform and time for the 3D scene and calibrated section. Derive the grayscale image, tissue overlay and calipers from that section. Keep the overlay registered during playback. Apply case changes to the geometry that both views use. Draw a caliper at its saved frame in its acquisition plane. A recorded acquisition retains its own tracked frames and calibration. |
| A readable 3D view | Include a shaded exterior, internal surfaces, a physical transducer, orientation axes and an identifiable field in one orbitable scene. The default oblique view should expose both contact and anatomy. Camera presets, orbit, zoom and skin opacity are inspection controls. They preserve the sampled plane and B-mode frame. Diagrams, waveforms and acquired images can sit alongside the scene. |

### Record and review the acquisition

- **Pin the source and recipe.** Record the subject and anatomy revisions or case recipe, selected parts, spatial axes, transforms and units, probe poses, field dimensions, section palette, orbit target and keyframe names and frame numbers. For acquired comparisons, retain the author, source, reuse terms, edits and case differences. Cross-case references support visual comparison. Claims of pixel alignment or measured anatomical agreement need matched acquisitions. [Source records](../../../experiments/ultrasound-sweep/research/README.md)
- **Review anatomy and acquisition together.** Replay the pinned inputs. For new or changed task-critical anatomy, retain a representative scene, the corresponding B-mode and overlay, the source comparison, and the result of checking the protected structure or measured boundary in its scan plane at teaching scale. Use a matched baseline when replacing geometry. Inspect a second angle, check the actual probe contact at the authored windows, and ensure the target and named endpoint relationships are visible. Verify that a saved finding reopens the same pose, scan and calipers in both players, then scrub a neighboring frame. Exercise the relevant direct route, inspection controls, playback, sources and missing-media paths.
- **Record each review result.** Use [Development review](#development-review) for asset qualification, motion and rendering evidence. Playback and geometry checks establish the behavior they exercise. The anatomy assessment establishes fitness for the named task. Independent clinical review is required for claims about scanning technique or sonographic fidelity.

The regular sweeps and registered AAA cases use the [sweep scene](../../../experiments/ultrasound-sweep/scene.js). The [case scene](../../../experiments/ultrasound-sweep/case-scene.js) shares its camera and probe geometry and takes the case-specific surfaces and frame transform from the family acquisition module. The specialized echo and duplex studies also expose their registered acquisition geometry. These models illustrate authored teaching cases. Clinical fidelity and independent sonographer review are tracked with each family.

## Tour contract

| Surface or action | What the visitor gets |
| --- | --- |
| Select a sweep | A direct, reloadable route for the named organ and side. The sweep opens at its designated comparison with the corresponding pose and images. The previous gallbladder entry still opens the gallbladder sweep. |
| Orbit the patient | One orbitable scene containing patient exterior, probe, wireframe imaging field, and internal structures. The selected organ or regional vessel segment is the pivot. Changing frame or torso opacity preserves camera orientation. [Spatial terms](../../../GLOSSARY.md#ultrasound-acquisition) |
| Select a camera view | Oblique, axial, coronal and sagittal presets orient the **3D camera**. Reselecting a preset restores its framing after manual orbit. The sweep timeline continues to own the sampled ultrasound plane. The carotid exam has a separate volume viewer for reslicing its recorded B-mode stack. |
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

Four supporting acquired views show the extrahepatic bile duct, a hepatic vein below the diaphragm, the pancreatic tail through the spleen, and the right kidney beside the liver. The first two have no independent segmentation in s1233. The right renal long-axis model includes only small fragments of liver. The acquired views supply a point of comparison for those gaps. Duct tracing and measurements, hepatic-vein assessment, Doppler flow and pathology require other evidence. The ordinary aortic sweep identifies vessel orientation. The screening survey below follows the nondilated model through three abdominal levels. The positive AAA tour uses authored wall and lumen surfaces. The worked scan depicts mural thrombus; a separately selectable thrombus boundary is an open part requirement. This prototype does not establish completeness of a diagnostic abdominal examination.

## AAA screening tours

Open [AAA screening](http://127.0.0.1:8874/tours/aaa/index.html) for the negative, positive and indeterminate exam tours. All three cases reuse the normal aortic sweep’s fitted torso, curved transducer and 3D camera controls. A registered case vessel model supplies the wall and lumen in the scene and the synchronized CT-backed B-mode section. At the positive maximum, the calipers span the modeled outer wall including the thrombus. The positive case continues into diagnostic characterization. The indeterminate case keeps the unsuccessful anterior window and the lateral repeat, with measurements withheld where the wall is obscured. Each impression links to the acquisition frame that supports it. The [worked vascular cases](../../../experiments/ultrasound-sweep/cases/vascular/README.md) provide the source material, illustrations and separate acquired evidence.

## Normal aortic screening survey

The [screening survey](http://127.0.0.1:8874/index.html?sweep=aortic-screening) follows the abdominal aorta from a proximal transverse section through the mid aorta to just above the iliac bifurcation. The imaging plane stays perpendicular to the local vessel centerline as the probe moves down the abdomen. A fitted BodyParts3D exterior supplies the torso, with its contact surface matched to the source CT along the probe path. Look for the aorta in front of the vertebral body and distinguish it from the adjacent inferior vena cava. **Long and short axes** opens the companion tour for inspection of the vessel in two orientations.

**AP span** shows the anterior–posterior extent of the segmented artery within the selected plane. The calipers are computed from the native CT mask and projected into the displayed scan. At the three reference stops they span about 24, 19 and 17 mm respectively. The acquired proximal image identifies the celiac trunk, the mid image identifies the superior mesenteric artery, and the distal image shows a single aortic cross-section. Those branches have no separate labels in the model. Its distal stop lies above the upper extent of the separate iliac masks.

This survey illustrates the sweep and measurement landmarks in one CT case. Clinical screening requires additional views, wall identification and acquisition-specific measurements. The model calipers describe the segmentation boundary. The original clinical calipers and annotations belong to the published cases. [Acquired sources and limitations](../../../experiments/ultrasound-sweep/research/aortic-screening.json) · [AIUM adult abdominal aorta practice parameter](https://doi.org/10.1002/jum.70167)

## Thyroid coverage

The [Bilateral thyroid orientation tour](http://127.0.0.1:8874/tours/thyroid-orientation/index.html) teaches four movements on one timeline. Slide from the isthmus toward the right lobe, then rotate in place. The tour returns to the midline for the slide and rotation on the left. On each side the two sections use consecutive frames of one lobe sweep.

The [right lobe](http://127.0.0.1:8874/index.html?sweep=thyroid-right) and [left lobe](http://127.0.0.1:8874/index.html?sweep=thyroid-left) each open in transverse section. Rotate toward the longitudinal stop to follow the lobe along its length. A high-frequency linear probe has a flat footprint. Its rectangular field uses parallel scan lines. The transverse image places patient right on screen left and the longitudinal view places cranial on screen left.

The trachea provides medial context and the paired common carotids provide lateral context. The **Isthmus** tick on either sweep opens the same midline pose and acquired view of the tissue bridge over the trachea. Playing from that tick moves the probe from the midline to the selected lobe before the rotation. The four lobe comparisons preserve the published side and plane. The right longitudinal reference includes color Doppler. The simulation shows grayscale anatomy. [Choi, standard thyroid images, Figure 1](https://clinicalultrasound.org/upload/pdf/cu-8-1-7.pdf#page=3)

The s1127 thyroid mask spans both lobes and their connecting bridge. Its gland lies deeper than the acquired examples. The tours demonstrate orientation and relationships in one model. Clinical acquisition requires additional levels, longitudinal positions and review of other neck structures. [AIUM head and neck practice parameter](https://www.aium.org/docs/default-source/resources/guidelines/extracranial_head_neck.pdf)

## Common carotid coverage

The [right](http://127.0.0.1:8874/index.html?sweep=carotid-right) and [left](http://127.0.0.1:8874/index.html?sweep=carotid-left) routes explore the common carotid trunk in grayscale. At **Transverse**, find the dark arterial cross-section. As the probe rotates, watch the lumen lengthen until both walls are visible at **Longitudinal**. The magnified section shows the same sampled plane at a smaller field of view.

The arteries come from the matched s1127 CT masks. A contrast-visible segment of the right internal jugular vein was traced on 34 consecutive CT slices cranial to the right brachiocephalic confluence. Each side has its own artery and probe poses. Only the right jugular has a verified vein trace in this study. The acquired transverse panel shows a carotid beside the jugular vein and leaves its side unspecified. The acquired longitudinal image shows a right common carotid and also provides a shape comparison for the left tour. Its wall markings belong to the published study. This is an orientation study of the common trunk. Duplex assessment adds flow imaging and further vessel segments. [Reference records](../../../experiments/ultrasound-sweep/research/carotid.json) · [AIUM extracranial cerebrovascular practice parameter](https://doi.org/10.1002/jum.15877)

### Bilateral carotid duplex exam

The [combined exam](http://127.0.0.1:8874/carotid-survey/) follows a normal-anatomy teaching protocol on both sides of one Z-Anatomy atlas. Select **Bilateral carotid exam** in the Neck picker or open it from either common-carotid sweep. The earlier CT views remain available for comparison with another anatomy source.

| Acquisition | What the visitor can examine or record |
| --- | --- |
| Tracked transverse sweep | Follow the accessible common carotid through its bifurcation and into its internal and external branches. The 3D view shows the probe, imaging field and recorded sections in the same anatomical coordinates. |
| Named stations on each side | Proximal and distal common carotid, bulb and bifurcation, proximal/mid/distal internal carotid, external carotid, vertebral and subclavian. The latter two are separate flow windows. |
| B-mode, color and pulsed-wave Doppler | Place two image calipers in millimetres. Sample a modeled waveform with a registered gate and angle correction. Playback saves the distal CCA inner-wall spans and the registered peak systolic and end-diastolic velocities. Manual calipers remain separate from the model-placed measurements. The same-side ratio uses the highest measured internal carotid PSV and distal common carotid PSV. |
| Stitched anatomy | Recording adjacent transverse sections builds a surface. Completing a side makes its reconstructed B-mode volume available for linked transverse, coronal and sagittal reslicing. Compare the stitched lumen with the teaching-model boundary at any slice. The original atlas comparison identifies the authored fork change and partial upper coverage. PLY exports the lumen surface. NRRD exports the grayscale voxels, orientation, spacing and field limits. |

The atlas supplies vessel geometry, skin and neighboring tissues. Tracked binary lumen contours supply the surface reconstruction. Stored grayscale scan pixels separately supply the B-mode volume. Adjacent sections support interpolation within their observed fields. The imaged cervical lengths end before the intrathoracic origins and skull base. The waveforms are illustrative. The acquired comparisons have their own subjects, directions and instrument settings. Independent sonographer review remains open. [Acquisition and replay](../../../experiments/ultrasound-sweep/carotid-survey/README.md) · [IAC extracranial documentation, §1.7B](https://intersocietal.org/wp-content/uploads/2026/08/IACVascularTestingStandardsAug2026.pdf#page=24)

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

## Development review

Browse the [asset qualification workbench](http://127.0.0.1:8874/development/assets.html) by **body region → tours and standalone sweeps → assets → parts**. Select a tour family, an individual tour or any combination. An orientation tour includes the sweeps on its timeline. Each source asset gets one card on the shelf. Selecting a card opens the assembled asset beside the shelf, with a visibility control for each part in the displayed acquisition.

**Scene** shows the surrounding anatomy from that same acquisition. Toggle whole assets here, or return to **Asset** to toggle individual parts. Both views preserve the placement of the meshes in the source scene. Use the acquisition picker to compare another case or chapter. A part’s variants and assessments link to the corresponding evidence and teaching frame.

The BodyParts3D body envelope, HRA female exterior and authored maternal exterior have separate origins. The three AAA cases reference the normal aortic sweep’s torso file. The bilateral thyroid sweeps share one neck fit; the bilateral carotid sweeps share another. The workbench identifies a shape variant from its indexed vertices at physical scale and orientation, to a micrometre, independent of placement. The source asset, part and geometry together determine reuse. A **sweep exemplar** retains its own subject, scale and revision.

**Study coverage** indexes 32 exam tours and 410 acquisition chapters across nine scenario families plus AAA screening. The four abdominal organ tours account for 49 chapters. The other 28 exam tours account for 361. The 28 standalone sweeps form a separate source collection. In this delivery their 220 sweep-to-mesh references resolve to 145 distinct SHA-256 file hashes. Those counts describe file reuse. Anatomical identity and Gallery lineage require source evidence.

Use **Browse geometry bindings** to look up a named part, its geometry, source revision and downstream chapters. Keep one asset identity across releases. Keep the subject, fitted variant, delivered file and teaching use traceable. A live scene can use a fitted asset in the case frame or show an independent reference in its own source frame. The acquisition picker identifies the frame being shown. [Gallery vocabulary](../../../GLOSSARY.md#gallery-and-surfaces)

| Binding kind | Evidence needed | Workbench example |
| --- | --- | --- |
| Exact source reused | A reference to the same packed mesh at the same scale, or a named source node whose indexed geometry is preserved during transfer. | The biliary case reuses the standalone s1233 gallbladder surface. |
| Existing asset adapted | The recipe names the source revision and describes a change to its geometry or fit. | The atlas body envelope is fitted to the abdominal or neck scan window. |
| Separately derived from source data | Independent extractions share an identified upstream dataset or subject. Record the extraction recipe and resulting geometry. | The abdominal sweeps extract their own surfaces from s1233 CT labels. |
| Independently authored | A case or sweep recipe constructs the surface. Record the recipe revision and the limits of its teaching use. | The pregnancy sweeps generate anatomy at a specified gestational stage. |
| Unresolved provenance | A source or construction path has yet to be established. | An unbound requirement carries its reason and downstream chapters. |

Record the immediate binding and its source history separately. For example, a tour can reuse an exact sweep mesh whose original geometry was adapted from a Gallery asset. Group repeated bindings for browsing while retaining the acquisition links and task-specific assessments. Calipers, motion and Doppler waveforms belong to the acquisition where they were recorded.

Choose **Rebuilds and missing parts** under **Availability** to see the remaining work. **Rebuild required** marks an asset whose necessary anatomy has no suitable geometry. **Missing part** identifies the individual structure or case state still needed, including gaps within a partly reusable asset. An existing whole-organ surface can support orientation while its wall, lumen or abnormal state still needs a source. Every wholly missing asset uses one labeled AI illustration across its teaching uses. For a missing part, the [gallbladder wall prototype](http://127.0.0.1:8874/development/assets.html?region=abdomen&tour=abdomen-biliary-stone#requirement/abdomen-biliary-stone/biliary-stone-supine/gallbladder-wall/1) pairs the orbitable source outline with a separately framed illustration. The amber rim identifies the requested wall. Geometry checks and scores require an actual bound surface and review evidence.

For available geometry, **Unrated** means no current assessment covers that part and teaching task. Opening another use of the same shape can reveal a review for a different task. Only a retained assessment with an explicit matching binding supplies the score.

A **qualification review** names one learner task and binds its evidence to the part and geometry revision. Use the [canonical four-axis rubric](../../guides/asset-quality.md). The ultrasound workbench uses **Qualified** for **4/4 on each axis**. Retain unrated and below-target results so the coverage is visible. An inventory entry, a fitted exterior, or a qualified part for a different task carries no qualification for the current acquisition.

In the standalone study, Development opens on the sweep collection so a reviewer can spot an outlier before opening an individual frame. See [batch replay and verification](../../../experiments/ultrasound-sweep/README.md#review-a-renderer-change).

| View | Review unit | What the reviewer sees |
| --- | --- | --- |
| Asset qualification | One source asset per shelf card, with its parts, geometry variants and uses | Compare the reviewed baseline and candidate at matched scale. Inspect the relevant source surface and see which rubric axes still need evidence. |
| Motion | One short, replayable clip per sweep | The probe on the patient, imaging field and synchronized B-mode through the movement. Use a stable camera for a review pass so a camera orbit cannot disguise a jump or loss of contact. Link to the sweep for interactive inspection. |
| B-mode rendering | One row per named comparison keyframe, grouped by sweep | The synthetic B-mode beside the identified acquired frame, with view name, case or plane differences and source credit. Show missing pairs explicitly. Open the exact sweep frame to inspect its anatomy and pose. |

For a renderer change, use the [batch comparison procedure](../../../experiments/ultrasound-sweep/README.md#review-a-renderer-change) to hold the case, pose, field, reference, crop and scale fixed. Report anatomy or acquisition changes with their own evidence.

Keep the identities and decisive images needed to reproduce a finding. Retire superseded trial clips and render batches under the [retention policy](../../WORKFLOW.md#retention).

## Asset display and integration

The exact-frame inspector links the assembled scene, simulated scan and acquired comparison. The [Asset Library](../asset-library.md) indexes reusable anatomy, props and generators by revision. Sweep-specific placements and media stay with the keyframe.

The earlier [fixed gallbladder stop](../../../lessons/ultrasound-anatomy/README.md) is still the built-in Anatomy Gallery candidate. The local sweep study is the tour under review. Public site integration, transport admission, and publication are later delivery decisions. The Echodemo project and the repository’s cardiac section package supply precedents for synchronized geometry and images. [Echodemo development notes](https://github.com/douyang/echodemo/blob/main/DEVELOPMENT.md) · [Cardiac imaging package](../../../heart/synthetic-imaging/beating-heart/imaging/README.md)

## Starting assets and standalone sweep limits

Use these source leads when choosing anatomy. The initial inventory used med-assets `e51891b`. The source limits below apply to the named standalone study or input. The [worked case packages](../../../experiments/ultrasound-sweep/cases/README.md) record the geometry and limits of the full visits.

| Topic | Available starting point | What the next level needs |
| --- | --- | --- |
| Abdomen | Same-case s1233 liver, gallbladder and right kidney. Sampled liver–gallbladder and liver–kidney mesh cuts produced closed contours. [Workshop anatomy](../../../body/anatomy-workshop-r1/README.md) · [Digestive assembly](../../../assemblies/workshop-s1233/README.md) | The local abdomen tour covers nine sweeps. Each has two acquired comparisons. Four supporting views extend the available normal anatomy. Bile ducts and hepatic veins have no independent label in this case. |
| Abdominal aortic aneurysm | The s1233 aorta, inferior vena cava and L3 appear on common axial slices. The retained iliac artery labels stop short of the aorta label. [Vascular sources](../../../assemblies/workshop-s1233/README.md) | The normal survey displays AP spans of the segmented artery. The positive worked case models the aneurysm wall, residual lumen and mural thrombus and links an independent acquired comparison. The model preserves the separation between the aortic and iliac masks. |
| Thyroid | The s1233 thyroid, trachea and paired carotids appear on common axial slices. The separate s0189 asset supports exterior orientation. [Same-case assembly](../../../assemblies/endocrine-locator/r02/README.md) · [s0189 exterior](../../../models/thyroid_ct_s0189/exports/illustrative-exterior-r02/README.md) | The prototype uses s1127 for both lobe sweeps to preserve its connected thyroid, same-case airway and vessels. The acquired midline view supplies an isthmus comparison. |
| Breast | The editable regional plate shows fat, lobules and ducts. The HRA breast pair provides gross exterior and posterior context. [Breast plate](../../../body/2d-v4/whole-body-anatomy-v4-spatial/regions/breast.svg) · [HRA breast pair](../../../models/breasts_hra/exports/teaching-economy-r01/README.md) | Three local routes pair breast layers, nipple and ducts, and axillary anatomy with six acquired comparisons. Deep layers and axillary anatomy include illustrative geometry. The worked visits add a retroareolar simple cyst and an abnormal axillary node with dedicated comparison sources. |
| Pregnancy | The regional schematic shows fetus, placenta, cord and amniotic cavity. The full-term placenta supports a separate surface-orientation example. [Pregnancy plate](../../../body/2d-v4/whole-body-anatomy-v4-spatial/regions/pregnancy.svg) · [Placenta](../../../models/placenta/exports/teaching-economy-r01/README.md) | The [four pregnancy stages](#pregnancy-coverage) now pair authored maternal and fetal geometry with published acquisitions and identify comparison-age differences. The worked visits add illustrative dating, biometry, fluid and Doppler measurements. Clinical plane qualification remains open. The retained fetal study is age-unspecified and its media are private. [Fetal study](../../../models/fetus/exports/head-face-junction-r01/README.md) · [ISUOG mid-trimester guidance](https://www.isuog.org/static/4e2ed89e-fa8a-42c2-9c0929cd89cb58ff/ISUOG-Practice-Guidelines-routine-mid-trimester-fetal-ultrasound.pdf) |

## Cardiac cycle

The adult study covers 17 views from parasternal, apical, subcostal and suprasternal windows. The default spatial pane shows the probe seated on an orbitable torso. Close-up and chest landmarks reveal the contact and beam, while the heart section shows the sampled tissues. Plane rotation and cardiac phase are independent. Open Doppler and measurements for view-specific exercises, or inspect licensed acquired cines, stills and spectra. Each recorded reference keeps its original plane. [Replay, licensed acquisition and landmark review](../../../experiments/ultrasound-sweep/cardiac/README.md)
