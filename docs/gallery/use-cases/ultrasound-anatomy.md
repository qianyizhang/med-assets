# Ultrasound Anatomy · Tour specification

The local Abdomen tour is the reference implementation for exploring ultrasound anatomy. Visitors can follow a probe through an authored sweep, inspect the corresponding section, and compare a modeled image with a named acquired view from another case. The collector and author-facing asset display will be designed jointly after reviewing the abdomen set. [Local tour and replay](../../../experiments/ultrasound-sweep/README.md) · [Campaign](../../../records/campaigns/ultrasound-gallery.md)

## Audience and outcome

A visitor familiar with basic anatomy should be able to connect the probe footprint, imaging sector, intersected structures, and projected image. At a reference keyframe they can point out the relationship and inspect differences in shape, depth or landmarks across cases. The current tour supports exploration. Exercises, assessment, measurements, disease classification and narration are possible later uses.

The five collection topics are Abdomen, abdominal aortic aneurysm (AAA), Thyroid, Breast and Pregnancy. Name the exam purpose for each topic. Abdomen provides a general anatomy exploration. Reserve screening claims for specifically supported contexts such as AAA. [AIUM abdominal aorta practice parameter](https://onlinelibrary.wiley.com/doi/10.1002/jum.70167) · [USPSTF thyroid guidance](https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/thyroid-cancer-screening)

## Tour contract

| Surface or action | What the visitor gets |
| --- | --- |
| Select a sweep | A direct, reloadable route for the named organ and side. The first comparison opens with the corresponding pose and images. The previous gallbladder entry still opens the gallbladder sweep. |
| Orbit the patient | One orbitable scene containing patient exterior, probe, wireframe imaging sector, and internal structures. The selected organ or regional vessel segment is the pivot. Changing frame or torso opacity preserves camera orientation. [Spatial terms](../../../GLOSSARY.md#ultrasound-acquisition) |
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
| Pancreas | Body and splenic vein | Oblique head |
| Spleen | Splenic long axis | Short axis toward the hilum |
| Right kidney | Right renal long axis | Right renal short axis |
| Left kidney | Left renal long axis | Left renal short axis |
| Abdominal aorta | Long axis | Transverse with adjacent IVC |
| Inferior vena cava | Long axis | Transverse with adjacent aorta |

The case has no independent bile-duct or hepatic-vein segmentation. A portal vein label supports a vessel comparison at the porta hepatis. Duct tracing and measurements, hepatic-vein assessment, Doppler flow, and pathology require other evidence. The ordinary aortic sweep identifies vessel orientation. The separate AAA topic requires a reviewed aneurysm, wall and lumen. This prototype does not establish completeness of a diagnostic abdominal examination.

## Content, assembly and acceptance

The sweep record identifies the CT case and axes, selected masks, unit conversion, ordered probe poses, curved field dimensions, section palette, orbit target, keyframe labels, frame numbers and reference identities. Use the same pose for 3D and raster sampling. Verify actual contact at each authored window. Give an atlas-derived display exterior, sampled patient envelope and any other illustrative placement explicit provenance. Store each acquired image’s author, source, reuse terms, editing history and case differences with the image record. The ordered sequence is the source for a future video export. [Sweep recipes](../../../experiments/ultrasound-sweep/README.md) · [Source and replay policy](../../WORKFLOW.md)

Accept a sweep after replay from pinned inputs, verifying the target inside the imaging sector and the named endpoint relationships, inspecting the simulated/section/acquired views together, and exercising the direct route, orbit, presets, opacity, play/pause, source and error paths. Independent clinical review is required for claims about scanning technique or sonographic fidelity. The acquired set is the baseline for later appearance work.

## Asset display and integration

Preserve the existing return from an asset to its originating keyframe. The abdominal set now gives us concrete material to review together: shared models and props, sweep-specific placements, image pairs, revisions, rights, and defects. The asset hierarchy, display and editing workflow remain open for that session. The broader [Asset Library](../asset-library.md) owns revision and download identity.

The earlier [fixed gallbladder stop](../../../lessons/ultrasound-anatomy/README.md) is still the built-in Anatomy Gallery candidate. The local sweep study is the tour under review. Public site integration, transport admission, and publication are later delivery decisions. The Echodemo project and the repository’s cardiac section package supply precedents for synchronized geometry and images. [Echodemo development notes](https://github.com/douyang/echodemo/blob/main/DEVELOPMENT.md) · [Cardiac imaging package](../../../heart/synthetic-imaging/beating-heart/imaging/README.md)

## Starting assets and open gaps

The initial inventory used med-assets `e51891b`. Local s1233 masks shared a spatial header, and sampled axial sections confirmed the coverage described below. The nine abdomen sweeps now have paired image review. Independent sonographic assessment remains open.

| Topic | Available starting point | What the next level needs |
| --- | --- | --- |
| Abdomen | Same-case s1233 liver, gallbladder and right kidney. Sampled liver–gallbladder and liver–kidney mesh cuts produced closed contours. [Workshop anatomy](../../../body/anatomy-workshop-r1/README.md) · [Digestive assembly](../../../assemblies/workshop-s1233/README.md) | The local abdomen tour now covers nine sweeps. Review the two acquired comparisons for each. Bile ducts and hepatic veins have no independent label in this case. |
| Abdominal aortic aneurysm | The s1233 aorta, inferior vena cava and L3 appear on common axial slices. The retained iliac artery labels stop short of the aorta label. [Vascular sources](../../../assemblies/workshop-s1233/README.md) | Author and review the infrarenal aneurysm, wall and lumen to teach a measurement. Review the bifurcation before depicting it as continuous. |
| Thyroid | The s1233 thyroid, trachea and paired carotids appear on common axial slices. The separate s0189 asset supports exterior orientation. [Same-case assembly](../../../assemblies/endocrine-locator/r02/README.md) · [s0189 exterior](../../../models/thyroid_ct_s0189/exports/illustrative-exterior-r02/README.md) | Review the isthmus, superficial tissue and intended probe view. |
| Breast | The editable regional plate shows fat, lobules and ducts. The HRA breast pair provides gross exterior and posterior context. [Breast plate](../../../body/2d-v4/whole-body-anatomy-v4-spatial/regions/breast.svg) · [HRA breast pair](../../../models/breasts_hra/exports/teaching-economy-r01/README.md) | Review a section through skin, fat, glandular tissue and chest wall before building a paired grayscale view. Give any lesion example its own source and review. |
| Pregnancy | The regional schematic shows fetus, placenta, cord and amniotic cavity. The full-term placenta supports a separate surface-orientation example. [Pregnancy plate](../../../body/2d-v4/whole-body-anatomy-v4-spatial/regions/pregnancy.svg) · [Placenta](../../../models/placenta/exports/teaching-economy-r01/README.md) | Obtain a stage-specific fetal and maternal source before teaching a standard plane or measurement. The retained fetal study is age-unspecified and its media are private. [Fetal study](../../../models/fetus/exports/head-face-junction-r01/README.md) · [ISUOG mid-trimester guidance](https://www.isuog.org/static/4e2ed89e-fa8a-42c2-9c0929cd89cb58ff/ISUOG-Practice-Guidelines-routine-mid-trimester-fetal-ultrasound.pdf) |
