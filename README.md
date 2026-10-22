# Medical teaching assets

Animated heart and respiratory teaching assets, imported on 2026-10-22.
Binary models and preview images are stored with Git LFS. Documentation,
manifests, licenses, and authoring scripts are stored in normal Git.

## Download

Install Git LFS, then clone and fetch the asset bytes:

```sh
git lfs install
git clone https://github.com/qianyizhang/med-assets.git
cd med-assets
git lfs pull
shasum -a 256 -c SHA256SUMS
```

## Included assets

- `heart/Cardiac_Atlas_Animated/`: three animated heart GLBs, the editable
  Blender source, export scripts, source documentation, and retained QA reports.
- `body/breathing/`: eleven animated organ GLBs, the editable Blender assembly,
  authoring scripts, two phase preview images, attribution, and CC BY 4.0 text.
- `metadata/asset-manifest.json`: source archive hashes and the exact extracted
  file inventory, including identical shared files merged during extraction.
- `SHA256SUMS`: SHA-256 hashes of all 35 imported asset files.

The four source ZIPs were extracted without modifying their member bytes.
Nine repeated, byte-identical documentation/metadata entries were merged.
The repository contains the extracted files only; source ZIPs are not duplicated
in Git LFS. The GLBs are self-contained. Original source scripts retain their
authoring-environment paths; read their package documentation before rebuilding.
No generation or rebuild scripts were run during import.

## Earlier collection

The earlier 13 ZIPs (static cardiac meshes/textures, synthetic imaging,
whole-body 2D v4, and Anatomy Workshop 3D r1) are **not included in this commit**.
Their Library entries and Drive checksum records were resolved, but the
supported Mac batch-download helper reported that its Library materialization
action was unavailable. `metadata/earlier-collection.json` records each omitted
archive and expected checksum. `metadata/earlier-README.md` and
`metadata/earlier-SHA256SUMS.txt` preserve the original collection index and
checksums as reference metadata, not as proof that those assets were downloaded.

## Attribution and scope

Preserve the original package notices and license files. The respiratory assets
retain attribution to Jakob Wasserthal, TotalSegmentator contributors, and
University Hospital Basel. No blanket license is added to this repository;
the authored Cardiac Atlas package has no separate public license declaration.
These are simplified educational illustrations; retain the scope and limitations
in each package's README. Original QA reports describe the source delivery and
are not new clinical or visual validation from this sync.

Published viewers remain at
https://heart-anatomy-imaging-lab.landy123007.chatgpt.site/ and
https://heart-anatomy-imaging-lab.landy123007.chatgpt.site/body/3d/.
