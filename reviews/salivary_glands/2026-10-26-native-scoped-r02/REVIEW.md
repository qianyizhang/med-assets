# Independent r01 review

## Decision
Useful improvement over actual baseline, but **not a validated submandibular duct-course model**. Source preservation passes; source anatomical adequacy is a separate gate.

## Human inspection
Viewed five gland-only native PNGs, context side/superior/inferior/oblique, and actual baseline-renders/whole.png. Viewed WSU Lab 22 page 20 locally and extracted page 19 text. WSU/Netter imagery is reference only, excluded from redistribution.

- Baseline has three smooth blob pairs and near-straight parotid sticks. r01 has differentiated gland envelopes, curved ducts, and useful same-source context.
- Context side/oblique supports gross parotid location by posterior mandibular ramus and duct crossing lateral masseter. Missing buccinator, papillae and oral endpoints preclude oral-entry claims.
- Superior view supports sublingual position between mandibular body and genioglossus; no sublingual duct geometry exists or should be inferred.
- Default opaque context hides lower glands. Add superior/inferior presets and independent context visibility; keep isolated geometry view, not only oblique screenshot.
- Ducts are pale and thin, glands relatively homogeneous; labels/legend and optional family colors would improve teaching without changing geometry.

## Exact source/export evidence
Independently loaded Startup.blend in installed Blender and evaluated all 17 selected objects after view-layer update. All recorded world matrices match exactly. Context GLB reimport vertices match evaluated source world vertices within 1.21e-7 native units (nearest-source-vertex test). This is transform/position evidence, not manifold or clinical proof.

- Source SHA256 matches source-members.json.
- context.glb has exactly 17 meshes/nodes; glands-ducts.glb has exactly 10, expected names/extras.
- Export hashes match manifest. Six glands + four source curves, each Bezier with five controls; context mandible + bilateral mylohyoid, superficial masseter, genioglossus.
- Source/export scripts preserve native effective transforms; no procedural curve replacement or invented duct anatomy.

## Anatomical blocker: posterior submandibular duct/mylohyoid interpenetration
Sampled left source Bezier centerline with 31 samples per segment and tested each segment against the same-source mylohyoid surface BVH. Two surface intersections occur near posterior gland origin:
1. (0.024087213, -0.038469922, 1.518845320)
2. (0.021368455, -0.039884407, 1.519557238)

This demonstrates modeled interpenetration, not merely apparent overlap in projection. Do not infer clinical error mechanism solely from this coarse atlas mesh; nevertheless it prevents a clean validated route-around-floor claim. The next four duct control points are above the top mylohyoid surface at their x/y locations, so 'entire duct is below the floor' would be false.

Required resolution: inspect posterior gland/deep-process/duct relationship with source anatomy and appropriate references before changing either mesh; do not shift the curve arbitrarily just to clear collisions. Until then omit/hide this duct pair by default or explicitly mark its course unvalidated, restricting accepted scope to gross gland/context relationships and limited parotid surface course. No patency, connected gland lumen, outlet, full salivary tree, nerve relationship, or complete anatomy claim.

## Packaging obligations
Local source Readme/License requests Z-Anatomy CC BY-SA 4.0 and BodyParts3D/Database Center for Life Science CC BY-SA 2.1 Japan attribution. Retain source commit/hash and adaptation statement (selection, evaluated export, display materials only), source license notices, and share-alike notice in distributable derivative package. Manifest alone is not an attribution page. Do not include reference PDF/page20 PNG in deployable artifacts.

All checks were local with preinstalled tools. No installations, Mac access, or external writes.
