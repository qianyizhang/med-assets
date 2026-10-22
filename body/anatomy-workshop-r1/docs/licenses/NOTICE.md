# Shared anatomy assets

Requested by the user on 2026-09-22 to replace overly abstract organ shapes.
These are reusable teaching models, not a generic healthy atlas or scored
predictions. They are not presented as a reconstruction of the selected case. Native task examples keep
their own provenance. Lesions, correspondences and motion overlaid by task scenes
remain authored illustrations.

## Source-derived organ surfaces

Attribution: Jakob Wasserthal and the TotalSegmentator contributors, University
Hospital Basel. TotalSegmentator v2.0.1, https://zenodo.org/records/10047263 .
Paper: https://doi.org/10.1148/ryai.230024 .

The 18 JSON meshes derive from retained public segmentation masks: s1233 for
abdominal and thoracic structures and a lumbar vertebra; s1336 for the prostate.
The source cases also appear in existing research records. These are examples
of particular anatomy, not claims about normal population
shape. No CT intensities, facial surface, identifying metadata or new prediction
is included. The source case is retained solely for traceability.

Retain CC BY 4.0 attribution with these derived assets. Its full text is included
in CC-BY-4.0.txt. The selected-source receipt additionally records Apache-2.0 for
labels; that full license is retained in ../assets/Apache-2.0.txt. No source author
endorses these illustrations.

Source and output SHA-256 values, affine matrices and extraction settings are in
manifest.json. Derivation: keep the largest mask component, smooth sigma 0.65
voxels, extract at 0.5, apply 15 windowed-sinc iterations with passband 0.1, reduce
triangles by quadrics, retain a smaller assembly mesh (at most 300 triangles per
organ) for the distant torso overview, and round vertices to 0.01 mm. The close
abdominal teaching scene uses the fuller retained surfaces. Truncated organs are rejected.
This discards detail and cannot support clinical measurements or scoring.

JSON vertices retain source RAS millimetres. Display maps RAS to (-R, S, A), then
centers and uniformly scales each assembly. Organ assemblies preserve relative
size and position within the same source case. Individually displayed organs are
fitted separately; cross-card size is not a physical comparison. Camera rotation
does not redefine anatomical sides.

For explanatory display, presentation/frontend/task-visuals/anatomy.ts applies one Loop subdivision step to
the retained triangulated surfaces before fitting the assembly. This rounds the
coarse silhouettes and can slightly shrink or smooth local features. It is a
runtime display treatment, not recovered anatomical detail: retained JSON meshes,
source masks and manifest hashes stay unchanged. Do not measure these displays.

## Authored models

Brain hemispheres, cortical folds, cerebellum, brainstem and dental crowns/roots
are procedural schematics in presentation/frontend/task-visuals/anatomy.ts. They are not extracted anatomy.
They carry no measured surface detail or tooth identity claim. Their features
exist to make the subject recognizable.

## Rebuilding and extending

Normal offline builds use the retained mesh JSON and do not require scans,
scientific libraries, downloads or inference. Optional authoring command:

    .venv-br030/bin/python scripts/build_anatomy_assets.py --source-root runs/br004-v1/source --output NEW_LOCAL_DIRECTORY

The authoring environment needs nibabel, numpy, scipy, scikit-image and VTK.
The builder runs only when invoked explicitly. Review a fresh output visually,
check source hashes and terms, then deliberately replace selected assets. Never
regenerate historical masks or frozen task material as part of asset maintenance.
