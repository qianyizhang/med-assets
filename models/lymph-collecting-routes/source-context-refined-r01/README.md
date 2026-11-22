# Refined source-route context and optional directional highlight

![Original / Updated — English](comparison-en.png)
![Original / Updated — 中文](comparison-zh.png)

[Open self-contained EN/中文 lesson](index.html)

- **Change:** editorial head/neck, shoulder, limb and hand/foot contours; labeled external regional cues. Original7 source-route positions and cap anchors retained, with central selected-route hierarchy. Context contrast intentionally adjusted; this is not an all-pixel-color identity claim.
- **Unchanged:** original source-context-r01 package, 7 route objects, 372 triangles. No new ducts, shifted caps or model-body registration. New contour is illustrative, not a measured adult template or clinical validation.
- **Direction:** only the source-named thoracic route gets optional moving color dashes, along the actual projected5 ring centers. Other6 paths remain static. Four exclusion masks protect the source-cap markers; motion stops short of them and does not establish a vein connection or continuous lumen.
- **Controls:** EN/中文, initial pause, persistent pause/resume and reduced-motion static fallback. Animation is educational direction only; no measured speed/pulse claim.

## Reference and evidence

[OpenStax §1.6/Fig1.12](https://openstax.org/books/anatomy-and-physiology-2e/pages/1-6-anatomical-terminology) informs qualitative regional relationships, not population proportions. [§21.1/Fig21.4](https://openstax.org/books/anatomy-and-physiology-2e/pages/21-1-anatomy-of-the-lymphatic-and-immune-systems) supports typical thoracic drainage toward the left venous angle and the right-upper-region exception. Source names/caps do not prove these anatomical endpoints. Original artwork; no source illustrations copied. Current reference notice CC BY-NC-SA4.0; no blanket license inferred for commissioned geometry.

Actual static EN/中文 comparisons and Inkscape-rendered example highlight phases were independently inspected. Nineteen source-bound Node/DOM-double assertions test the controls. The original review stopped at static and simulated checks because its environment could not reach the browser preview.

The 2026-11-21 [Gallery verification](../../../records/work-items/items/AG-GAL-016-integrate-retained-teaching.md#legacy-teaching-supplements) checked both rendered route overlays, cap masks, language controls, reduced motion and laptop layout in disposable Chrome. The regenerated standalone page also opened offline and passed a bilingual play/pause smoke check. Keep this self-contained HTML for offline use and replay.

## Reproduce and check

- `python3 plate.py`: regenerates comparisons from adjacent unchanged source-context-r01 package. Python/Pillow/NumPy/SciPy and NotoSansCJK Regular/Bold required.
- `python3 build.py`: assembles HTML from comparisons and retained source projection; Python standard library only.
- `python3 check_binding.py`: checks fixed accepted image hashes, five-ring paths, cap masks and19 simulated control assertions. Node required.
- `python3 test_binding.py`: negative guard regressions.
- `python3 render_phase.py`: optional static illustration of a highlight phase via Inkscape, not browser QA.

`projection.json` retains only the selected source-object projection needed by the animation. `projection-binding.json` pins exact image hashes and path coordinates; `retention-proof.json` records matched camera/cap evidence and editorial contour controls.

## Retention

Two PNGs are reviewed bilingual comparison deliverables. HTML deliberately embeds the same images for a portable, offline single-file lesson, without dependencies or hosted assets. Recipes permit reproducibility. Source masters, rejected style trials, redundant earlier conceptual diagrams, private operational receipts and temporary phase/body images are excluded; original source-context-r01 remains intact.
