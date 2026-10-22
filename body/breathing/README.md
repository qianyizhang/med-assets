# Respiratory teaching animation — 2026-10-22

This package extends the retained source-derived static organ assets with authored, illustrative motion. It is not patient-specific motion capture, clinical validation, biomechanical simulation or CFD.

## What moves
- Left/right lungs: a shared per-vertex inspiration field preserves the superior apex while lower regions descend up to 18 mm and widen preferentially in lateral/anterior directions. Lobes use the same spatial field; there is no whole-object balloon scaling.
- Diaphragm: independently authored, open double-dome teaching surface flattens and descends. It does not claim source-case segmentation or model attachments/openings.
- Liver/gallbladder descend up to 8 mm; stomach/spleen 6 mm; kidneys 4 mm; pancreas 3 mm; source heart 2 mm. These modest translations are illustrative, not measured.
- The portable clips are 4 seconds (15 illustrative breaths/minute). Inspiration takes 40% and expiration 60%; endpoints match for looping. Each GLB contains its own baked animation, embedded materials and retained provenance.

## Files and editing
- `Breathing_Assembly.blend`: editable imported morph targets and animation actions; 30 fps, frames 1–121. Lung shape-key targets and neighbor transforms can be edited separately.
- `build_motion.py`: authoring script retaining original GLB buffers/materials and adding targets/clip samplers. Paths at the top should be adjusted to the source Site checkout. The unchanged original static meshes remain in `assets/meshes/`.
- `native_assembly.py`: imports the delivered clips into the editable Blender assembly.
- `breathing-glbs.zip`: 11 self-contained animated GLBs. Each asset retains source attribution through extras and the Site manifest; see original Site `NOTICE.md` and licensing files before reuse.
- `component-qa.json`: actual Three.js GLB parsing and CPU vertex deformation, with DOM/control tests. This is not browser/WebGL validation.
- `expiration.webp`, `inspiration.webp`: Blender phase renders from the delivered imported GLBs, not browser screenshots.

The optional separate animated Cardiac Atlas heart is supplied by the heart package. In the body viewer it uses a uniform teaching fit, not source-case registration. It runs 75 illustrative beats/minute (five heart cycles per respiratory timeline). This fixed ratio is a playback convenience, not measured heart–breath synchronization. Full and cutaway animated GLBs are mutually exclusive views; the original static detailed heart remains separately available.
