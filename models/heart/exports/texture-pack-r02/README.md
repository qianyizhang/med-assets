# Heart · body shell teaching edition

Use the texture-packed shell with the same-case CT cuts to identify the broad ventricular body and its superior segmented extent.

The same one-part 24,000-triangle shell, three PNG textures and translation clip use 1,638,296 GLB bytes, down 398,932 bytes (19.6%). The earlier vertex contractions displaced the ventricular margin. The protected geometry and every texture sample are exact, with no matched pixel differences.

The ventricular body and superior sweep separate in front and reverse views. Axial and coronal s1233 CT/label cuts account for the irregular sweep as the closed heart-label boundary alongside the separate aorta label. The worst upper-quarter mesh vertex was 1.984 mm from its nearest label-isosurface vertex. The upper shell cannot demonstrate vessel openings.

[Teaching plate](../../../../reviews/teaching-assessments/reopen-paired/plates/heart-teaching.webp) · [Original and updated views](../../../../reviews/teaching-assessments/reopen-paired/plates/heart-comparison.webp) · [Replay and evidence](../../../../reviews/teaching-assessments/reopen-paired/README.md) · [Exact input and output](../../../../reviews/teaching-assessments/reopen-paired/build.json)

Jakob Wasserthal and contributors, TotalSegmentator v2.0.1, University Hospital Basel, CC BY 4.0. Workshop author materials and illustrative translation retain their original notices. [Source](https://zenodo.org/records/10047263) · [Attribution and original scope](../metadata-cleanup-r01/README.md)

## Rebuild

From the repository root, use the hydrated source and Python 3.12 and Pillow 11.3.0. The recipe checks the new output against the reviewed SHA-256 and byte count before writing it to a fresh directory.

```sh
python3.12 tools/rebuild_asset.py models/heart/recipes/texture-pack-r02.json .artifacts/rebuild-heart-texture-pack-r02
```
