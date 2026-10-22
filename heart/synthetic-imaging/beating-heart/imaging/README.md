# Match the model to a slice

**Every image and volume here is a synthetic teaching example, generated from the same idealized geometric heart as the Blender model. These are not patient scans or validated CT, MRI, or ultrasound simulations.**

## Start here
1. Begin with `start_here_same_slice.png`, then look at `labels_orthogonal_and_cardiac_planes.png`: LV/RV are the left/right lower pumping chambers; LA/RA are the left/right upper receiving chambers. The surrounding darker material is the chamber wall.
2. Compare the exact same position in `ct_orthogonal_and_cardiac_planes.png` and `mri_orthogonal_and_cardiac_planes.png`. Color labels become a deliberately simple grayscale contrast preset. Both presets make the chamber contents brighter than their walls; their intensities are arbitrary.
3. `ultrasound_style_fan.png` shows a different plane convention: a fan expanding from a virtual apex-side probe. `ultrasound_labeled_fan.png` overlays the same structure labels. The speckle-like texture is only a graphic effect. This is not an acquired echocardiogram or acoustic simulation.
4. The interactive viewer can sample the supplied raw volumes at any position and map the same plane into the 3D model. Its moving slice is always at reference frame 1, not a phase-varying cine scan.

An anatomical slice cuts the three-dimensional shape: a hollow chamber becomes a bright oval surrounded by a darker wall. Moving through the shape changes that cross-section. The grayscale teaching presets preserve this geometric relationship without claiming diagnostic appearance.

## Files and reproducibility
- `generate_samples.py`: run with Python, NumPy, SciPy and Matplotlib. Imports shared `../heart_geometry.py`, `../vessel_geometry.json` and `occupancy.py`; uses no downloaded or AI-generated unrelated anatomy.
- `volume_io.py`: dependency-light NIfTI-1 and NRRD writers.
- `render_examples.py`: reslices volumes and generates comparison figures and geometric ultrasound-style fan.
- `structure_labels.nii.gz` / `.nrrd`: integer segmentation IDs.
- `ct_like_arbitrary_contrast.nii.gz` / `.nrrd` and `mri_like_bright_blood.nii.gz` / `.nrrd`: arbitrary normalized contrast volumes, not HU or T1/T2.
- `synthetic_volumes.npz`: all three arrays and the affine, readable with NumPy.
- `metadata.json`: authoritative dimensions, label table, source hash, present/absent labels, phase, affine and contrast settings.
- `slice_planes.json`: plane origins, bases and sampling conventions for every figure, including the fan.
- `web/manifest.json` and three `.uint8.raw` files: browser-friendly 3D arrays. Raw arrays use x/i fastest indexing: `i + nx*(j + ny*k)`. The manifest gives all dimensions and transforms.

From the package root: `python imaging/generate_samples.py`.

## Orientation and registration contract
The model has +X patient-left, +Y posterior, +Z superior, and 1 Blender unit = 25 mm. Thus RAS millimeters = (-25 X, -25 Y, +25 Z). This is a declared idealized coordinate frame, not a patient scanner origin. Volume indices map to RAS voxel centers through the affine in the metadata. All example images are frame 1, reference end-diastole. Screen left is explicitly labeled and is not assumed to be patient left. `start_here_same_slice.png` places patient left on image left; `start_here_radiological_display.png` mirrors this same slice into conventional axial radiological display, with patient right on image left. This is only a display flip: array data and spatial affine are unchanged. RAS-to-LPS negates the first two coordinates only.

Patient axial, coronal, and sagittal planes are distinguished from LV-relative oblique long/short axes. Short-axis planes are perpendicular to the LV apex-to-base direction. The illustrative long-axis plane is **not** presented as a prescribed clinical two- or four-chamber view. Oblique edge letters indicate dominant direction components; exact bases are in JSON.

The volumes and native mesh share the declared model space. Chambers and the curved ventricular septum use the same analytic geometry. The right ventricle has a crescent cross-section wrapping the left ventricle. The atrial septum uses the same ellipsoid parameters. Vessel lumens use a nearest-piecewise-linear-centerline/interpolated-radius approximation to the model’s transported cross-section tubes, clipped at their terminal planes; curvature and edges can therefore differ. Polygon tessellation and 1 mm voxelization add further differences. Vessel walls are not separately voxelized. Imported real imaging will not automatically align: preserve its original spatial affine, units, orientation, phase and provenance; then establish a patient-specific transform/segmentation and verify landmarks. A reference-phase shape does not by itself solve beat-to-beat or respiratory motion.

## Limitations
Idealized geometry is not a detailed anatomical reconstruction. The model has no patient torso, pathology, scanner field, sequence physics, noise calibration, CT reconstruction, MR relaxation, ultrasound propagation, Doppler, measured blood velocities or diagnostic measurements. The presets do not establish realistic modality-specific tissue discrimination. IDs may be defined in the shared anatomy schema yet absent from the sampled occupancy; `absent_defined_labels` makes this explicit. Structures outside the sampled schema are not fabricated.

The fan is a geometrically specified plane clipped into a sector. It does not simulate a real transducer, beam width, shadowing, reverberation, attenuation, timing or standard echo acquisition. A physical scan requires substantially more modeling and independent validation.

## Primary documentation and imaging background
- NiBabel documentation, voxel-to-world coordinates and RAS+: https://nipy.org/nibabel/coordinate_systems.html
- NiBabel documentation, image orientation: https://nipy.org/nibabel/image_orientation.html
- 3D Slicer coordinate systems and RAS/LPS: https://slicer.readthedocs.io/en/5.10/user_guide/coordinate_systems.html
- ACR/RSNA RadiologyInfo, cardiac MRI principles: https://www.radiologyinfo.org/en/info/cardiacmr
- ACR/RSNA RadiologyInfo, CT angiography principles: https://www.radiologyinfo.org/en/info/angioct

These explain orientation and the physical modalities; they do not validate this illustrative generator.
- FDA, ultrasound imaging principles: https://www.fda.gov/radiation-emitting-products/medical-imaging/ultrasound-imaging
- American Heart Association, echocardiogram: https://www.heart.org/en/health-topics/heart-attack/diagnosing-a-heart-attack/echocardiogram

## Overlap and teaching-model topology
The primitive geometric surfaces are not all disjoint. The shared label function gives chamber blood pools priority over overlapping wall envelopes; the native ventricular display walls are clipped against the opposite ventricle's pool to reflect that priority. At the supplied 1 mm grid, cross-circuit chamber blood-pool overlaps are zero. The LV/LA primitives have a 25-voxel contact overlap at the idealized atrioventricular junction. The RV pool intersects the LV outer envelope at 893 voxels, which is resolved as RV blood pool rather than LV wall in the label volume. These are construction/label-precedence details, not measured anatomy. The model is not a conforming multi-material mesh, flow domain, CFD topology or physiological chamber-volume benchmark. See `validation.json` for reproducible counts.
