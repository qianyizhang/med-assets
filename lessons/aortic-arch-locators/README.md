# Aortic arch branch locators / 主动脉弓分支定位

Private preparation for [issue #149](https://github.com/qianyizhang/med-assets/issues/149).
One bilingual teaching sheet connects the same four numbered source groups in
overview and junction detail. Two matched Original/Updated sheets expose the
editorial change. Every pair uses identical raster bytes, dimensions and crop.

| ID | Exact retained source group | Teaching name / 教学名称 |
|---|---|---|
| 1 | `Brachiocephalic trunk + Right common carotid artery` | Brachiocephalic trunk + right common carotid artery / 头臂干＋右颈总动脉 |
| 2 | `Left common carotid artery.001` | Left common carotid artery / 左颈总动脉 |
| 3 | `Left subclavian artery.001` | Left subclavian artery / 左锁骨下动脉 |
| 4 | `Right subclavian artery.001` | Right subclavian artery / 右锁骨下动脉 |

ID 1 deliberately names the joined source group: the retained GLB does not retain
an internal component boundary that would justify a separate source-verified
trunk/right-carotid segmentation. ID 4 is a branch of the brachiocephalic system,
not a fourth direct arch origin. The three direct arch branches and the
right-sided subdivision agree with
[OpenStax Anatomy and Physiology 2e, §20.5](https://openstax.org/books/anatomy-and-physiology-2e/pages/20-5-circulatory-pathways).
The source names, not that schematic reference, bind the actual leaders.

The nine source meshes and 15 named structures remain unchanged. Numeric circles
and leaders are separate SVG graphics. Open/unfused intersections and cropped
ends remain visible; no lumen or missing anatomy is fabricated. The original
illustrative material is retained. These are static educational locators, with no
clinical or browser-runtime approval.

## Rebuild privately

Requires Python 3.11+, Blender 4.3.2, Inkscape 1.4, Pillow, DejaVu Sans and Noto Sans
CJK SC. Use the exact retained GLB, SHA-256
`d4b3dbd2d09fd76795f47bb96844acdeba5f1b4f48dd630f2a294f33816deaeb`,
881,168 bytes. No download, credential, upload or publication occurs in these tools.
The renderer refuses a pointer or different source and requires a new output
directory. All generated rasters and embedded-image SVGs are private deliverables;
they are not added to the public repository by this preparation.

```sh
blender --background --factory-startup --python-exit-code 1 \
  --python tools/aortic_arch_locators/render.py -- \
  --source PATH_TO_EXACT_GLB --output PRIVATE_DIR/renders
python3 tools/aortic_arch_locators/build.py \
  --source PATH_TO_EXACT_GLB --renders PRIVATE_DIR/renders --output PRIVATE_DIR/plates
python3 tools/aortic_arch_locators/check_visuals.py \
  --source PATH_TO_EXACT_GLB --renders PRIVATE_DIR/renders \
  --plates PRIVATE_DIR/plates --output PRIVATE_DIR/checked
python3 tools/verify.py offline
```

Open `plates/arch-locators.svg` for the teaching sheet; `overview-comparison.svg`
and `junction-comparison.svg` hold matched comparisons. Each SVG embeds its exact
source PNG and opens independently of the repository. `checked/` contains native
PNG exports, a grayscale sheet and the pixel-binding report. The composer replays
byte-identically from the same retained render receipt and images. Blender PNG
container metadata can differ between runs; the checked replay pixels are exact.

The historical camera recipe is explicitly unbundled in the retained
[dependency manifest](../../sources/datasets/z-anatomy/small-static-studies/dependency-manifest.json).
These are **new recorded-camera captures of the unchanged source**, not a replay
of historical review pixels. Both cameras look from source +Z with source +Y up.
Source-name and coordinate checks on three bilateral pairs place source left on
screen right. The [review record](../../reviews/aortic_tree_z/2026-10-29-arch-locators/README.md)
provides matrices, actual per-node surface hits and the exact image identities.

## Attribution

Geometry, renders and adapted teaching plates retain **CC BY-SA 4.0**:
https://creativecommons.org/licenses/by-sa/4.0/.

**Z-Anatomy — The libre 3D atlas of anatomy — CC BY-SA 4.0**.
**BodyParts3D — The Database Center for Life Science — CC BY-SA 2.1 Japan**
(historical attribution). Original model: Kousaku Okubo; Z-Anatomy design/3D/anatomy:
Gauthier Kervyn; Blender add-on: Marcin Zielinski. New recorded-camera renders and
editorial locators added 2026-10-29. No endorsement is implied. Retained
[attribution and upstream license](../../sources/datasets/z-anatomy/small-static-studies/ATTRIBUTION.md)
remain authoritative for this bounded source package; no whole-atlas license is inferred.
