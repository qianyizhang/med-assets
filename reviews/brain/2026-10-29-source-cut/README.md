# Brain source-cut presentation — v2

**Change:** a separate [EN/中文 teaching presentation](../../../lessons/brain-source-cut/README.md)
marks the retained brainstem's inferior source cutoff in overview and detail.
The front bracket spans both visible medulla surfaces; the side sheet preserves
the nearby brainstem/cerebellum context. It is a numbered, unfilled editorial
bracket outside the tissue, not an anatomical cap or reconstructed cord.

**Evidence:** matched Original/Updated front and left sheets are committed as
small SVGs referencing the existing exact contact image. Native PNG comparisons,
portable SVGs and printable PDFs were produced locally; the front comparison was
shared privately and independently reviewed. New public raster transport is pending
explicit scope. The committed SVG's external image may not display in GitHub's
restricted image preview; it was verified in Inkscape against the portable export.

## Iteration and scoped decision

- **V1 failed:** native Inkscape export ignored nested SVG overflow clipping, so
  uncropped contact-image regions covered neighboring panels and text. Retained
  local v1 SVGs/PNGs record the failure; they are not teaching deliverables.
- **V2 corrected:** explicit clip paths contain each viewport. A single shared
  source image supplies both variants. Author inspection of both teaching sheets,
  both comparisons, front grayscale and the front PDF reload found readable
  bilingual labels and visible tissue surfaces. Detail magnifies retained pixels;
  it does not add high-resolution surface information.
- **Technical pass:** exact unchanged source identities, all 49 meshes, both
  medulla node names, byte-identical portable replay, independent linked/portable
  native exports, and four Original/Updated pixel differences confined to the cue.
  See [visual-binding.json](visual-binding.json) and [review.json](review.json).
- **Independent static pass:** at `38d09238df799ac48cd3f234ffe2bd7205b77501`,
  the parent reviewer verified private bundle hashes/sizes and inspected both
  comparisons, front grayscale and independently rendered standalone SVG layouts.
  The correct inferior boundary is marked outside tissue; Original/Updated crops
  and scales match, and EN/中文 labels distinguish the editorial cue. Builder/diff
  review confirmed pinned inputs, 49 meshes/two medulla names and no mesh writes.
  No blocking presentation finding. PDF reload was author-only, not independently
  verified; this verdict does not certify anatomy, browser display or publication.
- **Pending:** public raster evidence authority and browser display. The first
  PR-image embed was rejected by automatic approval review; the text-only draft
  remains. Chromium stopped before page launch at its misconfigured SUID sandbox
  helper. No public raster retry, security change or protected probe was attempted.

## Reproduce

```sh
python3 -m unittest discover -s tests -p test_brain_source_cut.py
python3 tools/brain_source_cut/check_visuals.py --output /tmp/brain-cut-check-NEW
python3 tools/verify.py offline
```

The first command runs six offline failure/identity/comparison-structure tests
without third-party dependencies. Native checks additionally require the exact
hydrated GLB and contact PNG, Pillow, Inkscape and the fonts named in the teaching
README. They produce PNGs, PDFs, grayscale images and a source/export hash receipt;
they make no network requests. Native rendering and pixel differences do not
certify anatomy, browser/WebGL behavior or publication. The historical source
camera recipe is not claimed portable, and no new 3-D render was needed.
