# Historical ulnar elbow teaching views

The [shared right-arm recipe](../../../joints/recipes/z-right-arm/README.md) builds
the current native ulnar-elbow selection. The exact [original GLB](../../exports/ulnar-elbow-r01/README.md)
and original raw captures support the older [bilingual teaching sheet](../../../../reviews/peripheral_nerves/2026-10-30-ulnar-elbow-r01/README.md).

Use `render.py` with Blender 4.3.2, `--factory-startup --disable-autoexec`, and
`-- --glb FILE --sha256 HASH --out NEW_DIRECTORY` to capture the retained
geometry. The cameras and the source graphical endpoint bindings live in the
script. It uses 128 Cycles samples without denoising. The labels identify
visible region and source extent.

`compose.py --review REVIEW_DIRECTORY` uses the retained capture folders
`v1/matched-128` and `v2/raw-128` to recreate the historical sheets. Copy the
raw folders to a fresh review directory before running. Use Python 3.11+,
Pillow, DejaVu Sans and Noto Sans CJK at the paths in the script. The recorded
geometry, hashes and earlier test results are in the
[historical validation receipt](../../../../reviews/peripheral_nerves/2026-10-30-ulnar-elbow-r01/validation.md).
