# Portable, non-overwriting replay

Requires Python 3 + Pillow, Blender 4.3.2 and a Chinese-capable font (default Noto Sans CJK Regular). Inputs are explicit, external dependencies; no network download occurs:

```
python tests/parathyroid_localization/rebuild.py \
  --source /absolute/path/to/Startup.blend \
  --baseline /absolute/path/to/parathyroids.glb \
  --output /absolute/path/to/NEW-review-directory
```

Optional `--blender /path/to/blender` and `--font /path/to/NotoSansCJK-Regular.ttc`.

Source SHA-256 must be `9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd`; baseline must be `9741ddb9dabac9504c9587caafa7a6f51a6765d38a75be48c6229f00a769391f`. Source URL/license is retained with the exports; baseline URL: https://heart-anatomy-imaging-lab.landy123007.chatgpt.site/body/3d/assets/drafts/head/parathyroids.glb . Baseline bytes are not bundled or relicensed.

The command refuses an existing output directory **before writing**, verifies both pinned input hashes, evaluates only the five named atlas meshes with Blender `--disable-autoexec`, exports without geometry changes, reimports for finite/topology/vertex-distance checks, and renders matched baseline/candidate views. Frozen GLB SHA-256 values are assertions, not inferred passes. Outputs include a local selected `.blend` for inspection, raw renders and clean display derivatives; these are generated in the new directory, not written into the repository. A failed run leaves diagnostic files in its own directory and requires a new destination on retry.

Comparison is independently bounds-normalized with matched viewing/light directions, not cross-source spatial registration or absolute-size comparison. Metadata removal from the selected oblique display derivative is checked against identical decoded RGBA pixels. Teaching labels are bilingual, with explicit variation and uninterpreted-projection caveats. No anatomy, clinical or runtime pass follows from replay.

Fresh replay receipt and guard tests are retained under the review directory. Publication bundle deliberately omits redundant views, raw source, reference illustrations and `.blend`; all can be recreated locally from the pinned external inputs.
