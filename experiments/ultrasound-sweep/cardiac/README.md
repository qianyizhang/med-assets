# Adult transthoracic echocardiography

Open **Study → Heart → Adult echocardiography**. Use the view picker or arrows to walk through the exam. The default **Torso pose** shows where the lens meets the body. **Close-up** keeps the selected contact centered, and **Chest landmarks** reveals the ribs, heart and beam beneath the skin. The teal probe marker corresponds to screen right. **Heart section** opens the tissue cutaway. [Torso placement review](torso/placement.webp) · [Captured beat](review/beat.webp)

| Window | Views | What to inspect or measure |
| --- | --- | --- |
| Parasternal | Long axis, RV inflow, RV outflow, short axis at the aortic valve, mitral valve, papillary muscles and apex | LV walls and cavity, mitral and aortic motion, LVOT diameter, right-sided valves and flow |
| Apical | Four chamber, RV-focused, five chamber, two chamber and three chamber | Biplane volume and EF, longitudinal motion, RV area change, TAPSE, mitral inflow, tissue velocities and outflow |
| Subcostal | Four chamber, IVC, short-axis RV outflow and abdominal aorta | Septum, venous entry into the right atrium, respiratory IVC example and distinction from the aorta |
| Suprasternal | Aortic arch | Arch course, branch origins and descending aortic flow |

The same moving chamber, vessel and leaflet surfaces supply the grayscale section and its overlay. Scrub to freeze a phase, then rotate the plane. Orbiting moves only the observer. The [torso recipe](torso/README.md) binds the registered probe positions to BodyParts3D skin, ribs, cartilage, sternum and clavicles. The central ray clears the thoracic cage at each nominal window. The atlas and teaching heart come from independent sources. Compression, full-sector shadowing and patient-specific registration are outside the fit. [Window review](review/windows.webp) · [Default view](review/study.webp)

## Measurements and Doppler

Open **Doppler & measurements** and choose a check for this window. Place two calipers on a frozen modeled section, compare neutral biplane LV contours at end diastole and end systole, or follow lateral tricuspid annular motion. The workbench also supports atrial size, RV fractional area change, model longitudinal strain, tissue Doppler, color flow, pulsed-wave and continuous-wave spectral exercises. A saved modeled LVOT diameter feeds the outflow calculation. [Methods, assumptions and replay](measure/README.md) · [Measurement captures](measure/review.webp)

The motion, grayscale scattering and flow are illustrative. Color velocity is the beam projection of an authored local flow field. The spectral exercises have independently prescribed waveforms and adjustable beam or gate settings. Respiratory IVC change is a separate exercise. A derived number describes the selected exercise. The geometry does not impose equal stroke volumes across circuits. Source spectra, calipers and patient-specific results remain confined to their original images. [ASE adult TTE examination](https://www.asecho.org/wp-content/uploads/2019/01/2019_Comprehensive-TTE.pdf) · [BSE adult minimum dataset](https://doi.org/10.1530/ERP-20-0026)

## Acquired reference review

**Acquired examples** offers the related recording or the original published panels for the selected view. At eight windows the learner can inspect an independent cine at approximate end diastole, end systole and early filling. The ninth recording, the suprasternal arch, retains its native playback controls because ventricular event timing is poorly resolved in that view. The gallery keeps the recorded orientation while the modeled plane rotates.

| Cine | Source frames at the three model landmarks, zero-based | Review cue |
| --- | --- | --- |
| Parasternal long axis | 2 / 20 / 29 | Compare cavity narrowing with the excursion of the mitral valve. |
| Short axis, papillary level | 1 / 18 / 27 | The wall thickens around a smaller cavity. Compare the positions and shape of the papillary muscles. |
| Short axis, apical level | 2 / 19 / 28 | Follow the inward motion of the muscular ring. Valve timing is inferred from chamber motion here. |
| Apical four chamber | 2 / 18 / 26 | The annular plane approaches the apex during contraction. The mitral tips separate again in filling. |
| Apical five chamber | 1 / 22 / 32 | Compare systolic narrowing with reopening of the inlet. The source outflow tract is clearer at some phases. |
| Apical two chamber | 3 / 18 / 26 | Compare long-axis shortening between the anterior and inferior walls. |
| Apical three chamber | 4 / 22 / 32 | Inspect inlet and outflow in the same beat, allowing for different angulation. |
| Subcostal four chamber | 1 / 17 / 25 | Follow the oblique AV plane between the atria and ventricles. |

These matches use visible changes in shape and leaflet motion across independent cases. They are approximate visual landmarks. The model has cleaner borders and simpler valve and outflow joins. The subcostal acquisition includes a liver window that the heart-only tissue renderer omits. The age of each acquired subject is unspecified. Clinical sonographer acceptance, disease grading and a validated diagnostic examination remain open. [A4C matched-landmark plate](review/landmarks.webp)

**Cine rights.** I.A.C. van der Bilt, MD (Vdbilt), Department of Echocardiography, AMC, via CardioNetworks / ECHOpedia. The eight phase-matched sheets are complete frames resized and tiled under CC BY-SA 3.0. The arch WebM is the original. [A4C source, transform and landmark indices](acquisition.json) · [Additional source identities, frame selections and URLs](reference/sources.json) · [License](CC-BY-SA-3.0.txt)

**Published example rights.** Robinson et al., © 2021 the authors. The BSE table images are included for noncommercial teaching under CC BY-NC-ND 4.0. The assembler verifies the original archive hash and extracts all 88 JPEGs byte-for-byte. The filenames in its inventory identify the actual image pixels. For example, file 52 displays an MR continuous-wave spectrum and file 88 displays mitral annular tissue velocities. The interface classifies them by the visible acquisition, since the numbering and XML row context do not always agree. Some cases demonstrate findings beyond normal anatomy. [Original publication](https://doi.org/10.1530/ERP-20-0026) · [Source and panel inventory](reference/sources.json) · [License](reference/CC-BY-NC-ND-4.0.txt)

The [earlier idealized heart package](../../../heart/synthetic-imaging/beating-heart/imaging/README.md) samples its atlas at end diastole. Echodemo’s Views and Cycle chapters informed the interaction. The new cardiac geometry, renderer, signal profiles and controls are original. [Echodemo](https://github.com/douyang/echodemo)

## Local replay

Use the [gallery Python environment and prepared stage](../README.md#replay) with the cardiac LFS files hydrated. From the repository root, assemble into a fresh directory and serve on loopback.

```sh
python experiments/ultrasound-sweep/assemble_tours.py "$STUDY_OUTPUT" --delivery "$ECHO_GALLERY"
python3 -m http.server 8887 --bind 127.0.0.1 --directory "$ECHO_GALLERY"
```

Open [the first protocol view](http://127.0.0.1:8887/cardiac/?view=plax) or [the original A4C entry](http://127.0.0.1:8887/cardiac/). The short-axis views use the parasternal contact, the apical set shares its chest window, and the separate projection bases determine the modeled plane. The probe, section, color map and calipers share the same fan calibration.

Seven additional sheets reproduce from the pinned original WebM with FFmpeg 8.1 and Pillow 11.3.0. For example, run `python reference/rebuild_cine.py plax PLAXnormal.webm plax.webp` in this directory. For the original A4C sheet, decode all 50 frames with `ffmpeg -i a4c-normal.webm -vf 'scale=520:400:flags=lanczos,tile=10x5' -frames:v 1 sheet.png`, then use Pillow to save the sheet as WebP at quality 90, method 6.

Run the geometry and signal checks with Node 24+. The browser checks use the same Playwright environment as the shared gallery. Supply a capture directory as a second argument to a browser check to retain the rendered evidence.

```sh
node verify-cycle.mjs
node torso/verify-contact.mjs
node measure/verify-measure.mjs
node verify-exam.mjs 'http://127.0.0.1:8887/cardiac/?view=plax'
node verify-browser.mjs http://127.0.0.1:8887/
node measure/verify-ui.mjs 'http://127.0.0.1:8887/cardiac/?view=a4c'
```
