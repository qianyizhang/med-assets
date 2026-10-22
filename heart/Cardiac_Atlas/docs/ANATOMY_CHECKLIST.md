# Anatomy and imaging teaching checklist

This is a practical review checklist, not certification of clinical accuracy. The model is representative procedural geometry, not patient-derived segmentation or a physiological simulation.

## Core anatomy
- RV is anterior and wraps the LV; LV has the thicker wall and forms the apex. Atria are thinner-walled; LA is posterior. Avoid symmetric four-lobe geometry.
- Cavae enter RA; tricuspid connects RA/RV; pulmonary outflow connects RV to pulmonary trunk and right/left pulmonary arteries. Pulmonary veins enter LA; mitral connects LA/LV; aortic outflow connects LV to ascending aorta.
- Representative normal anatomy: four pulmonary veins and three arch branches (brachiocephalic trunk, left common carotid, left subclavian). Variants exist.
- Mitral has two primary leaflets; tricuspid three; aortic and pulmonary valves each three pocket-like cusps. Chordae and papillary muscles support AV valves only. Leaflets respond to pressure; papillary muscles prevent prolapse rather than actively opening valves.
- Distinct interatrial/interventricular septa; no unintended circuit-crossing holes. Endocardium lines cavities, myocardium is muscular wall, epicardium covers exterior. Pericardium is a separate enclosing sac.
- Coronary arteries start at aortic sinuses: left main divides into LAD and circumflex; RCA follows right AV groove. Representative right dominance includes PDA from RCA. Veins drain via great/middle/small cardiac veins and posterior coronary sinus into RA; actual venous patterns vary.

References:
- https://www.vhlab.umn.edu/atlas/anatomy-tutorial/cardiac-valve-nomenclature.shtml
- https://www.vhlab.umn.edu/atlas/comparative-anatomy-tutorial/ventricles.shtml
- https://www.vhlab.umn.edu/atlas/external-images/anterior/
- https://www.vhlab.umn.edu/atlas/physiology-tutorial/the-human-heart.shtml
- https://www.vhlab.umn.edu/atlas/coronary-system-tutorial/what-is-the-coronary-system.shtml
- https://www.vhlab.umn.edu/atlas/coronary-system-tutorial/coronary-venous-anatomy.shtml
- https://openstax.org/books/anatomy-and-physiology-2e/pages/19-1-heart-anatomy
- https://www.ncbi.nlm.nih.gov/sites/books/NBK499911/

## Motion and presentation
- Atrial contraction precedes ventricular contraction. AV valves open during filling, closed during ejection. Semilunar valves do the opposite; both sets are closed during isovolumetric contraction and relaxation.
- Do not empty ventricles completely or move particles through closed valves/walls. If inlet/outlet tunnels are absent, disclose that lumen continuity is simplified.
- A short animation is illustrative, not CFD or a calibrated measurement. Tissue shading is procedural. Blue/red are teaching colors, not natural blood/tissue colors.
- End-diastolic static slices must not be presented as corresponding to a differently phased animated mesh.
Reference: https://openstax.org/books/anatomy-and-physiology-2e/pages/19-3-cardiac-cycle

## Imaging geometry and limits
- State RAS/LPS convention, units, model-to-patient affine and phase. Patient right is not screen right. RAS/LPS conversion reverses first two coordinate axes.
- Cardiac short-axis planes are orthogonal to LV long axis, not necessarily patient axial. A generic long-axis or coronal plane is not automatically standard four-chamber.
- Generated intensity/speckle images illustrate geometry only. Do not call arbitrary intensities HU, MRI signal, Doppler velocity, or scanner simulation.
- Independent real reference images are not registered to the model or phase-matched; retain provenance and licenses.
References:
- https://slicer.readthedocs.io/en/5.10/user_guide/coordinate_systems.html
- https://www.ncbi.nlm.nih.gov/books/NBK606871/bin/15-48-20-supp1.pdf

## Bounded review of current renders and copy, 2026-10-20
Viewer English/Chinese copy reviewed without material misleading anatomy/physics claim spotted. Clinical limitations, arbitrary intensities, static reference phase, virtual US sector and unregistered references are appropriately qualified. This was a copy review, not a clinical validation.

Diagnostic cutaway and tissue-hero renders show thick LV, thinner RV and reasonable vessel hierarchy. Items requiring source-level verification: continuity of chamber inlets/outlets, tall cuff-like AV leaflet appearance (builder reported subsequent revision), and abrupt pulmonary trunk/branch junction. Current procedural representation should retain an idealized teaching label.

### Final implementation note
The final AV geometry uses separate scalloped leaflets rather than the earlier tall cuff. Ventricular trabeculae were shortened and embedded in the wall, and representative coronary paths were revised to follow the surface. The lumen-continuity concern remains an explicit limitation: reference pools are closed for sampling and adjoining structures can overlap rather than form one watertight flow network. No flow traversal or physiological simulation is claimed. These changes do not constitute clinical validation.
