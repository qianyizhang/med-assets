# FDI31 reveal / isolate / reset controls

![Source pose, all layers visible](media/control-source.jpg)
![Separated layers, fixed camera](media/control-separated.jpg)
![Pulp isolated without reframing](media/control-pulp.jpg)

**New bounded implementation for #216.** #222 is the separate shooting-script and
Blender timeline proposal. This package adds manual control state and a
self-contained Canvas2D viewer; it does not replace that timeline or change a mesh.
The images/GIF are actual parser/controller/CPU-render pixels with a composited
control panel, **not browser screenshots**. [Preview GIF](media/FDI31-reveal-isolate-reset.gif).

## What works in the checked CPU scope

- Reveal is an absolute 0–1 display offset, never an accumulated transform.
- Isolate one of the four exact source labels. Other layers become invisible.
- Show all preserves the current reveal. Reset restores captured matrices and
  all-layer visibility exactly, including after repeated or mixed actions.
- A fixed camera encloses source and fully separated poses. Control changes do
  not reframe. Resize refits the full envelope, not the selected layer.
- The source SHA-256 must match before parsing or enabling controls. Bad input,
  missing Web Crypto, and setup failure leave controls disabled.

## Replay

Requires Python 3.11+ and Node.js 18+. Preview compositing additionally needs Pillow.
The browser file has no external scripts, libraries, fonts or model fetches.

```sh
SOURCE=models/swirendo_fdi31/exports/balanced-20261028/FDI31-balanced.glb
PACKAGE=tools/dental/layer-controls
# SOURCE must be hydrated, not the LFS pointer. No tool here downloads it.
python3 "$PACKAGE/build.py" --source "$SOURCE" --out "$PACKAGE/output/FDI31-interactive-controls.html"
node --test "$PACKAGE/controller.test.cjs"                         # 15 pure state cases
DENTAL_SOURCE="$SOURCE" node --test "$PACKAGE/controller.test.cjs" "$PACKAGE/app.test.cjs" # 21 cases
node "$PACKAGE/render_preview.cjs" "$SOURCE"
python3 "$PACKAGE/compose_preview.py"
python3 tools/verify.py offline
```

The self-contained HTML is a review prototype. Open it in a supported browser
with Web Crypto and Canvas2D; local-file support and interaction remain unverified.
The companion downloaded source bundle supplies the same GLB as
`inputs/FDI31-balanced.glb`; use that path when replaying the bundle.

The offline repository gate runs the 15 media-free state tests plus packaging
checks. The 21-case command above additionally checks actual source byte/array
immutability, viewport bounds, and actual app event handlers with DOM/canvas/RAF
doubles. It is **not** browser E2E, keyboard, accessibility or performance testing.
The preview uses all 105,370 source triangles, including degenerate triangles
which do not draw. Prior Blender import evidence counted 105,346 after its
24 degenerate-triangle exclusions; no source geometry was edited here.

## Evidence and limits

[Review receipt](review.json) binds code, exact source and retained preview bytes.
[Frame states](preview-frames.json) record the continuous sequence and fixed camera.
The source and reset raw pixel buffers are identical. Independent source review
also checked desktop and 300 px-wide viewports; no source clipping was found.

Browser runtime is **unverified**. The available cloud browser could not reach
the workspace HTTP server, and its policy forbids file URLs. No alternative route
was used to bypass that restriction. No private Site was published. A supported
browser review should test slider input, all isolate buttons, show all, reset,
keyboard focus, narrow layout, and fail-closed errors before runtime acceptance.

This is a source-specific GLB reader for the pinned specimen, not a general glTF
loader. The fixed-envelope method was checked for this source and is not a generic
no-cropping guarantee. There is no user camera manipulation, so reset means source
placement and visibility, not restoration of a user-moved camera. No material,
rig, cutting, deformation, procedure, clinical or physiological validation is implied.

## Source, rights and retention

SWIRendo A_1_31_T2_SEG_na, Benz, Heck and Walter (2024),
[dataset DOI](https://doi.org/10.5282/ubm/data.477),
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
The asset is the repository's Balanced simplified derivative of a prepared T2
FDI 31 specimen. It is **not healthy anatomy**; source defects remain visible.
Buccolingual orientation is unresolved. Enamel, dentin, pulp and bone are source
labels, not independent anatomical approval. Colours and separation are editorial.
Source-derived render assets remain CC BY-SA 4.0, with this attribution.

Canonical GLB: `models/swirendo_fdi31/exports/balanced-20261028/FDI31-balanced.glb`,
2,052,220 bytes, SHA-256
`90006e54c2b9f79f6c201397a50f92228d9ad6fa4450f20e0ad20c5fe70c19f7`.
The repository retains code, one GIF and compact review images for reviewers.
It does not duplicate the GLB or retain the 20 raw RGBA buffers / generated HTML.
The portable HTML embeds the unchanged source only in the delivered artifact,
so the recipient can inspect it without a network dependency. Historical #222
artifacts and original meshes remain untouched. Source-specific parser/rasterizer
code is reused from the private specimen explorer; only display state is new.

Next: inspect the prototype, then conduct an authorized browser review. This PR
is draft and partial #216 evidence; it does not close the issue or authorize merge.
