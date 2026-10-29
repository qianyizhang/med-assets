# Testis pathway · readable transport summary / 输送路径

The r01 transport strip uses 17px type: about 9.7px when the full diagram is
800px wide. Its internal and between-stage arrows share a single line.
This revision groups the route into five panels, raises primary labels to 24px
(about 13.7px at that teaching size), and explicitly names the epididymis.
The head → body → tail subline is 20px. No anatomical curve or leader moved.

- [English display SVG](testis-pathway-en.svg)
- [中文 display SVG](testis-pathway-zh.svg)
- [Editable sources and bounded builder](../../../../sources/authored/testis_pathway/r02/)
- [Scoped review and exact identities](../../../../reviews/testis_pathway/2026-10-29-r02/readability.json)

🟢 Positive: matched EN/中文 overview and detail review at 800px and native size;
grayscale detail review; zero changed pixels outside the summary; all visible
display lettering outlined. The English export retains r01's empty `text31`
element and its ID. Display SVGs need no external fonts, images or network access.

🟡 Pending: independent visual acceptance and supported viewer/runtime checks.
This is an author-reviewed readability revision, not anatomical or clinical
approval. The [r01 limitations and attribution](../r01/README.md) still apply:
symbolic coils/counts, omitted epididymal duct coiling, no specimen geometry and
no change to passed-organ/3D-study counts. No separate public license is added.

The route labels were screened against NCI SEER's [cross-section](https://training.seer.cancer.gov/testicular/anatomy/cross-section.html)
and [testis anatomy](https://training.seer.cancer.gov/testicular/anatomy/)
on 2026-10-29. No source artwork was copied. Existing OpenStax attribution is
preserved in the diagram and r01 package.

Rebuild from the repository root with Python 3, Inkscape 1.4 and Noto Sans CJK SC /
Noto Sans installed. Use a new output directory:

```sh
python3 sources/authored/testis_pathway/r02/build.py --output /tmp/testis-r02-new
inkscape diagrams/testis_pathway/exports/r02/testis-pathway-en.svg --export-width=800 --export-filename=/tmp/testis-r02-en.png
```

Only the summary fragment is outlined anew; the builder verifies the four frozen
r01 SVG hashes and retains the rest of each document. Review PNGs remain local;
this package adds no binary payload or LFS pointer. The original r01 replay still
targets its frozen r01 exports and receipts.
