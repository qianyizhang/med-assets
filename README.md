# Medical teaching assets

Reusable cardiac, respiratory, whole-body 2D, and Anatomy Workshop 3D teaching
assets, imported on 2026-10-22. Binary models, images, and synthetic volumes use
Git LFS. Documentation, licenses, manifests, SVG artwork, and authoring scripts
are stored in normal Git.

## Download

Install Git LFS, then clone and fetch the asset bytes:

```sh
git lfs install
git clone https://github.com/qianyizhang/med-assets.git
cd med-assets
git lfs pull
shasum -a 256 -c SHA256SUMS
```

## Collections

| Directory | Contents |
| --- | --- |
| `heart/Cardiac_Atlas_Animated/` | Three animated heart GLBs, editable Blender source, export scripts, and delivery QA. |
| `heart/Cardiac_Atlas/` | Earlier editable cardiac master, static GLB/STL exports, baked PBR textures, geometry, and source scripts. |
| `heart/synthetic-imaging/beating-heart/` | Synthetic teaching volumes in NIfTI, NRRD, NumPy, and raw formats, illustrations, orientation metadata, and generators. These are not patient scans. |
| `body/breathing/` | Eleven animated organ GLBs, editable Blender assembly, phase renders, scripts, and attribution. |
| `body/anatomy-workshop-r1/` | Eighteen grouped static 3D assets, Blender source, texture maps, original meshes, rebuild scripts, and provenance. |
| `body/2d-v4/whole-body-anatomy-v4-spatial/` | SVG anatomy parts, variants, overlays, regional views, previews, coordinate mappings, and provenance. |

The collection contains all 17 requested source bundles: four priority animation
bundles from Library and the earlier 13 original archives from Drive. The 13
Drive ZIPs match the original SHA-256 checksum list. There are **591 extracted
asset files totaling 370,698,859 bytes**. One hundred repeated, byte-identical
archive entries were merged. No assets were regenerated or edited during import.

Source ZIPs are not duplicated in Git LFS alongside the extracted files.
`metadata/asset-manifest.json` records all archive and member hashes and the exact
extraction paths. `SHA256SUMS` covers every imported asset file.
`metadata/earlier-README.md`, `metadata/earlier-SHA256SUMS.txt`, and
`metadata/earlier-collection.json` retain the original earlier-collection index,
archive checksums, and completed import status.

## Editing and reuse

GLBs are self-contained. Preserve the Anatomy Workshop texture paths and the
sibling `body-3d-assets`, `body-3d-source`, and `body-3d-delivery` directories.
Synthetic-imaging geometry remains separate from the cardiac master. Original
scripts retain their authoring-environment paths; read the relevant package
documentation before rebuilding. None of the generation or rebuild scripts was
run during this import. Source QA reports are retained evidence from delivery,
not new clinical or visual validation from this sync.

## Attribution and scope

Preserve each collection's notices, source receipts, and full license texts.
The 2D adaptations credit Servier Medical Art under CC BY 4.0. Source-derived
3D organ surfaces credit Jakob Wasserthal, the TotalSegmentator contributors,
and University Hospital Basel under CC BY 4.0; the retained label-source
Apache 2.0 notice does not replace that attribution. No blanket license is added
to this repository. The authored cardiac and synthetic-imaging packages do not
declare a separate public license.

These are simplified educational assets. Retain the package-specific scope and
limitations. The Anatomy Workshop collection focuses on thoracic and abdominal
anatomy with selected extras; it is not a complete 3D body atlas.

Published viewers remain at
https://heart-anatomy-imaging-lab.landy123007.chatgpt.site/ and
https://heart-anatomy-imaging-lab.landy123007.chatgpt.site/body/3d/.
