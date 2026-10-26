# Local replay

Requires Python3+Pillow and Inkscape (tested Inkscape1.4). These dependencies are not bundled or installed by this script.

```
python replay.py --out NEW_OUTPUT_DIRECTORY
```

The script resolves its package root, verifies all source/portableSVG hashes, probes Inkscape, and then requires a new output directory. It checks self-contained outlined SVGs and renders them, strips incidental PNG metadata, and compares decoded pixels to packaged PNGs. It does not overwrite existing outputs.

Editable sourceSVGs use DejaVu Sans and Noto Sans CJK SC. To edit/re-outline in an environment where those fonts are installed:

```
inkscape EDITABLE.svg --export-text-to-path --export-plain-svg --export-type=svg --export-filename=NEW_OUTLINED.svg
```

Re-outlining with a different font installation may alter outlines; review the result and create a new revision. The portable SVG/PNG pair does not require these fonts. The exact render replay is a rendered local Inkscape check, not a browser interaction or clinical validation.
