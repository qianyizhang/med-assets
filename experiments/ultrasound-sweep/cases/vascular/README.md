# Worked vascular ultrasound cases

Compare three AAA screening outcomes and three bilateral carotid duplex outcomes. Each visit has its own ordered stationary images, saved measurements, impression and acquisition limitations. The positive AAA visit continues into a diagnostic characterization of the same modeled aneurysm. The limited visits record both the initial window and an alternate attempt. The schematics preserve anatomy and relative measurement relationships for the worked examples. The existing [CT aortic sweep](../../README.md) and [tracked duplex atlas](../../carotid-survey/README.md) remain the anatomy and acquisition interaction packages.

## Sources and boundaries

- AAA interpretation and acquisition follow the cited AIUM aorta parameter. The three normal AP values start from the approximate segmented spans in the existing screening tour. The bifurcation, iliac vessels, outer walls, aneurysm, thrombus and obscured windows are original teaching geometry. Transverse and longitudinal AP calipers represent the same physical span in the authored model. The screening report and diagnostic characterization use the complete sac outline, including the modeled thrombus. The linked CC0 acquired image by Mikael Häggström belongs to an independent case. Inspect its mural thrombus alongside the modeled sac sections. [AIUM parameter](https://doi.org/10.1002/jum.70167) · [Acquired mural-thrombus comparison](https://commons.wikimedia.org/w/index.php?title=File:Ultrasonography_of_abdominal_aortic_aneurysm_with_mural_thrombus.jpg&oldid=1264972910)
- Carotid documentation follows IAC §1.6B and §1.7B for native, unstented vessels. The authored spectra show two synthetic cycles with PSV and EDV tied to the modeled envelope and use a consistent 250 cm/s scale. The plaque visit uses the modified IAC criteria and the peak from the focal jet relative to its ipsilateral distal CCA. The linked Li et al. figure shows a separate, higher-grade lesion. Panel A shows eccentric grayscale plaque and panel B shows the color sample and accompanying acquired spectrum. [IAC documentation](https://intersocietal.org/wp-content/uploads/2026/08/IACVascularTestingStandardsAug2026.pdf#page=24) · [IAC modified SRU criteria](https://intersocietal.org/document/carotid-stenosis-interpretation-criteria/) · [Acquired comparison, Figure 1A–B](https://cdn.amegroups.cn/journals/amepc/files/journals/2/articles/61527/public/61527-PB6-2943-R2.pdf#page=3)

The linked acquired comparisons have their own instrumentation, settings and severity. Both links open original publication material. All local plates are original SVG schematics. They model static landmarks and selected waveform relationships. Independent sonographer review of clinical coverage and fidelity remains open.

## Replay

Run with Python 3.11+ from the repository root. The destination accepts a fresh directory for byte-for-byte comparison. With no destination, the generator updates the consumer-ready JSON and SVGs in this package.

```sh
python3.12 experiments/ultrasound-sweep/cases/vascular/build_cases.py "$VASCULAR_REPLAY"
```

The six visit records in [cases.json](cases.json) bind each named view to an SVG beside it. The generator embeds the case data and annotations. No private inputs, subscriptions or downloads are needed for replay.

## Playable exams

The aortic player uses a continuous authored vessel volume through the common iliac split. The sac includes distinct lumen, mural thrombus and outer-wall regions. Orthogonal sampling supplies the maximum transverse and AP calipers, and long-axis color separates the sac outline from the residual channel. The limited anterior and lateral beam paths have separate orientations and retain the distal blind spot.

The carotid player sweeps through the CCA fork into the ICA and ECA. Each side has its own grayscale, color and pulsed-wave windows. The abnormal right ICA uses a continuous eccentric plaque profile. The narrowest residual lumen and the unaffected distal lumen reproduce the paired short-axis estimate. PW velocities are authored along vessel paths and depend on the sampled gate location. The flow traces illustrate changes in velocity and spectral width. They do not solve blood flow or model scanner calibration.

Both players evaluate the same millimetre-based anatomy and plane for the scan and locator. The original atlas packages offer complementary probe and anatomy views. Their acquired examples and contours supply comparison context. Their images are independent of the authored cases here. Run the focused replay from the repository root.

```sh
node experiments/ultrasound-sweep/cases/vascular/verify-playable.mjs
```

The tissue overlay reuses each grayscale sample’s tissue classification, with the same acoustic shadow applied before labeling. At the maximum sac section, the outer wall, mural thrombus and residual lumen have separate colors. The carotid and iliac branches are labeled only where sampled. The locator’s transverse contours and longitudinal cutaway use the vessel model at the active scan plane. Orbiting the locator changes the viewpoint while preserving the saved acquisition and caliper positions.

The scan viewport fits the complete field with one pixels-per-millimetre scale for its two orthogonal axes. Padding around narrower images preserves the shape of the sampled anatomy. The regression checks both the displayed caliper lengths and the rasterized outer wall at the maximum AAA section.
