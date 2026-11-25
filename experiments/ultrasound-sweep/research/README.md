# Ultrasound reference studies

Use the acquired image for each reference keyframe to judge the shape of the lumen, brightness and definition of the wall, surrounding tissue, and depth. The acquisition lead-in and intermediate rotations are modeled transitions. The control names the closest endpoint when a reference stays on screen during a transition.

## Abdomen reference inventory

The [hepatopancreatic record](hepatopancreatic.json) covers liver, portal vein and pancreas. Four cropped panels from Figure 1 show the labeled liver and pancreas views. Two POCUS Atlas stills show the main portal vein along and across its course. The record pins original and exported hashes, crop coordinates, attribution, and transformations. WebP derivatives use Pillow 11.3.0, quality 94 and method 6. [Okaniwa et al., abdominal ultrasound manual](https://doi.org/10.1007/s10396-022-01272-w) · [POCUS Atlas biliary collection](https://www.thepocusatlas.com/hepatobiliary)

The [renal and splenic records](renal-splenic.json) preserve side and axis, while the [source receipt](renal-splenic-receipt.md) records each original and crop. The [great-vessel records](great-vessels.json) and [extraction receipt](great-vessels-sources.json) identify the acquired windows and clinical level differences. Crops and stills retain their source-specific terms. Several POCUS Atlas images are licensed for noncommercial reuse. These records cover 16 endpoint stills. The gallbladder builder extracts its two endpoint stills from the originals below.

The modeled spleen rotates at one left posterior contact. The section spans about 88 mm along the organ’s dominant axis at the long-axis stop and 16 mm at the short-axis stop. These distances describe the sampled CT mask. The acquired transverse image specifically shows the hilum.

## Abdominal aortic screening

The [aortic screening record](aortic-screening.json) pairs the proximal, mid and distal stops with Figures 1–3 from the same publication. The three transverse sonograms keep their original depth scales, calipers and annotations. The proximal image identifies the celiac trunk. The mid image shows the superior mesenteric artery, with its relation to the renal origins unspecified. The distal image shows one aortic lumen and leaves the bifurcation outside the frame. The publication does not establish a shared participant. [Bryczkowski et al.](https://doi.org/10.7759/cureus.33822)

The AIUM practice parameter uses the celiac and renal levels and the iliac bifurcation to define coverage. For transverse diameter, the image plane is perpendicular to the vessel axis and measurements span the outer walls. The published examples retain their native calipers with no verified wall convention. The modeled survey illustrates anatomical coverage. [AIUM 2025 practice parameter](https://doi.org/10.1002/jum.70167)

## Supporting normal anatomy

Four additional panels from the same published figure fill specific gaps in the endpoint comparisons. Open **Keyframe assets → Related anatomy** on a listed sweep. Each panel comes from a separate acquisition and is displayed once per sweep. The [landmark record](normal-landmarks.json) binds each crop in original pixels to the source and exported file hashes. [Published Figure 1 and section key](https://pmc.ncbi.nlm.nih.gov/articles/PMC9868003/figure/Fig1/)

| Acquired view | Sweeps | Reason to include it |
| --- | --- | --- |
| Extrahepatic bile duct, panel 14 | Gallbladder, liver, portal vein | Shows the duct in a right subcostal oblique view. The model has no separate duct mask. |
| Hepatic vein below the diaphragm, panel 21 | Liver, IVC | Shows hepatic venous anatomy in a region where the model labels only the IVC. |
| Pancreatic tail through the spleen, panel 3 | Pancreas, spleen | Adds the left intercostal window to the modeled pancreatic body and head views. |
| Right kidney and posterior liver, bottom-right panel | Right kidney, liver | Shows the two organs together. The modeled right renal long axis includes little liver. The published key calls this section 25 and the panel is printed as 26. |

## Gallbladder

| Keyframe | Acquired witness | What to compare |
| --- | --- | --- |
| Long axis, frame 12 | Claudia Lucius and colleagues, *Life* 2025, 15(6), 941. [Figure 2 and caption](https://www.mdpi.com/2075-1729/15/6/941#fig_body_display_life-15-00941-f002). From C. Lucius’s own collection, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). [Original PNG](https://mdpi-res.com/life/life-15-00941/article_deploy/html/images/life-15-00941-g002.png). Resize the complete still for display. | The elongated lumen meets liver at a fine boundary. The image shows both calipers in a single longitudinal view. The local synthesis has a deeper target and more uniform surrounding echoes. |
| Short axis, frame 48 | Kathryn Pade, MD, Rady Children's Hospital San Diego, “Normal Gallbladder, Short Axis,” [The POCUS Atlas, Pediatric Biliary](https://www.thepocusatlas.com/pedsbiliary). [Original cine](https://images.squarespace-cdn.com/content/v1/58118909e3df282037abfad7/1685730947863-XN5NVI78PUAAFGQU5454/ezgif.com-optimize+%2826%29.gif), [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). Use frame 12 at 1.2 seconds, converted to WebP. | Compare the compact cross-section and adjacent liver. This adolescent reference has a different acoustic window, scale and case anatomy. Its noncommercial terms apply to reuse. |
| Motion study | [ACEP Sonoguide, Gallbladder](https://www.acep.org/sonoguide/basic/gallbladder), videos 1 and 4–6. Source links for studying acquisition, rotation, and the endpoint views. | The authored track lets a learner follow a lateral sweep into the organ, then rotate while holding the window. Probe contact, the sweep direction, and scan appearance await independent technique review. |

The [build recipe](../build_study.py) verifies the original image identities, CT, same-case labels, and grid. The extra [rib hashes](rib-pins.json) are from the s1233 source receipt. The CT and segmentation source is [TotalSegmentator v2.0.1](https://zenodo.org/records/10047263), Jakob Wasserthal, contributors and University Hospital Basel, CC BY 4.0. The earlier fixed-camera prototype used a small regional locator from the anterior view of the [reviewed BodyParts3D skin export](../../../models/skin/exports/teaching-economy-r01/README.md), © DBCLS, [CC BY 4.0](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html). That historical inset indicated the region on a separate adult atlas. The live study uses the [full-resolution BodyParts3D exterior](../../../models/skin/exports/bp3d-envelope-r01/README.md) and [atlas skeleton](../../../models/skeleton/exports/teaching-economy-r01/README.md), under the same DBCLS terms. Right ribs 6–10 supply the atlas-to-case fit. The fitted contact window follows the CT skin. The flank sweeps stage the atlas arm to expose the side of the abdomen. The internal organs, probe track and sector use the s1233 frame.

The different cases support visual comparisons. Specialist review of probe technique, ultrasound appearance and use for teaching is open. The original gallbladder study illustrates normal anatomy. The later aortic survey adds a calibrated span of the segmented vessel.

## Thyroid

The [thyroid record](thyroid.json) binds each reference to its original PDF, page, panel, pixel crop, license and exported image hash. Choi’s Figure 1 shows the right lobe in transverse and longitudinal planes (A and B), the isthmus in transverse (C), and the left lobe in transverse and longitudinal planes (D and E). Each crop includes its original depth scale and probe orientation diagram. Panel B retains the published color Doppler. [Primary figure, page 3](https://clinicalultrasound.org/upload/pdf/cu-8-1-7.pdf#page=3) · [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)

The two modeled sweeps use s1127, whose thyroid label forms a continuous bridge. Compare the lobe outline, relative vessel position and tracheal boundary at each stop. The modeled field extends to 7.8 cm. The acquired panels show the gland at a shallower depth in a field of about 3 cm. The CT-derived model and the ultrasound subject have different skin contours and tissue depths. Its grayscale images illustrate anatomy without a Doppler calculation.

## Breast

The [breast record](breast.json) pins four acquired derivatives, their transformations and their reuse terms. Shah and Jankharia distinguish skin, subcutaneous fat, fibroglandular tissue, retromammary fat and chest-wall muscle. Gokhale supplies a mid-transverse view of the layers. Neither publication locates its image at the specific modeled survey pass. Chiorean and colleagues supply axial and longitudinal nipple views from adjacent panels. Their technique description supports coupling gel, radial alignment, probe angulation and alternating compression when examining the retroareolar region. The modeled breast routes use surface contact. The focused route also shows how a further 3 mm of displacement changes the nipple and ducts. No applied force or patient-specific tissue properties were measured. [Shah and Jankharia, Figure 2](https://doi.org/10.4103/0971-3026.63045) · [Gokhale, Figure 1](https://doi.org/10.4103/0971-3026.54878) · [Chiorean et al., Figure 1](https://doi.org/10.3348/kjr.2019.0831)

The [axillary record](axilla.json) pins two comparisons. Chang and colleagues label their elongated node normal and describe a thin cortex and echogenic fatty hilum. Its acquisition plane and laterality are unspecified. Fenech and colleagues supply a short-axis section across the regional vessels with muscle landmarks. That panel identifies the vessels and surrounding anatomy, and makes no claim about a short-axis node. Each reference retains its source scale, annotations and terms. [Chang et al., Figure 1B](https://doi.org/10.4048/jbc.2021.24.e47) · [Fenech et al., Figure 7B](https://doi.org/10.1002/jmrs.840)

The HRA model provides duct surfaces. Small terminal openings are closed locally for image sampling. The focused radial section samples an oblique native duct near the modeled nipple base. The simulation assigns them a dark ultrasound appearance. Each acquired comparison illustrates a relationship in its own subject. Lumen caliber and flow require separate evidence.

### Structural comparison at the breast keyframes

Each comparison uses the emitted grayscale scan and the full retained clinical panel. The shared features below can be inspected before opening the anatomical overlay. Different subjects, acquisition settings and fields of view limit comparisons of size and intensity.

| Stop | Features shared with the acquired view | Visible difference |
| --- | --- | --- |
| Upper breast layers | A nearly flat skin line, dark superficial fat with septa, a brighter glandular band and deeper muscle interfaces. | Dark fat between the gland and pectoralis is wider in the model. The acquired interfaces have more curvature. |
| Lower breast layers | The fat–gland boundary slopes across the field. The brighter gland thickens toward one side. | The clinical gland has more internal echoes and occupies a larger fraction of its frame. |
| Nipple in cross-section | The flattened superficial surface overlies a rounded nipple body. A basal echo and posterior shadow distinguish it from adjacent fat. | The acquired basal interface is brighter and the surrounding tissue has fewer regularly spaced echoes. |
| Nipple and longitudinal duct | The superficial nipple lies near the left of the field. Dark oblique duct segments extend into the adjacent breast. | Several modeled branches are conspicuous. The published panel marks one finer duct. |
| Axillary node, long axis | A shallow field isolates the elongated cortex and bright hilum. | The model has a more uniform hilum and less variation in its cortical outline. |
| Axillary region, short axis | A deeper field exposes the adjacent artery and vein in section near muscle. | The publication labels regional vessels and a wider set of muscles. The node itself is specific to the model at this stop. |

## Pregnancy

The [early pregnancy](early-pregnancy.json), [11–14-week](pregnancy.json) and [mid/late pregnancy](gestational.json) records identify the authors, scope, source file, reuse license, transformations and delivered identity of each reference. Retain the license on each derivative. The early transvaginal B-mode and M-mode panels are **CC BY-NC 4.0**. The magnified nuchal profile is **CC BY-SA 3.0**. The other pregnancy acquisitions are **CC BY 4.0**.

At about 7 weeks, compare the modeled transabdominal overview with Murugan and colleagues’ serial transvaginal images. Panel D shows the gestational sac, panel A shows the yolk sac beside the measured embryo, and panel E includes the original cardiac M-mode trace. The source exams were obtained at 6 weeks 5 days and 7 weeks following a symptomatic presentation. The route explains the approach and magnification difference. The seven-week model separates the amniotic fluid around the embryo from the chorionic cavity containing the yolk sac. Published first-trimester volumetry informs the scale of these authored spaces. [Seven-week fluid volumetry](https://pubmed.ncbi.nlm.nih.gov/19468738/) · [Gestational and amniotic sac volumes](https://pubmed.ncbi.nlm.nih.gov/18314515/) [Original acquisition, Fig. 7](https://www.e-ultrasonography.org/journal/view.php?doi=10.14366/usg.19043#f7-usg-19043)

At 11–14 weeks, Wolfgang Moroder’s sagittal view at 13 weeks 3 days retains the nuchal translucency and nasal bone annotations. The modeled posterior neck contains a subcutaneous fluid layer. The acquired measurement applies only to that image. [Original nuchal scan and license](https://commons.wikimedia.org/wiki/File:Nuchal_translucency_Dr._Wolfgang_Moroder.jpg)

The model and probe path are original repository work. Springhall’s atlas of 11–14-week sections and the ISUOG guidance informed the modeled relationships. [Springhall et al.](https://doi.org/10.1002/ajum.12109) · [ISUOG](https://doi.org/10.1002/uog.26106)

| Route and stop | Source evidence | What to compare |
| --- | --- | --- |
| Placenta · sagittal | George et al., dating scan at 12 weeks 4 days. The authors report a normal posterior placenta at this visit and a complication later in pregnancy. [Figure 1](https://www.ijcriog.com/archive/article-full-text/100085Z08HG2021#figure1) | Follow the placental band deep to fluid and fetus. The acquired view is more tightly framed. |
| Placenta · transverse | Melero-Jiménez et al., upper-left acquired view of the placental contour in a first-trimester ultrasound volume. [Figure 1a](https://doi.org/10.3390/children13111475) | Compare the curving tissue–fluid boundary. The acquired placenta is nearer the probe and its contour includes power Doppler. The maternal plane of this displayed slice is unspecified. |
| Fetus · midsagittal | Korniluk et al., profile labeled 12 weeks 2 days and 5.66 cm crown–rump length. [Figure 1A](https://doi.org/10.3390/jcm15176560) | Identify crown, profile and rump together. The published calipers apply to that acquisition. |
| Fetus · axial head | Korniluk et al., axial section from the 11 weeks to 13 weeks 6 days cohort. [Figure 1D](https://doi.org/10.3390/jcm15176560) | Identify the bright paired choroid plexuses on either side of the midline. Compare outline and symmetry across the different rotation and magnification. |

Original pixel coordinates use Pillow’s left, top, right, bottom convention. Convert to RGB, apply the recorded crop and optional Lanczos resize, then save a lossless WebP with Pillow 11.3.0 and the method in the record. Published marks on the retained views are preserved.


The mid-trimester collection uses named planes to compare fetal anatomy, the placental margin and the placental end of the cord. The 20-week placental edge–cervix acquisition is also a related view on the late placenta sweep. The published 3VT panel does not state an exact acquisition age. The third-trimester acquisitions include vertex presentation, an anterior placenta, fluid pocket, biometry and umbilical artery Doppler. The fetal cord insertion comparison comes from a second-trimester scan. Related references show a posterior placental edge relative to the cervical os, and acquired middle cerebral and uterine artery spectra. The spectra retain source calipers and instrument settings. No Doppler trace or patient measurement is generated from the model. [Mid-trimester standard planes](https://link.springer.com/article/10.1007/s00404-022-06569-2/figures/1) · [Third-trimester acquisition guidance and figures](https://doi.org/10.1002/uog.27538)

The anatomy builders check fluid space after accounting for the fetus and other contents. These are design checks on the modeled stage. The late fluid stop uses the tissue boundaries of a cord-free pocket. [Measured amniotic fluid volumes across gestation](https://pubmed.ncbi.nlm.nih.gov/2764058/)
