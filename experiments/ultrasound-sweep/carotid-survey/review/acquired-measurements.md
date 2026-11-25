# Carotid duplex measurement review

This review uses the original published pixel data and the registered gates in the assembled local survey from geometry revision `da9f323`. Modeled results use the centered gate, its registered angle at about 60°, 5 MHz, and 6.5 kHz PRF. Acquired values come from independent subjects. Compare waveform shape and teaching landmarks without treating the differences as measurement error against a patient reference.

The reviewed `protocol-geometry.json` has SHA-256 `a177f0c2caa856006f3819797b4ab0124f00247e276e69eb70f4292310888dd3`.

| Station and correspondence | Acquired spectrum, PSV / EDV (cm/s) | Modeled spectrum, PSV / EDV (cm/s) | Scope |
| --- | ---: | ---: | --- |
| Right distal CCA, same segment and longitudinal plane | 103 / 21.4 at displayed 60° | 71.0 / 16.0 | Both show a fast upstroke and sustained diastolic flow. The acquired contour has additional fine systolic structure. |
| Right ICA, longitudinal, exact level unreported | 36.46 / 12.15 as magnitudes | 83.0 / 26.0 at proximal ICA | Both show forward diastolic flow. Source angle text is marginal in the published original, and the station match is provisional. |
| ECA, longitudinal, side and level unreported | 54.48 / 10.22 as magnitudes, displayed 55° | 76.0 / 8.2 right and 73.0 / 7.9 left | Compare the more resistive curve in the source S portion. The W portion includes temporal tapping. |
| Right vertebral artery, longitudinal, exact cervical level unreported | 32.82 / 15.04 as magnitudes, displayed 55° | 48.0 / 18.0 | Sustained diastolic flow in both. Opposite color in the adjacent acquired vein illustrates beam-relative direction. |
| Subclavian artery, mid-to-distal longitudinal infraclavicular source | No scale | 95.8 / 2.0 right and 91.9 / 1.9 left | Compare the triphasic sequence of forward systole, early reversal, and renewed forward flow. The figure panel leaves the side and arm position unspecified. |

The source displays preserve the instrument axis, inversion, and signs. The table uses magnitudes for the reported Lee velocities. The model shows positive or negative spectral velocities according to its own gate and beam. The ratios of peak observed ICA PSV to ipsilateral distal CCA PSV are about **1.17 on both sides**. The two model sides share waveform profiles and their side factors cancel in the ratio. The independent acquired sources do not provide paired ICA and CCA observations, so no acquired ratio is calculated.

The [right distal CCA comparison plate](distal-cca-measurements.webp) shows a **6.1 ± 0.6 mm** visual lumen estimate in the acquired image and a **7.8 mm** projected inner-wall span in the model. In the native 2048 × 1536 acquired figure, the 0, 2, and 3 cm ticks are approximately `(1675, 122)`, `(1664, 641)`, and `(1657, 892)`, with pixel origin at the upper left. The selected near and far inner echoes are `(1440, 412)` and `(1440, 568)`, beyond the Doppler color overlay and laterally displaced from the scanner gate. At the earlier x ≈ 865 pick near the gate, the color fill abuts the near wall. The revised measurement uses the clear grayscale wall interfaces. The `156 px × 30 mm / 770 px` calculation uses vertical depths in a photographed display. The ruler's approximately 18-pixel diagonal drift, local wall slope, and visual edge picks limit precision. The uncertainty is an approximate reading tolerance. Cardiac phase and pose are unspecified, and the compared caliper spans use different sites within their respective distal CCA views. The acquired PSV/EDV numbers remain the original scanner measurements at the scanner gate.

The modeled wall points project to approximately `(81.38, 185.15)` and `(81.37, 237.15)` on the 280 × 302-pixel image. Applying its 0.15 mm/pixel calibration gives the displayed 7.8 mm. The model spectrum is plotted directly from the centered registered gate output. The other acquired images lack a suitable lumen ruler or adequately matched vessel level. The cropped Ahlgren CCA image shows 5 mm annotation lines along the vessel, with no independently verified axial pixel scale.

The left subclavian example illustrates a separate geometric limit. Its image-plane left-to-right span is 22.6 mm, while the longitudinal wall-to-wall gate chord is 4.7 mm. The former is a span of an oblique section through a bending vessel. It should be recorded as an image-plane distance for that view.

- [Right distal CCA, Vascular Sonography Figure 10-36](https://pressbooks.palni.org/ultrasoundphysicsanditsapplicationinmedicine/chapter/vascular-sonography/)
- [ICA, ECA and vertebral spectra, Lee Figures 1 and 6](https://pmc.ncbi.nlm.nih.gov/articles/PMC4058969/)
- [Subclavian waveform, Bishop and Bartlett Figure 2](https://doi.org/10.1177/20480040211006571)
- [AIUM 2026 angle-corrected spectral acquisition guidance](https://doi.org/10.1002/jum.70476)
