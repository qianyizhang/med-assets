# Where the source model ends / 源模型到此截断

Two bilingual teaching sheets identify the retained brain model's flat lower
brainstem boundary as a **source cut**. A numbered dashed bracket sits outside the
surface in overview and detail. The detail is a magnified viewport of the same
retained image; no tissue or missing spinal cord is drawn. This implements the
bounded presentation outcome in [#147](https://github.com/qianyizhang/med-assets/issues/147).

| Teaching sheet | Matched Original / Updated |
| --- | --- |
| [Front: both retained medulla surfaces](sheets/front-teaching.svg) | [Front overview and detail](sheets/front-comparison.svg) |
| [Left: brainstem and cerebellum context](sheets/left-teaching.svg) | [Left overview and detail](sheets/left-comparison.svg) |

## Open and print

Open a sheet in Inkscape from a checkout containing the exact retained contact
PNG at `reviews/brain/bodyparts3d-4.0-atlas-r2/screenshots/contact.png`.
The small committed SVGs link that existing image; a text/LFS-pointer-only checkout
or GitHub's restricted SVG preview cannot display the tissue pixels. No new media
or network request is made by the build command.

For a portable local sheet, the builder embeds the verified source PNG once:

```sh
python3 tools/brain_source_cut/build.py --output /tmp/brain-source-cut-NEW --embed
inkscape /tmp/brain-source-cut-NEW/front-teaching.svg \
  --export-text-to-path --export-filename=/tmp/brain-source-cut-NEW/front-teaching.pdf
```

Use Python 3.11+; native exports were inspected with Inkscape 1.4, DejaVu Sans and
Noto Sans CJK SC. The output directory must be new, retaining previous trials.
The builder verifies the exact GLB and PNG hashes before writing, including all
49 meshes and both source medulla node names. The model is read-only throughout.
Portable exports are local deliverables; this PR does not upload binary/LFS media
or publish a Site.

## Review and sources

[Review and exact bindings](../../reviews/brain/2026-10-29-source-cut/README.md)
cover the corrected v2, four matched pairs, grayscale and native PDF inspection.
The normal Chromium launch failed at the environment's SUID sandbox helper;
browser display remains unverified. No security override was used.

The image is the existing exact-GLB reimport render in the
[source review](../../reviews/brain/bodyparts3d-4.0-atlas-r2/final-review.json).
BodyParts3D / Anatomography, © The Database Center for Life Science (DBCLS),
[CC BY 4.0](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html), with
[retained provenance](../../sources/datasets/bp3d-4.0-head-studies/external-source-map.json).
Change: editorial bracket, captions and image viewports, 2026-10-29. Existing
reduced-resolution faceting, display material and omitted anatomy remain.
[OpenStax 13.2](https://openstax.org/books/anatomy-and-physiology-2e/pages/13-2-the-central-nervous-system)
supports the brainstem–spinal cord continuity described in the caption; it does
not identify this source's cut as a normal anatomical boundary. This is a static
teaching presentation, not anatomical/clinical or 3-D runtime approval.
