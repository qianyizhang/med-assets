# Worked vascular ultrasound cases

Open [Tours → AAA screening](http://127.0.0.1:8874/tours/aaa/index.html) to compare the three screening outcomes. This package also contains three bilateral carotid duplex cases. Each visit has its own ordered stationary images, saved measurements, impression and acquisition limitations. The positive AAA visit continues into a diagnostic characterization of the same modeled aneurysm. The limited visits record both the initial window and an alternate attempt. The schematics preserve anatomy and relative measurement relationships for the worked examples. The three cases share the torso, probe and sector presentation of the [CT aortic sweep](../../README.md). The [tracked duplex atlas](../../carotid-survey/README.md) supplies the separate carotid acquisition study.

## Sources and boundaries

- AAA interpretation and acquisition follow the cited AIUM aorta parameter. The three normal AP values start from the approximate segmented spans in the existing screening tour. The bifurcation, iliac vessels, outer walls, aneurysm, thrombus and obscured windows are original teaching geometry. Transverse and longitudinal AP calipers represent the same physical span in the authored model. The screening report and diagnostic characterization use the complete sac outline, including the modeled thrombus. The linked CC0 acquired image by Mikael Häggström belongs to an independent case. Inspect its mural thrombus alongside the modeled sac sections. [AIUM parameter](https://doi.org/10.1002/jum.70167) · [Acquired mural-thrombus comparison](https://commons.wikimedia.org/w/index.php?title=File:Ultrasonography_of_abdominal_aortic_aneurysm_with_mural_thrombus.jpg&oldid=1264972910)
- Carotid documentation follows IAC §1.6B and §1.7B for native, unstented vessels. The authored spectra show two synthetic cycles with PSV and EDV tied to the modeled envelope and use a consistent 250 cm/s scale. The plaque visit uses the modified IAC criteria and the peak from the focal jet relative to its ipsilateral distal CCA. The linked Li et al. figure shows a separate, higher-grade lesion. Panel A shows eccentric grayscale plaque and panel B shows the color sample and accompanying acquired spectrum. [IAC documentation](https://intersocietal.org/wp-content/uploads/2026/08/IACVascularTestingStandardsAug2026.pdf#page=24) · [IAC modified SRU criteria](https://intersocietal.org/document/carotid-stenosis-interpretation-criteria/) · [Acquired comparison, Figure 1A–B](https://cdn.amegroups.cn/journals/amepc/files/journals/2/articles/61527/public/61527-PB6-2943-R2.pdf#page=3)

The linked acquired comparisons have their own instrumentation, settings and severity. Both links open original publication material. The calibrated plates are original SVG schematics. They model static landmarks and selected waveform relationships. Independent sonographer review of clinical coverage and fidelity remains open.

### Generated cutaway

The positive AAA visit pairs its maximum section with an [ImageGen anatomical cutaway](aaa-transverse-cutaway.webp). The reference was the transverse overlay at frame 15 of the sac-maximum chapter in revision `140e352`. The generation brief called for an anterior residual lumen, a posterior crescent of mural thrombus and three labeled boundaries. The selected image preserves that relationship. Its perspective and tissue textures are illustrative. Read the calibrated dimensions from the [saved exam frame](http://127.0.0.1:8874/tours/aaa/aaa-positive.html?chapter=sac-maximum&frame=14#exam). The independently acquired comparison shows a different distribution of thrombus in another patient.

The retained WebP is the delivery master. Its case record pins the exact bytes for assembly. The case builder regenerates the calibrated SVGs and rebinds the retained illustration.

## Replay

Run with Python 3.11+ from the repository root. The destination accepts a fresh directory for byte-for-byte comparison. With no destination, the generator updates the consumer-ready JSON and SVGs in this package.

```sh
python3.12 experiments/ultrasound-sweep/cases/vascular/build_cases.py "$VASCULAR_REPLAY"
```

The six visit records in [cases.json](cases.json) bind each named view to an SVG beside it. The generator embeds the case data and annotations. No private inputs, subscriptions or downloads are needed for replay.

## Playable exams

The aortic player uses a continuous authored vessel volume through the common iliac split. The sac includes distinct lumen, mural thrombus and outer-wall regions. Orthogonal sampling supplies the maximum transverse and AP calipers, and long-axis color separates the sac outline from the residual channel. The limited anterior and lateral beam paths have separate orientations and retain the distal blind spot.

The carotid player sweeps through the CCA fork into the ICA and ECA. Each side has its own grayscale, color and pulsed-wave windows. The abnormal right ICA uses a continuous eccentric plaque profile. The narrowest residual lumen and the unaffected distal lumen reproduce the paired short-axis estimate. PW velocities are authored along vessel paths and depend on the sampled gate location. The flow traces illustrate changes in velocity and spectral width. They do not solve blood flow or model scanner calibration.

The [carotid case adapter](playable-scene.js) uses the B-mode acquisition basis to place its linear probe and scan plane on the fitted neck. The vessel surfaces use the same wall, lumen and plaque geometry as the sampled section. Outer and inner walls meet in an annular rim at each editorial cut. Adaptive station spacing follows both wall and lumen error. The [qualification review](../../development/asset-reviews/vascular/README.md) compares the revised openings, contours and mesh costs with the original capped segments. The AAA cases use the registered aortic sweep scene. The original atlas packages offer complementary probe and anatomy views. Their acquired examples and contours supply comparison context. Their images are independent of the authored cases here. Run the focused replay from the repository root.

```sh
node experiments/ultrasound-sweep/cases/vascular/verify-playable.mjs
```

The tissue overlay reuses each grayscale sample’s tissue classification, with the same acoustic shadow applied before labeling. At the maximum sac section, the outer wall, mural thrombus and residual lumen have separate colors. The carotid and iliac branches are labeled only where sampled.

The registered AAA presentation places the authored arterial wall, lumen and iliac branches inside the normal sweep’s fitted BodyParts3D torso. Its [acquisition recipe](../../aaa_acquisition.py) uses the s1233 CT and masks, with native vessels locally removed before sampling the case vessels. Registration fits the trunk to the native aortic axis and preserves transverse dimensions. The positive variant moves anteriorly just far enough for the enlarged sac to clear the segmented spine. The acquisition receipt records that offset. Probe contact is computed against the fitted torso for each frame, including the left lateral repeat. The shared renderer displays that frame’s contact, beam and sector. B-mode and the anatomy overlay sample the same plane. The positive long-axis views offer an illustrative patent-channel color display. The limited distal views model an acoustic shadow and withhold calipers. These are authored case variants within one anatomical context.

The [AAA browser check](../../tours/aaa/verify-tours.mjs) exercises the three tours, saved measurements, camera controls, case differences and isolated failures of scan images and 3D display. The [vascular model check](verify-playable.mjs) also exercises the original procedural scan projection and vessel surfaces.
