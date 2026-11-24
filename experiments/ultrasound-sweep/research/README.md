# Ultrasound reference studies

Use the acquired image for each reference keyframe to judge the shape of the lumen, brightness and definition of the wall, surrounding tissue, and depth. The acquisition lead-in and intermediate rotations are modeled transitions. The control names the closest endpoint when a reference stays on screen during a transition.

## Abdomen reference inventory

The [hepatopancreatic record](hepatopancreatic.json) covers liver, portal vein and pancreas. Four cropped panels from Figure 1 show the labeled liver and pancreas views. Two POCUS Atlas stills show the main portal vein along and across its course. The record pins original and exported hashes, crop coordinates, attribution, and transformations. WebP derivatives use Pillow 11.3.0, quality 94 and method 6. [Okaniwa et al., abdominal ultrasound manual](https://doi.org/10.1007/s10396-022-01272-w) · [POCUS Atlas biliary collection](https://www.thepocusatlas.com/hepatobiliary)

The [renal and splenic records](renal-splenic.json) preserve side and axis, while the [source receipt](renal-splenic-receipt.md) records each original and crop. The [great-vessel records](great-vessels.json) and [extraction receipt](great-vessels-sources.json) identify the acquired windows and clinical level differences. Crops and stills retain their source-specific terms. Several POCUS Atlas images are licensed for noncommercial reuse. These records cover 16 endpoint stills. The gallbladder builder extracts its two endpoint stills from the originals below.

The modeled spleen rotates at one left posterior contact. The section spans about 88 mm along the organ’s dominant axis at the long-axis stop and 16 mm at the short-axis stop. These distances describe the sampled CT mask. The acquired transverse image specifically shows the hilum.

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

The different cases support visual comparisons. Specialist review of probe technique, ultrasound appearance and use for teaching is open. The experiment provides no disease examples or quantitative measurement task.

## Thyroid

The [thyroid record](thyroid.json) binds each reference to its original PDF, page, panel, pixel crop, license and exported image hash. Choi’s Figure 1 shows the right lobe in transverse and longitudinal planes (A and B), the isthmus in transverse (C), and the left lobe in transverse and longitudinal planes (D and E). Each crop includes its original depth scale and probe orientation diagram. Panel B retains the published color Doppler. [Primary figure, page 3](https://clinicalultrasound.org/upload/pdf/cu-8-1-7.pdf#page=3) · [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)

The two modeled sweeps use s1127, whose thyroid label forms a continuous bridge. Compare the lobe outline, relative vessel position and tracheal boundary at each stop. The modeled field extends to 7.8 cm. The acquired panels show the gland at a shallower depth in a field of about 3 cm. The CT-derived model and the ultrasound subject have different skin contours and tissue depths. Its grayscale images illustrate anatomy without a Doppler calculation.
