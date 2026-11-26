# Worked ultrasound cases

[Browse tours](http://127.0.0.1:8874/tours/index.html) or [open the casebook](http://127.0.0.1:8874/cases/index.html) from the local ultrasound study. Select an exam family and a referral. The player follows a single modeled visit through its ordered chapters. Play the whole exam, select a chapter, scrub with the exam position slider or select a measurement or observation to restore its evidence frame. **Tissue overlay** labels the sampled tissue in the B-mode frame. **Orbit** rotates the modeled anatomy, probe and field together while preserving the scan. The casebook collects the corresponding labeled plates and source images. Use **Views in this case** to jump to a particular acquisition and **Acquired comparisons** to inspect independently sourced clinical images. A limited visit shows what the repeat attempt resolved and what the report must leave open.

| Package | Material |
| --- | --- |
| [Vascular](vascular/README.md) | Negative, positive and indeterminate AAA screens, diagnostic aneurysm characterization, and bilateral carotid duplex with focal stenosis and limited visualization. |
| [Abdominal and superficial organs](organs/README.md) | Abdominal survey, biliary and urinary tract exams, thyroid and nodules, bilateral breast screening, and targeted retroareolar and axillary findings. |
| [Pregnancy](pregnancy/README.md) | Early location and dating, the 11–14-week scan, mid-trimester anatomy and third-trimester interval growth. Each stage has its own independent cases. |
| [Adult echo](echo/build.mjs) | A normal baseline, a high-gradient aortic stenosis case with two CW Doppler windows, and an incomplete jet envelope. The LV volumes and RV area change use the same chamber contours as the interactive echo study. Velocities are prescribed. The mean gradient integrates the squared velocity across ejection. |

The material implements the [ten scenarios in the completion survey](../../../docs/gallery/use-cases/ultrasound-anatomy.md#next-batch) as playable visits with accompanying illustrated records. A plate can model a wall boundary, sample gate, fetal pose or acquisition limitation. Acquired images belong to separate exams and carry their original credit and terms. The four pregnancy stages reuse the underlying anatomy volumes. The adult heart uses the same beating geometry and registered windows as the standalone echo study. Abdominal, superficial-organ and vascular visits use case-specific modeled anatomy. Case Doppler signals are illustrative. The separate sweep and duplex atlas routes retain their original scope. Sonographer review of clinical coverage, anatomy and fidelity is pending.

## Replay and review

Run the [usual tour assembly](../README.md#replay) with the desired regional sweeps and hydrated echo and case-comparison media. It writes each visit under `tours/<family>/` and its worked reading page under `cases/`. The shared timeline runs across the visit’s acquisitions. A report link seeks to its saved frame, and **Open standalone sweep** opens that acquisition at the displayed frame. The former `exams/` addresses forward saved bookmarks. Direct case links and the reading sequence also work with JavaScript disabled. A partial assembly includes the case pages and only offers locally available sweep comparisons.

From the repository root, run:

```sh
python3.12 experiments/ultrasound-sweep/cases/verify_cases.py
python3.12 experiments/ultrasound-sweep/verify_assembly.py "$STUDY_OUTPUT"
node experiments/ultrasound-sweep/tours/aaa/verify-tours.mjs http://127.0.0.1:8874/ "$AAA_CAPTURES"
node experiments/ultrasound-sweep/tours/verify-case-geometry.mjs "$STUDY_DELIVERY"
node experiments/ultrasound-sweep/cases/vascular/verify-surfaces.mjs "$STUDY_DELIVERY"
node experiments/ultrasound-sweep/tours/verify-case-tours.mjs http://127.0.0.1:8874/ "$EXAM_CAPTURES"
node experiments/ultrasound-sweep/cases/verify-browser.mjs http://127.0.0.1:8874/ "$REVIEW_CAPTURES"
```

Set `STUDY_DELIVERY` to the complete assembled study directory. The geometry check inspects scan axes, crop registration and sampled external probe contacts against the delivered meshes. The cardiac package supplies its own chest-contact check. Use the same Python environment and Playwright configuration as the sweep package. The replay check covers the case records and diagrams. The browser check opens every case from the assembled family index, decodes its illustrations and checks the study entry points and laptop layout. Its optional capture directory receives the catalogue, selected worked cases and plate contact sheets.

The AAA check exercises the composed tours, their standalone sweeps, finding links and legacy bookmarks. The case tour browser check advances every sampled frame on the shared timeline. It follows saved evidence into the standalone sweeps, verifies that changing sections preserves orbit and overlay settings, and exercises older exam bookmarks. The package records document geometry, calibration and known fidelity limits. [Acquired finding sources and original-media replay](acquired/README.md)

## Editable anatomy and B-mode assets

The family scene adapters provide case geometry in patient coordinates to the [shared case scene](../case-scene.js). The [3D modeling standard](../../../docs/gallery/use-cases/ultrasound-anatomy.md#3d-modeling-standard-for-sweeps-and-tours) defines the relationship to standalone sweeps and the checks at a saved finding.

| Family | Geometry, acquisition and inspection |
| --- | --- |
| Aorta and carotids | [Vessel centerlines, walls, lumens, thrombus and plaque](vascular/playable-model.js) · [probe paths, tissue sampling and spectra](vascular/playable.js) |
| Abdomen, thyroid and breast | [Abdominal anatomy](organs/playable-abdomen.js) · [neck and breast anatomy](organs/playable-neck-breast.js) · [physical planes and caliper intersections](organs/playable-geometry.js) · [B-mode and overlay](organs/playable-render.js) |
| Pregnancy | [Stage volume recipe](pregnancy/build_playable.py) · [case-specific anatomy](pregnancy/playable-model.js) · [acquisition planes and measurements](pregnancy/playable-chapters.js) · [B-mode, labels and time traces](pregnancy/playable.js) |
| Adult echo | [Beating heart geometry](../cardiac/heart-geometry.js) · [cardiac section intersections](../cardiac/heart-slice.js) · [B-mode renderer](../cardiac/heart-echo.js) · [case-specific valve, calipers, spectra and 3D view](echo/playable.js) |

The source assets use physical coordinates. At a saved observation, the player applies the same case, plane and time to the tissue rendering and calipers. The 3D camera can orbit independently. Chapter links in the reading pages and numeric links in the exam report point to exact saved acquisitions. The companion SVGs can be reproduced from their family recipes.
