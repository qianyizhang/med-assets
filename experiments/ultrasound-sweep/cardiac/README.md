# Apical four-chamber beat

Hold the probe still and follow the mitral leaflets from closure through opening. The first adult transthoracic study lives under **Study → Heart → Apical four chamber** in the local ultrasound gallery. **Plane rotation** turns the probe about its central beam. **Cardiac phase** sets time independently. Orbiting changes only the observer. [Captured beat](review/beat.webp) · [Default view](review/study.webp)

## What moves

One original set of chamber surfaces in [heart-geometry.js](heart-geometry.js) supplies the spatial cutaway, section contours, B-mode tissue boundaries and overlay. The apex is near the probe, screen right is patient left, and the tricuspid annulus sits closer to the apex than the mitral annulus. Both annuli move toward the apex during contraction. Inner ventricular surfaces narrow more than outer surfaces, while the atria act as reservoirs. Two intersected leaflet profiles represent each atrioventricular valve. The cycle wraps in 980 ms. The [ASE adult examination guide](https://www.asecho.org/wp-content/uploads/2019/01/2019_Comprehensive-TTE.pdf) describes the A4C window.

The earlier [beating-heart imaging package](../../../heart/synthetic-imaging/beating-heart/imaging/README.md) samples its own atlas at end diastole. Its oblique fan is illustrative and carries no phase-resolved A4C acquisition. This study authors its A4C geometry and speckle independently. Echodemo’s Views and Cycle chapters informed the shared heart, plane and phase interaction. All geometry, textures and code here were written for this study. [Echodemo](https://github.com/douyang/echodemo)

**Flow timing** defaults off. Its text uses the same phase state as the leaflets. Both valve sets close during the modeled isovolumetric intervals. Inflow follows atrioventricular reopening, slows during diastasis and rises again with atrial contraction. Ejection travels out of this image plane. Drawing a jet across A4C would suggest a direction or velocity this section cannot establish. The prescribed wall motion does not conserve blood volume across the two circuits. Pressures, stroke volumes and Doppler measurements are outside its scope. [University of Minnesota cardiac physiology](https://www.vhlab.umn.edu/atlas/physiology-tutorial/the-human-heart.shtml)

## Acquired comparison

The acquired **A4C normal** loop is credited to I.A.C. van der Bilt, MD (Vdbilt), Dept. of Echocardiography, AMC, via CardioNetworks / ECHOpedia. Its source describes a normal heart and gives no subject age. All 50 acquired frames retain the source markings and orientation. The tiled WebP and [matched-landmark plate](review/landmarks.webp) use the same CC BY-SA 3.0 license. The plate resizes and arranges the original frames beside independent model captures. [Acquisition record and byte identities](acquisition.json) · [Original cine](https://commons.wikimedia.org/wiki/File:A4C_normal_(CardioNetworks_ECHOpedia).webm) · [Full license](CC-BY-SA-3.0.txt)

| Model stop | Acquired frame, zero-based | What to compare |
| --- | --- | --- |
| End diastole, 0% | 2, 0.039 s | The LV is long and wide. The AV plane lies farther from the apex than at end systole. The late-diastolic mitral leaflets approach coaptation around this landmark. |
| End systole, 35% | 18, 0.353 s | The LV pool is narrower, the annuli are nearer the apex and the atrial pools are larger. The mitral leaflets span the inlet. |
| Early filling, 52% | 26, 0.510 s | The visible mitral leaflet tips separate into the LV, which begins to widen again. The source tricuspid tips are less distinct. |

These are visual matches across cases. The player interpolates monotonically between the three selected landmarks, then wraps to the first one. The acquisition stays at its recorded angle during model rotation. The model shows a cleaner lateral border, smoother chamber interiors and more conspicuous leaflet edges than the acquired cine. The posterior 3D view reveals joins between the lofted walls. No patient-specific registration, torso contact model, strain validation or independent sonographer review was performed.

## Replay

Use the [ordinary gallery assembly](../README.md#replay) with the LFS media hydrated. From the repository root, point the assembler at the existing generated sweep stage and use a fresh delivery directory.

```sh
python experiments/ultrasound-sweep/assemble_tours.py "$STUDY_OUTPUT" --delivery "$ECHO_GALLERY"
python3 -m http.server 8886 --bind 127.0.0.1 --directory "$ECHO_GALLERY"
```

Open [the cardiac study](http://127.0.0.1:8886/cardiac/). The textual geometry and rendering modules need no build step. The assembler checks the acquired sheet against its pinned SHA-256. To reproduce the sheet from the pinned WebM, FFmpeg 8.1 decoded and tiled the 50 frames, then Pillow 11.3.0 encoded the result.

```sh
ffmpeg -i a4c-normal.webm -vf 'scale=520:400:flags=lanczos,tile=10x5' -frames:v 1 sheet.png
python -c "from PIL import Image; Image.open('sheet.png').save('acquired-a4c.webp', quality=90, method=6)"
```

Run the [geometry checks](verify-cycle.mjs) with Node 24+. In the gallery Playwright environment, run the browser check against the assembled root. Its optional second argument captures the live interface, 25 fixed-pose phases and the matched cine panels.

```sh
node experiments/ultrasound-sweep/cardiac/verify-cycle.mjs
node experiments/ultrasound-sweep/cardiac/verify-browser.mjs http://127.0.0.1:8886/ .artifacts/echo-review/browser
```

The retained loop presents those 25 browser-rendered phases over one 980 ms beat. The browser check also exercises continuous playback, reduced motion, phase scrubbing, independent rotation, orbit, overlay, reference failure/retry, model failure and gallery return. The geometry check exercises 100 phases at three plane angles, the closed-loop boundary, valve coaptation and opening, annular motion, wall thickening and changes in chamber section area. These checks establish behavior of the teaching model.
