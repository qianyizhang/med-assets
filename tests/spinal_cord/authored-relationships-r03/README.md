# Reproduce and check

Dependencies actually used: Blender 4.3.2; Python 3+Pillow; Inkscape 1.4; DejaVu Sans and Noto Sans CJK SC for annotation rendering. Dependencies/fonts are not bundled; scripts do not install or download anything.

Obtain exact original comparison GLB from the linked model README and verify its SHA. Generation is authored procedural geometry; the baseline hash is a provenance guard, not a segmented data dependency.

```
blender -b --python-exit-code 1 --python build.py -- --source BASELINE.glb --out NEW_BUILD_DIR
blender -b --python-exit-code 1 --python render.py -- --source BASELINE.glb --candidate NEW_BUILD_DIR/candidate.glb --out NEW_RENDER_DIR
blender -b --python-exit-code 1 --python check_contacts.py -- --candidate NEW_BUILD_DIR/candidate.glb --out NEW_CONTACT_JSON
blender -b --python-exit-code 1 --python check_origins.py -- --candidate NEW_BUILD_DIR/candidate.glb --controls REVIEW_DIR/builder-record.json --out NEW_ORIGIN_JSON
python annotate.py --out NEW_ANNOTATION_DIR
```

All outputs must be new; input hashes checked first. `--python-exit-code 1` is essential to propagate script failures. Checks are finite-precision BVH/SAT/ray screens, not exact-arithmetic proof, exhaustive intra-object intersection certification, or anatomy validation. Exact-coordinate welding is for topology checks only; raw GLB normal/cap splits remain as serialized.

Render outputs are PNG; packaged WebPs preserve every decoded pixel losslessly. Annotation is separate context, embeds the exact lower-view image, and labels authored orientation and non-neural filum. Its portable published PNG needs no fonts; rebuilding its text requires the named fonts and was tested only in the recorded environment.
