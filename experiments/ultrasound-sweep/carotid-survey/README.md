# Bilateral carotid duplex exam

Open the [combined exam](http://127.0.0.1:8874/carotid-survey/). **Play exam** follows the transverse stack and the named grayscale, color and spectral views on the right, then the left. Pause to move the probe through the stack, inspect an acquired comparison, place calipers or adjust the sample gate. The measurement record persists in this browser tab for the current dataset.

Each side has nine stations covering proximal and distal common carotid artery (CCA), bulb and bifurcation, proximal/mid/distal internal carotid artery (ICA), external carotid artery (ECA), vertebral artery and subclavian artery. The atlas shows a normal-anatomy teaching example. This exam demonstrates acquisition and documentation. Independent clinical and sonographer review remains open. [Study specification](../../../docs/gallery/use-cases/ultrasound-anatomy.md#bilateral-carotid-duplex-exam) · [IAC extracranial cerebrovascular documentation, §1.7B](https://intersocietal.org/wp-content/uploads/2026/08/IACVascularTestingStandardsAug2026.pdf#page=24)

## Measurement and reconstruction

- **Distance.** Two image calipers use the saved scan's physical pixel spacing. Record a wall-to-wall span by placing them at opposite inner walls of the chosen section. During playback the two distal CCA long-axis views place and save their own modeled spans (7.8 mm right and 7.7 mm left). A manually placed caliper keeps its own record and exact scan image. Oblique sections can give a longer span than the vessel’s perpendicular diameter.
- **Velocity.** Each sample gate has a location, length, arterial flow axis and steered beam. The modeled pulsed-wave spectrum responds to gate position, flow profile, angle correction and pulse repetition frequency. Peak systolic velocity (PSV) and end-diastolic velocity (EDV) come from the trace. The ipsilateral ICA/CCA ratio uses the highest saved ICA PSV across its three stations and the distal CCA PSV. Invalid or aliased acquisitions withhold the measurement. All velocities are simulated.
- **Lumen surface.** The transverse stack records image planes and binary lumen masks in native right–anterior–superior millimetres. Masks come from visible intersections with the teaching model. The reconstruction maps those masks to a common volume, interpolates their signed distances and extracts the measured surface. Mask data and probe poses are the only inputs to this step. The orbitable view distinguishes acquired from remaining sections. A complete side exports its reconstructed surface as PLY.
- **B-mode volume.** A separate process projects the decoded grayscale scan pixels into the same anatomical coordinates. Adjacent sections support interpolation where both fields overlap. The [volume viewer](http://127.0.0.1:8874/carotid-survey/volume.html) provides linked transverse, coronal and sagittal sections. A calibrated signed 16-bit NRRD carries these grayscale samples and the spatial header. Values 0–255 are modeled B-mode intensities. −1 marks unobserved space.
- **Coverage.** The surface follows the observed cervical CCA and ICA/ECA branches. The transverse stack ends before the carotid canal and the deep origins. Vertebral and subclavian stations have their own scan and Doppler measurements. They are outside the carotid lumen reconstruction.

[Three tracked model sections and the reconstructed right carotid](review/stitched-carotid.webp) show the common trunk and its two daughters. The acquisition has 117 transverse sections over 139 mm on the right and 124 over 148 mm on the left. Each reconstructed artery tree is connected through the fork. Median intersection-over-union against held-out teaching-model sections is 0.988 on each side, with 97.8% of the reference lumen area recovered within each acquired slab. The fine outlines mark arterial pixels used in the reconstruction. The adjacent jugular stays visible in grayscale.

## Anatomy and comparisons

The atlas contributes named arteries, jugular veins, cervical tissues, bones and regional skin patches in one frame. The probe view draws the original exterior faces with consistent outward winding. The acquisition uses the sealed atlas skin for contact calculations. Across 279 scan-center rays and 18 Doppler rays, the displayed exterior and the acquisition surface gave the same first intersection to numerical precision. [Matched neck views](review/neck-exterior.webp)

The two source branches start at the CCA endpoint but their beveled surfaces overlap for several centimetres. A bounded [branch correction](branch_geometry.py) separates the daughter tubes along the native interbranch direction and preserves their cross-sectional sizes, shared origin and superior courses. Its maximum displacement is about 3.4 mm per daughter. The reconstructed lumen is evaluated against this disclosed teaching geometry. The bilateral atlas uses largely mirrored distal courses. Velocity profiles, scatter and near-field tissue texture are authored.

Over the acquired length, an independent 3D comparison of the exported surfaces measured 0.975 right and 0.977 left intersection-over-union with the teaching geometry. Against the original atlas these values are 0.825 and 0.831. In the uppermost millimetre of each stack, about 59–60% of the teaching-model lumen is recovered. **Compare lumen** in the volume viewer overlays the stitched lumen and teaching-model boundary at the selected slice. [Original atlas and teaching-model comparison](review/source-vs-stitch.webp) · [Bilateral metrics and mesh hashes](review/source-vs-stitch.json)

The earlier [right](http://127.0.0.1:8874/index.html?sweep=carotid-right) and [left](http://127.0.0.1:8874/index.html?sweep=carotid-left) CT orientation sweeps remain separate cases.

Model credit is **Z-Anatomy – The libre 3D atlas of anatomy** and **BodyParts3D – The Database Center for Life Science**. The exported anatomy, derived scans and reconstructions carry CC BY-SA 4.0. The original BodyParts3D attribution is CC BY-SA 2.1 Japan. The source manifest pins the atlas archive, Blender member and extracted objects. The acquired image records identify their respective source, laterality, view, attribution, license and transformations. [Pinned atlas](source-manifest.json) · [Original license and credits](../../../sources/datasets/z-anatomy/salivary-region/License.txt) · [Duplex references](sources.json) · [Original CCA references](../research/carotid.json)

The [distal CCA measurement comparison](review/distal-cca-measurements.webp) pairs the right model station with an independent right distal CCA acquisition. Its scanner reports 103/21.4 cm/s PSV/EDV at 60°. The model produces 71.0/16.0 cm/s. The acquired lumen estimate (about 6.1 mm) uses visible grayscale inner walls outside the color overlay and the source depth ruler. [Review of velocities, spans and comparison limits](review/acquired-measurements.md)

## Replay

Use the [ultrasound study environment and staging tree](../README.md#replay), including the two s1127 orientation sweeps. Hydrate the acquired WebPs in Git LFS. Obtain the pinned Z-Anatomy archive from the [source manifest](source-manifest.json). Extract its original member and run from the repository root, using fresh paths for the extraction, generated data and compact tour.

```sh
unzip -p "$Z_ANATOMY_ZIP" Z-Anatomy/Startup.blend > "$Z_ANATOMY_BLEND"
survey=experiments/ultrasound-sweep/carotid-survey
"$BLENDER" -b -Y "$Z_ANATOMY_BLEND" --python-exit-code 1 -P "$survey/extract_atlas.py" -- "$CAROTID_ATLAS"
python "$survey/build_survey.py" "$CAROTID_ATLAS/atlas.json" "$STUDY_OUTPUT/carotid-survey/data"
python "$survey/verify_survey.py" "$CAROTID_ATLAS/atlas.json" "$STUDY_OUTPUT/carotid-survey/data"
python "$survey/verify_volume.py" "$STUDY_OUTPUT/carotid-survey/data"
node "$survey/verify-duplex.mjs"
python experiments/ultrasound-sweep/assemble_tours.py "$STUDY_OUTPUT" --delivery "$TOUR_OUTPUT"
```

Serve the compact root. Run `node "$survey/verify_browser.mjs" http://127.0.0.1:8874/carotid-survey/` and `node "$survey/verify-volume.mjs" http://127.0.0.1:8874/` in the Gallery Playwright environment. The original gallery playback and assembly checks cover the routes into the exam. Intermediate builders and review data remain under the ignored local artifact directory.

For the original-atlas comparison, run `python "$survey/compare_reconstruction.py" "$CAROTID_ATLAS/atlas.json" "$TOUR_OUTPUT/carotid-survey/data" "$COMPARISON_OUTPUT"`. It rasterizes the final surface, original atlas and teaching model on the same 0.35 mm grid, and writes the bilateral plate and measurements.
