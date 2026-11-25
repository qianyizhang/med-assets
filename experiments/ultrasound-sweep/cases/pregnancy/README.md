# Pregnancy worked scan scenarios

Open the scenario library from the ultrasound tour and select Early pregnancy, 11–14 weeks, mid-trimester anatomy or third-trimester growth. Each family includes a normal visit, a finding and a technically limited exam with the views, measurements and impression saved in order. Different visits depict independent synthetic patients. The 28- and 32-week observations in each growth scenario depict the same modeled pregnancy.

| Family | Worked finding | Limited acquisition |
| --- | --- | --- |
| Early pregnancy | Extraovarian sac with a yolk sac, consistent with right tubal ectopic pregnancy | Pregnancy of unknown location with obscured right adnexa |
| 11–14 weeks | Increased nuchal translucency | Posterior neck and amnion cannot be separated reliably |
| Mid-trimester anatomy | Membrane-covered abdominal wall defect with cord insertion into the sac | Repeat cardiac outflow and three-vessel planes still obscured |
| Third-trimester growth | Low estimated weight, small fluid pocket and persistent absent end-diastolic flow | Abdominal circumference, fluid pocket and Doppler envelope remain unreliably seen |

[Case records](cases.json) link clinical protocols and acquired comparison figures. The acquired figures depict separate visits and retain their own measurements and rights. The exam schematics use authored contrast, anatomy outlines, acoustic shadow, calipers and time traces. Modeled values support the worked calculations for early CRL dating and the BMUS-corrected Robinson–Fleming curve at 11–14 weeks, cardiac cycle rate and Hadlock fetal weight. The separate Hadlock 1991 weight standard provides the plotted 28- and 32-week reference values.

## Omphalocele illustration

The mid-trimester finding pairs the fetal abdominal cord insertion with an [editable SVG](omphalocele-transverse-cutaway.svg). Follow the bowel through the midline defect, then trace the covering membrane to the cord attachment at the sac apex. Compare the transverse `insertion` and `omphalocele-sagittal` chapters with the tissue overlay at evidence frame index 8. Read the 15 mm modeled neck measurement from the transverse acquisition.

The built-in ImageGen tool used the [transverse](views/mid-abnormal-04.svg) and [sagittal](views/mid-abnormal-05.svg) case schematics as references. The generated PNG was traced into separately editable anatomical paths and labeled with SVG text. The trace removes an artificial line across the open neck. The drawing simplifies proportions and bowel geometry. The acquired comparison is a different twin pregnancy. Figure 1B marks bowel herniation in one fetus. [Dahal et al., 2025](https://link.springer.com/article/10.1186/s13256-025-05449-y#Fig1)

The [original ImageGen PNG](omphalocele-source/imagegen-original.png), [generation prompt](omphalocele-source/imagegen-prompt.txt) and [vector tracing recipe](omphalocele-source/trace.py) are retained together. To reproduce the initial editable artwork with OpenCV and NumPy, run `python3 trace.py imagegen-original.png /tmp/omphalocele.svg` from the source directory. The download on the worked case page contains the individual anatomy paths, leader lines and text labels.

## Replay and verification

Run from the repository root with Python 3.12.

```sh
python3.12 experiments/ultrasound-sweep/cases/pregnancy/build.py --output /tmp/pregnancy-worked-replay
python3.12 experiments/ultrasound-sweep/cases/pregnancy/build.py --check
```

The byte check covers the case records, 51 generated schematics and the retained illustration. The payload was checked for 12 unique case IDs, all three outcomes for each stage, parseable SVG, matching time labels and rates, and separate source links for modeled measurements and acquired comparisons. The anatomy diagrams and procedural sketches require sonographer review for clinical coverage and fidelity.

## Playable exams

Open the **Full exams** list in the assembled ultrasound study. Use each case’s chapter picker or its impression links to replay a saved acquisition. The [chapter recipe](playable-chapters.js) binds each acquired plane or signal to a worked view above. The [player adapter](playable.js) computes a probe contact, orientation, imaging plane and crop at each frame. The scan samples that plane through the case geometry. The adjacent locator projects the same contact and crop in the case coordinates. The anatomy overlay tints the visible tissue labels on the same B-mode samples and lists the tissues present in the current frame. The scan, calipers and gated trace retain their coordinates. The locator can rotate about the maternal longitudinal axis while the sampled pose and scan stay registered.

[The volume exporter](build_playable.py) reuses the four existing early, 11–14-week, mid- and late-stage anatomy fields. It records categorical tissue voxels at 0.75–1.8 mm spacing, together with the stage landmarks and maternal transforms used by the chapter recipe. The runtime adds the case-specific sac and yolk sac, nuchal space, abdominal wall defect, calibrated biometry contours and fluid boundaries. It also models attenuation and altered probe approaches for the repeat attempts. The first-trimester cord crop interpolates brightness with the existing samples. M-mode and umbilical artery spectral traces are reconstructed from authored periodic motion or flow envelopes at the marked site.

| Stage | Visit coverage |
| --- | --- |
| Early pregnancy | Abdominal orientation, transvaginal localization, both adnexa and cul-de-sac, and CRL and M-mode when there is an intrauterine embryo to measure. The right tubal case includes a separately visualized ovary and extraovarian yolk-sac rim. The limited right adnexal case has an oblique repeat and retains a residual blind spot. |
| 11–14 weeks | Count, CRL, NT, M-mode, brain, face, spine, stomach, bladder, abdominal insertion, four limbs, placenta and cervix. The limited visit separates the acceptable dating plane from unsuccessful initial and repeat NT attempts. |
| Mid-trimester | Separate biometry, heart rate, cerebral and facial planes, diaphragm and lung fields, four chambers and four great-vessel planes, kidneys and bladder, wall and cord, longitudinal and transverse spine, all limbs and digits, placenta, cervix and fluid. The finding is confirmed across two wall planes. Each limited great-vessel view has an alternate acquisition. |
| Third trimester | Lie, placenta, maternal vertical fluid pocket, HC, AC and FL, 28- to 32-week estimated-weight comparison, and a free-loop sample. Absent flow is confirmed at a second position. The limited case reattempts AC, fluid and the arterial waveform before restricting the impression. |

Use the ultrasound builder’s Python environment to reproduce the four volumes and run the CPU acceptance checks.

```sh
python experiments/ultrasound-sweep/cases/pregnancy/build_playable.py --check
node experiments/ultrasound-sweep/cases/pregnancy/verify-playable.mjs
```

The CPU check exercises every route and verifies that every worked view maps to a changing, registered chapter. It checks sampled anatomy at selected evidence frames, confirms the ectopic ring and tissue-anchored labels, compares primary and repeat paths, checks overlay pixels and shadow boundaries, and verifies the authored measurement and waveform results. Locator checks cover both endpoints of the orbit slider. The probe contact shell and acoustic intensity are schematic. The image zooms and grading support modeled teaching use. Clinical coverage and fidelity still require sonographer review.
