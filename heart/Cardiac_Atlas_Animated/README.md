# Cardiac Atlas — portable heartbeat edition

## What changed
The prior GLBs were end-diastolic static snapshots. These files carry an actual `CardiacCycle_75BPM` glTF animation clip (0.8 seconds), baked from the original authored continuous controls, with independently timed atrial contraction, ventricular shortening/torsion, AV and semilunar leaflet movement, and AV chordae tracking. No whole-heart scale animation is used.

- `Heart_Clinical_Animated.glb`: full heart, clinical teaching colors.
- `Heart_Cutaway_Animated.glb`: anterior teaching section, same synchronized cycle.
- `Heart_Tissue_Animated.glb`: full heart with the original actual baked 2K wall PBR maps; fine anatomy retains standard clinical materials. Three maps are embedded, not external.
- `Cardiac_Atlas_Animated_Source.blend`: original editable driver/shape-key source and packed texture maps. Four main controls remain on `HEART CONTROL • material + cutaway + pulse`; native tissue, clinical and transparent presets remain. Timeline 1–25 at 30fps. The export recipe is embedded as a Blender text block.

## Playback
One cycle = frames 1–25 native = seconds 0–0.8 GLB. Loop with an animation mixer. Phase = clip time / 0.8. Changing playback speed changes educational playback rate, not the anatomical model. Play/pause and scrub refer to this clip.

| Phase | Native frame | Authored event |
|---|---:|---|
| 0 | 1 | End-diastolic reference; atrial contraction begins |
| 0.0833 | 3 | Atrial contraction peak |
| 0.1667 | 5 | AV valves closed |
| 0.2083 | 6 | Semilunar valves open |
| 0.375–0.4583 | 10–12 | Ventricular contraction peak |
| 0.4583 | 12 | Semilunar valves closed |
| 0.5417 | 14 | AV valves reopened |
| 0.7083 | 18 | Ventricular deformation returned to relaxed state |
| 1 | 25 | Exact loop closure |

These are schematic timing choices, not measured patient physiology. Phases overlap and interpolation is smooth. Reference imaging remains a static end-diastolic dataset; it must not be portrayed as time-resolved matched imaging.

## Units and coordinates
GLB world coordinates are metres, with a scene-root factor 0.025 applied to native geometry. +X is patient left, +Y superior, +Z anterior. Keep the root transform. No external file is required by a GLB.

## Reproduce
With Blender 4.3.2, run `blender -b Cardiac_Atlas_Animated_Source.blend -P export_animated.py`, then `python validate_glb.py`. The recipe samples the original rig at every native frame, removes export-only drivers, bakes topology-preserving leaflet modifiers on every morph target, writes linear weight tracks, selects full/cutaway geometry, and exports glTF SCENE animation. The validator adds the explicit metre root and common clip name and verifies track range/duration/loop closure. It is idempotent for already scaled exports.

## Verification
`GLB_VALIDATION.json`: clip count, duration, animated node counts, nonconstant weights, exact endpoint closure, nonzero vertex deltas, self-contained resources, hashes.
`BLENDER_ROUNDTRIP_QA.json`: independently imports each delivered GLB into a fresh Blender scene and measures deformed world-space vertices over playback, including chamber walls and both valve types.
Browser playback and controls are verified separately by the Site integration owner.

## Limits
Procedural educational idealization, not patient-specific, diagnostic, biomechanical, CFD, or clinical validation. Anatomy and junctions are simplified. Blue is a teaching convention for circulation categories, not literal blood color. This update preserves the source deformation recipe rather than asserting physiological accuracy. Tissue maps cover four complete walls, not every small structure. Cutaway is a presentation section. See original asset documentation for detailed anatomy and source scope.
